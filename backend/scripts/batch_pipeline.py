"""
批量年报采集与分析管道 — 模拟论文方法论的全市场覆盖

功能:
1. 遍历数据库中所有符合条件的企业（剔除金融类、ST类）
2. 对每家企业逐一下载 2012-2025 年度年报 PDF（从巨潮资讯）
3. 解析并提取 MD&A 章节
4. 执行语句分类 + 情感打分 + GW 指数计算
5. 结果存入数据库，支持断点续传、进度追踪

用法:
    python scripts/batch_pipeline.py                    # mock 模式，全量处理
    python scripts/batch_pipeline.py --year 2024        # 仅处理指定年份
    python scripts/batch_pipeline.py --company 600519   # 仅处理指定企业
    python scripts/batch_pipeline.py --real             # 真实 LLM 模式（需要 API Key）
    python scripts/batch_pipeline.py --force            # 强制重新分析已处理的记录
    python scripts/batch_pipeline.py --resume           # 从断点继续

论文参考规模:
    - 3600+ 家企业 × 24 年 = 45,104 条观测值
    - 924,617 条环境语句 → 167,316 条描述性语句
    - 三模型一致率 Fleiss' Kappa = 0.84
"""
import sys
import os
import re
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional

# Windows控制台编码修复
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR.parent))

from app.core.database import SessionLocal, init_db
from app.core.config import get_settings
from app.models.company import Company, FINANCIAL_INDUSTRIES
from app.models.analysis import AnalysisRecord
from app.models.sentence import Sentence
from app.services.cninfo_crawler import fetch_report_with_fallback
from app.services.pdf_parser import parse_report_full, get_analysis_text
from app.services.text_utils import split_sentences, filter_env_sentences
from app.services.mock_service import run_mock_analysis
from app.services.industry_service import compute_industry_benchmarks, update_risk_levels, get_industry_median
# GW指数 = max(0, 企业语调 - 行业中位数)，与论文公式一致

# 进度文件路径
PROGRESS_FILE = BASE_DIR / "batch_progress.txt"

# 默认处理年份范围（论文: 2001-2024，系统: 2012-2025）
DEFAULT_YEARS = list(range(2012, 2026))

# 本地 MD&A 数据目录配置（与 analysis_orchestrator 保持一致）
_settings = get_settings()
MDA_ROOT = Path(_settings.mda_root)
MDA_FILE_PATTERN = re.compile(r"^(\d{6})_(.+?)_(\d{4}-\d{2}-\d{2})\.txt$")
TEXT_SUBDIR = "文本"


def load_progress() -> set:
    """加载已完成的 (company_id, year) 集合"""
    if not PROGRESS_FILE.exists():
        return set()
    completed = set()
    with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                parts = line.split(",")
                if len(parts) == 2:
                    completed.add((int(parts[0]), int(parts[1])))
    return completed


def save_progress(company_id: int, year: int):
    """记录完成进度"""
    with open(PROGRESS_FILE, "a", encoding="utf-8") as f:
        f.write(f"{company_id},{year}\n")


def get_companies(db, company_code: str = None) -> list:
    """获取待处理企业列表（剔除金融类、ST类）"""
    query = db.query(Company).filter(
        Company.is_active == True,
        Company.is_st == False,
        Company.industry.notin_(FINANCIAL_INDUSTRIES),
    )
    if company_code:
        query = query.filter(Company.stock_code == company_code)
    return query.order_by(Company.id).all()


def company_has_analysis(db, company_id: int, year: int) -> bool:
    """检查企业某年是否已有分析记录"""
    return db.query(AnalysisRecord).filter(
        AnalysisRecord.company_id == company_id,
        AnalysisRecord.year == year,
        AnalysisRecord.analysis_status == "completed",
    ).count() > 0


def _get_local_mda_text(stock_code: str, year: int) -> str:
    """从本地MD&A数据目录读取指定企业指定年份的MD&A文本

    扫描 MDA_ROOT/{year}/文本/ 目录，找到匹配股票代码的文件。
    文件命名格式：{股票代码}_{公司名}_{日期}.txt
    从指定年份目录查找，找不到则返回空字符串。
    支持 utf-8 和 gbk 编码。
    """
    if not stock_code:
        return ""
    if not MDA_ROOT.exists():
        return ""

    year_dir = MDA_ROOT / str(year)
    text_dir = year_dir / TEXT_SUBDIR
    if not text_dir.exists():
        return ""

    for f in text_dir.iterdir():
        if not f.is_file() or f.suffix.lower() != ".txt":
            continue
        m = MDA_FILE_PATTERN.match(f.name)
        if not m:
            continue
        file_code = m.group(1)
        if file_code == stock_code:
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    return fh.read().strip()
            except UnicodeDecodeError:
                try:
                    with open(f, "r", encoding="gbk") as fh:
                        return fh.read().strip()
                except Exception:
                    return ""
            except Exception:
                return ""
    return ""


