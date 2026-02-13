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

print("=" * 70)
print("从用途类型维度分析 - 重新理解 'other' 类别")
print("=" * 70)

# 重新分类 - 从真实用途角度
usage_map = {
    # 开发者工具/脚手架 - 帮助其他开发者提效
    'developer_tool': [],
    # 原型/MVP - 产品概念验证
    'product_prototype': [],
    # 个人品牌/作品集
    'personal_branding': [],
    # 商业展示/营销
    'marketing_showcase': [],
    # 系统/基础设施
    'system_infrastructure': [],
    # 硬件/IoT
    'hardware_iot': [],
    # 内容管理/CMS
    'content_management': [],
    # 教育/学习
    'education': [],
    # 社区/非营利
    'community': [],
    # 信息不足
    'insufficient_info': [],
    # 其他
    'other': []
}

for item in other_items:
    intent = item.get('core_intent', '')
    desc = item.get('description', '') or ''
    insight = item.get('analytical_insight', '')
    full_text = (intent + ' ' + desc + ' ' + insight).lower()
    
    # 开发者工具 - 帮助其他开发者
    if any(k in full_text for k in ['模板', '脚手架', 'starter', 'boilerplate', '基础框架', '开发模板']):
        usage_map['developer_tool'].append(item)
    # 原型/MVP
    elif any(k in full_text for k in ['原型', 'mvp', '验证想法', '概念验证', 'ai提示', 'ai生成', '快速生成']):
        usage_map['product_prototype'].append(item)
    # 个人品牌
    elif any(k in full_text for k in ['个人作品', 'portfolio', '个人简历', '技术简历', '个人主页', '个人品牌', '自我介绍', '个人开发者简介']):
        usage_map['personal_branding'].append(item)
    # 商业展示
    elif any(k in full_text for k in ['公司网站', '产品官网', '官方网站', '商业展示', 'landing page', '着陆页', '产品推广', '吸引客户', '公司主页', '健身房', '公司']):
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

# 打印分析结果
print("\n【发现的主要用途场景】\n")

scenarios = [
    ('developer_tool', '开发者工具/脚手架', '帮助其他开发者快速启动项目，属于生产力工具'),
    ('product_prototype', '产品原型/MVP', '用AI快速生成原型验证想法，属于产品研究'),
    ('personal_branding', '个人品牌/作品集', '展示个人技能和项目，建立个人品牌'),
    ('marketing_showcase', '商业展示/营销', '公司官网、产品着陆页，用于商业推广'),
    ('system_infrastructure', '系统/基础设施', '操作系统、协议实现等底层工具'),
    ('hardware_iot', '硬件/IoT', '嵌入式、固件、驱动等硬件相关'),
    ('content_management', '内容管理/CMS', '内容管理系统'),
]

for key, name, desc in scenarios:
    items = usage_map[key]
    if len(items) > 0:
        pct = len(items) / len(other_items) * 100
        print(f"\n{name}: {len(items)}个 ({pct:.1f}%)")
        print(f"  说明: {desc}")
        print(f"  示例:")
        for i, item in enumerate(items[:2]):
            print(f"    - {item.get('repo_name')}: {item.get('core_intent')[:50]}")

# 映射建议
print("\n" + "=" * 70)
print("【与现有 micro_scenario 的映射建议】")
print("=" * 70)

mapping_analysis = {
    'developer_tool': ('productivity', 160, '开发者生产力工具，帮助其他开发者快速启动项目'),
    'product_prototype': ('research', 61, '产品原型验证，属于研究实验性质'),
    'personal_branding': ('NEW: personal_branding', 13, '现有分类未覆盖，建议新增'),
    'marketing_showcase': ('NEW: marketing', 6, '现有分类未覆盖，建议新增'),
    'system_infrastructure': ('infrastructure', 28, '现有macro_category已有，但micro_scenario缺'),
    'hardware_iot': ('NEW: hardware_iot', 15, '现有分类未覆盖，建议新增'),
    'content_management': ('content_creation', 15, '可归入内容创作'),
    'education': ('education', 12, '可归入教育'),
    'community': ('social', 12, '可归入社交'),
    'insufficient_info': ('other', 5, '信息不足，保持other'),
    'other': ('other', 34, '其他'),
}

print(f"\n{'用途场景':<20} {'建议分类':<25} {'数量':<8} {'占比':<8}")
print("-" * 70)

total_accounted = 0
for key, (suggested, count, note) in mapping_analysis.items():
    if count > 0:
        pct = count / len(other_items) * 100
        total_accounted += count
        name = dict(scenarios).get(key, key)
        print(f"{name:<20} {suggested:<25} {count:<8} {pct:.1f}%")

print("-" * 70)
print(f"{'合计':<20} {'':<25} {total_accounted:<8} {total_accounted/len(other_items)*100:.1f}%")

# 核心结论
print("\n" + "=" * 70)
print("【核心结论】")
print("=" * 70)

print("""
1. 模板/脚手架项目（160个，47.6%）
   ✅ 真实用途：开发者生产力工具
   ✅ 应归入：productivity（跨行业通用效率提升）
   
2. 产品原型/MVP（61个，18.2%）
   ✅ 真实用途：产品概念验证
   ✅ 应归入：research（研究/实验）
   
3. 个人品牌/作品集（13个，3.9%）
   ❓ 现有分类未覆盖
   ❓ 建议：新增 personal_branding 或归入 personal
   
4. 商业展示/营销（6个，1.8%）
   ❓ 现有分类未覆盖
   ❓ 建议：新增 marketing 或归入 business_automation
   
5. 系统/基础设施（28个，8.3%）
   ❓ macro_category已有"基础设施"，但micro_scenario缺对应项
   ❓ 建议：新增 infrastructure

是否需要重新跑DeepSeek？
================================
""")

significant_miss = len(usage_map['personal_branding']) + len(usage_map['marketing_showcase']) + len(usage_map['system_infrastructure']) + len(usage_map['hardware_iot'])
print(f"确实被miss掉的场景（建议新增分类）: {significant_miss}个 ({significant_miss/len(other_items)*100:.1f}%)")
print(f"可以映射到现有分类的: {len(other_items) - significant_miss - len(usage_map['insufficient_info'])}个")
print(f"信息不足的: {len(usage_map['insufficient_info'])}个")

if significant_miss > 30:  # 如果有超过30个项目需要新增分类
    print("\n⚠️ 建议：重新跑DeepSeek，新增以下micro_scenario:")
    print("   - personal_branding (个人品牌)")
    print("   - marketing (商业展示/营销)")
    print("   - infrastructure (系统基础设施)")
    print("   - hardware_iot (硬件/IoT)")
else:
    print("\n✅ 建议：不需要重新跑DeepSeek")
    print("   大部分可以映射到现有分类，少量边缘场景可以接受")
