"""
直接请求东方财富API获取全部A股行业数据 - 增强版（更稳定的重试）
"""
import sys
import os
import json
import time
from pathlib import Path
from collections import defaultdict

for k in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']:
    os.environ.pop(k, None)

import requests

BASE_DIR = Path(__file__).resolve().parent

code_to_industry = {}
code_to_name = {}

url = "https://push2.eastmoney.com/api/qt/clist/get"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}
session = requests.Session()
session.headers.update(headers)

EM_TO_SW = {
    "银行": "银行", "保险": "非银金融", "证券": "非银金融", "信托": "非银金融", "期货": "非银金融", "多元金融": "非银金融",
    "房地产开发": "房地产", "房地产服务": "房地产",
    "白酒": "食品饮料", "啤酒": "食品饮料", "饮料乳品": "食品饮料", "食品加工": "食品饮料", "调味发酵品": "食品饮料", "休闲食品": "食品饮料", "保健品": "食品饮料", "食品饮料": "食品饮料",
    "化学制药": "医药生物", "中药": "医药生物", "生物制品": "医药生物", "医疗器械": "医药生物", "医疗服务": "医药生物", "医药商业": "医药生物", "中药Ⅱ": "医药生物", "医疗美容": "医药生物",
    "乘用车": "汽车", "商用车": "汽车", "汽车零部件": "汽车", "摩托车及其他": "汽车", "汽车服务": "汽车",
    "白色家电": "家用电器", "黑色家电": "家用电器", "小家电": "家用电器", "厨卫电器": "家用电器", "家电零部件": "家用电器", "照明设备": "家用电器", "其他家电": "家用电器", "其他家电Ⅱ": "家用电器",
    "IT服务": "计算机", "软件开发": "计算机", "计算机设备": "计算机", "IT服务Ⅱ": "计算机",
    "通信设备": "通信", "通信服务": "通信",
    "半导体": "电子", "消费电子": "电子", "光学光电子": "电子", "元件": "电子", "电子化学品": "电子", "电子化学品Ⅱ": "电子", "被动元件": "电子", "印制电路板": "电子", "面板": "电子", "其他电子": "电子", "其他电子Ⅱ": "电子",
    "电力设备": "电力设备", "光伏设备": "电力设备", "风电设备": "电力设备", "电池": "电力设备", "电网设备": "电力设备", "其他电源设备": "电力设备", "其他电源设备Ⅱ": "电力设备", "电机": "电力设备", "电机Ⅱ": "电力设备",
    "通用设备": "机械设备", "专用设备": "机械设备", "仪器仪表": "机械设备", "工程机械": "机械设备", "自动化设备": "机械设备", "轨交设备": "机械设备",
    "钢铁": "钢铁", "普钢": "钢铁", "特钢": "钢铁", "冶钢原料": "钢铁",
    "工业金属": "有色金属", "贵金属": "有色金属", "小金属": "有色金属", "能源金属": "有色金属", "金属新材料": "有色金属", "非金属材料": "有色金属", "非金属材料Ⅱ": "有色金属",
    "化学原料": "基础化工", "化学制品": "基础化工", "化学纤维": "基础化工", "农化制品": "基础化工", "塑料": "基础化工", "橡胶": "基础化工", "纯碱": "基础化工",
    "煤炭开采": "煤炭", "焦炭": "煤炭",
    "油气开采": "石油石化", "炼化及贸易": "石油石化", "油服工程": "石油石化",
    "水泥": "建筑材料", "玻璃玻纤": "建筑材料", "装修建材": "建筑材料", "管材": "建筑材料",
    "房屋建设": "建筑装饰", "基础建设": "建筑装饰", "专业工程": "建筑装饰", "工程咨询服务": "建筑装饰", "工程咨询服务Ⅱ": "建筑装饰", "装修装饰": "建筑装饰",
    "航空装备": "国防军工", "航天装备": "国防军工", "地面兵装": "国防军工", "船舶制造": "国防军工", "军工电子": "国防军工", "军工电子Ⅱ": "国防军工", "航天装备Ⅱ": "国防军工", "航海装备": "国防军工", "航海装备Ⅱ": "国防军工",
    "一般零售": "商贸零售", "专业连锁": "商贸零售", "互联网电商": "商贸零售", "贸易": "商贸零售", "旅游零售": "商贸零售", "旅游零售Ⅱ": "商贸零售",
    "旅游及景区": "社会服务", "酒店餐饮": "社会服务", "教育": "社会服务", "专业服务": "社会服务", "体育": "社会服务",
    "航运港口": "交通运输", "航空机场": "交通运输", "铁路公路": "交通运输", "公交": "交通运输", "物流": "交通运输",
    "电力": "公用事业", "燃气": "公用事业", "水务": "公用事业", "燃气Ⅱ": "公用事业",
    "环境治理": "环保", "环保设备": "环保", "环保设备Ⅱ": "环保",
    "养殖业": "农林牧渔", "种植业": "农林牧渔", "饲料": "农林牧渔", "动物保健": "农林牧渔", "林业": "农林牧渔", "渔业": "农林牧渔", "农产品加工": "农林牧渔", "农业综合": "农林牧渔",
    "服饰": "纺织服装", "服装家纺": "纺织服装", "纺织制造": "纺织服装", "饰品": "纺织服装",
    "造纸": "轻工制造", "包装印刷": "轻工制造", "家居用品": "轻工制造", "文娱用品": "轻工制造", "珠宝首饰": "轻工制造",
    "广告营销": "传媒", "游戏": "传媒", "影视院线": "传媒", "出版": "传媒", "数字媒体": "传媒", "电视广播": "传媒",
    "综合": "综合", "综合Ⅱ": "综合",
    "个护用品": "美容护理", "化妆品": "美容护理",
}

