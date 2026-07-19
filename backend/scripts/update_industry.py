"""
批量更新企业行业分类为申万2021一级行业标准

功能:
1. 调用 sw_industry_mapping.fetch_sw_industry_map() 获取最新申万行业分类映射
2. 网络失败时从本地 sw_industry_backup.json 加载备份
3. 遍历数据库中所有企业，用申万分类更新 Company.industry 字段
4. 统计更新前后的行业分布变化
5. 输出更新失败的股票代码列表

用法:
    python scripts/update_industry.py

说明:
    申万一级行业共31个（含银行、非银金融），但后续分析时需剔除银行和非银金融。
"""
import sys
import io
import json
from pathlib import Path
from collections import Counter

# ---------- Windows 控制台 UTF-8 编码 ----------
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ---------- 路径与模块导入 ----------
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR.parent))

from app.core.database import SessionLocal
from app.models.company import Company, FINANCIAL_INDUSTRIES
from sw_industry_mapping import fetch_sw_industry_map

# 备份文件路径
BACKUP_FILE = BASE_DIR / "sw_industry_backup.json"


def load_backup() -> dict:
    """从本地备份文件加载申万行业映射"""
    if not BACKUP_FILE.exists():
        return {}
    try:
        with open(BACKUP_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"  ⚠️  读取本地备份失败: {e}")
        return {}


def save_backup(mapping: dict) -> bool:
    """保存申万行业映射到本地备份文件"""
    try:
        with open(BACKUP_FILE, "w", encoding="utf-8") as f:
            json.dump(mapping, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"  ⚠️  保存本地备份失败: {e}")
        return False


def get_industry_map() -> dict:
    """获取申万行业映射：优先在线下载，失败则加载本地备份"""
    print("=" * 60)
    print("步骤 1: 获取申万行业分类映射")
    print("=" * 60)

    # 尝试在线下载
    print("  → 尝试在线下载申万行业分类...")
    mapping = fetch_sw_industry_map()

    if mapping:
        print(f"  ✅ 在线下载成功，共 {len(mapping)} 只股票")
        # 保存备份
        if save_backup(mapping):
            print(f"  → 已保存本地备份: {BACKUP_FILE}")
        return mapping

    # 在线失败，加载本地备份
    print("  ⚠️  在线下载失败，尝试加载本地备份...")
    mapping = load_backup()
    if mapping:
        print(f"  ✅ 本地备份加载成功，共 {len(mapping)} 只股票")
    else:
        print("  ❌ 本地备份也不存在或为空，无法继续")
    return mapping


def compute_distribution(companies) -> Counter:
    """统计企业行业分布"""
    return Counter(c.industry for c in companies)


def print_distribution(title: str, dist: Counter, exclude_financial: bool = False):
    """打印行业分布表"""
    print(f"\n--- {title} ---")
    total = sum(dist.values())
    print(f"  企业总数: {total}")

    items = sorted(dist.items(), key=lambda x: (-x[1], x[0]))
    financial_count = 0
    for ind, cnt in items:
        is_fin = ind in FINANCIAL_INDUSTRIES
        if exclude_financial and is_fin:
            financial_count += cnt
            continue
        flag = " [金融-剔除]" if is_fin else ""
        print(f"  {ind:<10}: {cnt:>5}  ({cnt/total*100:5.1f}%){flag}")

    if exclude_financial and financial_count > 0:
        non_fin_total = total - financial_count
        print(f"  --- 剔除金融类后有效企业: {non_fin_total} ---")


