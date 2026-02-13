#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vibe Coding 分析结果汇总与可视化

功能:
- 读取分析结果，生成统计报告
- 生成可视化图表
- 导出洞察摘要
"""

import json
import csv
import os
from collections import Counter
from datetime import datetime


def load_results(jsonl_file: str = "vibe_coding_analysis.jsonl"):
    """加载分析结果"""
    results = []
    if not os.path.exists(jsonl_file):
        print(f"❌ 文件不存在: {jsonl_file}")
        return results
    
    with open(jsonl_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                results.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    
    return results


def generate_summary(results):
    """生成统计摘要"""
    if not results:
        print("没有数据")
        return
    
    total = len(results)
    
    # 基础统计
    macro_cats = Counter([r.get('macro_category', 'unknown') for r in results])
    micro_scenes = Counter([r.get('micro_scenario', 'unknown') for r in results])
    ai_scores = Counter([r.get('ai_generation_score', 0) for r in results])
    complexity = Counter([r.get('complexity_level', 0) for r in results])
    languages = Counter([r.get('language', 'Unknown') for r in results])
    tiers = Counter([r.get('tier', 'unknown') for r in results])
    
    # Stars 统计
    stars_list = [r.get('stars', 0) for r in results]
    avg_stars = sum(stars_list) / len(stars_list) if stars_list else 0
    
    # 高星级项目 (>50 stars)
    high_star_repos = [r for r in results if r.get('stars', 0) > 50]
    
    # AI 高分项目 (>=4)
    high_ai_repos = [r for r in results if r.get('ai_generation_score', 0) >= 4]
    
    print("=" * 80)
    print("📊 Vibe Coding 分析结果汇总")
    print("=" * 80)
    print(f"\n📈 总体统计 (样本数: {total})")
    print(f"   平均 Stars: {avg_stars:.1f}")
    print(f"   高星项目 (>50★): {len(high_star_repos)} ({len(high_star_repos)/total*100:.1f}%)")
    print(f"   高 AI 浓度 (>=4★): {len(high_ai_repos)} ({len(high_ai_repos)/total*100:.1f}%)")
    
    print(f"\n🏗️ 宏观类别分布:")
    for cat, count in macro_cats.most_common():
        pct = count / total * 100
        bar = "█" * int(pct / 2)
        print(f"   {cat:20s}: {count:4d} ({pct:5.1f}%) {bar}")
    
    print(f"\n🎯 微观场景分布 (Top 10):")
    for scene, count in micro_scenes.most_common(10):
        pct = count / total * 100
        bar = "█" * int(pct / 2)
        print(f"   {scene:20s}: {count:4d} ({pct:5.1f}%) {bar}")
    
    print(f"\n🤖 AI 生成分数分布:")
    for score in range(1, 6):
        count = ai_scores.get(score, 0)
        pct = count / total * 100
        bar = "█" * int(pct / 2)
        print(f"   {'★' * score}{'☆' * (5-score)} ({score}): {count:4d} ({pct:5.1f}%) {bar}")
    
    print(f"\n📊 复杂度分布:")
    for level in range(1, 6):
        count = complexity.get(level, 0)
        pct = count / total * 100
        bar = "█" * int(pct / 2)
        labels = {1: "简单脚本", 2: "轻量工具", 3: "中等应用", 4: "复杂系统", 5: "企业级"}
        print(f"   {level} - {labels[level]:8s}: {count:4d} ({pct:5.1f}%) {bar}")
    
    print(f"\n💻 编程语言分布 (Top 10):")
    for lang, count in languages.most_common(10):
        pct = count / total * 100
        bar = "█" * int(pct / 2)
        print(f"   {lang or 'Unknown':15s}: {count:4d} ({pct:5.1f}%) {bar}")
    
    print(f"\n⭐ 分层分布:")
    for tier, count in tiers.most_common():
        pct = count / total * 100
        label = "沉默大多数" if tier == "silent" else "高价值信号"
        print(f"   {tier} ({label}): {count:4d} ({pct:5.1f}%)")
    
    # 交叉分析
    print(f"\n🔍 关键洞察:")
    
    # AI 浓度 vs 项目类型
    ai_by_macro = {}
    for r in results:
        macro = r.get('macro_category', 'unknown')
        ai = r.get('ai_generation_score', 0)
        if macro not in ai_by_macro:
            ai_by_macro[macro] = []
        ai_by_macro[macro].append(ai)
    
    print(f"\n   AI 浓度 vs 项目类型 (平均 AI 分数):")
    for macro, scores in sorted(ai_by_macro.items(), key=lambda x: -sum(x[1])/len(x[1])):
        avg = sum(scores) / len(scores)
        print(f"      {macro:20s}: {avg:.2f}/5.0")
    
    # 热门场景组合
    print(f"\n   热门场景组合 (Macro + Micro):")
    combos = Counter([(r.get('macro_category'), r.get('micro_scenario')) for r in results])
    for (macro, micro), count in combos.most_common(5):
        print(f"      {macro} + {micro}: {count} 个项目")
    
    print("\n" + "=" * 80)
    
    # 导出详细洞察
    export_insights(results, high_star_repos, high_ai_repos)


def export_insights(results, high_star_repos, high_ai_repos):
    """导出洞察摘要"""
    output_file = "analysis_insights.txt"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("🌟 Vibe Coding 赛道深度洞察\n")
        f.write("=" * 80 + "\n\n")
        
        f.write("【一、高价值项目案例 (>50 stars)】\n\n")
        for r in sorted(high_star_repos, key=lambda x: -x.get('stars', 0))[:10]:
            f.write(f"  📌 {r.get('repo_name')}\n")
            f.write(f"     ⭐ {r.get('stars')} | AI浓度: {r.get('ai_generation_score')}/5\n")
            f.write(f"     📝 {r.get('core_intent')}\n")
            f.write(f"     🔗 {r.get('repo_url')}\n")
            f.write(f"     💡 洞察: {r.get('analytical_insight')}\n\n")
        
        f.write("\n【二、典型 AI Native 项目 (AI浓度 >=4)】\n\n")
        for r in sorted(high_ai_repos, key=lambda x: -x.get('ai_generation_score', 0))[:10]:
            f.write(f"  🤖 {r.get('repo_name')} (AI浓度: {r.get('ai_generation_score')}/5)\n")
            f.write(f"     ⭐ {r.get('stars')} | {r.get('macro_category')}\n")
            f.write(f"     📝 {r.get('core_intent')}\n")
            f.write(f"     💡 {r.get('analytical_insight')}\n\n")
        
        # 场景洞察
        f.write("\n【三、场景分布洞察】\n\n")
        
        scenes = {}
        for r in results:
            scene = r.get('micro_scenario', 'other')
            if scene not in scenes:
                scenes[scene] = []
            scenes[scene].append(r)
        
        for scene, repos in sorted(scenes.items(), key=lambda x: -len(x[1]))[:5]:
            avg_ai = sum(r.get('ai_generation_score', 0) for r in repos) / len(repos)
            f.write(f"  📍 {scene} ({len(repos)} 个项目)\n")
            f.write(f"     平均 AI 浓度: {avg_ai:.2f}/5\n")
            # 找代表性项目
            example = max(repos, key=lambda x: x.get('stars', 0))
            f.write(f"     代表项目: {example.get('repo_name')} - {example.get('core_intent')}\n\n")
    
    print(f"📄 详细洞察已导出到: {output_file}")


def main():
    results = load_results()
    if results:
        generate_summary(results)
    else:
        print("请确保已运行 deepseek_analyzer.py 生成分析结果")


if __name__ == "__main__":
    main()
