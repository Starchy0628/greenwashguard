"""企业相关 API"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from app.core.database import get_db
from app.models.company import Company, FINANCIAL_INDUSTRIES
from app.models.analysis import AnalysisRecord
from app.models.sentence import Sentence
from app.schemas import CompanyResponse, CompanySearchResult, SearchQuery
from app.services.industry_service import validate_and_fix_industry

router = APIRouter(prefix="/api/companies", tags=["companies"])


@router.get("/search", response_model=list[CompanySearchResult])
def search_companies(
    q: str = Query("", description="搜索关键词（名称或代码）"),
    db: Session = Depends(get_db),
):
    """搜索企业（自动剔除金融类、ST类、数据缺失企业）"""
    if not q:
        return []

    companies = (
        db.query(Company)
        .filter(
            Company.is_active == True,
            Company.is_st == False,
            Company.industry.notin_(FINANCIAL_INDUSTRIES),
            or_(
                Company.company_name.contains(q),
                Company.stock_code.contains(q),
                Company.short_name.contains(q),
            ),
        )
        .order_by(Company.id)
        .limit(10)
        .all()
    )

    results = []
    for company in companies:
        validate_and_fix_industry(db, company.stock_code, company.industry)
        
        latest = (
            db.query(AnalysisRecord)
            .filter(
                AnalysisRecord.company_id == company.id,
                AnalysisRecord.is_latest == True,
            )
            .first()
        )
        results.append(
            CompanySearchResult(
                id=company.id,
                stock_code=company.stock_code,
                company_name=company.company_name,
                industry=company.industry,
                latest_gw_index=latest.gw_index if latest else None,
                latest_risk_level=latest.risk_level if latest else None,
            )
        )
    return results


@router.get("/market/trend", response_model=list[dict])
def get_market_trend(db: Session = Depends(get_db)):
    """获取全市场年度GW指数趋势（按年份聚合）"""
    from collections import defaultdict

    all_records = (
        db.query(AnalysisRecord.year, AnalysisRecord.gw_index)
        .join(Company, AnalysisRecord.company_id == Company.id)
        .filter(
            AnalysisRecord.gw_index.isnot(None),
            AnalysisRecord.analysis_status == "completed",
            Company.is_st == False,
            Company.industry.notin_(FINANCIAL_INDUSTRIES),
        )
        .all()
    )

    year_gw = defaultdict(list)
    for r in all_records:
        year_gw[r.year].append(r.gw_index)

    result = []
    for year in sorted(year_gw.keys()):
        gws = sorted(year_gw[year])
        n = len(gws)
        median = gws[n // 2] if n % 2 == 1 else (gws[n // 2 - 1] + gws[n // 2]) / 2
        mean = sum(gws) / n
        result.append({
            "year": year,
            "avg_gw_index": round(mean, 6),
            "median_gw_index": round(median, 6),
            "company_count": n,
        })

    return result


@router.get("/industry/trend", response_model=list[dict])
def get_industry_trend(industry: str = None, db: Session = Depends(get_db)):
    """获取行业年度GW指数趋势"""
    from collections import defaultdict

    query = (
        db.query(AnalysisRecord.year, AnalysisRecord.gw_index, Company.industry)
        .join(Company, AnalysisRecord.company_id == Company.id)
        .filter(
            AnalysisRecord.gw_index.isnot(None),
            AnalysisRecord.analysis_status == "completed",
            Company.is_st == False,
            Company.industry.notin_(FINANCIAL_INDUSTRIES),
        )
    )
    if industry:
        query = query.filter(Company.industry == industry)

    records = query.all()

    year_gw = defaultdict(list)
    for r in records:
        year_gw[r.year].append(r.gw_index)

    result = []
    for year in sorted(year_gw.keys()):
        gws = sorted(year_gw[year])
        n = len(gws)
        median = gws[n // 2] if n % 2 == 1 else (gws[n // 2 - 1] + gws[n // 2]) / 2
        mean = sum(gws) / n
        result.append({
            "year": year,
            "avg_gw_index": round(mean, 6),
            "median_gw_index": round(median, 6),
            "company_count": n,
        })

    return result


@router.get("/{company_id}", response_model=CompanyResponse)
def get_company(company_id: int, db: Session = Depends(get_db)):
    """获取企业详情"""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="企业不存在")

    validate_and_fix_industry(db, company.stock_code, company.industry)

    latest = (
        db.query(AnalysisRecord)
        .filter(
            AnalysisRecord.company_id == company_id,
            AnalysisRecord.is_latest == True,
        )
        .first()
    )

    return CompanyResponse(
        id=company.id,
        stock_code=company.stock_code,
        company_name=company.company_name,
        industry=company.industry,
        short_name=company.short_name,
        is_active=company.is_active,
        has_analysis=latest is not None,
        latest_gw_index=latest.gw_index if latest else None,
        latest_risk_level=latest.risk_level if latest else None,
    )


@router.get("/{company_id}/sentences/all", response_model=dict)
def get_company_all_sentences(company_id: int, db: Session = Depends(get_db)):
    """获取企业所有年份的环境语句（按年份分组）"""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="企业不存在")
    
    validate_and_fix_industry(db, company.stock_code, company.industry)

    records = (
        db.query(AnalysisRecord)
        .filter(
            AnalysisRecord.company_id == company_id,
            AnalysisRecord.analysis_status == "completed",
        )
        .order_by(AnalysisRecord.year.desc(), AnalysisRecord.is_latest.desc())
        .all()
    )
    year_map = {}
    unique_records = []
    for r in records:
        if r.year not in year_map:
            year_map[r.year] = r
            unique_records.append(r)
    records = unique_records

    category_order = {"substantive": 0, "descriptive": 1, "dispute": 2, "non_env": 3, "non_environmental": 4}

    year_groups = []
    total_substantive = 0
    total_descriptive = 0
    total_dispute = 0
    total_env = 0

    for record in records:
        sentences = (
            db.query(Sentence)
            .filter(Sentence.analysis_record_id == record.id)
            .order_by(Sentence.sentence_order)
            .all()
        )
        sentences.sort(key=lambda s: category_order.get(s.final_category, 5))

        year_substantive = 0
        year_descriptive = 0
        year_dispute = 0
        year_env = 0

        sentence_list = []
        if sentences:
            for s in sentences:
                if s.needs_review:
                    year_dispute += 1
                    year_env += 1
                elif s.final_category == "substantive":
                    year_substantive += 1
                    year_env += 1
                elif s.final_category == "descriptive":
                    year_descriptive += 1
                    year_env += 1

                sentence_list.append({
                    "id": s.id,
                    "sentence_text": s.sentence_text,
                    "sentence_order": s.sentence_order,
                    "deepseek_result": s.deepseek_result,
                    "qwen_result": s.qwen_result,
                    "glm_result": s.glm_result,
                    "final_category": s.final_category,
                    "vote_type": s.vote_type,
                    "confidence": s.confidence,
                    "sentiment_score": s.sentiment_score,
                    "needs_review": s.needs_review,
                })
        else:
            year_substantive = record.substantive_count or 0
            year_descriptive = record.descriptive_count or 0
            year_dispute = record.dispute_count or 0
            year_env = record.env_sentences or 0

        total_substantive += year_substantive
        total_descriptive += year_descriptive
        total_dispute += year_dispute
        total_env += year_env

        year_groups.append({
            "year": record.year,
            "substantive_count": year_substantive,
            "descriptive_count": year_descriptive,
            "dispute_count": year_dispute,
            "env_sentences": year_env,
            "sentences": sentence_list,
        })

    return {
        "year_groups": year_groups,
        "summary": {
            "total_substantive": total_substantive,
            "total_descriptive": total_descriptive,
            "total_dispute": total_dispute,
            "total_env_sentences": total_env,
            "total_years": len(year_groups),
        },
    }


def get_industry_tone_median(db: Session, industry: str, year: int) -> float:
    """获取指定行业指定年份的语调中位数（真实值，可能为负）"""
    records = (
        db.query(AnalysisRecord.tone_score)
        .join(Company, AnalysisRecord.company_id == Company.id)
        .filter(
            Company.industry == industry,
            Company.is_st == False,
            AnalysisRecord.year == year,
            AnalysisRecord.tone_score.isnot(None),
            AnalysisRecord.analysis_status == "completed",
        )
        .all()
    )

    if not records:
        from app.services.mock_service import _get_mock_industry_median
        return _get_mock_industry_median(industry)

    tones = sorted([r[0] for r in records])
    n = len(tones)
    if n % 2 == 1:
        return tones[n // 2]
    return (tones[n // 2 - 1] + tones[n // 2]) / 2


@router.get("/{company_id}/trend", response_model=list[dict])
def get_company_trend(company_id: int, db: Session = Depends(get_db)):
    """获取企业全部年份GW指数趋势（2012-2025完整范围）"""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="企业不存在")

    validate_and_fix_industry(db, company.stock_code, company.industry)

    records = (
        db.query(AnalysisRecord)
        .filter(
            AnalysisRecord.company_id == company_id,
            AnalysisRecord.gw_index.isnot(None),
            AnalysisRecord.analysis_status == "completed",
        )
        .order_by(AnalysisRecord.year)
        .all()
    )

    record_map = {r.year: r for r in records}

    industry_tone_medians = {}
    for year in range(2012, 2026):
        tone_median = get_industry_tone_median(db, company.industry, year)
        industry_tone_medians[year] = tone_median

    result = []
    for year in range(2012, 2026):
        record = record_map.get(year)
        result.append({
            "year": year,
            "gw_index": record.gw_index if record else None,
            "tone_score": record.tone_score if record else None,
            "risk_level": record.risk_level if record else None,
            "industry_median_gw": industry_tone_medians.get(year),
        })

    return result