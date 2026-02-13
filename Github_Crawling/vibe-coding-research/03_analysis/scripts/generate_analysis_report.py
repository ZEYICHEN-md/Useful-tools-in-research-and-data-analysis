#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vibe Coding 分析报告生成器
整合分析、统计、案例展示功能
输出：量化数据 + 真实案例 + 原文引用

输出目录: analysis_report/
"""

import json
import csv
import os
import sys
import re
from collections import Counter, defaultdict
from datetime import datetime
from typing import List, Dict, Any, Optional

sys.stdout.reconfigure(encoding='utf-8')

# ========== 配置 ==========
INPUT_FILE = "vibe_coding_analysis_8cat.jsonl"  # 使用8分类版本的分析结果
OUTPUT_DIR = "analysis_report"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_data() -> List[Dict]:
    """加载分析结果数据"""
    results = []
    if not os.path.exists(INPUT_FILE):
        print(f"❌ 错误: 找不到输入文件 {INPUT_FILE}")
        print("   请先运行 deepseek_analyzer_8cat.py 生成分析结果")
        return results
    
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                results.append(data)
            except json.JSONDecodeError:
                continue
    
    print(f"✅ 已加载 {len(results)} 条分析结果")
    return results


def save_csv(filename: str, headers: List[str], rows: List[List]):
    """保存CSV文件"""
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
    print(f"   📄 CSV: {filepath}")


def analyze_by_macro_category(results: List[Dict]) -> Dict[str, Dict]:
    """按宏观分类分析"""
    macro_categories = defaultdict(list)
    
    for r in results:
        macro = r.get('macro_category', 'unknown')
        macro_categories[macro].append(r)
    
    analysis = {}
    for macro_name, repos in macro_categories.items():
        ai_scores = [r.get('ai_generation_score', 0) for r in repos]
        complexity_scores = [r.get('complexity_level', 0) for r in repos]
        stars_list = [r.get('stars', 0) for r in repos]
        
        # 收集该宏观分类下的微观场景分布
        micro_scenes = Counter([r.get('micro_scenario', 'unknown') for r in repos])
        
        analysis[macro_name] = {
            'count': len(repos),
            'percentage': len(repos) / len(results) * 100,
            'avg_ai_index': sum(ai_scores) / len(ai_scores) if ai_scores else 0,
            'avg_complexity': sum(complexity_scores) / len(complexity_scores) if complexity_scores else 0,
            'avg_stars': sum(stars_list) / len(stars_list) if stars_list else 0,
            'micro_distribution': dict(micro_scenes.most_common()),
        }
    
    return analysis


def generate_overview(results: List[Dict], macro_analysis: Dict) -> Dict:
    """生成总体概览统计"""
    total = len(results)
    
    # 基础统计
    macro_cats = Counter([r.get('macro_category', 'unknown') for r in results])
    micro_scenes = Counter([r.get('micro_scenario', 'unknown') for r in results])
    ai_scores = [r.get('ai_generation_score', 0) for r in results]
    complexity_scores = [r.get('complexity_level', 0) for r in results]
    stars_list = [r.get('stars', 0) for r in results]
    
    # 计算指标
    high_ai_count = sum(1 for s in ai_scores if s >= 4)
    high_complexity_count = sum(1 for c in complexity_scores if c >= 4)
    high_star_count = sum(1 for s in stars_list if s >= 20)
    
    overview = {
        'total': total,
        'avg_ai_index': sum(ai_scores) / total if total > 0 else 0,
        'avg_complexity': sum(complexity_scores) / total if total > 0 else 0,
        'avg_stars': sum(stars_list) / total if total > 0 else 0,
        'high_ai_pct': high_ai_count / total * 100 if total > 0 else 0,
        'high_complexity_pct': high_complexity_count / total * 100 if total > 0 else 0,
        'high_star_pct': high_star_count / total * 100 if total > 0 else 0,
        'macro_distribution': dict(macro_cats.most_common()),
        'micro_distribution': dict(micro_scenes.most_common()),
        'macro_analysis': macro_analysis,
    }
    
    return overview


def analyze_by_category(results: List[Dict]) -> Dict[str, Dict]:
    """按微观场景分类分析"""
    categories = defaultdict(list)
    
    for r in results:
        micro = r.get('micro_scenario', 'unknown')
        categories[micro].append(r)
    
    analysis = {}
    for cat_name, repos in categories.items():
        ai_scores = [r.get('ai_generation_score', 0) for r in repos]
        complexity_scores = [r.get('complexity_level', 0) for r in repos]
        stars_list = [r.get('stars', 0) for r in repos]
        
        # 找典型案例（高AI分数 + 有描述）
        typical_cases = sorted(
            [r for r in repos if r.get('ai_generation_score', 0) >= 3 and r.get('core_intent')],
            key=lambda x: (x.get('ai_generation_score', 0), x.get('stars', 0)),
            reverse=True
        )[:5]  # 每个分类取前5个典型案例
        
        # 找原文引用（有洞察的项目）
        insights = [r for r in repos if r.get('analytical_insight')]
        
        analysis[cat_name] = {
            'count': len(repos),
            'percentage': len(repos) / len(results) * 100,
            'avg_ai_index': sum(ai_scores) / len(ai_scores) if ai_scores else 0,
            'avg_complexity': sum(complexity_scores) / len(complexity_scores) if complexity_scores else 0,
            'avg_stars': sum(stars_list) / len(stars_list) if stars_list else 0,
            'typical_cases': typical_cases,
            'insights': insights[:3],  # 取3个洞察
        }
    
    return analysis


def generate_markdown_report(results: List[Dict], overview: Dict, category_analysis: Dict):
    """生成 Markdown 分析报告"""
    report_path = os.path.join(OUTPUT_DIR, "vibe_coding_analysis_report.md")
    
    with open(report_path, 'w', encoding='utf-8') as f:
        # 标题
        f.write("# Vibe Coding 赛道分析报告\n\n")
        f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write(f"**样本规模**: {overview['total']} 个项目\n\n")
        
        # 执行摘要
        f.write("---\n\n")
        f.write("## 📋 执行摘要\n\n")
        f.write(f"- **平均 AI 特征指数**: {overview['avg_ai_index']:.2f}/5.0\n")
        f.write(f"  - AI特征指数反映项目中体现出的AI coding工具的使用特征\n")
        f.write(f"  - 5分表示具备明显的AI原生特征（如AGENTS.md、.cursorrules等配置文件）\n")
        f.write(f"- **高 AI 特征项目 (≥4分)**: {overview['high_ai_pct']:.1f}%\n")
        f.write(f"- **平均复杂度**: {overview['avg_complexity']:.2f}/5.0\n")
        f.write(f"- **平均 Stars**: {overview['avg_stars']:.1f}\n\n")
        
        # 宏观分类总表
        f.write("---\n\n")
        f.write("## 🏗️ 宏观分类分布总表\n\n")
        f.write("| 宏观分类 | 项目数 | 占比 | 平均AI特征指数 | 平均复杂度 | 平均Stars |\n")
        f.write("|----------|--------|------|----------------|------------|-----------|\n")
        for cat_name, cat_data in overview['macro_analysis'].items():
            f.write(f"| {cat_name} | {cat_data['count']} | {cat_data['percentage']:.1f}% | "
                    f"{cat_data['avg_ai_index']:.2f} | {cat_data['avg_complexity']:.2f} | "
                    f"{cat_data['avg_stars']:.1f} |\n")
        
        # 宏观分类详细分析
        f.write("\n### 宏观分类详细分析\n\n")
        for macro_name, macro_data in overview['macro_analysis'].items():
            f.write(f"\n#### {macro_name}\n\n")
            f.write(f"**统计概览**: {macro_data['count']}个项目 ({macro_data['percentage']:.1f}%) | "
                    f"AI特征指数 {macro_data['avg_ai_index']:.2f} | "
                    f"复杂度 {macro_data['avg_complexity']:.2f} | "
                    f"Stars {macro_data['avg_stars']:.1f}\n\n")
            
            f.write("**微观场景分布**:\n\n")
            f.write("| 微观场景 | 数量 | 占比 |\n")
            f.write("|----------|------|------|\n")
            for micro, count in list(macro_data['micro_distribution'].items())[:5]:
                micro_pct = count / macro_data['count'] * 100
                f.write(f"| {micro} | {count} | {micro_pct:.1f}% |\n")
        
        # 微观场景详细分析
        f.write("\n---\n\n")
        f.write("## 🎯 微观场景详细分析\n\n")
        
        # 按项目数量排序
        sorted_cats = sorted(category_analysis.items(), key=lambda x: -x[1]['count'])
        
        for cat_name, cat_data in sorted_cats:
            f.write(f"\n### {cat_name}\n\n")
            f.write(f"**项目数量**: {cat_data['count']} ({cat_data['percentage']:.1f}%)\n\n")
            f.write(f"**平均指标**: AI特征指数 {cat_data['avg_ai_index']:.2f} | ")
            f.write(f"复杂度 {cat_data['avg_complexity']:.2f} | ")
            f.write(f"Stars {cat_data['avg_stars']:.1f}\n\n")
            
            # 典型案例
            if cat_data['typical_cases']:
                f.write("**典型案例**:\n\n")
                for i, case in enumerate(cat_data['typical_cases'][:3], 1):
                    f.write(f"{i}. **{case.get('repo_name', 'N/A')}**\n")
                    f.write(f"   - AI特征指数: {'★' * case.get('ai_generation_score', 0)}{'☆' * (5-case.get('ai_generation_score', 0))}\n")
                    f.write(f"   - 核心意图: {case.get('core_intent', 'N/A')}\n")
                    f.write(f"   - 复杂度: {case.get('complexity_level', 0)}/5\n")
                    if case.get('description'):
                        f.write(f"   - 项目描述: {case.get('description')[:100]}...\n")
                    f.write(f"   - 原文洞察: *{case.get('analytical_insight', 'N/A')}*\n")
                    f.write(f"   - 链接: {case.get('repo_url', 'N/A')}\n\n")
            
            # 行业洞察引用
            if cat_data['insights']:
                f.write("**行业洞察引用**:\n\n")
                for insight_repo in cat_data['insights']:
                    f.write(f"> {insight_repo.get('analytical_insight', '')}\n")
                    f.write(f"> —— {insight_repo.get('repo_name')}\n\n")
        
        # 高价值项目 spotlight（仅考虑 Stars 维度）
        f.write("\n---\n\n")
        f.write("## ⭐ 高价值项目 Spotlight\n\n")
        f.write("> 筛选标准: Stars ≥ 20\n\n")
        
        high_value = sorted(
            [r for r in results if r.get('stars', 0) >= 20],
            key=lambda x: x.get('stars', 0),
            reverse=True
        )[:10]
        
        for r in high_value:
            f.write(f"### {r.get('repo_name')}\n\n")
            f.write(f"- **Stars**: {r.get('stars', 0)} | **AI特征指数**: {r.get('ai_generation_score', 0)}/5\n")
            f.write(f"- **分类**: {r.get('micro_scenario', 'N/A')}\n")
            f.write(f"- **核心意图**: {r.get('core_intent', 'N/A')}\n")
            if r.get('description'):
                f.write(f"- **描述**: {r.get('description')[:150]}...\n")
            f.write(f"- **原文洞察**: {r.get('analytical_insight', 'N/A')}\n")
            f.write(f"- **链接**: {r.get('repo_url', 'N/A')}\n\n")
    
    print(f"✅ Markdown 报告: {report_path}")
    return report_path


def generate_csv_reports(results: List[Dict], overview: Dict, category_analysis: Dict):
    """生成 CSV 数据文件"""
    
    # 0. 宏观分类总表
    rows = []
    for macro_name, macro_data in overview['macro_analysis'].items():
        rows.append([
            macro_name,
            macro_data['count'],
            f"{macro_data['percentage']:.1f}%",
            f"{macro_data['avg_ai_index']:.2f}",
            f"{macro_data['avg_complexity']:.2f}",
            f"{macro_data['avg_stars']:.1f}"
        ])
    save_csv("00_macro_category_overview.csv",
             ["宏观分类", "项目数", "占比", "平均AI特征指数", "平均复杂度", "平均Stars"],
             rows)
    
    # 1. 总体分布（微观场景）
    rows = []
    for scene, count in Counter([r.get('micro_scenario', 'unknown') for r in results]).most_common():
        cat_data = category_analysis.get(scene, {})
        rows.append([
            scene,
            count,
            f"{count/len(results)*100:.1f}%",
            f"{cat_data.get('avg_ai_index', 0):.2f}",
            f"{cat_data.get('avg_complexity', 0):.2f}",
            f"{cat_data.get('avg_stars', 0):.1f}"
        ])
    save_csv("01_micro_scenario_distribution.csv", 
             ["微观场景", "项目数", "占比", "平均AI特征指数", "平均复杂度", "平均Stars"], 
             rows)
    
    # 2. 宏观分类详细分布
    for macro_name, macro_data in overview['macro_analysis'].items():
        rows = []
        for micro, count in macro_data['micro_distribution'].items():
            micro_pct = count / macro_data['count'] * 100
            rows.append([micro, count, f"{micro_pct:.1f}%"])
        save_csv(f"macro_{macro_name.replace('/', '_')}_micro_distribution.csv",
                 ["微观场景", "数量", "占比"],
                 rows)
    
    # 3. 典型案例详情
    rows = []
    for cat_name, cat_data in category_analysis.items():
        for case in cat_data.get('typical_cases', []):
            rows.append([
                cat_name,
                case.get('repo_name', ''),
                case.get('core_intent', ''),
                case.get('ai_generation_score', 0),
                case.get('complexity_level', 0),
                case.get('stars', 0),
                case.get('analytical_insight', '')[:100] + '...',
                case.get('repo_url', '')
            ])
    save_csv("03_typical_cases.csv",
             ["微观场景", "仓库名", "核心意图", "AI特征指数", "复杂度", "Stars", "洞察摘要", "链接"],
             rows)
    
    # 4. 高价值项目（仅 Stars ≥ 20）
    high_value = sorted(
        [r for r in results if r.get('stars', 0) >= 20],
        key=lambda x: x.get('stars', 0),
        reverse=True
    )
    rows = []
    for r in high_value:
        rows.append([
            r.get('repo_name', ''),
            r.get('micro_scenario', ''),
            r.get('stars', 0),
            r.get('ai_generation_score', 0),
            r.get('core_intent', ''),
            r.get('analytical_insight', '')[:150] + '...',
            r.get('repo_url', '')
        ])
    save_csv("04_high_value_projects.csv",
             ["仓库名", "微观场景", "Stars", "AI特征指数", "核心意图", "洞察", "链接"],
             rows)


def generate_insight_summary(results: List[Dict], category_analysis: Dict):
    """生成洞察摘要文本"""
    summary_path = os.path.join(OUTPUT_DIR, "insights_summary.txt")
    
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("Vibe Coding 赛道核心洞察\n")
        f.write("=" * 80 + "\n\n")
        
        total = len(results)
        f.write(f"【数据概览】\n")
        f.write(f"样本规模: {total} 个项目\n")
        f.write(f"分析时间: {datetime.now().strftime('%Y-%m-%d')}\n\n")
        
        # Top 3 场景
        f.write("【主力微观场景 Top 3】\n\n")
        sorted_cats = sorted(category_analysis.items(), key=lambda x: -x[1]['count'])
        for i, (cat_name, cat_data) in enumerate(sorted_cats[:3], 1):
            f.write(f"{i}. {cat_name}\n")
            f.write(f"   项目数: {cat_data['count']} ({cat_data['percentage']:.1f}%)\n")
            f.write(f"   平均AI特征指数: {cat_data['avg_ai_index']:.2f}/5\n")
            f.write(f"   典型项目:\n")
            for case in cat_data['typical_cases'][:2]:
                f.write(f"     - {case.get('repo_name')}: {case.get('core_intent')}\n")
            f.write("\n")
        
        # AI 参与趋势
        high_ai = sum(1 for r in results if r.get('ai_generation_score', 0) >= 4)
        f.write(f"【AI 特征指数洞察】\n")
        f.write(f"AI特征指数反映项目中体现出的AI coding工具的使用特征\n")
        f.write(f"5分表示具备明显的AI原生特征（如AGENTS.md、.cursorrules等配置文件）\n")
        f.write(f"高AI特征项目 (≥4分): {high_ai} 个 ({high_ai/total*100:.1f}%)\n")
        f.write(f"平均AI特征指数: {sum(r.get('ai_generation_score', 0) for r in results)/total:.2f}/5\n\n")
        
        # 值得关注的项目
        f.write("【值得关注的高价值项目】\n\n")
        high_value = sorted(
            [r for r in results if r.get('stars', 0) >= 20 or r.get('ai_generation_score', 0) >= 4],
            key=lambda x: x.get('stars', 0),
            reverse=True
        )[:5]
        for r in high_value:
            f.write(f"- {r.get('repo_name')} ({r.get('stars')}★, AI特征指数:{r.get('ai_generation_score')}/5)\n")
            f.write(f"  {r.get('core_intent')}\n")
            f.write(f"  洞察: {r.get('analytical_insight')}\n\n")
    
    print(f"✅ 洞察摘要: {summary_path}")


def main():
    print("=" * 70)
    print("🚀 Vibe Coding 分析报告生成器")
    print("=" * 70)
    print(f"输入文件: {INPUT_FILE}")
    print(f"输出目录: {OUTPUT_DIR}/\n")
    
    # 加载数据
    results = load_data()
    if not results:
        print("❌ 没有数据，退出")
        return
    
    # 按宏观分类分析
    print("\n📊 按宏观分类分析...")
    macro_analysis = analyze_by_macro_category(results)
    
    # 生成总体概览
    print("📊 生成总体概览...")
    overview = generate_overview(results, macro_analysis)
    
    # 按微观场景分类分析
    print("📊 按微观场景分类分析...")
    category_analysis = analyze_by_category(results)
    
    # 生成 Markdown 报告
    print("\n📝 生成 Markdown 报告...")
    generate_markdown_report(results, overview, category_analysis)
    
    # 生成 CSV 报告
    print("\n📄 生成 CSV 数据文件...")
    generate_csv_reports(results, overview, category_analysis)
    
    # 生成洞察摘要
    print("\n💡 生成洞察摘要...")
    generate_insight_summary(results, category_analysis)
    
    print("\n" + "=" * 70)
    print("✅ 分析完成！")
    print(f"所有输出保存在: {OUTPUT_DIR}/")
    print("=" * 70)
    
    # 打印简要统计
    print(f"\n📈 简要统计:")
    print(f"   总项目数: {overview['total']}")
    print(f"   平均AI特征指数: {overview['avg_ai_index']:.2f}/5")
    print(f"   微观场景数量: {len(category_analysis)}")
    print(f"   宏观分类数量: {len(macro_analysis)}")
    print(f"\n   微观场景分布:")
    for cat, data in sorted(category_analysis.items(), key=lambda x: -x[1]['count'])[:5]:
        print(f"      {cat}: {data['count']} ({data['percentage']:.1f}%)")


if __name__ == "__main__":
    main()
