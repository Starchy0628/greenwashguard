"""
根据 GW指数_其他类企业申万行业重分类.md 更新 backend/data/industry_map.json
保证下次全量导入时行业分类一致。
"""
import sys
import re
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MAP_PATH = BASE_DIR / "backend" / "data" / "industry_map.json"
MD_PATH = BASE_DIR / "GW指数_其他类企业申万行业重分类.md"


def parse_md(path):
    md = open(path, 'r', encoding='utf-8').read()
    sections = re.split(r'\n##\s+', md)
    name_to_industry = {}
    excluded_non_fin = []
    excluded_delisted = []
    current_excluded = None

    for sec in sections[1:]:
        lines = sec.strip().split('\n')
        title_line = lines[0].strip()

        if title_line.startswith('已剔除企业清单'):
            for line in lines[1:]:
                line = line.strip()
                if line.startswith('### 非银金融'):
                    current_excluded = excluded_non_fin
                    continue
                elif line.startswith('### 退市股'):
                    current_excluded = excluded_delisted
                    continue
                if line.startswith('- ') and current_excluded is not None:
                    current_excluded.append(line[2:].strip())
            continue

        industry = title_line.split('（')[0].strip()
        for line in lines:
            line = line.strip()
            if not line.startswith('|'):
                continue
            parts = [p.strip() for p in line.split('|')]
            parts = [p for p in parts if p]
            if len(parts) >= 2 and parts[0] != '企业名称' and '---' not in parts[0]:
                name_to_industry[parts[0]] = industry

    return name_to_industry, excluded_non_fin, excluded_delisted


def main():
    name_to_industry, excluded_non_fin, excluded_delisted = parse_md(MD_PATH)

    with open(MAP_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    code_to_name = data.get("code_to_name", {})
    code_to_ind = data.get("code_to_industry_sw", {})
    fin_codes = set(data.get("fin_codes", []))
    valid_codes = set(data.get("valid_codes", []))

    # 反向名称到代码映射
    name_to_codes = {}
    for code, name in code_to_name.items():
        name_to_codes.setdefault(name, []).append(code)

    updated = 0
    not_found = []
    for name, industry in name_to_industry.items():
        codes = name_to_codes.get(name, [])
        if not codes:
            not_found.append(name)
            continue
        for code in codes:
            if code_to_ind.get(code) != industry:
                code_to_ind[code] = industry
                updated += 1
            # 确保这些代码在 valid_codes 中，并从 fin_codes 中移除
            valid_codes.add(code)
            if code in fin_codes:
                fin_codes.discard(code)

    # 处理剔除企业：从 valid_codes 移除，加入 fin_codes（金融类）或从活跃监测移除
    excluded_codes = set()
    for name in set(excluded_non_fin) | set(excluded_delisted):
        codes = name_to_codes.get(name, [])
        excluded_codes.update(codes)

    for code in excluded_codes:
        valid_codes.discard(code)
        if code in code_to_ind:
            # 退市股保留原行业但不再活跃；非银金融标记为金融
            if code_to_name.get(code) in excluded_non_fin:
                fin_codes.add(code)

    # 同步 valid_with_industry
    valid_with_industry = [code for code in valid_codes if code_to_ind.get(code) and code_to_ind[code] not in ("银行", "非银金融", "其他")]

    data["code_to_industry_sw"] = code_to_ind
    data["fin_codes"] = sorted(list(fin_codes))
    data["valid_codes"] = sorted(list(valid_codes))
    data["valid_with_industry"] = sorted(valid_with_industry)

    with open(MAP_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"更新行业映射: {updated} 条")
    print(f"金融类代码: {len(fin_codes)} 个")
    print(f"有效监测代码: {len(valid_codes)} 个")
    print(f"有行业有效代码: {len(valid_with_industry)} 个")
    if not_found:
        print(f"未找到代码的企业: {len(not_found)} 家")
        for n in not_found[:10]:
            print(f"  {n}")


if __name__ == "__main__":
    main()
