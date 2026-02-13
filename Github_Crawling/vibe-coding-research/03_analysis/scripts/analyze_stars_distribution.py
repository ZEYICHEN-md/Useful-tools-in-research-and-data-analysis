# -*- coding: utf-8 -*-
"""
统计 vibe_coding_analysis_8cat.jsonl 中项目的 stars 分布
"""
import json
import csv
import os
from collections import defaultdict

def analyze_stars_distribution():
    # 读取 JSONL 文件
    input_file = 'vibe_coding_analysis_8cat.jsonl'
    output_dir = 'analysis_report'
    output_file = os.path.join(output_dir, 'stars_distribution.csv')
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 统计变量
    total_count = 0
    less_than_20 = 0  # < 20 stars
    greater_than_20 = 0  # > 20 stars
    equal_20 = 0  # = 20 stars
    
    # 按 micro_scenario 统计
    scenario_stats = defaultdict(lambda: {'total': 0, 'lt_20': 0, 'gt_20': 0, 'eq_20': 0})
    
    # 更细粒度的区间统计
    star_ranges = {
        '0 stars': 0,
        '1-5 stars': 0,
        '6-10 stars': 0,
        '11-20 stars': 0,
        '21-50 stars': 0,
        '51-100 stars': 0,
        '101-500 stars': 0,
        '501+ stars': 0
    }
    
    print(f"正在读取 {input_file}...")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            
            try:
                record = json.loads(line.strip())
                stars = record.get('stars', 0)
                scenario = record.get('micro_scenario', '未知')
                
                total_count += 1
                scenario_stats[scenario]['total'] += 1
                
                # 统计 <20 和 >20
                if stars < 20:
                    less_than_20 += 1
                    scenario_stats[scenario]['lt_20'] += 1
                elif stars > 20:
                    greater_than_20 += 1
                    scenario_stats[scenario]['gt_20'] += 1
                else:  # stars == 20
                    equal_20 += 1
                    scenario_stats[scenario]['eq_20'] += 1
                
                # 统计区间
                if stars == 0:
                    star_ranges['0 stars'] += 1
                elif 1 <= stars <= 5:
                    star_ranges['1-5 stars'] += 1
                elif 6 <= stars <= 10:
                    star_ranges['6-10 stars'] += 1
                elif 11 <= stars <= 20:
                    star_ranges['11-20 stars'] += 1
                elif 21 <= stars <= 50:
                    star_ranges['21-50 stars'] += 1
                elif 51 <= stars <= 100:
                    star_ranges['51-100 stars'] += 1
                elif 101 <= stars <= 500:
                    star_ranges['101-500 stars'] += 1
                else:  # >= 501
                    star_ranges['501+ stars'] += 1
                    
            except json.JSONDecodeError:
                print(f"警告: 跳过无效的JSON行")
                continue
    
    # 输出统计结果
    print(f"\n{'='*60}")
    print(f"总项目数: {total_count}")
    print(f"{'='*60}")
    print(f"\n【Stars 分布统计】")
    print(f"小于 20 stars (< 20): {less_than_20} ({less_than_20/total_count*100:.2f}%)")
    print(f"等于 20 stars (= 20): {equal_20} ({equal_20/total_count*100:.2f}%)")
    print(f"大于 20 stars (> 20): {greater_than_20} ({greater_than_20/total_count*100:.2f}%)")
    
    print(f"\n【详细区间分布】")
    for range_name, count in star_ranges.items():
        pct = count / total_count * 100
        print(f"{range_name}: {count} ({pct:.2f}%)")
    
    print(f"\n【按 Micro-Scenario 统计】")
    print(f"{'类别':<20} {'总数':<8} {'<20':<8} {'=20':<8} {'>20':<8} {'>20占比':<10}")
    print("-" * 70)
    for scenario in sorted(scenario_stats.keys()):
        stats = scenario_stats[scenario]
        gt_20_pct = stats['gt_20'] / stats['total'] * 100 if stats['total'] > 0 else 0
        print(f"{scenario:<20} {stats['total']:<8} {stats['lt_20']:<8} {stats['eq_20']:<8} {stats['gt_20']:<8} {gt_20_pct:.2f}%")
    
    # 写入 CSV 文件
    with open(output_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.writer(csvfile)
        
        # 第一部分：总体统计
        writer.writerow(['Stars 分布统计'])
        writer.writerow(['分类', '数量', '占比'])
        writer.writerow(['小于 20 stars (< 20)', less_than_20, f'{less_than_20/total_count*100:.2f}%'])
        writer.writerow(['等于 20 stars (= 20)', equal_20, f'{equal_20/total_count*100:.2f}%'])
        writer.writerow(['大于 20 stars (> 20)', greater_than_20, f'{greater_than_20/total_count*100:.2f}%'])
        writer.writerow(['总计', total_count, '100.00%'])
        writer.writerow([])  # 空行
        
        # 第二部分：详细区间统计
        writer.writerow(['详细区间分布'])
        writer.writerow(['Stars 区间', '数量', '占比'])
        for range_name, count in star_ranges.items():
            pct = count / total_count * 100
            writer.writerow([range_name, count, f'{pct:.2f}%'])
        writer.writerow([])  # 空行
        
        # 第三部分：按类别统计
        writer.writerow(['按 Micro-Scenario 统计'])
        writer.writerow(['类别', '总数', '<20', '=20', '>20', '>20占比'])
        for scenario in sorted(scenario_stats.keys()):
            stats = scenario_stats[scenario]
            gt_20_pct = stats['gt_20'] / stats['total'] * 100 if stats['total'] > 0 else 0
            writer.writerow([scenario, stats['total'], stats['lt_20'], stats['eq_20'], stats['gt_20'], f'{gt_20_pct:.2f}%'])
    
    print(f"\n{'='*60}")
    print(f"[OK] CSV 文件已保存: {output_file}")
    print(f"{'='*60}")
    
    return {
        'total': total_count,
        'less_than_20': less_than_20,
        'equal_20': equal_20,
        'greater_than_20': greater_than_20,
        'star_ranges': star_ranges,
        'scenario_stats': dict(scenario_stats)
    }

if __name__ == '__main__':
    result = analyze_stars_distribution()
