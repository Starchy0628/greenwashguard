"""
从真实CMDA文件夹导入企业数据（高效版）

策略：
1. 扫描CMDA获取所有企业（股票代码+名称+年份）
2. 导入全部企业到Company表（仅基础信息，用于实时监测计数和搜索）
3. 对已知行业的企业（~272家），处理所有年份MD&A：
   - 读取真实文本、切句、提取环境语句、mock分类和打分、保存Sentence
4. 计算行业基准、GW指数、风险等级
"""
import sys
import re
import time
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR.parent))

from app.core.database import SessionLocal, init_db
from app.models.company import Company, FINANCIAL_INDUSTRIES
from app.models.analysis import AnalysisRecord
from app.models.sentence import Sentence
from app.models.industry import IndustryBenchmark
from app.services.text_utils import split_sentences, filter_env_sentences, clean_text
from app.services.mock_service import mock_classify_sentence, mock_sentiment_score, _stable_seed
import random

MDA_FILE_PATTERN = re.compile(r"^(\d{6})_(.+?)_(\d{4}-\d{2}-\d{2})\.txt$")
TEXT_SUBDIR = "文本"

# ============================================================
#  已知行业映射
# ============================================================
FULL_DEMO_COMPANIES = [
    {"code": "600519", "name": "贵州茅台", "industry": "食品饮料"},
    {"code": "000858", "name": "五粮液", "industry": "食品饮料"},
    {"code": "000333", "name": "美的集团", "industry": "家用电器"},
    {"code": "002594", "name": "比亚迪", "industry": "汽车"},
    {"code": "300750", "name": "宁德时代", "industry": "电力设备"},
    {"code": "600048", "name": "保利发展", "industry": "房地产"},
    {"code": "600028", "name": "中国石化", "industry": "石油石化"},
    {"code": "601857", "name": "中国石油", "industry": "石油石化"},
    {"code": "000002", "name": "万科A", "industry": "房地产"},
    {"code": "600309", "name": "万华化学", "industry": "基础化工"},
    {"code": "000725", "name": "京东方A", "industry": "电子"},
    {"code": "601012", "name": "隆基绿能", "industry": "电力设备"},
]

