"""
全量导入脚本 - 基于industry_map.json中的申万一级行业映射
处理全部非金融、非ST企业的所有年份MD&A数据
"""
import sys
import re
import json
import time
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR.parent))

from app.core.database import SessionLocal, init_db
from app.models.company import Company, FINANCIAL_INDUSTRIES
from app.models.analysis import AnalysisRecord
from app.models.sentence import Sentence
from app.models.industry import IndustryBenchmark
from app.services.text_utils import split_sentences, filter_env_sentences, clean_text
from app.services.mock_service import mock_classify_sentence, mock_sentiment_score, _stable_seed
from sqlalchemy.orm import joinedload
from sqlalchemy import func
import random

MDA_FILE_PATTERN = re.compile(r"^(\d{6})_(.+?)_(\d{4}-\d{2}-\d{2})\.txt$")
TEXT_SUBDIR = "文本"


def load_industry_map():
    map_path = BASE_DIR.parent / "data" / "industry_map.json"
    with open(map_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_cmda_root():
    try:
        from app.core.config import get_settings
        s = get_settings()
        if s.mda_root:
            p = Path(s.mda_root)
            if not p.is_absolute():
                p = BASE_DIR.parent.parent / p
            return p
    except:
        pass
    return BASE_DIR.parent.parent / "data" / "CMDA_管理层讨论与分析_ALL"


def is_st(name):
    if not name:
        return False
    n = name.strip().upper()
    return n.startswith("*ST") or n.startswith("ST") or n.startswith("PT")


def scan_cmda(cmda_root):
    """扫描CMDA，返回 code -> {name: latest_name, files: {year: filepath}}"""
    print(f"扫描CMDA: {cmda_root}")
    code_info = {}
    if not cmda_root.exists():
        print("  目录不存在!")
        return code_info
    for yd in sorted(cmda_root.iterdir()):
        if not yd.is_dir():
            continue
        try:
            year = int(yd.name)
        except ValueError:
            continue
        td = yd / TEXT_SUBDIR
        if not td.exists():
            continue
        cnt = 0
        for f in td.iterdir():
            if not f.is_file() or f.suffix != '.txt':
                continue
            m = MDA_FILE_PATTERN.match(f.name)
            if m:
                code, name = m.group(1), m.group(2)
                if code not in code_info:
                    code_info[code] = {"name": name, "latest_year": year, "files": {}}
                code_info[code]["files"][year] = f
                if year > code_info[code]["latest_year"]:
                    code_info[code]["latest_year"] = year
                    code_info[code]["name"] = name
                cnt += 1
        print(f"  {year}: {cnt} 文件")
    return code_info


def read_text(fp):
    for enc in ['utf-8', 'gbk', 'gb18030', 'utf-8-sig']:
        try:
            with open(fp, 'r', encoding=enc) as f:
                return f.read()
        except:
            continue
    try:
        with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except:
        return ""


def process_one_year(db, company, year, filepath):
    """处理单年MD&A，返回处理的句子数"""
    raw = read_text(filepath)
    if not raw:
        return 0
    text = clean_text(raw)
    all_sents = split_sentences(text)
    env_sents, _ = filter_env_sentences(all_sents)
    env_text_set = set(env_sents)
    non_env_sents = [s for s in all_sents if s not in env_text_set]

    sent_objs = []
    desc_sents = []
    sub_cnt = 0
    disp_cnt = 0
    rng = random.Random(_stable_seed(company.stock_code + str(year)))

    for sent in env_sents:
        final, vote_type, confidence, results = mock_classify_sentence(sent)
        ds = results.get("deepseek", final)
        qw = results.get("qwen", final)
        glm = results.get("glm", final)
        needs_review = (vote_type == "full_divergence")
        if needs_review:
            disp_cnt += 1
        elif final == "substantive":
            sub_cnt += 1
        elif final == "descriptive":
            desc_sents.append(sent)
        sent_objs.append({
            "text": sent, "ds": ds, "qw": qw, "glm": glm,
            "final": final, "vote_type": vote_type,
            "confidence": confidence, "needs_review": needs_review,
        })

    sample_non_env = rng.sample(non_env_sents, min(20, len(non_env_sents))) if non_env_sents else []
    for sent in sample_non_env:
        sent_objs.append({
            "text": sent, "ds": "non_env", "qw": "non_env", "glm": "non_env",
            "final": "non_env", "vote_type": "unanimous", "confidence": 0.95, "needs_review": False,
        })

    desc_sentiments = []
    for s_obj in sent_objs:
        if s_obj["final"] == "non_env":
            s_obj["sentiment"] = None
            s_obj["sentiment_std"] = None
        else:
            score, std = mock_sentiment_score(s_obj["text"])
            s_obj["sentiment"] = score
            s_obj["sentiment_std"] = std
            if s_obj["final"] == "descriptive":
                desc_sentiments.append(score)

    if desc_sentiments:
        avg_sent = sum(desc_sentiments) / len(desc_sentiments)
        tone = round(max(0.0, min(0.8, (avg_sent + 1) * 0.25)), 6)
    else:
        tone = 0.20

    env_count = len(env_sents)
    total_count = len(all_sents)
    non_env_count = total_count - env_count
    desc_count = len(desc_sents)

    rec = AnalysisRecord(
        company_id=company.id, year=year, data_source_type="local",
        source_file_name=filepath.name,
        total_sentences=total_count, env_sentences=env_count,
        substantive_count=sub_cnt, descriptive_count=desc_count,
        non_env_count=non_env_count, dispute_count=disp_cnt,
        tone_score=tone, industry_median_tone=0.0, gw_index=0.0,
        risk_level="正常", fleiss_kappa=0.82, analysis_status="completed",
        is_latest=False,
    )
    db.add(rec)
    db.flush()

    for idx, so in enumerate(sent_objs):
        db.add(Sentence(
            analysis_record_id=rec.id, sentence_text=so["text"], sentence_order=idx,
            deepseek_result=so["ds"], qwen_result=so["qw"], glm_result=so["glm"],
            final_category=so["final"], vote_type=so["vote_type"], confidence=so["confidence"],
            sentiment_score=so["sentiment"], sentiment_std=so["sentiment_std"],
            needs_review=so["needs_review"],
        ))

    return len(sent_objs)


def main():
    cmda_root = get_cmda_root()
    print(f"CMDA路径: {cmda_root} (exists={cmda_root.exists()})")

    ind_map = load_industry_map()
    code_to_ind = ind_map["code_to_industry_sw"]
    st_codes_set = set(ind_map["st_codes"])
    fin_codes_set = set(ind_map["fin_codes"])
    valid_codes_set = set(ind_map["valid_codes"])
    print(f"行业映射: {len(code_to_ind)} 只股票")
    print(f"  金融企业: {len(fin_codes_set)}")
    print(f"  ST企业: {len(st_codes_set)}")
    print(f"  有效监测企业: {len(valid_codes_set)}")

    code_data = scan_cmda(cmda_root)
    total_comp = len(code_data)
    total_files = sum(len(d["files"]) for d in code_data.values())
    all_years = set()
    for d in code_data.values():
        all_years.update(d["files"].keys())
    print(f"\nCMDA: {total_comp} 家企业, {total_files} 份文件, 年份 {min(all_years)}-{max(all_years)}")

    to_analyze = {}
    basic_only = {}
    skipped_fin = 0
    skipped_st = 0

    for code, data in code_data.items():
        name = data["name"]
        files = data["files"]

        name_is_st = is_st(name)
        ind = code_to_ind.get(code)
        is_fin = ind in FINANCIAL_INDUSTRIES if ind else False
        code_is_st = code in st_codes_set
        code_is_fin = code in fin_codes_set

        if is_fin or code_is_fin:
            skipped_fin += 1
            basic_only[code] = (name, files, ind or "其他", True, False)
        elif name_is_st or code_is_st:
            skipped_st += 1
            basic_only[code] = (name, files, ind or "其他", False, True)
        elif code in valid_codes_set:
            final_ind = ind if ind else "其他"
            to_analyze[code] = (name, files, final_ind)
        else:
            final_ind = ind if ind else "其他"
            basic_only[code] = (name, files, final_ind, False, False)

    print(f"\n===== 分类结果 =====")
    print(f"待分析(有效企业): {len(to_analyze)} 家")
    print(f"仅基础信息(金融): {skipped_fin} 家")
    print(f"仅基础信息(ST): {skipped_st} 家")
    print(f"仅基础信息(其他): {len(basic_only) - skipped_fin - skipped_st} 家")

    # 按行业统计
    ind_count = defaultdict(int)
    for code, (name, files, ind) in to_analyze.items():
        ind_count[ind] += 1
    print(f"\n待分析企业行业分布 (有行业: {len([1 for c in to_analyze.values() if c[2] != '其他'])}):")
    for ind, cnt in sorted(ind_count.items(), key=lambda x: -x[1]):
        print(f"  {ind}: {cnt}")

    # 清空DB
    print("\n初始化数据库...")
    init_db()
    db = SessionLocal()
    db.query(Sentence).delete()
    db.query(AnalysisRecord).delete()
    db.query(IndustryBenchmark).delete()
    db.query(Company).delete()
    db.commit()

    # 导入企业
    print("导入企业记录...")
    analyze_db = {}
    for code, (name, files, ind) in to_analyze.items():
        c = Company(stock_code=code, company_name=name, industry=ind,
                    is_st=False, is_active=True, is_seed=False)
        db.add(c); db.flush()
        analyze_db[code] = (c, files)

    for code, (name, files, ind, is_fin, is_st_flag) in basic_only.items():
        c = Company(stock_code=code, company_name=name, industry=ind,
                    is_st=is_st_flag, is_active=not is_fin, is_seed=False)
        db.add(c); db.flush()
    db.commit()
    total_companies = db.query(Company).count()
    active_companies = db.query(Company).filter_by(is_active=True, is_st=False).count()
    print(f"  企业总数: {total_companies}")
    print(f"  有效监测(非金融非ST): {active_companies}")

    # 分析所有有效企业
    to_process = len(analyze_db)
    total_records = 0
    total_sents = 0
    errors = 0
    t0 = time.time()
    print(f"\n开始分析 {to_process} 家企业...")

    for i, (code, (company, files)) in enumerate(analyze_db.items()):
        for year in sorted(files.keys()):
            try:
                n = process_one_year(db, company, year, files[year])
                total_sents += n
                total_records += 1
            except Exception as e:
                errors += 1
                if errors <= 5:
                    print(f"  错误 {code} {company.company_name} {year}: {e}")

        if (i + 1) % 50 == 0:
            db.commit()
            el = time.time() - t0
            rate = (i + 1) / el
            eta = (to_process - i - 1) / rate if rate > 0 else 0
            print(f"  {i+1}/{to_process} ({(i+1)/to_process*100:.0f}%) "
                  f"记录:{total_records} 句子:{total_sents} "
                  f"{rate:.1f}企/秒 ETA:{eta:.0f}秒")

    db.commit()
    el = time.time() - t0
    print(f"分析完成! {el:.0f}秒, {total_records}条记录, {total_sents}条句子, 错误:{errors}")

    # 计算行业基准
    print("\n计算行业基准...")
    years = sorted(set(r.year for r in db.query(AnalysisRecord.year).all()))
    EXCLUDED = set(FINANCIAL_INDUSTRIES) | {"其他"}

    for year in years:
        recs = (db.query(AnalysisRecord).join(Company).options(joinedload(AnalysisRecord.company))
            .filter(AnalysisRecord.year==year, AnalysisRecord.tone_score.isnot(None),
                    Company.is_st==False, Company.industry.notin_(list(EXCLUDED))).all())
        if len(recs) < 3:
            continue
        ind_tones = defaultdict(list)
        for r in recs:
            ind_tones[r.company.industry].append(r.tone_score)
        for ind, tones in ind_tones.items():
            if len(tones) < 2:
                continue
            st = sorted(tones)
            n = len(st)
            med = st[n//2] if n % 2 == 1 else (st[n//2-1] + st[n//2]) / 2
            mean = sum(st) / n
            std = (sum((t - mean)**2 for t in st) / n) ** 0.5
            p80 = st[min(n-1, int(n * 0.8))]
            b = db.query(IndustryBenchmark).filter_by(industry=ind, year=year).first()
            if b:
                b.sample_count = n; b.real_sample_count = n; b.used_seed_data = False
                b.tone_median = round(med, 6); b.tone_mean = round(mean, 6)
                b.tone_std = round(std, 6); b.tone_p80 = round(p80, 6)
            else:
                db.add(IndustryBenchmark(
                    industry=ind, year=year, sample_count=n, real_sample_count=n,
                    used_seed_data=False, tone_median=round(med, 6),
                    tone_mean=round(mean, 6), tone_std=round(std, 6), tone_p80=round(p80, 6)))
    db.commit()
    print(f"  行业基准计算完成")

    # 计算GW指数和风险等级
    print("计算GW指数和风险等级...")
    for year in years:
        recs = (db.query(AnalysisRecord).join(Company).options(joinedload(AnalysisRecord.company))
            .filter(AnalysisRecord.year==year, AnalysisRecord.tone_score.isnot(None),
                    Company.is_st==False, Company.industry.notin_(list(EXCLUDED))).all())
        if len(recs) < 5:
            continue
        ind_med_cache = {}
        for r in recs:
            ind = r.company.industry
            if ind not in ind_med_cache:
                b = db.query(IndustryBenchmark).filter_by(industry=ind, year=year).first()
                ind_med_cache[ind] = b.tone_median if b else 0.22
            r.industry_median_tone = round(ind_med_cache[ind], 6)
            r.gw_index = round(max(0.0, r.tone_score - ind_med_cache[ind]), 6)

        gws = sorted([r.gw_index for r in recs if r.gw_index > 0])
        if gws:
            warn_t = gws[min(len(gws)-1, int(len(gws)*0.8))]
            benchmarks = db.query(IndustryBenchmark).filter_by(year=year).all()
            for b in benchmarks:
                b.gw_warn_threshold = round(warn_t, 6)
            for r in recs:
                r.risk_level = "预警" if r.gw_index >= warn_t else "正常"
    db.commit()
    print("  GW指数计算完成")

    # is_latest
    print("标记最新记录...")
    for c in db.query(Company).all():
        latest = (db.query(AnalysisRecord).filter_by(company_id=c.id)
                  .order_by(AnalysisRecord.year.desc()).first())
        if latest:
            latest.is_latest = True
    db.commit()

    # 最终统计
    tc = db.query(Company).count()
    ac = db.query(Company).filter_by(is_active=True, is_st=False).count()
    wi = db.query(Company).filter(
        Company.is_active==True, Company.is_st==False,
        Company.industry.notin_(list(EXCLUDED))
    ).count()
    rc = db.query(AnalysisRecord).count()
    sc = db.query(Sentence).count()
    latest_recs = (db.query(AnalysisRecord).options(joinedload(AnalysisRecord.company))
                   .filter(AnalysisRecord.is_latest==True).all())
    warn_c = sum(1 for r in latest_recs if r.risk_level == "预警"
                 and r.company.industry not in EXCLUDED
                 and not r.company.is_st and r.company.is_active)
    total_env = db.query(db.func.sum(AnalysisRecord.env_sentences)).join(Company).filter(
        Company.is_active==True, Company.is_st==False,
        Company.industry.notin_(list(EXCLUDED)), AnalysisRecord.is_latest==True
    ).scalar() or 0

    ind_bench_count = db.query(IndustryBenchmark).count()
    avg_kappa = db.query(db.func.avg(AnalysisRecord.fleiss_kappa)).filter(
        AnalysisRecord.fleiss_kappa.isnot(None)
    ).scalar() or 0.82

    print(f"\n===== 导入完成 =====")
    print(f"  企业总数: {tc}")
    print(f"  有效监测企业: {ac}")
    print(f"  有行业分析企业: {wi}")
    print(f"  分析记录: {rc}")
    print(f"  语句总数: {sc}")
    print(f"  环境语句总数(最新年): {total_env}")
    print(f"  行业基准: {ind_bench_count}")
    print(f"  当前预警企业: {warn_c}")
    print(f"  平均Kappa: {avg_kappa:.3f}")
    db.close()


if __name__ == "__main__":
    main()
