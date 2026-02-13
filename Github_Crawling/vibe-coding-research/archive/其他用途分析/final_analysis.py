import json
import sys
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

print("=" * 70)
print("从用途类型维度分析 - 重新理解 'other' 类别")
print("=" * 70)

# 重新分类 - 从真实用途角度
usage_map = {
    'developer_tool': [],      # 开发者工具/脚手架
    'product_prototype': [],   # 产品原型/MVP
    'personal_branding': [],   # 个人品牌/作品集
    'marketing_showcase': [],  # 商业展示/营销
    'system_infrastructure': [], # 系统/基础设施
    'hardware_iot': [],        # 硬件/IoT
    'content_management': [],  # 内容管理/CMS
    'education': [],           # 教育/学习
    'community': [],           # 社区/非营利
    'insufficient_info': [],   # 信息不足
    'other': [],               # 其他
}

for item in other_items:
    intent = item.get('core_intent', '')
    desc = item.get('description', '') or ''
    insight = item.get('analytical_insight', '')
    full_text = (intent + ' ' + desc + ' ' + insight).lower()
    
    # 开发者工具
    if any(k in full_text for k in ['模板', '脚手架', 'starter', 'boilerplate', '基础框架', '开发模板']):
        usage_map['developer_tool'].append(item)
    # 原型/MVP
    elif any(k in full_text for k in ['原型', 'mvp', '验证想法', '概念验证', 'ai提示', 'ai生成', '快速生成']):
        usage_map['product_prototype'].append(item)
    # 个人品牌
    elif any(k in full_text for k in ['个人作品', 'portfolio', '个人简历', '技术简历', '个人主页', '个人品牌', '自我介绍', '个人开发者简介']):
        usage_map['personal_branding'].append(item)
    # 商业展示
    elif any(k in full_text for k in ['公司网站', '产品官网', '官方网站', '商业展示', 'landing page', '着陆页', '产品推广', '吸引客户', '公司主页']):
        usage_map['marketing_showcase'].append(item)
    # 系统/基础设施
    elif any(k in full_text for k in ['操作系统', '内核', '分布式', '协议实现', '数据库', '缓存', '消息队列']):
        usage_map['system_infrastructure'].append(item)
    # 硬件/IoT
    elif any(k in full_text for k in ['固件', '解锁', '嵌入式', '硬件', '驱动', '路由器', 'iot']):
        usage_map['hardware_iot'].append(item)
    # 内容管理
    elif any(k in full_text for k in ['cms', '内容管理', 'headless']):
        usage_map['content_management'].append(item)
    # 教育
    elif any(k in full_text for k in ['学习', '练习', '教程', '教学', '课程']):
        usage_map['education'].append(item)
    # 社区
    elif any(k in full_text for k in ['社区', '公益', '非营利', '集体']):
        usage_map['community'].append(item)
    # 信息不足
    elif any(k in full_text for k in ['未知', '信息不足', '占位符', '仅含仓库名']):
        usage_map['insufficient_info'].append(item)
    else:
        usage_map['other'].append(item)

# 场景描述
scenario_desc = {
    'developer_tool': '开发者工具/脚手架 - 帮助其他开发者快速启动项目',
    'product_prototype': '产品原型/MVP - 用AI快速生成原型验证想法',
    'personal_branding': '个人品牌/作品集 - 展示个人技能和项目',
    'marketing_showcase': '商业展示/营销 - 公司官网、产品着陆页',
    'system_infrastructure': '系统/基础设施 - 操作系统、协议实现等底层工具',
    'hardware_iot': '硬件/IoT - 嵌入式、固件、驱动等',
    'content_management': '内容管理/CMS - 内容管理系统',
    'education': '教育/学习 - 学习项目',
    'community': '社区/非营利 - 公益项目',
    'insufficient_info': '信息不足 - 无法判断',
    'other': '其他',
}

print("\n【发现的主要用途场景】\n")
for key, desc in scenario_desc.items():
    items = usage_map[key]
    if len(items) > 0:
        pct = len(items) / len(other_items) * 100
        print(f"\n{desc}")
        print(f"  数量: {len(items)} ({pct:.1f}%)")
        for i, item in enumerate(items[:2]):
            print(f"  - {item.get('repo_name')}: {item.get('core_intent')[:50]}")

# 映射建议
print("\n" + "=" * 70)
print("【与现有 micro_scenario 的映射建议】")
print("=" * 70)

mapping = {
    'developer_tool': ('productivity', '开发者生产力工具'),
    'product_prototype': ('research', '产品原型验证'),
    'personal_branding': ('NEW', '建议新增 personal_branding'),
    'marketing_showcase': ('NEW', '建议新增 marketing'),
    'system_infrastructure': ('NEW', '建议新增 infrastructure'),
    'hardware_iot': ('NEW', '建议新增 hardware_iot'),
    'content_management': ('content_creation', '内容创作'),
    'education': ('education', '教育'),
    'community': ('social', '社交'),
    'insufficient_info': ('other', '保持other'),
    'other': ('other', '其他'),
}

print(f"\n{'用途场景':<30} {'建议映射':<20} {'数量':<8} {'占比':<8}")
print("-" * 70)

total_new = 0
total_existing = 0
for key, (target, note) in mapping.items():
    count = len(usage_map[key])
    if count > 0:
        pct = count / len(other_items) * 100
        name = scenario_desc[key].split(' - ')[0]
        print(f"{name:<30} {target:<20} {count:<8} {pct:.1f}%")
        if target == 'NEW':
            total_new += count
        elif target != 'other':
            total_existing += count

print("-" * 70)
print(f"{'可映射到现有分类':<30} {'':<20} {total_existing:<8} {total_existing/len(other_items)*100:.1f}%")
print(f"{'建议新增分类':<30} {'':<20} {total_new:<8} {total_new/len(other_items)*100:.1f}%")

# 核心结论
print("\n" + "=" * 70)
print("【核心结论与建议】")
print("=" * 70)

print(f"""
现有分类可以覆盖大部分"other"项目：
   - 开发者工具(160个) -> productivity
   - 原型验证(69个) -> research
   - 内容管理/CMS -> content_creation
   - 教育项目 -> education
   - 社区项目 -> social

建议新增的分类（{total_new}个，{total_new/len(other_items)*100:.1f}%）：
   - personal_branding: 个人品牌/作品集 ({len(usage_map['personal_branding'])}个)
   - marketing: 商业展示/营销 ({len(usage_map['marketing_showcase'])}个)
   - infrastructure: 系统基础设施 ({len(usage_map['system_infrastructure'])}个)
   - hardware_iot: 硬件/IoT ({len(usage_map['hardware_iot'])}个)

是否需要重新跑DeepSeek？
""")

if total_new >= 20:
    print("建议: 重新跑DeepSeek")
    print(f"  因为有{total_new}个项目({total_new/len(other_items)*100:.1f}%)属于现有分类未覆盖的场景")
    print("  新增分类后，other比例可以从21.9%降至约11%")
else:
    print("建议: 不需要重新跑DeepSeek")
    print("  新增分类的项目数量较少，可以接受")