SEED_INDUSTRY_MAP = {
    "食品饮料": ["泸州老窖", "山西汾酒", "洋河股份", "海天味业", "伊利股份", "青岛啤酒", "重庆啤酒", "张裕A", "双汇发展", "安琪酵母"],
    "房地产": ["碧桂园", "华润置地", "招商蛇口", "金地集团", "新城控股", "华夏幸福", "荣盛发展", "金科股份", "中南建设", "阳光城"],
    "汽车": ["上汽集团", "广汽集团", "长安汽车", "长城汽车", "吉利汽车", "蔚来", "理想汽车", "小鹏汽车", "一汽解放", "东风汽车"],
    "电力设备": ["通威股份", "阳光电源", "特变电工", "国电南瑞", "金风科技", "明阳智能", "汇川技术", "亿纬锂能", "赣锋锂业", "天齐锂业"],
    "石油石化": ["中国海油", "中国神华", "中煤能源", "陕西煤业", "恒力石化", "荣盛石化", "东方盛虹", "卫星化学", "宝丰能源", "广汇能源"],
    "基础化工": ["扬农化工", "新安股份", "合盛硅业", "龙佰集团", "华鲁恒升", "鲁西化工", "沧州大化", "巨化股份", "三友化工", "中泰化学"],
    "电子": ["立讯精密", "歌尔股份", "闻泰科技", "韦尔股份", "兆易创新", "北方华创", "中微公司", "海康威视", "大华股份", "紫光国微"],
    "医药生物": ["恒瑞医药", "药明康德", "迈瑞医疗", "爱尔眼科", "片仔癀", "云南白药", "智飞生物", "长春高新", "复星医药", "人福医药"],
    "计算机": ["用友网络", "金山办公", "科大讯飞", "三六零", "深信服", "启明星辰", "浪潮信息", "中科曙光", "紫光股份", "中国软件"],
    "传媒": ["分众传媒", "芒果超媒", "光线传媒", "华策影视", "完美世界", "三七互娱", "吉比特", "巨人网络", "昆仑万维", "东方明珠"],
    "通信": ["中兴通讯", "中国联通", "中国移动", "中国电信", "烽火通信", "亨通光电", "中天科技", "中际旭创", "新易盛", "光迅科技"],
    "机械设备": ["三一重工", "徐工机械", "中联重科", "中国中车", "潍柴动力", "先导智能", "晶盛机电", "迈为股份", "捷佳伟创", "大族激光"],
    "国防军工": ["中航沈飞", "中航西飞", "航发动力", "中国卫星", "中国船舶", "中航光电", "振华科技", "高德红外", "大立科技", "鸿远电子"],
    "有色金属": ["紫金矿业", "江西铜业", "铜陵有色", "云南铜业", "中国铝业", "南山铝业", "云铝股份", "中国稀土", "北方稀土", "厦门钨业"],
    "钢铁": ["宝钢股份", "鞍钢股份", "首钢股份", "武钢股份", "包钢股份", "太钢不锈", "马钢股份", "华菱钢铁", "新钢股份", "南钢股份"],
    "煤炭": ["兖州煤业", "潞安环能", "山西焦煤", "淮北矿业", "平煤股份", "冀中能源", "盘江股份", "昊华能源", "露天煤业", "晋控煤业"],
    "建筑材料": ["海螺水泥", "中国建材", "北新建材", "东方雨虹", "伟星新材", "海螺新材", "旗滨集团", "福莱特", "南玻A", "金晶科技"],
    "建筑装饰": ["中国建筑", "中国中铁", "中国铁建", "中国交建", "中国电建", "中国能建", "中国中冶", "中国化学", "中国核建", "中国一重"],
    "轻工制造": ["顾家家居", "欧派家居", "索菲亚", "尚品宅配", "志邦家居", "我乐家居", "金牌橱柜", "皮阿诺", "顶固集创", "好莱客"],
    "家用电器": ["格力电器", "海尔智家", "老板电器", "苏泊尔", "九阳股份", "海信家电", "TCL家电", "小熊电器", "新宝股份", "飞科电器"],
    "纺织服装": ["海澜之家", "雅戈尔", "杉杉股份", "安踏体育", "李宁", "特步国际", "361度", "波司登", "报喜鸟", "七匹狼"],
    "农林牧渔": ["牧原股份", "温氏股份", "新希望", "正邦科技", "海大集团", "大北农", "隆平高科", "登海种业", "圣农发展", "仙坛股份"],
    "商贸零售": ["永辉超市", "苏宁易购", "国美零售", "王府井", "天虹股份", "百联股份", "重庆百货", "大商股份", "鄂武武A", "合肥百货"],
    "社会服务": ["中国中免", "宋城演艺", "锦江酒店", "首旅酒店", "华住集团", "海底捞", "九毛九", "颐海国际", "广州酒家", "全聚德"],
    "交通运输": ["顺丰控股", "中通快递", "韵达股份", "圆通速递", "申通快递", "中国国航", "南方航空", "东方航空", "大秦铁路", "京沪高铁"],
    "公用事业": ["长江电力", "华能国际", "华电国际", "国电电力", "大唐发电", "中广核", "中国核电", "川投能源", "国投电力", "粤电力A"],
    "环保": ["碧水源", "龙净环保", "三聚环保", "清新环境", "伟明环保", "高能环境", "瀚蓝环境", "东江环保", "格林美", "光大环境"],
    "美容护理": ["珀莱雅", "丸美股份", "上海家化", "贝泰妮", "华熙生物", "爱美客", "昊海生科", "水羊股份", "拉芳家化", "名臣健康"],
}


def build_industry_maps():
    code_to_ind = {}
    name_to_ind = {}
    for c in FULL_DEMO_COMPANIES:
        code_to_ind[c["code"]] = c["industry"]
        name_to_ind[c["name"]] = c["industry"]
    for ind, names in SEED_INDUSTRY_MAP.items():
        for n in names:
            name_to_ind[n] = ind
    return code_to_ind, name_to_ind


def get_cmda_root():
    try:
        from app.core.config import get_settings
        s = get_settings()
        if s.mda_root:
            p = Path(s.mda_root)
            if not p.is_absolute():
                p = BASE_DIR.parent.parent / p
            return p
    except:
        pass
    return BASE_DIR.parent.parent / "data" / "CMDA_管理层讨论与分析_ALL"


