from app.core.database import SessionLocal
from app.models.company import Company
from app.models.analysis import AnalysisRecord
from app.models.sentence import Sentence

db = SessionLocal()

company = db.query(Company).filter(Company.stock_code == '600519').first()
if company:
    print(f'Company: {company.company_name}, ID: {company.id}')
    records = db.query(AnalysisRecord).filter(AnalysisRecord.company_id == company.id).order_by(AnalysisRecord.year.desc()).all()
    for r in records:
        sent_count = db.query(Sentence).filter(Sentence.analysis_record_id == r.id).count()
        print(f'  Year:{r.year}, ID:{r.id}, Env:{r.env_sentences}, Sentences_in_db:{sent_count}, is_latest:{r.is_latest}')
else:
    print('Company not found')

db.close()