def fetch_and_parse_report(company: Company, year: int, use_real_crawler: bool = False) -> tuple:
    """
    获取并解析年报

    Args:
        use_real_crawler: 是否使用真实爬虫（需要网络 + 巨潮资讯可访问）

    Returns:
        (text, data_source_type, key_indicators, error_message)
    """
    if use_real_crawler:
        # 真实模式：尝试巨潮资讯爬虫
        try:
            pdf_bytes, error, ann = fetch_report_with_fallback(company.stock_code, year=year)
            if pdf_bytes and not error:
                parsed = parse_report_full(pdf_bytes, ann.title if ann else "")
                text = get_analysis_text(parsed)
                data_source = "MD&A"
                key_indicators = parsed.key_indicators
                return text, data_source, key_indicators, None
            else:
                return "", "", [], error or "无法获取年报"
        except Exception as e:
            return "", "", [], str(e)
    else:
        # 本地模式：从MD&A根目录读取文本
        text = _get_local_mda_text(company.stock_code, year)
        return text, "MD&A", [], None


def _normalize_is_latest_for_company(db, company_id: int):
    """规范化企业分析记录的 is_latest 标记：年份最大的那条为 latest（同年取最新记录）"""
    records = (
        db.query(AnalysisRecord)
        .filter(
            AnalysisRecord.company_id == company_id,
            AnalysisRecord.analysis_status == "completed",
        )
        .order_by(AnalysisRecord.year.desc(), AnalysisRecord.id.desc())
        .all()
    )
    if not records:
        return
    latest_id = records[0].id
    for r in records:
        r.is_latest = (r.id == latest_id)


def run_analysis_for_company_year(
    db,
    company: Company,
    year: int,
    use_real_llm: bool = False,
    use_real_crawler: bool = False,
) -> Optional[AnalysisRecord]:
    """
    对单个企业在单一年份执行完整分析流程（阶段1：先不计算GW，阶段3统一回填）

    Returns:
        AnalysisRecord 或 None（失败时）
    """
    # 1. 获取文本（本地MD&A文件）
    text, data_source, key_indicators, fetch_error = fetch_and_parse_report(company, year, use_real_crawler)
    if fetch_error or not text or len(text.strip()) < 50:
        print(f"  [FAIL] {company.stock_code} {company.company_name} {year}年 文本获取失败: {fetch_error or '内容过短'}")
        return None

    # 2. 语句切分与环保关键词过滤
    raw_sentences = split_sentences(text)
    if not raw_sentences:
        raw_sentences = [text]
    env_sentences, _ = filter_env_sentences(raw_sentences)

    if not env_sentences:
        print(f"  [WARN] {company.stock_code} {company.company_name} {year}年 无环境关键词语句（共{len(raw_sentences)}句），跳过")
        return None

    # 3. 分类与情感打分
    if use_real_llm:
        try:
            from app.services.analysis_orchestrator import AnalysisOrchestrator
            import asyncio
            result = asyncio.run(
                AnalysisOrchestrator._run_real_classification(env_sentences, company.industry, db)
            )
        except Exception as e:
            print(f"  [FAIL] {company.stock_code} {company.company_name} {year}年 LLM分类失败: {e}")
            return None
    else:
        # 阶段1先不计算GW，industry_median=None（阶段3统一回填）
        result = run_mock_analysis(text, company.industry, industry_median=None)

    # 4. 计算语调分数
    descriptive_results = [
        r for r in result["sentence_results"]
        if r["final_category"] == "descriptive"
    ]
    if descriptive_results:
        tone_score = sum(r["sentiment_score"] for r in descriptive_results) / len(descriptive_results)
    else:
        tone_score = 0.5

    # 5. 阶段1先不计算GW指数，gw_index 和 industry_median_tone 临时设为 0.0，阶段3统一回填
    gw_index = 0.0
    industry_median = 0.0

    # 6. 保存到数据库
    # 先将同年旧记录标记为非最新（避免重复 latest）
    db.query(AnalysisRecord).filter(
        AnalysisRecord.company_id == company.id,
        AnalysisRecord.year == year,
        AnalysisRecord.is_latest == True,
    ).update({"is_latest": False})

    record = AnalysisRecord(
        company_id=company.id,
        year=year,
        data_source_type=data_source,
        total_sentences=result["total_sentences"],
        env_sentences=result["env_sentences"],
        substantive_count=result["substantive_count"],
        descriptive_count=result["descriptive_count"],
        non_env_count=result["non_env_count"],
        tone_score=round(tone_score, 6),
        industry_median_tone=round(industry_median, 6),
        gw_index=round(gw_index, 6),
        risk_level="正常",
        fleiss_kappa=result["fleiss_kappa"],
        dispute_count=result["divergence_count"],
        analysis_status="completed",
        is_latest=False,  # 先设为 False，下方规范化
        analyzed_at=datetime.now(),
    )
    db.add(record)
    db.flush()

    # 7. 规范化 is_latest：该企业所有分析记录中年份最大的那条为 latest
    _normalize_is_latest_for_company(db, company.id)

    # 8. 保存语句（仅最新记录保存完整语句，节省空间）
    if record.is_latest:
        for s in result["sentence_results"]:
            sentence = Sentence(
                analysis_record_id=record.id,
                sentence_text=s["sentence_text"],
                sentence_order=s["sentence_order"],
                deepseek_result=s["deepseek_result"],
                qwen_result=s["qwen_result"],
                glm_result=s["glm_result"],
                final_category=s["final_category"],
                vote_type=s["vote_type"],
                confidence=s["confidence"],
                sentiment_score=s["sentiment_score"],
                sentiment_std=s["sentiment_std"],
                needs_review=s["needs_review"],
            )
            db.add(sentence)

    db.commit()
    return record