def map_to_sw(em_industry):
    if not em_industry or em_industry == "-":
        return None
    if em_industry in EM_TO_SW:
        return EM_TO_SW[em_industry]
    for key, val in EM_TO_SW.items():
        if key in em_industry or em_industry in key:
            return val
    return None

# 先加载已有数据（如果之前已获取一部分）
existing_file = BASE_DIR.parent / "data" / "industry_map_partial.json"
if existing_file.exists():
    with open(existing_file, 'r', encoding='utf-8') as f:
        prev = json.load(f)
        code_to_name = prev.get("code_to_name", {})
        code_to_industry = prev.get("code_to_industry_em", {})
    print(f"加载已有数据: {len(code_to_name)} 只")

page_size = 100
page = len(code_to_name) // page_size + 1
total = None
max_consecutive_failures = 20
consecutive_failures = 0

print(f"从第{page}页开始获取...")

while True:
    params = {
        "pn": str(page), "pz": str(page_size), "po": "1", "np": "1",
        "ut": "bd1d9ddb04089700cf9c27f6f7426281", "fltt": "2", "invt": "2", "fid": "f12",
        "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81+s:2048",
        "fields": "f12,f14,f100",
    }
    try:
        resp = session.get(url, params=params, timeout=20)
        data = resp.json()
        diff = data.get("data", {}).get("diff", [])
        if total is None:
            total = data.get("data", {}).get("total", 0)
            print(f"总共: {total} 只股票")
        if not diff:
            break
        new_count = 0
        for item in diff:
            code = str(item.get("f12", "")).strip()
            name = str(item.get("f14", "")).strip()
            industry = str(item.get("f100", "")).strip()
            if code and name:
                if code not in code_to_name:
                    new_count += 1
                code_to_name[code] = name
                if industry and industry != "-" and industry != "":
                    code_to_industry[code] = industry
        consecutive_failures = 0
        if page % 5 == 0 or len(code_to_name) >= total:
            print(f"  第{page}页: +{new_count}, 累计{len(code_to_name)}/{total}")
        if len(code_to_name) >= total:
            break
        page += 1
        time.sleep(0.5)
    except Exception as e:
        consecutive_failures += 1
        if consecutive_failures > max_consecutive_failures:
            print(f"\n连续失败{consecutive_failures}次，停止在第{page}页")
            break
        time.sleep(2)

