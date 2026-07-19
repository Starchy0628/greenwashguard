"""
根据申万一级行业分类_已剔除ST退市.xlsx 重新处理并统计各行业企业数量
1. 读取xlsx文件中"公司列表"sheet的数据
2. 严格剔除名称中包含"ST"、"*ST"、"PT"的风险企业
3. 更新数据库中企业的行业分类
4. 统计并打印各行业企业数量
"""
import sys
import os
import re
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

# 配置路径
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.models.company import Company, FINANCIAL_INDUSTRIES

# xlsx文件路径
XLSX_PATH = BASE_DIR.parent / "data" / "申万一级行业分类_已剔除ST退市.xlsx"
# SQLite数据库路径
DB_PATH = BASE_DIR.parent / "data" / "db" / "greenwash_guard.db"


def is_risk_company(name: str) -> bool:
    """判断是否为风险企业（ST/*ST/PT）"""
    if not name or not isinstance(name, str):
        return False
    name = name.strip().upper()
    # 严格匹配 ST、*ST、PT 标识
    patterns = [
        r'^\*?ST',           # 开头的 *ST 或 ST
        r'\s\*?ST',          # 中间含 *ST 或 ST
        r'^PT',              # 开头的 PT
        r'\sPT',             # 中间含 PT
        r'\*ST',             # 任意位置含 *ST
    ]
    for pattern in patterns:
        if re.search(pattern, name):
            return True
    return False


def main():
    if not XLSX_PATH.exists():
        print(f"错误: xlsx文件不存在 - {XLSX_PATH}")
        return

    if not DB_PATH.exists():
        print(f"错误: 数据库不存在 - {DB_PATH}")
        return

    print("=" * 60)
    print("申万一级行业分类数据处理")
    print("=" * 60)

    # 1. 读取xlsx数据
    print(f"\n[1] 读取xlsx文件: {XLSX_PATH.name}")
    xls = pd.ExcelFile(XLSX_PATH)
    print(f"    Sheets: {xls.sheet_names}")

    df = pd.read_excel(xls, sheet_name='公司列表')
    print(f"    原始记录数: {len(df)}")
    print(f"    列名: {list(df.columns)}")

    # 2. 严格剔除 ST/*ST/PT 企业
    print(f"\n[2] 严格剔除风险企业（ST/*ST/PT）")
    initial_count = len(df)
    df = df.dropna(subset=['企业名称', '行业分类'])
    df['企业名称'] = df['企业名称'].astype(str).str.strip()
    df['行业分类'] = df['行业分类'].astype(str).str.strip()

    risk_mask = df['企业名称'].apply(is_risk_company)
    risk_companies = df[risk_mask]
    print(f"    发现风险企业: {len(risk_companies)} 家")
    if len(risk_companies) > 0:
        print(f"    风险企业示例:")
        for _, row in risk_companies.head(10).iterrows():
            print(f"      {row['企业名称']} -> {row['行业分类']}")

    df = df[~risk_mask].reset_index(drop=True)
    print(f"    剔除后剩余: {len(df)} 家企业")

    # 3. 去重
    print(f"\n[3] 企业去重")
    df = df.drop_duplicates(subset=['企业名称'], keep='first').reset_index(drop=True)
    print(f"    去重后: {len(df)} 家企业")

    # 4. 统计各行业企业数量
    print(f"\n[4] 各行业企业数量统计")
    industry_stats = df.groupby('行业分类').size().reset_index(name='企业数量')
    industry_stats = industry_stats.sort_values('企业数量', ascending=False).reset_index(drop=True)

    total = industry_stats['企业数量'].sum()
    print(f"    总计: {total} 家企业, {len(industry_stats)} 个行业\n")
    print(f"    {'行业名称':<12} {'企业数量':>8} {'占比':>8}")
    print(f"    {'-' * 32}")
    for _, row in industry_stats.iterrows():
        pct = row['企业数量'] / total * 100
        print(f"    {row['行业分类']:<12} {row['企业数量']:>8} {pct:>7.2f}%")

    # 5. 更新数据库
    print(f"\n[5] 更新数据库")
    DATABASE_URL = f"sqlite:///{DB_PATH}"
    engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False})
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = Session()

    try:
        # 构建企业名称到行业的映射
        industry_map = dict(zip(df['企业名称'], df['行业分类']))
        print(f"    构建映射: {len(industry_map)} 条")

        # 标记风险企业（数据库中已存在的ST企业）
        db_risk_companies = db.query(Company).filter(
            (Company.company_name.like('%ST%')) |
            (Company.company_name.like('%PT%'))
        ).all()
        print(f"    数据库中含 ST/PT 标识的企业: {len(db_risk_companies)} 家")
        for c in db_risk_companies:
            if is_risk_company(c.company_name):
                c.is_st = True
                c.is_active = False
                print(f"      标记为不活跃: {c.stock_code} {c.company_name}")
        db.commit()

        # 更新企业的行业分类
        all_companies = db.query(Company).all()
        print(f"\n    数据库中现有企业: {len(all_companies)} 家")
        updated_count = 0
        not_found_count = 0

        for company in all_companies:
            if company.company_name in industry_map:
                new_industry = industry_map[company.company_name]
                if company.industry != new_industry:
                    company.industry = new_industry
                    updated_count += 1
            else:
                not_found_count += 1

        db.commit()
        print(f"    已更新 {updated_count} 家企业的行业分类")
        print(f"    未在xlsx中找到匹配: {not_found_count} 家")

        # 6. 输出更新后的行业统计
        print(f"\n[6] 数据库更新后各行业企业数量")
        print(f"    仅统计 is_active=True AND is_st=False AND 非金融行业")

        results = (
            db.query(Company.industry, func.count(Company.id))
            .filter(
                Company.is_active == True,
                Company.is_st == False,
                ~Company.industry.in_(FINANCIAL_INDUSTRIES),
            )
            .group_by(Company.industry)
            .order_by(func.count(Company.id).desc())
            .all()
        )

        db_total = sum(cnt for _, cnt in results)
        print(f"    总计: {db_total} 家企业\n")
        print(f"    {'行业名称':<12} {'企业数量':>8} {'占比':>8}")
        print(f"    {'-' * 32}")
        for industry, cnt in results:
            pct = cnt / db_total * 100 if db_total > 0 else 0
            print(f"    {industry:<12} {cnt:>8} {pct:>7.2f}%")

        print("\n[完成] 所有处理已完成!")

    except Exception as e:
        db.rollback()
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == '__main__':
    main()
