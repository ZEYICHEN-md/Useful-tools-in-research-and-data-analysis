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

print(f"Total 'other' items: {len(other_items)}\n")

# 从真实用途维度重新分类
usage_analysis = {
    # 开发者工具/脚手架 - 服务于其他开发者
    'dev_tool_boilerplate': [],
    # 个人品牌/作品集展示
    'personal_brand': [],
    # 公司/产品官网（商业展示）
    'business_showcase': [],
    # 原型验证/MVP
    'prototype_mvp': [],
    # 系统/基础设施工具
    'system_infrastructure': [],
    # 硬件/IoT
    'hardware_iot': [],
    # 内容创作相关
    'content_creation': [],
    # 教育/学习
    'education_learning': [],
    # 社区/非营利
    'community_nonprofit': [],
    # 信息不足
    'insufficient_info': [],
    # 其他
    'other': []
}

for item in other_items:
    intent = item.get('core_intent', '')
    desc = item.get('description', '') or ''
    insight = item.get('analytical_insight', '')
    repo_name = item.get('repo_name', '').lower()
    full_text = (intent + ' ' + desc + ' ' + insight + ' ' + repo_name).lower()
    
    # 开发者工具/脚手架 - 帮助其他开发者快速启动项目
    if any(k in full_text for k in ['模板', '脚手架', 'starter', 'boilerplate', '基础框架', '开发模板']):
        usage_analysis['dev_tool_boilerplate'].append(item)
    
    # 个人品牌/作品集 - 展示个人技能、简历、项目
    elif any(k in full_text for k in ['个人作品', 'portfolio', '个人简历', '技术简历', '个人主页', '个人品牌', '自我介绍', '个人开发者简介']):
        usage_analysis['personal_brand'].append(item)
    
    # 公司/产品官网 - 商业展示、产品推广
    elif any(k in full_text for k in ['公司网站', '产品官网', '官方网站', '商业展示', 'landing page', '着陆页', '产品推广', '吸引客户', '公司主页']):
        usage_analysis['business_showcase'].append(item)
    
    # 原型/MVP - 验证想法、快速试错
    elif any(k in full_text for k in ['原型', 'mvp', '验证想法', '概念验证', '快速试错']):
        usage_analysis['prototype_mvp'].append(item)
    
    # 系统/基础设施
    elif any(k in full_text for k in ['操作系统', '内核', '分布式', '协议实现', '数据库', '缓存', '消息队列']):
        usage_analysis['system_infrastructure'].append(item)
    
    # 硬件/IoT
    elif any(k in full_text for k in ['固件', '解锁', '嵌入式', '硬件', '驱动', '路由器', 'iot']):
        usage_analysis['hardware_iot'].append(item)
    
    # 内容创作
    elif any(k in full_text for k in ['博客', 'cms', '内容管理', '媒体', '视频', '文档']):
        usage_analysis['content_creation'].append(item)
    
    # 教育学习
    elif any(k in full_text for k in ['学习', '练习', '教程', '教学', '课程']):
        usage_analysis['education_learning'].append(item)
    
    # 社区/非营利
    elif any(k in full_text for k in ['社区', '公益', '非营利', '集体', '公民']):
        usage_analysis['community_nonprofit'].append(item)
    
    # 信息不足
    elif any(k in full_text for k in ['未知', '信息不足', '占位符', '仅含仓库名']):
        usage_analysis['insufficient_info'].append(item)
    
    else:
        usage_analysis['other'].append(item)

# 统计
print("=== 从真实用途维度重新分析 ===\n")
for usage, items in sorted(usage_analysis.items(), key=lambda x: -len(x[1])):
    if len(items) > 0:
        pct = len(items) / len(other_items) * 100
        print(f"\n{usage}: {len(items)} ({pct:.1f}%)")
        print("-" * 60)
        for i, item in enumerate(items[:5]):
            print(f"  {i+1}. {item.get('repo_name')}")
            print(f"     Intent: {item.get('core_intent')}")
        if len(items) > 5:
            print(f"     ... 还有 {len(items)-5} 个")

# 输出详细列表到文件
with open('usage_analysis_detail.txt', 'w', encoding='utf-8') as f:
    for usage, items in sorted(usage_analysis.items(), key=lambda x: -len(x[1])):
        if len(items) > 0:
            f.write(f"\n{'='*60}\n")
            f.write(f"{usage}: {len(items)} items\n")
            f.write(f"{'='*60}\n\n")
            for i, item in enumerate(items):
                f.write(f"{i+1}. {item.get('repo_name')}\n")
                f.write(f"   Intent: {item.get('core_intent')}\n")
                f.write(f"   Desc: {item.get('description') or 'N/A'}\n")
                f.write(f"   Macro: {item.get('macro_category')}\n\n")

print(f"\n\n详细分析已保存到: usage_analysis_detail.txt")

# 与现有micro_scenario的映射建议
print("\n" + "="*70)
print("与现有 micro_scenario 的映射建议")
print("="*70)

mapping = {
    'dev_tool_boilerplate': 'productivity (开发者生产力工具)',
    'personal_brand': '可以考虑新增: personal_branding',
    'business_showcase': '可以考虑新增: marketing_landing 或归入 business_automation',
    'prototype_mvp': 'research (产品研究/原型验证)',
    'system_infrastructure': '可以考虑新增: infrastructure',
    'hardware_iot': '可以考虑新增: hardware_iot',
    'content_creation': 'content_creation',
    'education_learning': 'education',
    'community_nonprofit': 'social 或新增 nonprofit',
    'insufficient_info': 'other',
    'other': 'other'
}

for k, v in mapping.items():
    count = len(usage_analysis[k])
    if count > 0:
        print(f"{k} ({count}个) -> {v}")