# 保存中间结果
with open(existing_file, 'w', encoding='utf-8') as f:
    json.dump({"code_to_name": code_to_name, "code_to_industry_em": code_to_industry}, f, ensure_ascii=False)

print(f"\n原始东财行业: {len(code_to_industry)}/{len(code_to_name)}")

sw_mapped = {}
unmapped_em = set()
for code, em_ind in code_to_industry.items():
    sw = map_to_sw(em_ind)
    if sw:
        sw_mapped[code] = sw
    else:
        unmapped_em.add(em_ind)

print(f"映射到申万一级: {len(sw_mapped)}")
if unmapped_em:
    print(f"未映射东财行业({len(unmapped_em)}个): {sorted(unmapped_em)}")

ind_counts = defaultdict(int)
for ind in sw_mapped.values():
    ind_counts[ind] += 1
print(f"\n申万一级行业 ({len(ind_counts)}个):")
for ind, cnt in sorted(ind_counts.items(), key=lambda x: -x[1]):
    print(f"  {ind}: {cnt}")

# CMDA对比
import re
cmda_root = BASE_DIR.parent.parent / "data" / "CMDA_管理层讨论与分析_ALL"
pattern = re.compile(r"^(\d{6})_(.+?)_\d{4}-\d{2}-\d{2}\.txt$")
cmda_codes = set()
cmda_file_names = {}
if cmda_root.exists():
    for yd in sorted(cmda_root.iterdir()):
        if not yd.is_dir(): continue
        td = yd / "文本"
        if not td.exists(): continue
        for f in td.iterdir():
            m = pattern.match(f.name)
            if m:
                c, n = m.group(1), m.group(2)
                cmda_codes.add(c)
                if c not in cmda_file_names:
                    cmda_file_names[c] = n

# ST/PT检测：用东财最新名称（更准确）
st_codes = set()
fin_codes = set()
for code in cmda_codes:
    # 使用东财最新名称判断ST
    em_name = code_to_name.get(code, cmda_file_names.get(code, ""))
    file_name = cmda_file_names.get(code, "")
    if "ST" in em_name or "*ST" in em_name or "PT" in em_name or "ST" in file_name or "*ST" in file_name or "PT" in file_name:
        st_codes.add(code)
    if sw_mapped.get(code) in ("银行", "非银金融"):
        fin_codes.add(code)

print(f"\nCMDA企业: {len(cmda_codes)}")
matched = sum(1 for c in cmda_codes if c in sw_mapped)
no_ind_list = [(c, cmda_file_names.get(c,""), code_to_name.get(c,""), code_to_industry.get(c,"")) for c in cmda_codes if c not in sw_mapped]
print(f"有申万行业: {matched}, 无行业: {len(no_ind_list)}")

valid_codes = cmda_codes - st_codes - fin_codes
valid_with_ind = [c for c in valid_codes if c in sw_mapped]
print(f"\n剔除ST/PT: {len(st_codes)}, 剔除金融(银行+非银): {len(fin_codes)}")
print(f"有效监测企业: {len(valid_codes)} (其中{len(valid_with_ind)}有行业可计算GW)")

# 展示ST企业示例
if st_codes:
    print(f"\nST/PT企业示例:")
    for c in list(st_codes)[:10]:
        print(f"  {c} {code_to_name.get(c, cmda_file_names.get(c,''))}")

output = BASE_DIR.parent / "data" / "industry_map.json"
output.parent.mkdir(parents=True, exist_ok=True)
with open(output, 'w', encoding='utf-8') as f:
    json.dump({
        "code_to_industry_em": code_to_industry,
        "code_to_industry_sw": sw_mapped,
        "code_to_name": code_to_name,
        "st_codes": list(st_codes),
        "fin_codes": list(fin_codes),
        "valid_codes": list(valid_codes),
    }, f, ensure_ascii=False, indent=2)
print(f"\n已保存: {output}")

# 清理中间文件
if existing_file.exists():
    existing_file.unlink()
