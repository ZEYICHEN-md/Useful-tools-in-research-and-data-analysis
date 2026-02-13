import json
from collections import Counter

# 统计所有场景
total = 0
micro_scenarios = Counter()
other_items = []

with open('vibe_coding_analysis.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        try:
            data = json.loads(line)
            total += 1
            micro = data.get('micro_scenario', 'UNKNOWN')
            micro_scenarios[micro] += 1
            if micro == 'other':
                other_items.append(data)
        except:
            pass

print('=== 微场景分布统计 ===')
for scene, count in micro_scenarios.most_common():
    pct = count / total * 100
    print(f'{scene}: {count} ({pct:.1f}%)')

other_count = micro_scenarios.get("other", 0)
print(f'\n总条目数: {total}')
print(f'other 类别数量: {other_count} ({other_count/total*100:.1f}%)')

# 将other项保存到文件以便进一步分析
with open('other_items.jsonl', 'w', encoding='utf-8') as f:
    for item in other_items:
        f.write(json.dumps(item, ensure_ascii=False) + '\n')

print(f'\n已保存 {len(other_items)} 个other项到 other_items.jsonl')
