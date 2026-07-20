"""
PDF 上传分析 API — 接收 PDF 文件，解析文本，执行分析，SSE 流式返回结果
"""
import asyncio
import logging
from datetime import datetime
from typing import AsyncGenerator
from fastapi import APIRouter, UploadFile, File, Form, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import get_settings
from app.core.utils import sse
from app.services.pdf_parser import parse_report_full, get_analysis_text
from app.services.text_utils import split_sentences, filter_env_sentences
from app.services.mock_service import run_mock_analysis
from app.services.industry_service import compute_industry_benchmarks, update_risk_levels
from app.models.company import Company
from app.models.analysis import AnalysisRecord
from app.models.sentence import Sentence

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/pdf", tags=["pdf_analysis"])


@router.post("/analyze")
async def analyze_pdf(
    file: UploadFile = File(...),
    force_refresh: bool = Form(False),
    db: Session = Depends(get_db),
):
    """上传 PDF 并执行分析（SSE 流式返回）"""
    return StreamingResponse(
        _analyze_pdf_stream(file, force_refresh, db),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def _analyze_pdf_stream(
    file: UploadFile,
    force_refresh: bool,
    db: Session,
) -> AsyncGenerator[str, None]:
    """PDF 分析 SSE 流"""

    # 阶段 0: 校验文件
    yield sse("status", {"phase": "uploading", "message": "正在接收文件..."})

    if not file.filename or not file.filename.lower().endswith('.pdf'):
        yield sse("analysis_error", {
            "phase": "upload",
            "message": "仅支持 PDF 格式文件，请上传 .pdf 文件",
            "retryable": False,
        })
        yield sse("done", {"status": "error"})
        return

    # 读取文件内容
    try:
        file_bytes = await file.read()
    except Exception as e:
        yield sse("analysis_error", {
            "phase": "upload",
            "message": f"文件读取失败：{str(e)}",
            "retryable": False,
        })
        yield sse("done", {"status": "error"})
        return

    if len(file_bytes) > 50 * 1024 * 1024:  # 50MB 限制
        yield sse("analysis_error", {
            "phase": "upload",
            "message": "文件过大（超过50MB），请压缩后重试",
            "retryable": False,
        })
        yield sse("done", {"status": "error"})
        return

    if len(file_bytes) < 100:
        yield sse("analysis_error", {
            "phase": "upload",
            "message": "文件内容为空或过小，请检查文件",
            "retryable": False,
        })
        yield sse("done", {"status": "error"})
        return

    # 阶段 1: 解析 PDF
    yield sse("status", {
        "phase": "parsing",
        "message": "正在解析 PDF 文件，提取文本内容...",
    })

    parsed = parse_report_full(file_bytes, file.filename)
    if not parsed.full_text:
        yield sse("analysis_error", {
            "phase": "parsing",
            "message": "PDF 解析失败，无法提取文本内容。请确认文件为文本型 PDF（非扫描图片）。",
            "retryable": False,
        })
        yield sse("done", {"status": "error"})
        return

    text = get_analysis_text(parsed)
    report_type = parsed.report_type
    company_name = parsed.company_name
    key_indicators = parsed.key_indicators

    yield sse("status", {
        "phase": "parsed",
        "message": f"PDF 解析完成，识别为 {report_type} 报告"
        + (f"，企业：{company_name}" if company_name else ""),
        "report_type": report_type,
        "company_name": company_name,
        "text_length": len(text),
    })

    # 阶段 2: 语句切分与过滤
    yield sse("status", {
        "phase": "segmenting",
        "message": "语句切分与环保相关性过滤...",
    })

    raw_sentences = split_sentences(text)
    if not raw_sentences:
        raw_sentences = [text]
    env_sentences, _ = filter_env_sentences(raw_sentences)

    total = len(env_sentences)
    total_sentences = len(raw_sentences)

    logger.info(
        "PDF解析完成: company=%s, text_len=%d, raw_sentences=%d, env_sentences=%d, mda_len=%d",
        company_name or parsed.company_name,
        len(text),
        total_sentences,
        total,
        len(parsed.mda_text),
    )

    if total == 0:
        logger.warning("未找到环境关键词，尝试使用全文进行分析")
        env_sentences = [s for s in raw_sentences if len(s.strip()) > 15]
        total = len(env_sentences)
        if total == 0:
            yield sse("analysis_error", {
                "phase": "segmenting",
                "message": (
                    "未找到任何环境相关语句。可能原因：\n"
                    "1. 该PDF为扫描件（图片型PDF），无法提取文本\n"
                    "2. 报告中确实未包含环境保护相关内容\n"
                    "3. PDF文本提取异常，请尝试重新上传或使用其他文件"
                ),
                "retryable": True,
            })
            yield sse("done", {"status": "error"})
            return
        yield sse("status", {
            "phase": "segmenting",
            "message": f"未匹配到明确环境关键词，使用全文{total}句进行宽松分析...",
            "fallback": True,
        })

    # 阶段 3: 三模型分类
    yield sse("status", {
        "phase": "classifying",
        "message": f"三模型独立分类投票中... ({total} 句环境相关语句)",
        "total": total,
        "done": 0,
    })

    # 自动识别行业：先尝试通过企业名称匹配数据库，再根据文本关键词推断
    settings = get_settings()
    industry = _detect_industry(text, company_name, db)

    if settings.app_mode == "real":
        # 真实模式
        from app.services.analysis_orchestrator import AnalysisOrchestrator
        result = await AnalysisOrchestrator._run_real_classification(
            env_sentences, industry, db
        )
    else:
        # Mock 模式
        result = run_mock_analysis(text, industry)

    yield sse("progress", {
        "phase": "classifying",
        "message": f"三模型独立分类投票中... ({total}/{total} 句)",
        "total": total,
        "done": total,
    })

    # 阶段 4: 多数投票确权
    yield sse("status", {
        "phase": "voting",
        "message": "多数投票确权，标记分歧语句...",
    })

    # 阶段 5: 情感打分 + GW指数合成
    yield sse("status", {
        "phase": "scoring",
        "message": "语境情感打分 + 行业基准修正，合成GW指数...",
    })

    # 尝试查找或创建企业记录
    company = None
    if company_name:
        company = (
            db.query(Company)
            .filter(
                (Company.company_name == company_name)
                | (Company.short_name == company_name)
                | (Company.company_name.contains(company_name))
            )
            .first()
        )

    if not company:
        # 创建临时企业记录
        company = Company(
            stock_code=f"PDF_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            company_name=company_name or f"PDF上传企业_{file.filename[:10]}",
            industry=industry,
            short_name=company_name,
            is_a_share=False,
            is_active=True,
        )
        db.add(company)
        db.flush()

    # 保存分析记录
    current_year = datetime.now().year

    db.query(AnalysisRecord).filter(
        AnalysisRecord.company_id == company.id,
        AnalysisRecord.is_latest == True,
    ).update({"is_latest": False})

    record = AnalysisRecord(
        company_id=company.id,
        year=current_year,
        data_source_type="MD&A",
        source_file_name=file.filename,
        total_sentences=total_sentences,
        env_sentences=total,
        substantive_count=result["substantive_count"],
        descriptive_count=result["descriptive_count"],
        non_env_count=result["non_env_count"],
        tone_score=result["tone_score"],
        industry_median_tone=result["industry_median_tone"],
        gw_index=result["gw_index"],
        risk_level="正常",
        fleiss_kappa=result["fleiss_kappa"],
        dispute_count=result["divergence_count"],
        analysis_status="completed",
        is_latest=True,
        analyzed_at=datetime.now(),
    )
    db.add(record)
    db.flush()

    for s in result["sentence_results"]:
        sentence = Sentence(
            analysis_record_id=record.id,
            sentence_text=s["sentence_text"],
            sentence_order=s["sentence_order"],
            deepseek_result=s["deepseek_result"],
            qwen_result=s["qwen_result"],
            glm_result=s["glm_result"],
            final_category=s["final_category"],
            vote_type=s["vote_type"],
            confidence=s["confidence"],
            sentiment_score=s["sentiment_score"],
            sentiment_std=s["sentiment_std"],
            needs_review=s["needs_review"],
        )
        db.add(sentence)

    db.commit()

    # 构建返回结果
    final_result = {
        "id": record.id,
        "company_id": company.id,
        "company_name": company.company_name,
        "stock_code": company.stock_code,
        "industry": company.industry,
        "year": record.year,
        "data_source_type": record.data_source_type,
        "source_file_name": record.source_file_name,
        "total_sentences": total_sentences,
        "env_sentences": total,
        "substantive_count": result["substantive_count"],
        "descriptive_count": result["descriptive_count"],
        "non_env_count": result["non_env_count"],
        "tone_score": result["tone_score"],
        "industry_median_tone": result["industry_median_tone"],
        "gw_index": result["gw_index"],
        "risk_level": "正常",
        "fleiss_kappa": result["fleiss_kappa"],
        "dispute_count": result["divergence_count"],
        "analysis_status": "completed",
        "analyzed_at": record.analyzed_at.isoformat() if record.analyzed_at else None,
        "trend": [],
        "sentences": [
            {
                "id": i,
                "sentence_text": s["sentence_text"],
                "sentence_order": s["sentence_order"],
                "deepseek_result": s["deepseek_result"],
                "qwen_result": s["qwen_result"],
                "glm_result": s["glm_result"],
                "final_category": s["final_category"],
                "vote_type": s["vote_type"],
                "confidence": s["confidence"],
                "sentiment_score": s["sentiment_score"],
                "needs_review": s["needs_review"],
            }
            for i, s in enumerate(result["sentence_results"])
        ],
    }

    # 分离已确权和待复核
    # 已确权：仅包含 final_category == "substantive" 且 needs_review == False
    # 待复核：所有 needs_review == True（不考虑其分类结果）
    # descriptive 和 non_env 不在任何清单中展示
    confirmed = [
        s for s in final_result["sentences"]
        if not s["needs_review"] and s["final_category"] == "substantive"
    ]
    disputed = [s for s in final_result["sentences"] if s["needs_review"]]
    final_result["confirmed_sentences"] = confirmed
    final_result["dispute_sentences"] = disputed
    final_result["key_indicators"] = key_indicators

    yield sse("result", {
        "cached": False,
        "result": final_result,
    })

    yield sse("done", {"status": "success"})


_COMPANY_NAME_INDUSTRY = [
    (["茅台", "茅台酒", "酒业", "酒厂", "五粮液", "泸州老窖", "汾酒", "洋河", "古井贡", "剑南春"], "食品饮料"),
    (["银行", "工行", "建行", "农行", "中行", "招行", "交行", "兴业", "浦发", "民生", "中信银行", "光大银行", "华夏银行", "平安银行", "北京银行", "宁波银行", "江苏银行"], "银行"),
    (["证券", "券商", "中信证券", "海通证券", "国泰君安", "华泰证券"], "非银金融"),
    (["保险", "人寿", "平安保险", "太平洋保险", "人保", "新华保险"], "非银金融"),
    (["信托", "期货", "融资租赁"], "非银金融"),
    (["万科", "保利", "恒大", "碧桂园", "融创", "中海地产", "华润置地", "招商蛇口"], "房地产"),
    (["美的", "格力", "海尔", "海信", "TCL", "长虹", "苏泊尔", "九阳"], "家用电器"),
    (["比亚迪", "上汽", "广汽", "一汽", "东风", "长安汽车", "长城汽车", "吉利", "蔚来", "小鹏", "理想"], "汽车"),
    (["华为", "中兴", "小米", "OPPO", "vivo", "浪潮", "联想", "用友", "金山"], "电子"),
    (["阿里", "腾讯", "百度", "京东", "美团", "拼多多", "网易", "滴滴", "字节"], "传媒"),
    (["中石油", "中石化", "中海油", "神华", "中煤", "兖矿"], "采掘"),
    (["宝钢", "鞍钢", "武钢", "沙钢", "首钢"], "钢铁"),
    (["万华", "巴斯夫", "恒力", "荣盛", "恒逸"], "化工"),
    (["中芯国际", "韦尔股份", "北方华创", "紫光国微"], "电子"),
    (["恒瑞", "药明康德", "迈瑞", "复星医药", "云南白药", "片仔癀", "同仁堂"], "医药生物"),
    (["伊利", "蒙牛", "海天味业", "双汇", "牧原", "温氏", "新希望"], "食品饮料"),
    (["宁德时代", "隆基", "通威", "阳光电源", "金风科技"], "电气设备"),
    (["国航", "东航", "南航", "海航", "顺丰", "中通", "圆通", "韵达", "申通"], "交通运输"),
    (["华能", "大唐", "华电", "国电投", "长江电力", "三峡能源"], "公用事业"),
    (["中铁", "中铁建", "中建", "中交建", "中国电建", "中国能建"], "建筑装饰"),
]

_INDUSTRY_KEYWORDS = {
    "银行": ["银行", "商业银行", "股份制银行", "城商行", "农商行", "信贷业务", "存款业务", "贷款业务"],
    "非银金融": ["证券公司", "保险公司", "信托公司", "期货公司", "基金管理公司", "券商", "资产管理公司", "融资租赁公司", "保险业务", "证券经纪", "投资银行"],
    "房地产": ["房地产开发", "地产开发", "住宅开发", "商业地产开发", "置业有限公司", "房地产项目", "土地储备", "商品房销售", "物业服务"],
    "建筑装饰": ["建筑工程", "工程施工", "装修装饰", "基建工程", "工程总承包", "施工总承包", "建筑安装"],
    "公用事业": ["火力发电", "水力发电", "风力发电", "光伏发电", "供电业务", "供水业务", "供气业务", "燃气销售", "自来水生产", "污水处理厂", "垃圾焚烧发电", "新能源发电"],
    "交通运输": ["航运业务", "航空运输", "港口运营", "快递业务", "铁路运输", "公路运输", "机场运营", "航空客运", "货运代理", "物流服务"],
    "汽车": ["汽车制造", "乘用车生产", "商用车生产", "新能源汽车", "电动汽车", "汽车零部件生产", "整车制造", "车辆销售"],
    "机械设备": ["装备制造", "机床制造", "工程机械", "自动化设备", "机器人制造", "专用设备制造"],
    "电气设备": ["输变电设备", "变压器制造", "光伏设备制造", "风电设备制造", "电机制造", "电气机械"],
    "家用电器": ["空调制造", "冰箱制造", "洗衣机制造", "家电生产", "厨房电器", "小家电", "白色家电"],
    "纺织服装": ["纺织生产", "服装制造", "服饰生产", "面料生产", "家纺产品", "纺织面料"],
    "医药生物": ["药品生产", "制药业务", "生物制药", "化学制药", "中药生产", "医疗器械制造", "疫苗研发", "医药研发", "药物制造"],
    "食品饮料": ["食品生产", "饮料制造", "白酒生产", "啤酒生产", "乳制品加工", "调味品生产", "生猪养殖", "家禽养殖", "屠宰加工", "酒类生产", "食品加工", "酿酒", "酿造", "制酒", "酒糟"],
    "农林牧渔": ["农业种植", "林业经营", "畜牧业", "渔业捕捞", "水产养殖", "饲料生产", "农产品加工"],
    "有色金属": ["铜矿开采", "铝业生产", "黄金开采", "稀土开采", "有色金属冶炼", "锂矿开采", "铜冶炼", "电解铝"],
    "钢铁": ["钢铁生产", "炼钢", "轧钢", "钢材生产", "钢铁冶炼", "热轧", "冷轧"],
    "化工": ["化工生产", "化学原料", "塑料制品", "橡胶制品", "化肥生产", "农药生产", "石化产品", "新材料研发", "精细化工", "煤化工"],
    "电子": ["半导体制造", "芯片设计", "集成电路", "PCB生产", "LED制造", "面板生产", "电子元器件", "电子制造"],
    "计算机": ["软件开发", "IT服务", "云计算服务", "大数据服务", "人工智能", "计算机系统", "信息技术服务", "系统集成"],
    "传媒": ["影视制作", "游戏开发", "广告业务", "出版发行", "互联网媒体", "视频平台", "内容创作"],
    "通信": ["通信设备制造", "电信运营", "5G通信", "通信服务", "移动通信", "光纤通信", "通信网络"],
    "采掘": ["煤炭开采", "石油开采", "天然气开采", "采矿业务", "矿山开采", "油田开发", "煤炭生产"],
    "国防军工": ["军工制造", "国防装备", "航天装备", "航空装备", "兵器制造", "船舶制造", "军工产品"],
    "轻工制造": ["造纸生产", "家具制造", "玩具制造", "文具生产", "印刷包装", "包装材料", "造纸及纸制品"],
    "商业贸易": ["零售业务", "百货商场", "超市连锁", "电子商务", "批发业务", "商业零售", "连锁经营"],
    "休闲服务": ["旅游服务", "酒店经营", "餐饮服务", "景区运营", "娱乐服务", "旅游景区"],
    "建筑材料": ["水泥生产", "玻璃制造", "建材生产", "陶瓷制造", "管材生产", "建筑陶瓷"],
}


def _detect_industry(text: str, company_name: str | None, db) -> str:
    """自动识别企业所属行业

    策略：
    1. 若提供了企业名称，先在数据库中匹配，若匹配到直接使用其行业
    2. 再根据企业名称关键词直接推断（公司名通常最准确）
    3. 否则根据PDF文本关键词加权匹配，取命中数最多的行业
    4. 都无法识别则返回"综合"
    """
    if company_name:
        matched = (
            db.query(Company)
            .filter(
                (Company.company_name == company_name)
                | (Company.short_name == company_name)
                | (Company.company_name.contains(company_name[:6]))
            )
            .first()
        )
        if matched and matched.industry and matched.industry != "其他":
            return matched.industry

        for kws, ind in _COMPANY_NAME_INDUSTRY:
            for kw in kws:
                if kw in company_name:
                    return ind

    search_text = text[:20000]

    scores: dict[str, int] = {}
    for industry, keywords in _INDUSTRY_KEYWORDS.items():
        count = 0
        for kw in keywords:
            if kw in search_text:
                count += 1
        if count > 0:
            scores[industry] = count

    if scores:
        return max(scores, key=scores.get)

    return "综合"
