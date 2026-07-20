"""
构建完整的申万一级行业映射，整合akshare数据 + CMDA文件夹扫描
输出: backend/data/industry_map.json
"""
import sys
import os
import re
import json
import time
from pathlib import Path
from collections import defaultdict, Counter

for k in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']:
    os.environ.pop(k, None)

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR.parent / "data"
AKSHARE_MAP_FILE = OUTPUT_DIR / "sw_industry_map_akshare.json"

FINANCIAL_INDUSTRIES = {"银行", "非银金融"}

# 名称关键词→行业映射（补全akshare未覆盖的企业）
NAME_KEYWORD_MAP = [
    ("银行", "银行"), ("证券", "非银金融"), ("保险", "非银金融"),
    ("信托", "非银金融"), ("期货", "非银金融"),
    ("白酒", "食品饮料"), ("酒业", "食品饮料"), ("啤酒", "食品饮料"),
    ("乳业", "食品饮料"), ("味业", "食品饮料"), ("茅台", "食品饮料"),
    ("药业", "医药生物"), ("医药", "医药生物"), ("生物", "医药生物"),
    ("医疗", "医药生物"), ("制药", "医药生物"), ("中药", "医药生物"),
    ("电子", "电子"), ("光电", "电子"), ("半导体", "电子"),
    ("芯片", "电子"), ("液晶", "电子"),
    ("软件", "计算机"), ("信息科技", "计算机"), ("云计算", "计算机"),
    ("新能源", "电力设备"), ("光伏", "电力设备"), ("风电", "电力设备"),
    ("电池", "电力设备"), ("锂业", "电力设备"), ("电网", "电力设备"),
    ("电气", "电力设备"),
    ("汽车", "汽车"), ("车业", "汽车"),
    ("机械", "机械设备"), ("重工", "机械设备"), ("机床", "机械设备"),
    ("化工", "基础化工"), ("化学", "基础化工"),
    ("煤业", "煤炭"), ("煤矿", "煤炭"),
    ("铜业", "有色金属"), ("铝业", "有色金属"), ("黄金", "有色金属"),
    ("矿业", "有色金属"), ("稀土", "有色金属"),
    ("建设", "建筑装饰"), ("建筑工程", "建筑装饰"),
    ("建材", "建筑材料"), ("水泥", "建筑材料"), ("玻璃", "建筑材料"),
    ("航空", "交通运输"), ("航运", "交通运输"), ("港口", "交通运输"),
    ("物流", "交通运输"), ("快递", "交通运输"), ("高速", "交通运输"),
    ("传媒", "传媒"), ("影视", "传媒"), ("出版", "传媒"), ("游戏", "传媒"),
    ("通信", "通信"), ("电信", "通信"), ("通讯", "通信"),
    ("环保", "环保"), ("节能", "环保"), ("环境", "环保"),
    ("军工", "国防军工"), ("航天", "国防军工"), ("船舶", "国防军工"),
    ("农业", "农林牧渔"), ("牧业", "农林牧渔"), ("渔业", "农林牧渔"),
    ("种业", "农林牧渔"), ("饲料", "农林牧渔"), ("养殖", "农林牧渔"),
    ("水务", "公用事业"), ("燃气", "公用事业"), ("热电", "公用事业"),
    ("发电", "公用事业"), ("水电", "公用事业"),
    ("家电", "家用电器"), ("电器", "家用电器"), ("空调", "家用电器"),
    ("纺织", "纺织服饰"), ("服装", "纺织服饰"), ("服饰", "纺织服饰"),
    ("家居", "轻工制造"), ("纸业", "轻工制造"), ("家具", "轻工制造"),
    ("百货", "商贸零售"), ("超市", "商贸零售"), ("零售", "商贸零售"),
    ("旅游", "社会服务"), ("酒店", "社会服务"), ("餐饮", "社会服务"),
    ("教育", "社会服务"), ("免税", "社会服务"),
    ("化妆品", "美容护理"), ("美容", "美容护理"),
    ("地产", "房地产"), ("置业", "房地产"),
    ("石油", "石油石化"), ("石化", "石油石化"),
]


def is_st_pt(name):
    """判断是否为ST/*ST/PT公司（中文股票名称中ST/PT总是作为前缀）"""
    if not name:
        return False
    n = name.strip().upper()
    return n.startswith("*ST") or n.startswith("ST") or n.startswith("PT")


def guess_industry_by_name(name):
    for keyword, ind in NAME_KEYWORD_MAP:
        if keyword in name:
            return ind
    return None


