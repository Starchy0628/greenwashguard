"""
重新计算行业中位数和 GW 指数脚本
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.company import Company
from app.models.analysis import AnalysisRecord


def main():
    DATABASE_URL = 'sqlite:///../data/db/greenwash_guard.db'
    engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False})
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = Session()

    try:
        # 1. 获取所有行业
        industries = db.query(Company.industry).distinct().all()
        print(f"行业数量: {len(industries)}")

        # 2. 计算每个行业的中位数
        print("\n计算行业中位数:")
        industry_medians = {}
        
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
                
                industry_medians[industry] = median
                print(f"  {industry}: {n} 家企业, 中位数: {median:.6f}")
            else:
                industry_medians[industry] = 0.5
                print(f"  {industry}: 无有效数据, 使用默认值 0.5")

        # 3. 更新分析记录中的行业中位数
        print("\n更新分析记录中的行业中位数...")
        records_updated = 0
        
        for (industry,) in industries:
            median = industry_medians.get(industry, 0.5)
            records = db.query(AnalysisRecord).join(Company).filter(Company.industry == industry).all()
            for record in records:
                record.industry_median_tone = median
                records_updated += 1
        
        db.commit()
        print(f"已更新 {records_updated} 条分析记录的行业中位数")

        # 4. 重新计算 GW 指数
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

        # 5. 统计更新后的行业分布
        print("\n更新后的行业分布:")
        industry_stats = db.query(Company.industry, func.count(Company.id)).group_by(Company.industry).order_by(func.count(Company.id).desc()).all()
        total_companies = sum(count for _, count in industry_stats)
        
        for industry, count in industry_stats:
            print(f"  {industry}: {count} 家")
        print(f"\n总计: {total_companies} 家企业")

        print("\n所有计算已完成!")
        
    except Exception as e:
        db.rollback()
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == '__main__':
    main()
