import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.core.database import SessionLocal
from app.services.industry_service import compute_industry_benchmarks, update_risk_levels

def main():
    db = SessionLocal()
    try:
        for year in range(2012, 2026):
            print(f'计算 {year} 年行业基准...')
            compute_industry_benchmarks(db, year)
            
            print(f'更新 {year} 年风险等级...')
            update_risk_levels(db, year)
            
            print(f'  → {year} 年完成')
        
        print('所有年份行业基准重算完成')
    finally:
        db.close()

if __name__ == '__main__':
    main()
