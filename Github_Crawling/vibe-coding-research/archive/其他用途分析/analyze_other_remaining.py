import json
from collections import Counter

# 读取other项
other_items = []
with open('other_items.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        try:
            data = json.loads(line)
            other_items.append(data)
        except:
            pass

# 排除已经识别的模板类项目
remaining = []
for item in other_items:
    intent = item.get('core_intent', '').lower()
    if not (('next.js' in intent and ('模板' in intent or '默认' in intent)) or 
            ('react' in intent and 'vite' in intent and '模板' in intent) or
            ('模板' in intent or '模版' in intent or '默认项目' in intent)):
        remaining.append(item)

print(f"Remaining items after excluding templates: {len(remaining)}\n")

# 分析关键词
print("=== Keywords in remaining 'other' items ===")
keywords = Counter()
patterns = {
    '迁移': [], '迁移项目': [], '迁移': [],
    '克隆': [], '复刻': [], 'clone': [],
    '官网': [], '官方网站': [],
    '文档': [], 'documentation': [],
    '初始化': [], '初始': [],
    '原型': [], 'prototype': [],
    '演示': [], 'demo': [],
    '测试': [], 'test': [],
    '学习': [], '练习': [],
    '实验': [], 'experimental': [],
    '配置': [], 'configuration': [],
    '工具库': [], 'library': [],
    '组件库': [], 'component': [],
    'monorepo': [],
    'boilerplate': [],
}

for item in remaining:
    intent = item.get('core_intent', '')
    insight = item.get('analytical_insight', '')
    full_text = (intent + ' ' + insight).lower()
    
    for keyword in ['迁移', '克隆', '复刻', '官网', '官方网站', '文档站', '初始化', '原型', 
                    '演示', 'demo', '测试', '学习', '练习', '实验', '配置', '工具库', 
                    '组件库', 'monorepo', 'boilerplate', '脚手架', '快速启动', 'mvp']:
        if keyword in full_text:
            keywords[keyword] += 1

for word, count in keywords.most_common(20):
    print(f"  {word}: {count}")

# 列出部分剩余项目的意图
print("\n=== Sample remaining 'other' items ===")
for i, item in enumerate(remaining[:40]):
    print(f"{i+1}. {item.get('repo_name')}")
    print(f"   Intent: {item.get('core_intent')}")
    desc = item.get('description') or 'N/A'
    print(f"   Desc: {desc[:80] if desc else 'N/A'}...")
    print()
