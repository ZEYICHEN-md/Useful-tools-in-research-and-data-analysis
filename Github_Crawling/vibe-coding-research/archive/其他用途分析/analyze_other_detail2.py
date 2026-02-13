import json
from collections import Counter
import re

# 读取other项
other_items = []
with open('other_items.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        try:
            data = json.loads(line)
            other_items.append(data)
        except:
            pass

print(f"Total other items: {len(other_items)}\n")

# 按关键词分类
categories = {
    'template_nextjs': [],
    'template_react_vite': [],
    'template_other': [],
    'personal_website': [],
    'figma_to_code': [],
    'design_system': [],
    'mobile_app_template': [],
    'unknown_placeholder': [],
    'hardware_tool': [],
    'official_website': [],
    'compile_time_tool': [],
    'other': []
}

for item in other_items:
    intent = item.get('core_intent', '').lower()
    
    if 'next.js' in intent and ('模板' in intent or '默认' in intent or '模版' in intent or 'starter' in intent):
        categories['template_nextjs'].append(item)
    elif 'react' in intent and 'vite' in intent and ('模板' in intent or '基础' in intent):
        categories['template_react_vite'].append(item)
    elif '模板' in intent or '模版' in intent or 'starter' in intent or '默认项目' in intent:
        categories['template_other'].append(item)
    elif '个人网站' in intent or '项目展示' in intent or 'portfolio' in intent:
        categories['personal_website'].append(item)
    elif 'figma' in intent:
        categories['figma_to_code'].append(item)
    elif '设计系统' in intent or 'design system' in intent:
        categories['design_system'].append(item)
    elif ('expo' in intent or 'flutter' in intent or 'mobile' in intent) and '模板' in intent:
        categories['mobile_app_template'].append(item)
    elif '未知' in intent or '占位符' in intent or '信息缺失' in intent:
        categories['unknown_placeholder'].append(item)
    elif '解锁' in intent or '固件' in intent or '硬件' in intent:
        categories['hardware_tool'].append(item)
    elif '官方网站' in intent:
        categories['official_website'].append(item)
    elif '编译' in intent or 'source generator' in intent:
        categories['compile_time_tool'].append(item)
    else:
        categories['other'].append(item)

print("=== Potential New Categories from 'other' ===\n")
for cat, items in sorted(categories.items(), key=lambda x: -len(x[1])):
    if len(items) > 0:
        print(f"{cat}: {len(items)} items")
        # 显示前3个示例
        for i, item in enumerate(items[:3]):
            print(f"  - {item.get('repo_name')}: {item.get('core_intent')[:60]}...")
        print()

# 统计模板类项目总数
template_total = len(categories['template_nextjs']) + len(categories['template_react_vite']) + len(categories['template_other'])
print(f"\n=== SUMMARY ===")
print(f"Template-related projects: {template_total} ({template_total/len(other_items)*100:.1f}% of other)")
print(f"This represents {template_total/1531*100:.1f}% of ALL projects")
