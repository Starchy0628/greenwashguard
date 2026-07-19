"""
更新企业行业分类脚本
1. 使用新的申万一级行业分类数据更新数据库中的企业分类
2. 删除银行和非银金融公司
3. 重新计算行业中位数
"""
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.company import Company, FINANCIAL_INDUSTRIES
from app.models.analysis import AnalysisRecord
from app.models.sentence import Sentence


def main():
    DATABASE_URL = 'sqlite:///../data/db/greenwash_guard.db'
    engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False})
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = Session()

    try:
        # 1. 读取新的行业分类数据
        print("读取行业分类数据...")
        xls = pd.ExcelFile('../data/申万一级行业分类_已处理.xlsx')
        df = pd.read_excel(xls, sheet_name='公司列表')
        
        print(f"读取到 {len(df)} 条记录")
        print(f"行业数量: {df['行业分类'].nunique()}")
        
        # 构建企业名称到行业的映射
        industry_map = {}
        for _, row in df.iterrows():
            company_name = str(row['企业名称']).strip()
            industry = str(row['行业分类']).strip()
            if company_name and industry:
                industry_map[company_name] = industry
        
        print(f"去重后企业数: {len(industry_map)}")

        # 2. 更新现有企业的行业分类
        print("\n更新企业行业分类...")
        companies = db.query(Company).all()
        updated_count = 0
        not_found_count = 0
        
        for company in companies:
            if company.company_name in industry_map:
                new_industry = industry_map[company.company_name]
                if company.industry != new_industry:
                    company.industry = new_industry
                    updated_count += 1
            else:
                not_found_count += 1
        
        db.commit()
        print(f"已更新 {updated_count} 家企业的行业分类")
        print(f"未找到匹配的企业: {not_found_count} 家")

        # 3. 删除银行和非银金融公司
        print("\n删除银行和非银金融公司...")
        financial_companies = db.query(Company).filter(Company.industry.in_(FINANCIAL_INDUSTRIES)).all()
        print(f"找到 {len(financial_companies)} 家金融类公司")
        
        for company in financial_companies:
            # 删除关联的分析记录和语句
            records = db.query(AnalysisRecord).filter(AnalysisRecord.company_id == company.id).all()
            for record in records:
                db.query(Sentence).filter(Sentence.analysis_record_id == record.id).delete()
                db.delete(record)
            db.delete(company)
        
        db.commit()
        print(f"已删除 {len(financial_companies)} 家金融类公司及其关联数据")

        # 4. 重新计算行业中位数
        print("\n重新计算行业中位数...")
        industries = db.query(Company.industry).distinct().all()
        
        for (industry,) in industries:
            # 获取该行业所有企业的最新分析记录的 tone_score
            subquery = db.query(
                AnalysisRecord.company_id,
                func.max(AnalysisRecord.year).label('latest_year')
            ).join(Company).filter(Company.industry == industry).group_by(AnalysisRecord.company_id).subquery()
            
            tone_scores = db.query(AnalysisRecord.tone_score).join(
                subquery,
                (AnalysisRecord.company_id == subquery.c.company_id) & (AnalysisRecord.year == subquery.c.latest_year)
            ).filter(AnalysisRecord.tone_score.isnot(None)).all()
            
            if tone_scores:
                scores = sorted([s[0] for s in tone_scores])
                n = len(scores)
                if n % 2 == 0:
                    median = (scores[n//2 - 1] + scores[n//2]) / 2
                else:
                    median = scores[n//2]
                
                print(f"  {industry}: {n} 家企业, 中位数: {median:.6f}")
            else:
                print(f"  {industry}: 无有效数据")

        # 5. 更新 AnalysisRecord 中的 industry_median_tone
        print("\n更新分析记录中的行业中位数...")
        for (industry,) in industries:
            subquery = db.query(
                AnalysisRecord.company_id,
                func.max(AnalysisRecord.year).label('latest_year')
            ).join(Company).filter(Company.industry == industry).group_by(AnalysisRecord.company_id).subquery()
            
            tone_scores = db.query(AnalysisRecord.tone_score).join(
                subquery,
                (AnalysisRecord.company_id == subquery.c.company_id) & (AnalysisRecord.year == subquery.c.latest_year)
            ).filter(AnalysisRecord.tone_score.isnot(None)).all()
            
            if tone_scores:
                scores = sorted([s[0] for s in tone_scores])
                n = len(scores)
                if n % 2 == 0:
                    median = (scores[n//2 - 1] + scores[n//2]) / 2
                else:
                    median = scores[n//2]
                
                # 更新该行业所有分析记录的 industry_median_tone
                records = db.query(AnalysisRecord).join(Company).filter(Company.industry == industry).all()
                for record in records:
                    record.industry_median_tone = median
        
        db.commit()
        print("已更新所有分析记录的行业中位数")

        # 6. 重新计算 GW 指数
        print("\n重新计算 GW 指数...")
        records = db.query(AnalysisRecord).filter(
            AnalysisRecord.tone_score.isnot(None),
            AnalysisRecord.industry_median_tone.isnot(None)
        ).all()
        
        for record in records:
            record.gw_index = max(0.0, record.tone_score - record.industry_median_tone)
            record.risk_level = "预警" if record.gw_index > 0.15 else "正常"
        
        db.commit()
        print(f"已重新计算 {len(records)} 条分析记录的 GW 指数")

        # 7. 统计更新后的行业分布
        print("\n更新后的行业分布:")
        industry_stats = db.query(Company.industry, func.count(Company.id)).group_by(Company.industry).order_by(func.count(Company.id).desc()).all()
        total_companies = sum(count for _, count in industry_stats)
        
        for industry, count in industry_stats:
            print(f"  {industry}: {count} 家")
        print(f"\n总计: {total_companies} 家企业")

        print("\n所有更新已完成!")
        
    except Exception as e:
        db.rollback()
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == '__main__':
    main()
