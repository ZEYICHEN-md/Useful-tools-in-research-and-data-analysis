import json
from collections import Counter
import sys

# 设置stdout编码
sys.stdout.reconfigure(encoding='utf-8')

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

for item in remaining:
    intent = item.get('core_intent', '')
    insight = item.get('analytical_insight', '')
    full_text = (intent + ' ' + insight).lower()
    
    for keyword in ['原型', '学习', '练习', '实验', '演示', '迁移', '克隆', '复刻', 
                    '官网', '文档站', '初始化', '测试', '配置', '工具库', 
                    '组件库', 'monorepo', 'boilerplate', '脚手架', '快速启动', 'mvp',
                    'figma', '设计系统', '编译时']:
        if keyword in full_text:
            keywords[keyword] += 1

for word, count in keywords.most_common(20):
    print(f"  {word}: {count}")

# 输出到文件
with open('remaining_other_analysis.txt', 'w', encoding='utf-8') as f:
    f.write(f"Remaining items after excluding templates: {len(remaining)}\n\n")
    f.write("=== Keywords in remaining 'other' items ===\n")
    for word, count in keywords.most_common(20):
        f.write(f"  {word}: {count}\n")
    
    f.write("\n=== Sample remaining 'other' items ===\n")
    for i, item in enumerate(remaining[:50]):
        f.write(f"{i+1}. {item.get('repo_name')}\n")
        f.write(f"   Intent: {item.get('core_intent')}\n")
        desc = item.get('description') or 'N/A'
        f.write(f"   Desc: {desc}\n")
        f.write(f"   Macro: {item.get('macro_category')}\n\n")

print("\nDetailed analysis saved to: remaining_other_analysis.txt")
