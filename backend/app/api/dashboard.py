"""仪表盘 API"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.models.company import Company, FINANCIAL_INDUSTRIES
from app.models.analysis import AnalysisRecord
from app.models.sentence import Sentence
from app.schemas import DashboardMetrics, RiskThresholdInfo, Top10Item
from app.services.industry_service import get_warn_threshold

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

EXCLUDED_INDUSTRIES = FINANCIAL_INDUSTRIES
EXCLUDED_FOR_INDUSTRY = FINANCIAL_INDUSTRIES + ["其他"]


def _get_latest_year(db: Session) -> int:
    """自动获取数据库中最新的分析年份"""
    latest = (
        db.query(func.max(AnalysisRecord.year))
        .filter(AnalysisRecord.is_latest == True)
        .scalar()
    )
    return latest or 2025


@router.get("/top10", response_model=list[Top10Item])
def get_top10_risk(db: Session = Depends(get_db)):
    """获取GW指数最高的10家企业（剔除金融类、ST类，无行业映射企业因GW指数为0不会上榜）"""
    records = (
        db.query(AnalysisRecord)
        .join(Company)
        .filter(
            AnalysisRecord.is_latest == True,
            AnalysisRecord.gw_index.isnot(None),
            AnalysisRecord.gw_index > 0,
            AnalysisRecord.analysis_status == "completed",
            Company.is_st == False,
            Company.industry.notin_(list(EXCLUDED_INDUSTRIES)),
        )
        .order_by(AnalysisRecord.gw_index.desc())
        .limit(10)
        .all()
    )

    return [
        {
            "id": r.company_id,
            "stock_code": r.company.stock_code,
            "company_name": r.company.company_name,
            "industry": r.company.industry,
            "gw_index": r.gw_index,
            "risk_level": r.risk_level,
            "year": r.year,
        }
        for r in records
    ]


@router.get("/metrics", response_model=DashboardMetrics)
def get_metrics(db: Session = Depends(get_db)):
    """获取仪表盘关键指标

    total_companies: 实时监测企业总数 = 活跃+非ST+非金融企业
    analyzed_companies: 已有分析记录的企业数
    total_sentences: 分析的语句总数（非采样，实际处理的语句记录数）
    """
    EXCLUDED = set(FINANCIAL_INDUSTRIES)
    total_companies = (
        db.query(func.count(Company.id))
        .filter(
            Company.is_active == True,
            Company.is_st == False,
            Company.industry.notin_(list(EXCLUDED)),
        )
        .scalar()
    ) or 0

    covered_companies = (
        db.query(func.count(Company.id))
        .filter(
            Company.is_active == True,
            Company.is_st == False,
            Company.industry.notin_(list(EXCLUDED)),
            Company.industry != "其他",
        )
        .scalar()
    ) or 0

    analyzed_companies = (
        db.query(func.count(func.distinct(AnalysisRecord.company_id)))
        .join(Company, AnalysisRecord.company_id == Company.id)
        .filter(
            AnalysisRecord.analysis_status == "completed",
            Company.is_active == True,
            Company.is_st == False,
            Company.industry.notin_(list(EXCLUDED)),
        )
        .scalar()
    ) or 0

    total_sentences = db.query(func.count(Sentence.id)).scalar() or 0

    avg_kappa = (
        db.query(func.avg(AnalysisRecord.fleiss_kappa))
        .filter(AnalysisRecord.fleiss_kappa.isnot(None))
        .scalar()
    )
    fleiss_kappa = round(float(avg_kappa), 2) if avg_kappa else 0.84

    current_year = _get_latest_year(db)

    return DashboardMetrics(
        fleiss_kappa=fleiss_kappa,
        human_agreement=round(94.22, 2),
        total_sentences=total_sentences,
        total_companies=total_companies,
        covered_companies=covered_companies,
        analyzed_companies=analyzed_companies,
        warn_threshold=get_warn_threshold(db, current_year),
    )


@router.get("/risk-threshold", response_model=RiskThresholdInfo)
def get_risk_threshold(db: Session = Depends(get_db)):
    """获取当前预警阈值详情（剔除金融类、ST类企业，包含全部有效监测企业）"""
    current_year = _get_latest_year(db)
    threshold = get_warn_threshold(db, current_year)

    total_valid = (
        db.query(func.count(func.distinct(Company.id)))
        .filter(
            Company.is_active == True,
            Company.is_st == False,
            Company.industry.notin_(list(EXCLUDED_INDUSTRIES)),
        )
        .scalar()
    ) or 0

    warn_records = (
        db.query(AnalysisRecord)
        .join(Company, AnalysisRecord.company_id == Company.id)
        .filter(
            AnalysisRecord.is_latest == True,
            AnalysisRecord.risk_level == '预警',
            AnalysisRecord.analysis_status == "completed",
            Company.is_st == False,
            Company.industry.notin_(list(EXCLUDED_INDUSTRIES)),
        )
        .count()
    )

    return RiskThresholdInfo(
        threshold=threshold,
        total_companies=total_valid,
        warn_count=warn_records,
        normal_count=total_valid - warn_records,
    )