def fetch_akshare_map():
    """通过akshare获取申万一级行业映射，缓存到JSON"""
    if AKSHARE_MAP_FILE.exists():
        print(f"加载已缓存的akshare映射: {AKSHARE_MAP_FILE.name}")
        with open(AKSHARE_MAP_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get("code_to_industry_sw", {})

    print("通过akshare获取申万一级行业成分股...")
    import akshare as ak
    code_to_ind = {}
    ind_df = ak.sw_index_first_info()
    for _, row in ind_df.iterrows():
        ind_code = row['行业代码'].split('.')[0]
        ind_name = row['行业名称']
        try:
            cons = ak.index_component_sw(symbol=ind_code)
            codes = cons['证券代码'].astype(str).str.zfill(6).tolist()
            for c in codes:
                code_to_ind[c] = ind_name
            print(f"  {ind_name}: {len(codes)}")
        except Exception as e:
            print(f"  {ind_name}: 失败 - {e}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(AKSHARE_MAP_FILE, 'w', encoding='utf-8') as f:
        json.dump({"code_to_industry_sw": code_to_ind}, f, ensure_ascii=False, indent=2)
    return code_to_ind


def scan_cmda():
    """扫描CMDA文件夹获取所有企业代码和名称（保留最新年份的名称）"""
    cmda_root = BASE_DIR.parent.parent / "data" / "CMDA_管理层讨论与分析_ALL"
    pattern = re.compile(r"^(\d{6})_(.+?)_(\d{4}-\d{2}-\d{2})\.txt$")
    code_info = {}

    if not cmda_root.exists():
        print(f"CMDA目录不存在: {cmda_root}")
        return code_info

    for yd in sorted(cmda_root.iterdir()):
        if not yd.is_dir():
            continue
        try:
            year = int(yd.name)
        except ValueError:
            continue
        td = yd / "文本"
        if not td.exists():
            continue
        for f in td.iterdir():
            m = pattern.match(f.name)
            if m:
                code, name = m.group(1), m.group(2)
                if code not in code_info or year > code_info[code][1]:
                    code_info[code] = (name, year)

    return {code: name for code, (name, _) in code_info.items()}


def main():
    # 1. 获取akshare申万行业映射
    sw_map = fetch_akshare_map()
    print(f"akshare映射: {len(sw_map)} 只股票")

    # 2. 扫描CMDA
    print("\n扫描CMDA文件夹...")
    cmda_names = scan_cmda()
    print(f"CMDA企业: {len(cmda_names)} 家")

    # 3. 构建最终映射
    code_to_ind = {}
    st_codes = set()
    fin_codes = set()
    name_map = {}  # code -> name (using akshare name if available, else CMDA)

    # 先用akshare映射
    for code, ind in sw_map.items():
        code_to_ind[code] = ind

    # 处理CMDA企业
    matched = 0
    name_guessed = 0
    for code, name in cmda_names.items():
        if is_st_pt(name):
            st_codes.add(code)
            name_map[code] = name
            continue

        name_map[code] = name

        if code in code_to_ind:
            matched += 1
            if code_to_ind[code] in FINANCIAL_INDUSTRIES:
                fin_codes.add(code)
            continue

        # 名称关键词猜测
        ind = guess_industry_by_name(name)
        if ind:
            code_to_ind[code] = ind
            name_guessed += 1
            if ind in FINANCIAL_INDUSTRIES:
                fin_codes.add(code)

    print(f"  akshare匹配: {matched} 家")
    print(f"  名称补全: {name_guessed} 家")
    print(f"  仍无行业: {len(cmda_names) - matched - name_guessed - len(st_codes)} 家")

    # 再次用名称检查ST和金融
    for code, name in cmda_names.items():
        if is_st_pt(name):
            st_codes.add(code)
        if code_to_ind.get(code) in FINANCIAL_INDUSTRIES:
            fin_codes.add(code)

    # 有效企业
    valid_codes = set()
    valid_with_ind = set()
    for code in cmda_names:
        if code in st_codes or code in fin_codes:
            continue
        valid_codes.add(code)
        if code in code_to_ind:
            valid_with_ind.add(code)

    # 统计
    ind_counts = Counter(code_to_ind.get(c, "其他") for c in valid_with_ind)
    print(f"\n===== 最终统计 =====")
    print(f"CMDA企业总数: {len(cmda_names)}")
    print(f"ST/*ST/PT: {len(st_codes)}")
    print(f"金融(银行+非银): {len(fin_codes)}")
    print(f"有效监测企业: {len(valid_codes)}")
    print(f"  - 有申万行业: {len(valid_with_ind)}")
    print(f"  - 无行业(标记为其他): {len(valid_codes) - len(valid_with_ind)}")

    print(f"\n行业分布 ({len(ind_counts)}个):")
    for ind, cnt in ind_counts.most_common():
        print(f"  {ind}: {cnt}")

    if st_codes:
        print(f"\nST企业示例:")
        for c in list(st_codes)[:10]:
            print(f"  {c} {cmda_names.get(c, '')}")

    # 保存
    output = OUTPUT_DIR / "industry_map.json"
    result = {
        "code_to_industry_sw": code_to_ind,
        "code_to_name": name_map,
        "st_codes": sorted(list(st_codes)),
        "fin_codes": sorted(list(fin_codes)),
        "valid_codes": sorted(list(valid_codes)),
        "valid_with_industry": sorted(list(valid_with_ind)),
    }
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n已保存: {output}")
    return result


if __name__ == "__main__":
    main()
