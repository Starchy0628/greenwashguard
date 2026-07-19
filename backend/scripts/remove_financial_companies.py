"""
删除金融类公司脚本
根据公司名称识别并删除银行和非银金融公司
"""
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.company import Company
from app.models.analysis import AnalysisRecord
from app.models.sentence import Sentence


def main():
    DATABASE_URL = 'sqlite:///../data/db/greenwash_guard.db'
    engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False})
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = Session()

    try:
        # 读取新的行业分类数据，获取有效企业名称列表
        print("读取行业分类数据...")
        xls = pd.ExcelFile('../data/申万一级行业分类_已处理.xlsx')
        df = pd.read_excel(xls, sheet_name='公司列表')
        
        valid_companies = set(str(row['企业名称']).strip() for _, row in df.iterrows())
        print(f"有效企业数: {len(valid_companies)}")

        # 获取所有数据库中的企业
        companies = db.query(Company).all()
        print(f"数据库企业总数: {len(companies)}")

        # 找出不在新分类中的企业（这些应该是银行和非银金融公司）
        to_remove = [c for c in companies if c.company_name not in valid_companies]
        print(f"\n需要删除的企业: {len(to_remove)} 家")
        
        if to_remove:
            print("列表:")
            for c in to_remove:
                print(f"  {c.company_name} ({c.stock_code})")

            # 删除这些企业及其关联数据
            for company in to_remove:
                records = db.query(AnalysisRecord).filter(AnalysisRecord.company_id == company.id).all()
                for record in records:
                    db.query(Sentence).filter(Sentence.analysis_record_id == record.id).delete()
                    db.delete(record)
                db.delete(company)
            
            db.commit()
            print(f"\n已删除 {len(to_remove)} 家企业及其关联数据")
        else:
            print("没有需要删除的企业")

        # 统计更新后的企业数量
        remaining = db.query(Company).count()
        print(f"\n更新后企业总数: {remaining} 家")

    except Exception as e:
        db.rollback()
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == '__main__':
    main()
