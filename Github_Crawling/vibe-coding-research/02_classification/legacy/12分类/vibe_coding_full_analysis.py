#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vibe Coding 完整分析脚本
- 基础分布统计
- 时间序列分析
- 交叉分析
- 轻量词频分析
- 输出CSV表格和可视化图表

输出目录: analysis_output/
"""

import json
import csv
import os
import sys
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

# 配置
INPUT_FILE = "vibe_coding_analysis_with_time.jsonl"
OUTPUT_DIR = "analysis_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


def load_data():
    """加载数据"""
    results = []
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found")
        return results
    
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                # 解析日期
                created_at = data.get('created_at')
                if created_at:
                    try:
                        data['created_date'] = datetime.fromisoformat(created_at.replace('Z', '+00:00')).date()
                    except:
                        data['created_date'] = None
                results.append(data)
            except json.JSONDecodeError:
                continue
    
    print(f"Loaded {len(results)} records")
    return results


def save_csv(filename, headers, rows):
    """保存CSV"""
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
    print(f"  Saved: {filepath}")


def basic_distribution(results):
    """基础分布统计"""
    print("\n" + "="*60)
    print("模块一：基础分布")
    print("="*60)
    
    total = len(results)
    
    # 宏观类别
    macro_cats = Counter([r.get('macro_category', 'unknown') for r in results])
    print(f"\n1. 宏观类别分布 (Total: {total})")
    rows = []
    for cat, count in macro_cats.most_common():
        pct = count / total * 100
        print(f"   {cat:25s}: {count:4d} ({pct:5.1f}%)")
        rows.append([cat, count, f"{pct:.1f}%"])
    save_csv("01_macro_category.csv", ["Category", "Count", "Percentage"], rows)
    
    # 微观场景
    micro_scenes = Counter([r.get('micro_scenario', 'unknown') for r in results])
    print(f"\n2. 微观场景分布 (Top 12)")
    rows = []
    for scene, count in micro_scenes.most_common(12):
        pct = count / total * 100
        print(f"   {scene:20s}: {count:4d} ({pct:5.1f}%)")
        rows.append([scene, count, f"{pct:.1f}%"])
    save_csv("02_micro_scenario.csv", ["Scenario", "Count", "Percentage"], rows)
    
    # AI生成分数
    ai_scores = Counter([r.get('ai_generation_score', 0) for r in results])
    print(f"\n3. AI生成分数分布")
    rows = []
    for score in range(1, 6):
        count = ai_scores.get(score, 0)
        pct = count / total * 100
        stars = '★' * score + '☆' * (5-score)
        print(f"   {stars} ({score}): {count:4d} ({pct:5.1f}%)")
        rows.append([score, stars, count, f"{pct:.1f}%"])
    save_csv("03_ai_score_distribution.csv", ["Score", "Stars", "Count", "Percentage"], rows)
    
    # 复杂度
    complexity = Counter([r.get('complexity_level', 0) for r in results])
    labels = {1: "简单脚本", 2: "轻量工具", 3: "中等应用", 4: "复杂系统", 5: "企业级"}
    print(f"\n4. 复杂度分布")
    rows = []
    for level in range(1, 6):
        count = complexity.get(level, 0)
        pct = count / total * 100
        print(f"   {level} - {labels[level]:8s}: {count:4d} ({pct:5.1f}%)")
        rows.append([level, labels[level], count, f"{pct:.1f}%"])
    save_csv("04_complexity_distribution.csv", ["Level", "Label", "Count", "Percentage"], rows)
    
    # 编程语言
    languages = Counter([r.get('language') or 'Unknown' for r in results])
    print(f"\n5. 编程语言分布 (Top 10)")
    rows = []
    for lang, count in languages.most_common(10):
        pct = count / total * 100
        print(f"   {lang or 'Unknown':15s}: {count:4d} ({pct:5.1f}%)")
        rows.append([lang, count, f"{pct:.1f}%"])
    save_csv("05_language_distribution.csv", ["Language", "Count", "Percentage"], rows)


def cross_analysis(results):
    """交叉分析"""
    print("\n" + "="*60)
    print("模块二：交叉分析")
    print("="*60)
    
    # 1. AI浓度 vs 项目类型
    print("\n1. AI浓度 vs 项目类型（平均AI分数）")
    ai_by_macro = defaultdict(list)
    for r in results:
        macro = r.get('macro_category', 'unknown')
        ai = r.get('ai_generation_score', 0)
        ai_by_macro[macro].append(ai)
    
    rows = []
    for macro, scores in sorted(ai_by_macro.items(), key=lambda x: -sum(x[1])/len(x[1])):
        avg = sum(scores) / len(scores)
        print(f"   {macro:25s}: {avg:.2f}/5.0 (n={len(scores)})")
        rows.append([macro, f"{avg:.2f}", len(scores)])
    save_csv("06_ai_by_macro_category.csv", ["Category", "Avg_AI_Score", "Count"], rows)
    
    # 2. AI浓度 vs 复杂度
    print("\n2. AI浓度 vs 复杂度")
    ai_by_complexity = defaultdict(list)
    for r in results:
        comp = r.get('complexity_level', 0)
        ai = r.get('ai_generation_score', 0)
        ai_by_complexity[comp].append(ai)
    
    rows = []
    for comp in range(1, 6):
        scores = ai_by_complexity.get(comp, [])
        if scores:
            avg = sum(scores) / len(scores)
            print(f"   复杂度{comp}: 平均AI分数 {avg:.2f} (n={len(scores)})")
            rows.append([comp, f"{avg:.2f}", len(scores)])
    save_csv("07_ai_by_complexity.csv", ["Complexity", "Avg_AI_Score", "Count"], rows)
    
    # 相关系数
    ai_scores = [r.get('ai_generation_score', 0) for r in results]
    comp_scores = [r.get('complexity_level', 0) for r in results]
    if len(ai_scores) > 1 and len(comp_scores) > 1:
        corr = np.corrcoef(ai_scores, comp_scores)[0, 1]
        print(f"\n   相关系数: {corr:.3f}")
    
    # 3. 场景AI浓度排名
    print("\n3. 各场景平均AI浓度排名")
    ai_by_scene = defaultdict(list)
    for r in results:
        scene = r.get('micro_scenario', 'unknown')
        ai = r.get('ai_generation_score', 0)
        ai_by_scene[scene].append(ai)
    
    rows = []
    for scene, scores in sorted(ai_by_scene.items(), key=lambda x: -sum(x[1])/len(x[1])):
        avg = sum(scores) / len(scores)
        print(f"   {scene:20s}: {avg:.2f}/5.0 (n={len(scores)})")
        rows.append([scene, f"{avg:.2f}", len(scores)])
    save_csv("08_ai_by_scenario.csv", ["Scenario", "Avg_AI_Score", "Count"], rows)


def word_frequency(results):
    """轻量词频分析"""
    print("\n" + "="*60)
    print("模块三：项目意图词频分析")
    print("="*60)
    
    # 提取所有core_intent
    intents = [r.get('core_intent', '') for r in results if r.get('core_intent')]
    
    # 简单分词（按常见模式）
    words = []
    for intent in intents:
        # 中文分词：按字符提取动词/名词
        # 简单规则：2-4个字符的中文词组
        import re
        # 提取中文词汇
        cn_words = re.findall(r'[\u4e00-\u9fa5]{2,4}', intent)
        words.extend(cn_words)
        # 提取英文单词
        en_words = re.findall(r'[a-zA-Z]+', intent)
        words.extend([w.lower() for w in en_words if len(w) > 2])
    
    word_counts = Counter(words)
    
    print("\nTop 30 高频词汇：")
    rows = []
    for word, count in word_counts.most_common(30):
        print(f"   {word:15s}: {count:3d}")
        rows.append([word, count])
    
    save_csv("09_word_frequency.csv", ["Word", "Count"], rows)


def time_series_analysis(results):
    """时间序列分析"""
    print("\n" + "="*60)
    print("模块四：时间序列分析")
    print("="*60)
    
    # 过滤有日期的数据
    dated_results = [r for r in results if r.get('created_date')]
    if not dated_results:
        print("No date information found")
        return
    
    # 按日期分组
    daily_data = defaultdict(list)
    for r in dated_results:
        date = r['created_date']
        daily_data[date].append(r)
    
    dates = sorted(daily_data.keys())
    print(f"\n数据时间范围: {dates[0]} 至 {dates[-1]} ({len(dates)} 天)")
    
    # 1. 每日创建量趋势
    print("\n1. 每日创建量统计")
    daily_counts = [(d, len(daily_data[d])) for d in dates]
    
    rows = []
    for date, count in daily_counts:
        print(f"   {date}: {count:3d} 个项目")
        rows.append([date, count])
    save_csv("10_daily_creation.csv", ["Date", "Count"], rows)
    
    # 2. 每日AI浓度趋势
    print("\n2. 每日平均AI分数")
    daily_ai = []
    for d in dates:
        scores = [r.get('ai_generation_score', 0) for r in daily_data[d]]
        avg_ai = sum(scores) / len(scores) if scores else 0
        high_ai_pct = sum(1 for s in scores if s >= 4) / len(scores) * 100 if scores else 0
        daily_ai.append((d, avg_ai, high_ai_pct))
    
    rows = []
    for date, avg_ai, high_pct in daily_ai:
        print(f"   {date}: 平均 {avg_ai:.2f}, 高AI占比 {high_pct:.1f}%")
        rows.append([date, f"{avg_ai:.2f}", f"{high_pct:.1f}%"])
    save_csv("11_daily_ai_trend.csv", ["Date", "Avg_AI_Score", "High_AI_Percentage"], rows)
    
    # 3. 场景热度趋势（简化版：统计每天的场景分布）
    print("\n3. 场景热度趋势（每日Top3场景）")
    rows = []
    for d in dates[:10]:  # 只显示前10天避免过长
        scenes = Counter([r.get('micro_scenario', 'unknown') for r in daily_data[d]])
        top3 = scenes.most_common(3)
        top3_str = ", ".join([f"{s}({c})" for s, c in top3])
        print(f"   {d}: {top3_str}")
        for scene, count in top3:
            rows.append([d, scene, count])
    save_csv("12_daily_scenario_trend.csv", ["Date", "Scenario", "Count"], rows)
    
    # 4. 质量趋势
    print("\n4. 每日质量指标")
    daily_quality = []
    for d in dates:
        day_repos = daily_data[d]
        stars = [r.get('stars', 0) for r in day_repos]
        avg_stars = sum(stars) / len(stars) if stars else 0
        complexities = [r.get('complexity_level', 0) for r in day_repos]
        avg_complexity = sum(complexities) / len(complexities) if complexities else 0
        signal_count = sum(1 for r in day_repos if r.get('tier') == 'signal')
        daily_quality.append((d, avg_stars, avg_complexity, signal_count))
    
    rows = []
    for date, avg_stars, avg_comp, sig_count in daily_quality:
        print(f"   {date}: 平均Stars {avg_stars:.1f}, 平均复杂度 {avg_comp:.2f}, Signal项目 {sig_count}")
        rows.append([date, f"{avg_stars:.2f}", f"{avg_comp:.2f}", sig_count])
    save_csv("13_daily_quality_trend.csv", ["Date", "Avg_Stars", "Avg_Complexity", "Signal_Count"], rows)
    
    # 绘制图表
    plot_time_series(dates, daily_counts, daily_ai, daily_quality)


def plot_time_series(dates, daily_counts, daily_ai, daily_quality):
    """绘制时间序列图表"""
    print("\n正在生成可视化图表...")
    
    # 转换日期格式
    date_objs = [datetime.strptime(str(d), '%Y-%m-%d').date() for d in dates]
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Vibe Coding Time Series Analysis', fontsize=14, fontweight='bold')
    
    # 1. 每日创建量
    counts = [c for _, c in daily_counts]
    axes[0, 0].plot(date_objs, counts, marker='o', linewidth=2, markersize=4)
    axes[0, 0].set_title('Daily Project Creation Count')
    axes[0, 0].set_xlabel('Date')
    axes[0, 0].set_ylabel('Count')
    axes[0, 0].grid(True, alpha=0.3)
    axes[0, 0].xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    plt.setp(axes[0, 0].xaxis.get_majorticklabels(), rotation=45)
    
    # 2. AI浓度趋势
    avg_ai_scores = [ai for _, ai, _ in daily_ai]
    axes[0, 1].plot(date_objs, avg_ai_scores, marker='s', color='orange', linewidth=2, markersize=4)
    axes[0, 1].set_title('Daily Average AI Generation Score')
    axes[0, 1].set_xlabel('Date')
    axes[0, 1].set_ylabel('Avg AI Score')
    axes[0, 1].set_ylim(0, 5)
    axes[0, 1].grid(True, alpha=0.3)
    axes[0, 1].xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    plt.setp(axes[0, 1].xaxis.get_majorticklabels(), rotation=45)
    
    # 3. 高AI占比
    high_ai_pcts = [pct for _, _, pct in daily_ai]
    axes[1, 0].plot(date_objs, high_ai_pcts, marker='^', color='green', linewidth=2, markersize=4)
    axes[1, 0].set_title('High AI Score (>=4) Percentage')
    axes[1, 0].set_xlabel('Date')
    axes[1, 0].set_ylabel('Percentage (%)')
    axes[1, 0].grid(True, alpha=0.3)
    axes[1, 0].xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    plt.setp(axes[1, 0].xaxis.get_majorticklabels(), rotation=45)
    
    # 4. 平均Stars（质量指标）
    avg_stars = [s for _, s, _, _ in daily_quality]
    axes[1, 1].plot(date_objs, avg_stars, marker='d', color='red', linewidth=2, markersize=4)
    axes[1, 1].set_title('Daily Average Stars (Quality Indicator)')
    axes[1, 1].set_xlabel('Date')
    axes[1, 1].set_ylabel('Avg Stars')
    axes[1, 1].grid(True, alpha=0.3)
    axes[1, 1].xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    plt.setp(axes[1, 1].xaxis.get_majorticklabels(), rotation=45)
    
    plt.tight_layout()
    chart_path = os.path.join(OUTPUT_DIR, "14_time_series_charts.png")
    plt.savefig(chart_path, dpi=150, bbox_inches='tight')
    print(f"  Saved chart: {chart_path}")
    plt.close()


def summary_insights(results):
    """汇总核心洞察"""
    print("\n" + "="*60)
    print("核心洞察摘要")
    print("="*60)
    
    total = len(results)
    
    # 时间范围
    dated = [r for r in results if r.get('created_date')]
    if dated:
        dates = [r['created_date'] for r in dated]
        date_range = f"{min(dates)} 至 {max(dates)}"
        days = (max(dates) - min(dates)).days + 1
        avg_per_day = len(dated) / days if days > 0 else 0
        
        print(f"\n1. 时间覆盖")
        print(f"   数据范围: {date_range} ({days} 天)")
        print(f"   日均项目: {avg_per_day:.1f} 个")
    
    # AI渗透
    high_ai = sum(1 for r in results if r.get('ai_generation_score', 0) >= 4)
    print(f"\n2. AI参与度")
    print(f"   高AI项目(>=4分): {high_ai} 个 ({high_ai/total*100:.1f}%)")
    
    avg_ai = sum(r.get('ai_generation_score', 0) for r in results) / total
    print(f"   平均AI分数: {avg_ai:.2f}/5.0")
    
    # 主力场景
    scenes = Counter([r.get('micro_scenario', 'unknown') for r in results])
    top3_scenes = scenes.most_common(3)
    print(f"\n3. 主力场景 (Top 3)")
    for scene, count in top3_scenes:
        print(f"   {scene}: {count} 个 ({count/total*100:.1f}%)")
    
    # 主力类型
    cats = Counter([r.get('macro_category', 'unknown') for r in results])
    print(f"\n4. 项目类型分布")
    for cat, count in cats.most_common():
        print(f"   {cat}: {count} 个 ({count/total*100:.1f}%)")
    
    # 保存摘要
    summary_path = os.path.join(OUTPUT_DIR, "00_summary.txt")
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write("Vibe Coding Analysis Summary\n")
        f.write("="*50 + "\n\n")
        f.write(f"Total Projects: {total}\n")
        f.write(f"Date Range: {date_range if dated else 'N/A'}\n")
        f.write(f"Avg AI Score: {avg_ai:.2f}/5.0\n")
        f.write(f"High AI Projects: {high_ai} ({high_ai/total*100:.1f}%)\n\n")
        f.write("Top 3 Scenes:\n")
        for scene, count in top3_scenes:
            f.write(f"  - {scene}: {count}\n")
    print(f"\n  Saved summary: {summary_path}")


def main():
    print("="*60)
    print("Vibe Coding 完整分析")
    print("="*60)
    print(f"输出目录: {OUTPUT_DIR}/")
    
    results = load_data()
    if not results:
        print("No data loaded, exit")
        return
    
    # 执行各模块
    summary_insights(results)
    basic_distribution(results)
    cross_analysis(results)
    word_frequency(results)
    time_series_analysis(results)
    
    print("\n" + "="*60)
    print("分析完成！所有输出保存在 analysis_output/ 目录")
    print("="*60)


if __name__ == "__main__":
    main()