def main():
    print("=" * 60)
    print("批量更新企业行业分类为申万2021一级行业标准")
    print("=" * 60)

    # ---------- 步骤1: 获取行业映射 ----------
    industry_map = get_industry_map()
    if not industry_map:
        print("\n❌ 无法获取申万行业映射，脚本终止")
        sys.exit(1)

    # ---------- 步骤2: 查询数据库所有企业 ----------
    print("\n" + "=" * 60)
    print("步骤 2: 查询数据库企业")
    print("=" * 60)

    db = SessionLocal()
    try:
        all_companies = db.query(Company).order_by(Company.id).all()
        total = len(all_companies)
        print(f"  数据库企业总数: {total}")

        if total == 0:
            print("  ⚠️  数据库无企业记录，脚本终止")
            return

        # ---------- 步骤3: 统计更新前的行业分布 ----------
        before_dist = compute_distribution(all_companies)
        print_distribution("更新前行业分布（全部）", before_dist, exclude_financial=False)
        print_distribution("更新前行业分布（剔除金融类）", before_dist, exclude_financial=True)

        # ---------- 步骤4: 遍历并更新 ----------
        print("\n" + "=" * 60)
        print("步骤 3: 批量更新企业行业分类")
        print("=" * 60)

        updated_count = 0
        unchanged_count = 0
        not_in_map_count = 0
        failed_codes = []  # 更新失败的股票代码列表
        progress_interval = max(1, total // 50)  # 每 2% 输出一次进度

        for idx, company in enumerate(all_companies, start=1):
            code = company.stock_code
            old_industry = company.industry

            new_industry = industry_map.get(code)
            if not new_industry:
                not_in_map_count += 1
                failed_codes.append(code)
                if idx % progress_interval == 0 or idx == total:
                    print(f"  进度: {idx}/{total} ({idx/total*100:5.1f}%)  "
                          f"已更新 {updated_count}  未变 {unchanged_count}  "
                          f"未匹配 {not_in_map_count}")
                continue

            if new_industry == old_industry:
                unchanged_count += 1
            else:
                company.industry = new_industry
                updated_count += 1

            # 分批 flush，避免长事务
            if idx % 500 == 0:
                db.flush()

            # 进度输出
            if idx % progress_interval == 0 or idx == total:
                print(f"  进度: {idx}/{total} ({idx/total*100:5.1f}%)  "
                      f"已更新 {updated_count}  未变 {unchanged_count}  "
                      f"未匹配 {not_in_map_count}")

        db.commit()
        print(f"\n  ✅ 数据库已提交")
        print(f"  → 成功更新: {updated_count}")
        print(f"  → 行业未变: {unchanged_count}")
        print(f"  → 未匹配  : {not_in_map_count}")

        # ---------- 步骤5: 统计更新后的行业分布 ----------
        # 重新查询以反映更新后的状态
        db.expire_all()
        all_companies_after = db.query(Company).order_by(Company.id).all()
        after_dist = compute_distribution(all_companies_after)

        print_distribution("更新后行业分布（全部）", after_dist, exclude_financial=False)
        print_distribution("更新后行业分布（剔除金融类）", after_dist, exclude_financial=True)

        # ---------- 步骤6: 行业分布变化对比 ----------
        print("\n" + "=" * 60)
        print("步骤 4: 行业分布变化对比")
        print("=" * 60)
        all_industries = sorted(set(before_dist.keys()) | set(after_dist.keys()))
        print(f"  {'行业':<12}{'更新前':>8}{'更新后':>8}{'变化':>8}")
        print(f"  {'-'*12}{'-'*8}{'-'*8}{'-'*8}")
        for ind in all_industries:
            before_cnt = before_dist.get(ind, 0)
            after_cnt = after_dist.get(ind, 0)
            diff = after_cnt - before_cnt
            diff_str = f"{diff:+d}" if diff != 0 else "0"
            print(f"  {ind:<12}{before_cnt:>8}{after_cnt:>8}{diff_str:>8}")

        # 金融类剔除统计
        before_fin = sum(before_dist.get(i, 0) for i in FINANCIAL_INDUSTRIES)
        after_fin = sum(after_dist.get(i, 0) for i in FINANCIAL_INDUSTRIES)
        before_non_fin = sum(before_dist.values()) - before_fin
        after_non_fin = sum(after_dist.values()) - after_fin
        print(f"\n  金融类企业（剔除范围）: {before_fin} → {after_fin}")
        print(f"  非金融类企业（分析范围）: {before_non_fin} → {after_non_fin}")

        # ---------- 步骤7: 输出失败股票代码 ----------
        print("\n" + "=" * 60)
        print("步骤 5: 更新失败股票代码列表")
        print("=" * 60)
        if failed_codes:
            print(f"  共 {len(failed_codes)} 只股票未在申万行业映射中找到:")
            # 每行10个，便于查看
            for i in range(0, len(failed_codes), 10):
                batch = failed_codes[i:i+10]
                print("  " + "  ".join(batch))
            # 同时保存到文件，便于后续处理
            failed_file = BASE_DIR / "update_industry_failed.txt"
            try:
                with open(failed_file, "w", encoding="utf-8") as f:
                    f.write("\n".join(failed_codes))
                print(f"\n  → 失败列表已保存到: {failed_file}")
            except Exception as e:
                print(f"  ⚠️  保存失败列表文件出错: {e}")
        else:
            print("  ✅ 所有企业均成功更新，无失败记录")

        # ---------- 总结 ----------
        print("\n" + "=" * 60)
        print("更新完成总结")
        print("=" * 60)
        print(f"  数据库企业总数  : {total}")
        print(f"  申万映射股票数  : {len(industry_map)}")
        print(f"  成功更新       : {updated_count}")
        print(f"  行业未变       : {unchanged_count}")
        print(f"  未匹配（失败） : {not_in_map_count}")
        print(f"  申万一级行业数 : {len(after_dist)} "
              f"(其中金融类 {sum(1 for i in after_dist if i in FINANCIAL_INDUSTRIES)} 个将剔除)")

    except Exception as e:
        db.rollback()
        print(f"\n❌ 执行出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
