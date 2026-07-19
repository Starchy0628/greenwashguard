"""清理重复的AnalysisRecord记录"""
from app.core.database import SessionLocal
from app.models.company import Company
from app.models.analysis import AnalysisRecord

db = SessionLocal()

try:
    companies = db.query(Company).filter(Company.is_a_share == True).all()
    print(f"共有 {len(companies)} 家企业")
    
    total_duplicates = 0
    
    for company in companies:
        records = db.query(AnalysisRecord).filter(
            AnalysisRecord.company_id == company.id,
            AnalysisRecord.analysis_status == "completed",
        ).order_by(AnalysisRecord.year.desc()).all()
        
        year_map = {}
        duplicates = []
        
        for r in records:
            key = (r.year, r.data_source_type)
            if key in year_map:
                duplicates.append(r)
            else:
                year_map[key] = r
        
        if duplicates:
            print(f"公司 {company.stock_code} {company.company_name}: 发现 {len(duplicates)} 条重复记录")
            for dup in duplicates:
                print(f"  删除: 年份={dup.year}, ID={dup.id}, is_latest={dup.is_latest}")
                db.delete(dup)
                total_duplicates += 1
        
    db.commit()
    print(f"共清理 {total_duplicates} 条重复记录")
    
finally:
    db.close()