def run_batch_pipeline(
    years: list = None,
    company_code: str = None,
    use_real_llm: bool = False,
    use_real_crawler: bool = False,
    force_refresh: bool = False,
    resume: bool = True,
    delay_between_companies: float = 0.0,
):
    """
    批量处理主函数（两阶段流程）

    阶段1：遍历所有企业×所有年份，读取本地MD&A文本，运行 run_mock_analysis，
           保存分析记录（tone_score 已计算，gw_index 临时为 0.0）
    阶段2：所有企业分析完成后，对每个年份调用 compute_industry_benchmarks 计算真实行业基准
    阶段3：用真实行业基准回填所有记录的 gw_index = max(0, tone_score - industry_median)
           和 industry_median_tone
    阶段4：调用 update_risk_levels 更新风险等级

    Args:
        years: 要处理的年份列表
        company_code: 仅处理指定企业（None = 全量）
        use_real_llm: 是否使用真实 LLM（需要 API Key）
        use_real_crawler: 是否使用真实爬虫（需要网络 + 巨潮资讯可访问）
        force_refresh: 是否强制重新分析
        resume: 是否从断点继续
        delay_between_companies: 企业间延迟（秒），读取本地文件无需延迟，默认 0
    """
    if years is None:
        years = DEFAULT_YEARS

    init_db()
    db = SessionLocal()

    # 加载进度
    completed = load_progress() if resume else set()

    # 获取企业列表
    companies = get_companies(db, company_code)
    total_companies = len(companies)
    total_tasks = total_companies * len(years)

    print("=" * 60)
    print("  批量年报采集与分析管道（两阶段流程）")
    print("=" * 60)
    print(f"  企业总数: {total_companies}")
    print(f"  年份范围: {years[0]}-{years[-1]} ({len(years)}年)")
    print(f"  总任务数: {total_tasks}")
    print(f"  LLM模式: {'真实LLM' if use_real_llm else 'Mock模拟'}")
    print(f"  文本来源: {'真实爬虫' if use_real_crawler else '本地MD&A文件'}")
    print(f"  MD&A根目录: {MDA_ROOT}")
    print(f"  断点续传: {'开启' if resume else '关闭'}")
    print(f"  强制刷新: {'开启' if force_refresh else '关闭'}")
    print(f"  已完成: {len(completed)} 条")
    print("=" * 60)
    print()

    # ========== 阶段1：遍历企业×年份，读取本地MD&A并分析 ==========
    print("【阶段1】读取本地MD&A文本并执行分析...")
    print("-" * 60)

    processed = 0
    skipped = 0
    failed = 0
    start_time = time.time()

    for idx, company in enumerate(companies):
        for year in years:
            task_key = (company.id, year)

            # 跳过已完成的
            if task_key in completed:
                skipped += 1
                continue

            # 跳过已有分析（非强制模式）
            if not force_refresh and company_has_analysis(db, company.id, year):
                save_progress(company.id, year)
                skipped += 1
                continue

            # 执行分析
            record = run_analysis_for_company_year(db, company, year, use_real_llm, use_real_crawler)
            if record:
                save_progress(company.id, year)
                processed += 1
                print(f"[{idx + 1}/{total_companies}] {company.stock_code} {company.company_name} {year} "
                      f"GW={record.gw_index:.4f} tone={record.tone_score:.4f} "
                      f"{record.substantive_count}实/{record.descriptive_count}描/{record.non_env_count}非")
            else:
                failed += 1

    stage1_elapsed = time.time() - start_time
    print("-" * 60)
    print(f"  阶段1完成: 成功 {processed}  跳过 {skipped}  失败 {failed}  耗时 {stage1_elapsed/60:.1f} 分钟")
    print()

    # ========== 阶段2：计算各年份真实行业基准 ==========
    print("【阶段2】计算各年份行业基准...")
    print("-" * 60)
    for year in years:
        compute_industry_benchmarks(db, year)
        print(f"  {year}年 行业基准计算完成")
    db.commit()
    print()

    # ========== 阶段3：回填 gw_index 和 industry_median_tone ==========
    print("【阶段3】回填GW指数和行业中位数...")
    print("-" * 60)
    backfilled = 0
    affected_companies = set()
    for year in years:
        records = (
            db.query(AnalysisRecord)
            .join(Company, AnalysisRecord.company_id == Company.id)
            .filter(
                AnalysisRecord.year == year,
                AnalysisRecord.analysis_status == "completed",
                AnalysisRecord.tone_score.isnot(None),
            )
            .all()
        )
        for r in records:
            industry_median = get_industry_median(db, r.company.industry, year)
            r.industry_median_tone = round(industry_median, 6)
            r.gw_index = round(max(0.0, (r.tone_score or 0.0) - industry_median), 6)
            backfilled += 1
            affected_companies.add(r.company_id)
    db.commit()
    print(f"  回填记录数: {backfilled}")

    # 规范化 is_latest（覆盖断点续传的旧记录）
    for cid in affected_companies:
        _normalize_is_latest_for_company(db, cid)
    db.commit()
    print(f"  is_latest 规范化完成（{len(affected_companies)} 家企业）")
    print()

    # ========== 阶段4：更新风险等级 ==========
    print("【阶段4】更新风险等级...")
    print("-" * 60)
    for year in years:
        update_risk_levels(db, year)
        print(f"  {year}年 风险等级更新完成")
    print()

    total_elapsed = time.time() - start_time
    print("=" * 60)
    print(f"  [DONE] 批量处理完成！")
    print(f"  成功: {processed}  跳过: {skipped}  失败: {failed}")
    print(f"  回填: {backfilled}  企业: {len(affected_companies)}")
    print(f"  总耗时: {total_elapsed/60:.1f} 分钟")
    print("=" * 60)

    db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="批量年报采集与分析管道")
    parser.add_argument("--year", type=int, help="仅处理指定年份")
    parser.add_argument("--years", type=str, help="年份范围，如 '2020-2024'")
    parser.add_argument("--company", type=str, help="仅处理指定股票代码")
    parser.add_argument("--real", action="store_true", help="使用真实 LLM（需要 API Key）")
    parser.add_argument("--crawler", action="store_true", help="使用真实爬虫（需要网络）")
    parser.add_argument("--force", action="store_true", help="强制重新分析")
    parser.add_argument("--no-resume", action="store_true", help="不从断点继续")
    parser.add_argument("--delay", type=float, default=0.0, help="企业间延迟（秒），读取本地文件无需延迟")

    args = parser.parse_args()

    # 解析年份
    if args.year:
        years = [args.year]
    elif args.years:
        parts = args.years.split("-")
        years = list(range(int(parts[0]), int(parts[1]) + 1))
    else:
        years = DEFAULT_YEARS

    run_batch_pipeline(
        years=years,
        company_code=args.company,
        use_real_llm=args.real,
        use_real_crawler=args.crawler,
        force_refresh=args.force,
        resume=not args.no_resume,
        delay_between_companies=args.delay,
    )
