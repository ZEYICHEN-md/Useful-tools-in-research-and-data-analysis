import json
from collections import defaultdict

# 读取数据
categories = defaultdict(list)
with open('vibe_coding_analysis.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        try:
            data = json.loads(line)
            micro = data.get('micro_scenario', 'UNKNOWN')
            categories[micro].append(data)
        except:
            pass

print("=" * 80)
print("基于典型案例的8分类体系重新设计")
print("=" * 80)

# 分析每个现有分类的核心特征
analysis = {
    'business_automation': {
        'count': len(categories['business_automation']),
        '核心特征': '商业流程自动化、企业管理系统',
        '典型案例': [
            '洗车店业务管理与交易处理',
            '机场航班与票务管理系统', 
            '为本地餐厅管理外卖订单',
            '通过AI代理自动化营销工作流'
        ]
    },
    'productivity': {
        'count': len(categories['productivity']),
        '核心特征': '个人/团队效率工具、开发者工具',
        '典型案例': [
            '在线编译器的前端界面',
            '用C++构建电子表格应用',
            '为产品经理提供AI辅助工作空间',
            '搭建个人博客站点'
        ]
    },
    'research': {
        'count': len(categories['research']),
        '核心特征': '技术研究、原型验证、基础设施',
        '典型案例': [
            '为Hono框架自动生成CRUD接口',
            '分析癌症基因变异对miRNA结合的影响',
            '构建可问责的多智能体系统框架',
            '控制机械臂的智能代理'
        ]
    },
    'entertainment': {
        'count': len(categories['entertainment']),
        '核心特征': '游戏、娱乐消费、休闲',
        '典型案例': [
            '基于符号匹配的计时游戏',
            '在VR/AR中可视化分形曲线',
            '自托管IPTV播放器',
            '在Android设备上阅读漫画'
        ]
    },
    'education': {
        'count': len(categories['education']),
        '核心特征': '教育平台、学习工具、知识传授',
        '典型案例': [
            '搭建在线教育平台',
            '通过闪卡应用辅助学习记忆',
            '提供统计概念代码示例',
            '存储神经数据分析课程材料'
        ]
    },
    'personal': {
        'count': len(categories['personal']),
        '核心特征': '个人生活管理、作品集展示',
        '典型案例': [
            '管理个人电影观看清单',
            '展示个人技能与项目的网站',
            '管理家庭家务的离线优先应用',
            '随机生成肯尼亚风味食谱'
        ]
    },
    'ecommerce': {
        'count': len(categories['ecommerce']),
        '核心特征': '电商、交易、商品买卖',
        '典型案例': [
            '为暗厨餐厅提供在线点餐系统',
            '在线房产租赁与买卖平台',
            '监控巴士票价并识别优惠',
            '通过WhatsApp下单的简单产品目录'
        ]
    },
    'fintech': {
        'count': len(categories['fintech']),
        '核心特征': '金融、支付、加密资产',
        '典型案例': [
            '整合投资数据并可视化',
            '增强Solana区块链客户端连接可靠性',
            '为中小企业提供非托管稳定币支付网关',
            '实时显示加密货币与外汇分析信号'
        ]
    },
    'content_creation': {
        'count': len(categories['content_creation']),
        '核心特征': '内容创作、媒体处理、CMS',
        '典型案例': [
            '为访谈视频自动添加视觉特效',
            '自托管音频转录服务器',
            '基于文件的内容管理系统',
            '提供旅行博客网站模板'
        ]
    },
    'social': {
        'count': len(categories['social']),
        '核心特征': '社交、通讯、社区、约会',
        '典型案例': [
            '为对话应用提供后端API服务',
            '构建类似Reddit的新闻社交后端API',
            '为特定地区用户提供约会匹配服务',
            '为大学社团创建官方网站'
        ]
    },
    'health': {
        'count': len(categories['health']),
        '核心特征': '医疗、健康、 wellness',
        '典型案例': [
            'AI驱动的兽医支持平台',
            '连接患者与药房的医疗市场平台',
            '提供加密的AI心理日记分析',
            '为医学生提供电子病历协作编辑工具'
        ]
    },
    'other': {
        'count': len(categories['other']),
        '核心特征': '模板/脚手架、原型、硬件、系统',
        '典型案例': [
            '基于Next.js的默认模板项目',
            '基于AI快速构建Web应用原型',
            '个人网站或项目展示',
            '免费解锁手机并管理固件'
        ]
    }
}

print("\n【现有12分类分析】\n")
for cat, info in analysis.items():
    print(f"\n{cat}: {info['count']}个项目")
    print(f"  核心特征: {info['核心特征']}")
    print(f"  典型案例:")
    for case in info['典型案例'][:3]:
        print(f"    - {case}")

# 新的8分类提案
print("\n\n" + "=" * 80)
print("【新的8分类体系提案】")
print("=" * 80)

new_8_categories = {
    'enterprise_business': {
        'name': '企业商业应用',
        'description': '商业流程自动化、企业管理系统、电商、金融科技',
        '合并来源': ['business_automation', 'ecommerce', 'fintech'],
        'estimated_count': (len(categories['business_automation']) + 
                           len(categories['ecommerce']) + 
                           len(categories['fintech']))
    },
    'productivity_tools': {
        'name': '效率工具',
        'description': '个人/团队效率工具、开发者工具、生产力应用',
        '合并来源': ['productivity', 'content_creation'],
        'estimated_count': (len(categories['productivity']) + 
                           len(categories['content_creation']))
    },
    'tech_infrastructure': {
        'name': '技术基础设施',
        'description': '技术研究、原型验证、系统工具、开发者基础设施',
        '合并来源': ['research'],
        'estimated_count': len(categories['research'])
    },
    'entertainment_media': {
        'name': '娱乐媒体',
        'description': '游戏、娱乐消费、媒体播放、内容消费',
        '合并来源': ['entertainment'],
        'estimated_count': len(categories['entertainment'])
    },
    'education_learning': {
        'name': '教育学习',
        'description': '教育平台、学习工具、知识传授、技能提升',
        '合并来源': ['education'],
        'estimated_count': len(categories['education'])
    },
    'social_community': {
        'name': '社交社区',
        'description': '社交应用、社区平台、通讯工具、约会匹配',
        '合并来源': ['social'],
        'estimated_count': len(categories['social'])
    },
    'health_wellness': {
        'name': '健康医疗',
        'description': '医疗应用、健康追踪、wellness、心理',
        '合并来源': ['health'],
        'estimated_count': len(categories['health'])
    },
    'personal_life': {
        'name': '个人生活',
        'description': '个人生活管理、作品集、家庭管理、个人品牌',
        '合并来源': ['personal'],
        'estimated_count': len(categories['personal'])
    }
}

# 处理other分类的项目
other_dev_tool = 160  # 开发者工具/模板
other_prototype = 69  # 原型/MVP
other_remaining = 336 - 160 - 69  # 剩余的

print("\n【新分类详细说明】\n")
total = 0
for key, cat in new_8_categories.items():
    count = cat['estimated_count']
    total += count
    pct = count / 1531 * 100
    print(f"\n{cat['name']} ({key})")
    print(f"  数量: ~{count} ({pct:.1f}%)")
    print(f"  描述: {cat['description']}")
    print(f"  来源: {', '.join(cat['合并来源'])}")

# 分配other项目
print(f"\n\n【other项目分配方案】")
print(f"  - 模板/脚手架 ({other_dev_tool}个) → 归入 productivity_tools")
print(f"  - 原型/MVP ({other_prototype}个) → 归入 tech_infrastructure")
print(f"  - 硬件/IoT、系统工具 ({other_remaining}个) → 归入 tech_infrastructure")

final_counts = {
    'enterprise_business': new_8_categories['enterprise_business']['estimated_count'],
    'productivity_tools': new_8_categories['productivity_tools']['estimated_count'] + other_dev_tool,
    'tech_infrastructure': new_8_categories['tech_infrastructure']['estimated_count'] + other_prototype + other_remaining,
    'entertainment_media': new_8_categories['entertainment_media']['estimated_count'],
    'education_learning': new_8_categories['education_learning']['estimated_count'],
    'social_community': new_8_categories['social_community']['estimated_count'],
    'health_wellness': new_8_categories['health_wellness']['estimated_count'],
    'personal_life': new_8_categories['personal_life']['estimated_count'],
}

print("\n\n【最终8分类分布预估】\n")
for name, count in sorted(final_counts.items(), key=lambda x: -x[1]):
    pct = count / 1531 * 100
    print(f"  {name}: ~{count} ({pct:.1f}%)")

print("\n\n建议:")
print("  1. 可以将12分类合并为8分类，逻辑更清晰")
print("  2. other项目可以被合理分配到现有分类")
print("  3. 不需要重新跑DeepSeek，只需在数据分析阶段重新归类")