def scan_cmda(cmda_root):
    print(f"扫描CMDA: {cmda_root}")
    company_files = defaultdict(dict)
    if not cmda_root.exists():
        print("  目录不存在!")
        return company_files
    for yd in sorted(cmda_root.iterdir()):
        if not yd.is_dir():
            continue
        year = yd.name
        td = yd / TEXT_SUBDIR
        if not td.exists():
            continue
        cnt = 0
        for f in td.iterdir():
            if not f.is_file() or f.suffix != '.txt':
                continue
            m = MDA_FILE_PATTERN.match(f.name)
            if m:
                code, name = m.group(1), m.group(2)
                company_files[(code, name)][int(year)] = f
                cnt += 1
        print(f"  {year}: {cnt} 文件")
    return company_files


def read_text(fp):
    for enc in ['utf-8', 'gbk', 'gb18030', 'utf-8-sig']:
        try:
            with open(fp, 'r', encoding=enc) as f:
                return f.read()
        except:
            continue
    try:
        with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except:
        return ""


def process_one_year(db, company, year, filepath):
    """处理单年MD&A，返回sentence数量"""
    raw = read_text(filepath)
    if not raw:
        return 0
    text = clean_text(raw)
    all_sents = split_sentences(text)
    env_sents, _ = filter_env_sentences(all_sents)
    env_text_set = set(s for s in env_sents)
    non_env_sents = [s for s in all_sents if s not in env_text_set]
    
    sent_objs = []
    desc_sents = []
    sub_cnt = 0
    disp_cnt = 0
    rng = random.Random(_stable_seed(company.stock_code + str(year)))
    
    # 环境语句：全部处理
    for sent in env_sents:
        final, vote_type, confidence, results = mock_classify_sentence(sent)
        ds = results.get("deepseek", final)
        qw = results.get("qwen", final)
        glm = results.get("glm", final)
        needs_review = (vote_type == "full_divergence")
        if needs_review:
            disp_cnt += 1
        elif final == "substantive":
            sub_cnt += 1
        elif final == "descriptive":
            desc_sents.append(sent)
        sent_objs.append({
            "text": sent, "ds": ds, "qw": qw, "glm": glm,
            "final": final, "vote_type": vote_type,
            "confidence": confidence, "needs_review": needs_review,
        })
    
    # 非环境语句：采样最多20条，标记为non_env
    sample_non_env = rng.sample(non_env_sents, min(20, len(non_env_sents))) if non_env_sents else []
    for sent in sample_non_env:
        sent_objs.append({
            "text": sent, "ds": "non_env", "qw": "non_env", "glm": "non_env",
            "final": "non_env", "vote_type": "unanimous", "confidence": 0.95, "needs_review": False,
        })
    
    # 计算tone_score（描述性语句情感均值，映射到[0,0.5]范围）
    desc_sentiments = []
    for s_obj in sent_objs:
        if s_obj["final"] == "descriptive":
            score, _ = mock_sentiment_score(s_obj["text"])
            s_obj["sentiment"] = score
            s_obj["sentiment_std"] = _
            desc_sentiments.append(score)
        else:
            score, std = mock_sentiment_score(s_obj["text"])
            s_obj["sentiment"] = score
            s_obj["sentiment_std"] = std
    
    if desc_sentiments:
        avg_sent = sum(desc_sentiments) / len(desc_sentiments)
        tone = round(max(0.0, min(0.8, (avg_sent + 1) * 0.25)), 6)
    else:
        tone = 0.20
    
    env_count = len(env_sents)
    desc_count = len(desc_sents)
    total_count = len(all_sents)
    non_env_count = total_count - env_count
    
    rec = AnalysisRecord(
        company_id=company.id, year=year, data_source_type="local",
        total_sentences=total_count, env_sentences=env_count,
        substantive_count=sub_cnt, descriptive_count=desc_count,
        non_env_count=non_env_count, dispute_count=disp_cnt,
        tone_score=tone, industry_median_tone=0.0, gw_index=0.0,
        risk_level="正常", fleiss_kappa=0.82, analysis_status="completed",
        is_latest=False,
    )
    db.add(rec)
    db.flush()
    
    for idx, so in enumerate(sent_objs):
        db.add(Sentence(
            analysis_record_id=rec.id, sentence_text=so["text"], sentence_order=idx,
            deepseek_result=so["ds"], qwen_result=so["qw"], glm_result=so["glm"],
            final_category=so["final"], vote_type=so["vote_type"], confidence=so["confidence"],
            sentiment_score=so["sentiment"], sentiment_std=so["sentiment_std"],
            needs_review=so["needs_review"],
        ))
    
    return len(sent_objs)


