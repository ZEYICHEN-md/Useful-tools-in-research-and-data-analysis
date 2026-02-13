import json
from collections import defaultdict

# 按micro_scenario分组
categories = defaultdict(list)

with open('vibe_coding_analysis.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        try:
            data = json.loads(line)
            micro = data.get('micro_scenario', 'UNKNOWN')
            categories[micro].append(data)
        except:
            pass

# 为每个分类提取典型案例
print("=" * 80)
print("现有分类典型案例分析")
print("=" * 80)

for micro, items in sorted(categories.items(), key=lambda x: -len(x[1])):
    print(f"\n\n{'='*80}")
    print(f"【{micro}】 - {len(items)}个项目")
    print("="*80)
    
    # 提取5个典型案例
    for i, item in enumerate(items[:5]):
        print(f"\n{i+1}. {item.get('repo_name')}")
        print(f"   Intent: {item.get('core_intent')}")
        print(f"   Desc: {item.get('description') or 'N/A'}")
        print(f"   Macro: {item.get('macro_category')}")

# 保存详细分析到文件
with open('category_cases_detail.txt', 'w', encoding='utf-8') as f:
    for micro, items in sorted(categories.items(), key=lambda x: -len(x[1])):
        f.write(f"\n{'='*80}\n")
        f.write(f"【{micro}】 - {len(items)}个项目\n")
        f.write(f"{'='*80}\n")
        
        for i, item in enumerate(items[:10]):
            f.write(f"\n{i+1}. {item.get('repo_name')}\n")
            f.write(f"   Intent: {item.get('core_intent')}\n")
            f.write(f"   Desc: {item.get('description') or 'N/A'}\n")
            f.write(f"   Macro: {item.get('macro_category')}\n")

print("\n\n详细分析已保存到: category_cases_detail.txt")
