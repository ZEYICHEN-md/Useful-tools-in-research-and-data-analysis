# -*- coding: utf-8 -*-
import json
import sys
from collections import defaultdict, Counter

# 读取所有记录
records = []
with open('vibe_coding_analysis_8cat.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            records.append(json.loads(line))

print(f'总记录数: {len(records)}')

# 按micro_scenario分组
groups = defaultdict(list)
for r in records:
    groups[r['micro_scenario']].append(r)

# 定义关键词映射
DOMAIN_KEYWORDS = {
    'AI/LLM工具': ['AI', 'LLM', '人工智能', '大模型', 'GPT', 'Claude', '代理', 'agent', '智能体', 'AI原生'],
    '开发工具/脚手架': ['模板', '脚手架', '开发工具', '生成器', 'boilerplate', 'starter', 'template'],
    '内容管理系统': ['CMS', '博客', '内容管理', 'headless', 'blog'],
    '电商平台': ['电商', '购物', '支付', '订单', 'e-commerce', 'store', '商城'],
    '数据可视化/BI': ['数据可视化', '仪表盘', 'dashboard', '图表', '分析', '报表', '数据'],
    '金融/交易': ['金融', '交易', '区块链', '加密货币', '股票', '支付', '钱包', 'DeFi', 'blockchain'],
    '医疗健康': ['医疗', '健康', '医院', '兽医', '药品', '诊断', '健康'],
    '教育学习': ['教育', '学习', '课程', '教学', '学生', '考试', '学习'],
    '企业管理': ['管理', 'CRM', 'ERP', '后台', 'admin', 'SaaS', '企业', '系统管理'],
    '游戏/娱乐': ['游戏', 'game', '娱乐', 'gaming', 'play'],
    '媒体/视频': ['视频', '媒体', '音频', '直播', '影视', 'video', 'audio'],
    '社交/社区': ['社交', '社区', '聊天', '论坛', 'social', 'chat'],
    '物联网/硬件': ['物联网', 'IoT', '硬件', '机器人', '嵌入式', 'robot'],
    '设计工具': ['设计', 'UI', '原型', 'Figma', 'design', 'design system'],
    '网站/门户': ['网站', '官网', '门户', 'web', 'landing page', 'homepage'],
    '自动化/工作流': ['自动化', '工作流', 'workflow', 'automation', '脚本'],
    '编译器/开发环境': ['编译器', 'IDE', '编辑器', '开发环境', 'compiler'],
    '代理/网关': ['代理', '网关', 'gateway', 'proxy', '路由'],
}

def extract_domains(core_intent, analytical_insight, description):
    text = f'{core_intent} {analytical_insight} {description if description else ""}'
    domains = []
    for domain, keywords in DOMAIN_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in text.lower():
                domains.append(domain)
                break
    return domains if domains else ['其他']

# 分析每个类别
results = {}
for scenario in ['效率工具', '技术基础设施', '企业商业应用', '个人生活', '娱乐媒体', '教育学习', '健康医疗', '社交社区']:
    items = groups[scenario]
    domain_counter = Counter()
    
    # 收集所有领域
    for item in items:
        domains = extract_domains(item['core_intent'], item['analytical_insight'], item.get('description', ''))
        domain_counter.update(domains)
    
    # 获取代表性项目（按stars排序，取前5个有描述的）
    sorted_items = sorted(items, key=lambda x: x['stars'], reverse=True)[:10]
    
    results[scenario] = {
        'count': len(items),
        'domains': domain_counter.most_common(8),
        'examples': [(item['repo_name'], item['repo_url'], item['stars'], item['core_intent']) 
                     for item in sorted_items[:5]]
    }
    
    print(f'\n{"="*80}')
    print(f'【{scenario}】 共 {len(items)} 个项目')
    print(f'{"="*80}')
    print('\n高频应用领域:')
    for domain, count in domain_counter.most_common(8):
        pct = count / len(items) * 100
        print(f'  - {domain}: {count} ({pct:.1f}%)')
    
    print('\n代表性项目 (按stars排序):')
    for name, url, stars, intent in results[scenario]['examples']:
        print(f'  - [{name}]({url}) stars:{stars}')
        print(f'    意图: {intent[:60]}...' if len(intent) > 60 else f'    意图: {intent}')

# 保存详细结果
with open('micro_scenario_analysis.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print('\n\n详细分析结果已保存到 micro_scenario_analysis.json')
