"""
根据 GW指数_其他类企业申万行业重分类.md 更新企业行业分类
1. 将 md 中 358 家企业按名称匹配更新行业
2. 将 5 家非银金融剔除企业和 52 家退市股标记为 active=False
3. 重新计算行业基准与 GW 指数
"""
import sys
import re
import json
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR / "backend"))

from app.core.database import SessionLocal
from app.models.company import Company, FINANCIAL_INDUSTRIES
from app.models.analysis import AnalysisRecord
from app.models.industry import IndustryBenchmark
from app.services.industry_service import compute_industry_benchmarks, update_risk_levels, get_industry_median, _update_warn_thresholds
from sqlalchemy import func
from sqlalchemy.orm import joinedload

MD_PATH = BASE_DIR / "GW指数_其他类企业申万行业重分类.md"


def parse_md(path):
    md = open(path, 'r', encoding='utf-8').read()
    sections = re.split(r'\n##\s+', md)
    name_to_industry = {}
    excluded_non_fin = []
    excluded_delisted = []
    current_excluded = None

    for sec in sections[1:]:
        lines = sec.strip().split('\n')
        title_line = lines[0].strip()

        if title_line.startswith('已剔除企业清单'):
            for line in lines[1:]:
                line = line.strip()
                if line.startswith('### 非银金融'):
                    current_excluded = excluded_non_fin
                    continue
                elif line.startswith('### 退市股'):
                    current_excluded = excluded_delisted
                    continue
                if line.startswith('- ') and current_excluded is not None:
                    current_excluded.append(line[2:].strip())
            continue

        industry = title_line.split('（')[0].strip()
        for line in lines:
            line = line.strip()
            if not line.startswith('|'):
                continue
            parts = [p.strip() for p in line.split('|')]
            parts = [p for p in parts if p]
            if len(parts) >= 2 and parts[0] != '企业名称' and '---' not in parts[0]:
                name_to_industry[parts[0]] = industry

    return name_to_industry, excluded_non_fin, excluded_delisted


def main():
    name_to_industry, excluded_non_fin, excluded_delisted = parse_md(MD_PATH)
    print(f"分类企业: {len(name_to_industry)} 家")
    print(f"剔除非银金融: {len(excluded_non_fin)} 家")
    print(f"剔除退市股: {len(excluded_delisted)} 家")

    db = SessionLocal()
    try:
        all_companies = db.query(Company).all()
        name_to_company = {c.company_name: c for c in all_companies}

        # 1. 更新 358 家企业行业
        updated = 0
        not_found_in_md = []
        for name, industry in name_to_industry.items():
            c = name_to_company.get(name)
            if not c:
                not_found_in_md.append(name)
                continue
            if c.industry != industry:
                c.industry = industry
                updated += 1
        print(f"  更新行业企业: {updated} 家")
        if not_found_in_md:
            print(f"  未在数据库中找到: {len(not_found_in_md)} 家")

        # 2. 标记剔除企业为 inactive
        excluded_names = set(excluded_non_fin) | set(excluded_delisted)
        excluded_updated = 0
        for name in excluded_names:
            c = name_to_company.get(name)
            if c and c.is_active:
                c.is_active = False
                excluded_updated += 1
        print(f"  标记剔除企业 inactive: {excluded_updated} 家")

        # 同时按名称中的 ST/*ST/PT 标记 is_st（如果存在且未标记）
        st_pattern = re.compile(r'^(\*ST|ST|PT)')
        st_updated = 0
        for c in all_companies:
            if st_pattern.match(c.company_name) and not c.is_st:
                c.is_st = True
                st_updated += 1
        print(f"  标记 ST/*ST/PT 企业: {st_updated} 家")

        db.commit()

        # 3. 重新计算行业基准与 GW 指数
        print("\n重新计算行业基准...")
        EXCLUDED = set(FINANCIAL_INDUSTRIES) | {"其他"}
        years = sorted({y[0] for y in db.query(AnalysisRecord.year).distinct().all()})

        for year in years:
            compute_industry_benchmarks(db, year)
        db.commit()
        print("  行业基准计算完成")

        print("重新计算 GW 指数...")
        for year in years:
            recs = (
                db.query(AnalysisRecord)
                .join(Company, AnalysisRecord.company_id == Company.id)
                .options(joinedload(AnalysisRecord.company))
                .filter(
                    AnalysisRecord.year == year,
                    AnalysisRecord.tone_score.isnot(None),
                    Company.is_st == False,
                    Company.industry.notin_(list(EXCLUDED)),
                )
                .all()
            )
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
                warn_t = gws[min(len(gws) - 1, int(len(gws) * 0.8))]
                benchmarks = db.query(IndustryBenchmark).filter_by(year=year).all()
                for b in benchmarks:
                    b.gw_warn_threshold = round(warn_t, 6)
                for r in recs:
                    r.risk_level = "预警" if r.gw_index >= warn_t else "正常"
        db.commit()
        print("  GW 指数计算完成")

        # 4. 更新 is_latest
        print("更新最新记录标记...")
        for c in db.query(Company).all():
            latest = (
                db.query(AnalysisRecord)
                .filter_by(company_id=c.id)
                .order_by(AnalysisRecord.year.desc())
                .first()
            )
            if latest:
                latest.is_latest = True
        db.commit()

        # 5. 最终统计
        total = db.query(func.count(Company.id)).scalar()
        active = db.query(func.count(Company.id)).filter(
            Company.is_active == True, Company.is_st == False
        ).scalar()
        monitored = db.query(func.count(Company.id)).filter(
            Company.is_active == True,
            Company.is_st == False,
            Company.industry.notin_(list(FINANCIAL_INDUSTRIES)),
        ).scalar()
        covered = db.query(func.count(Company.id)).filter(
            Company.is_active == True,
            Company.is_st == False,
            Company.industry.notin_(list(FINANCIAL_INDUSTRIES)),
            Company.industry != "其他",
        ).scalar()
        other_active = db.query(func.count(Company.id)).filter(
            Company.is_active == True,
            Company.is_st == False,
            Company.industry == "其他",
        ).scalar()

        print(f"\n===== 更新完成 =====")
        print(f"企业总数: {total}")
        print(f"活跃非ST企业: {active}")
        print(f"实时监测企业(剔除金融): {monitored}")
        print(f"覆盖企业(有具体行业): {covered}")
        print(f"其他行业活跃企业: {other_active}")

    except Exception as e:
        db.rollback()
        print(f"更新失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