def main():
    cmda_root = get_cmda_root()
    print(f"CMDA: {cmda_root} (exists={cmda_root.exists()})")
    
    company_files = scan_cmda(cmda_root)
    total_comp = len(company_files)
    total_files = sum(len(v) for v in company_files.values())
    all_years = set()
    for yd in company_files.values():
        all_years.update(yd.keys())
    max_year = max(all_years) if all_years else 2025
    print(f"\n总计: {total_comp} 家企业, {total_files} 份文件, 年份 {min(all_years)}-{max(all_years)}")
    
    code_map, name_map = build_industry_maps()
    
    # 对同一股票代码可能有多个名称（改名），只保留最新年份的名称
    code_latest_name = {}
    code_years = defaultdict(dict)
    for (code, name), yd in company_files.items():
        max_y = max(yd.keys())
        if code not in code_latest_name or max_y > code_latest_name[code][1]:
            code_latest_name[code] = (name, max_y)
        code_years[code].update(yd)
    
    # 重新构建去重后的company_files: code -> {name, years_dict}
    deduped = {}
    for code, (name, _) in code_latest_name.items():
        deduped[(code, name)] = code_years[code]
    company_files = deduped
    total_comp = len(company_files)
    total_files = sum(len(v) for v in company_files.values())
    print(f"去重后: {total_comp} 家企业, {total_files} 份文件")
    
    # 重新计算年份范围
    all_years = set()
    for yd in company_files.values():
        all_years.update(yd.keys())
    max_year = max(all_years) if all_years else 2025
    
    # 找有行业信息的企业
    known_companies = {}
    unknown_companies = {}
    for (code, name), yd in company_files.items():
        ind = code_map.get(code) or name_map.get(name)
        is_st = ("ST" in name or "*ST" in name)
        is_fin = ind in FINANCIAL_INDUSTRIES if ind else False
        if ind and not is_st and not is_fin:
            known_companies[(code, name)] = (yd, ind)
        else:
            unknown_companies[(code, name)] = (yd, ind, is_st, is_fin)
    
    print(f"有行业信息(待分析): {len(known_companies)} 家")
    print(f"无行业信息(仅导入基础信息): {len(unknown_companies)} 家")
    
    # 清空并重建DB
    print("\n初始化数据库...")
    init_db()
    db = SessionLocal()
    db.query(Sentence).delete()
    db.query(AnalysisRecord).delete()
    db.query(IndustryBenchmark).delete()
    db.query(Company).delete()
    db.commit()
    
    # 导入所有企业
    print("导入企业记录...")
    known_db = {}
    for (code, name), (yd, ind) in known_companies.items():
        c = Company(stock_code=code, company_name=name, industry=ind,
                     is_st=False, is_active=True, is_seed=False)
        db.add(c); db.flush()
        known_db[(code, name)] = (c, yd)
    for (code, name), (yd, ind, is_st, is_fin) in unknown_companies.items():
        c = Company(stock_code=code, company_name=name, industry=(ind or "其他"),
                     is_st=is_st, is_active=not is_fin, is_seed=False)
        db.add(c); db.flush()
    db.commit()
    print(f"  导入完成: {total_comp} 家")
    
    # 处理有行业信息的企业（全部年份）
    print(f"\n处理 {len(known_db)} 家企业的真实MD&A...")
    t0 = time.time()
    total_sents = 0
    total_records = 0
    errors = 0
    
    for i, ((code, name), (company, yd)) in enumerate(known_db.items()):
        for year in sorted(yd.keys()):
            try:
                n = process_one_year(db, company, year, yd[year])
                total_sents += n
                total_records += 1
            except Exception as e:
                errors += 1
                if errors <= 3:
                    print(f"  错误 {code} {name} {year}: {e}")
        
        if (i+1) % 20 == 0:
            db.commit()
            el = time.time() - t0
            rate = (i+1) / el
            eta = (len(known_db) - i - 1) / rate if rate > 0 else 0
            print(f"  {i+1}/{len(known_db)} ({(i+1)/len(known_db)*100:.0f}%) "
                  f"记录:{total_records} 句子:{total_sents} "
                  f"{rate:.1f}企/秒 ETA:{eta:.0f}秒")
    
    db.commit()
    el = time.time() - t0
    print(f"处理完成! {el:.0f}秒, {total_records}条记录, {total_sents}条句子, 错误:{errors}")
    
    # 计算行业基准和GW
    print("\n计算行业基准和GW指数...")
    years = sorted(set(r.year for r in db.query(AnalysisRecord.year).all()))
    
    EXCLUDED_INDUSTRIES = FINANCIAL_INDUSTRIES + ["其他"]
    
    for year in years:
        recs = (db.query(AnalysisRecord).join(Company)
            .filter(AnalysisRecord.year==year, AnalysisRecord.tone_score.isnot(None),
                    Company.industry.isnot(None), Company.is_st==False,
                    Company.industry.notin_(EXCLUDED_INDUSTRIES)).all())
        if len(recs) < 3:
            continue
        
        ind_tones = defaultdict(list)
        for r in recs:
            ind_tones[r.company.industry].append(r.tone_score)
        
        for ind, tones in ind_tones.items():
            if len(tones) < 2: continue
            st = sorted(tones)
            n = len(st)
            med = st[n//2] if n%2==1 else (st[n//2-1]+st[n//2])/2
            mean = sum(st)/n
            std = (sum((t-mean)**2 for t in st)/n)**0.5
            p80 = st[min(n-1, int(n*0.8))]
            b = db.query(IndustryBenchmark).filter_by(industry=ind, year=year).first()
            if b:
                b.sample_count=n; b.tone_median=round(med,6); b.tone_mean=round(mean,6)
                b.tone_std=round(std,6); b.tone_p80=round(p80,6)
                b.real_sample_count=n; b.used_seed_data=False
            else:
                db.add(IndustryBenchmark(industry=ind, year=year, sample_count=n,
                    real_sample_count=n, used_seed_data=False,
                    tone_median=round(med,6), tone_mean=round(mean,6),
                    tone_std=round(std,6), tone_p80=round(p80,6)))
    db.commit()
    
    for year in years:
        recs = (db.query(AnalysisRecord).join(Company)
            .filter(AnalysisRecord.year==year, AnalysisRecord.tone_score.isnot(None),
                    Company.industry.isnot(None), Company.is_st==False,
                    Company.industry.notin_(EXCLUDED_INDUSTRIES)).all())
        if len(recs) < 5: continue
        ind_med = {}
        for r in recs:
            ind = r.company.industry
            if ind not in ind_med:
                b = db.query(IndustryBenchmark).filter_by(industry=ind, year=year).first()
                ind_med[ind] = b.tone_median if b else 0.22
            r.industry_median_tone = round(ind_med[ind], 6)
            r.gw_index = round(max(0.0, r.tone_score - ind_med[ind]), 6)
        
        gws = sorted([r.gw_index for r in recs if r.gw_index > 0])
        if gws:
            warn_t = gws[min(len(gws)-1, int(len(gws)*0.8))]
            for b in db.query(IndustryBenchmark).filter_by(year=year).all():
                b.gw_warn_threshold = round(warn_t, 6)
            for r in recs:
                r.risk_level = "预警" if r.gw_index >= warn_t else "正常"
    db.commit()
    
    # is_latest
    for c in db.query(Company).all():
        latest = (db.query(AnalysisRecord).filter_by(company_id=c.id)
                  .order_by(AnalysisRecord.year.desc()).first())
        if latest:
            latest.is_latest = True
    db.commit()
    
    # 最终统计
    tc = db.query(Company).count()
    ac = db.query(Company).filter_by(is_active=True).count()
    wi = db.query(Company).filter(Company.industry.isnot(None), Company.is_st==False,
                                   Company.industry.notin_(FINANCIAL_INDUSTRIES + ["其他"])).count()
    rc = db.query(AnalysisRecord).count()
    sc = db.query(Sentence).count()
    warn_c = db.query(AnalysisRecord).join(Company).filter(
        AnalysisRecord.is_latest==True, AnalysisRecord.risk_level=="预警",
        Company.is_st==False, Company.industry.notin_(FINANCIAL_INDUSTRIES + ["其他"])).count()
    
    print(f"\n完成!")
    print(f"  企业总数: {tc}")
    print(f"  活跃企业: {ac}")
    print(f"  有行业分析: {wi}")
    print(f"  分析记录: {rc}")
    print(f"  语句总数: {sc}")
    print(f"  当前预警企业: {warn_c}")
    db.close()


if __name__ == "__main__":
    main()
