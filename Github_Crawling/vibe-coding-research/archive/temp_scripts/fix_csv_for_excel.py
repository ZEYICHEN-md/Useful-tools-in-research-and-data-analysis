#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复CSV文件，使其在Excel中正确显示
- 添加UTF-8 BOM头
- 将多行内容转为单行
- 清理格式问题
"""

import csv
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')


def fix_csv(input_file: str, output_file: str = None):
    """修复CSV文件以便Excel正确打开"""
    
    if output_file is None:
        # 默认输出为原文件名加 _fixed
        p = Path(input_file)
        output_file = str(p.parent / f"{p.stem}_fixed{p.suffix}")
    
    print(f"读取: {input_file}")
    
    # 读取原始CSV
    with open(input_file, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)
    
    print(f"总行数: {len(rows)}")
    
    # 清理数据
    cleaned_rows = []
    for i, row in enumerate(rows):
        cleaned = dict(row)
        
        # 清理 readme_cleaned: 转为单行
        if cleaned.get("readme_cleaned"):
            text = cleaned["readme_cleaned"]
            text = text.replace("\r\n", " ").replace("\n", " ").replace("\r", " ")
            # 合并多个空格
            text = " ".join(text.split())
            cleaned["readme_cleaned"] = text[:10000]  # 限制长度
        
        # 清理 readme_raw: 保留结构但限制长度
        if cleaned.get("readme_raw"):
            text = cleaned["readme_raw"]
            # 将换行符统一为 \n，便于查看
            text = text.replace("\r\n", "\\n").replace("\r", "\\n").replace("\n", "\\n")
            cleaned["readme_raw"] = text[:30000]  # Excel单元格限制约32767字符
        
        # 清理 description
        if cleaned.get("description"):
            text = cleaned["description"]
            text = text.replace("\r\n", " ").replace("\n", " ").replace("\r", " ")
            text = " ".join(text.split())
            cleaned["description"] = text[:500]
        
        cleaned_rows.append(cleaned)
        
        if (i + 1) % 100 == 0:
            print(f"  已处理: {i + 1}/{len(rows)}")
    
    # 保存为UTF-8 with BOM (Excel兼容格式)
    with open(output_file, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(cleaned_rows)
    
    print(f"\n✅ 已保存: {output_file}")
    print(f"   总行数: {len(cleaned_rows)}")
    print(f"\n💡 Excel打开方式:")
    print(f"   1. 直接双击打开 {Path(output_file).name}")
    print(f"   2. 或使用 Excel -> 数据 -> 从文本/CSV 导入")


def main():
    import glob
    
    # 查找所有 unbiased_*.csv 文件
    csv_files = glob.glob("unbiased_*.csv")
    
    if not csv_files:
        print("未找到 unbiased_*.csv 文件")
        return
    
    print("找到以下CSV文件:")
    for i, f in enumerate(csv_files, 1):
        print(f"  {i}. {f}")
    
    # 默认处理最大的那个（通常是 all）
    all_files = [f for f in csv_files if "_all_" in f]
    if all_files:
        target = all_files[0]
    else:
        target = csv_files[0]
    
    print(f"\n正在处理: {target}")
    fix_csv(target)


if __name__ == "__main__":
    main()
