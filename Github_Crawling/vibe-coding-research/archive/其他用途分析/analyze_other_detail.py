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

print(f"共有 {len(other_items)} 个other项\n")

# 分析core_intent关键词
print("=== Core Intent 关键词分析（前30个高频词）===")
intent_words = Counter()
for item in other_items:
    intent = item.get('core_intent', '')
    # 简单分词
    words = intent.lower().replace('的', ' ').replace('和', ' ').replace('与', ' ').replace('为', ' ').split()
    for w in words:
        if len(w) >= 2 and w not in ['提供', '构建', '创建', '基于', '一个', '用于']:
            intent_words[w] += 1

for word, count in intent_words.most_common(30):
    print(f"  {word}: {count}")

# 分析analytical_insight关键词
print("\n=== Analytical Insight 关键词分析（前20个）===")
insight_words = Counter()
for item in other_items:
    insight = item.get('analytical_insight', '')
    words = insight.lower().replace('的', ' ').replace('和', ' ').replace('与', ' ').split()
    for w in words:
        if len(w) >= 2 and w not in ['反映了', '该项目', '以及', '通过']:
            insight_words[w] += 1

for word, count in insight_words.most_common(20):
    print(f"  {word}: {count}")

# 列出部分other项的详细信息
print("\n=== 部分other项详情（前50个）===")
for i, item in enumerate(other_items[:50]):
    print(f"\n{i+1}. {item.get('repo_name')}")
    print(f"   Core Intent: {item.get('core_intent')}")
    print(f"   Macro: {item.get('macro_category')}")
    print(f"   Description: {item.get('description')}")
