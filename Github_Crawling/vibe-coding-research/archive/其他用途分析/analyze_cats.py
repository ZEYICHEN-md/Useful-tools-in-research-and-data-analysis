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

# 保存详细分析到文件
with open('category_detail.txt', 'w', encoding='utf-8') as f:
    f.write("现有分类典型案例分析\n")
    f.write("=" * 80 + "\n\n")
    
    for micro, items in sorted(categories.items(), key=lambda x: -len(x[1])):
        f.write(f"\n{'='*80}\n")
        f.write(f"【{micro}】 - {len(items)}个项目\n")
        f.write(f"{'='*80}\n")
        
        for i, item in enumerate(items[:10]):
            f.write(f"\n{i+1}. {item.get('repo_name')}\n")
            f.write(f"   Intent: {item.get('core_intent')}\n")
            f.write(f"   Desc: {item.get('description') or 'N/A'}\n")
            f.write(f"   Macro: {item.get('macro_category')}\n")

print("分析完成，保存到 category_detail.txt")
