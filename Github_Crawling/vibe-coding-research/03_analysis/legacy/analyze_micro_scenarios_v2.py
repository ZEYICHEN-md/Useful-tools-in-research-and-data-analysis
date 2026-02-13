# -*- coding: utf-8 -*-
import json
import sys
import os
from collections import defaultdict, Counter

# 设置输出编码
sys.stdout.reconfigure(encoding='utf-8')

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
    'AI/LLM工具': ['AI', 'LLM', '人工智能', '大模型', 'GPT', 'Claude', '代理', 'agent', '智能体', 'AI原生', '大语言模型', '生成式AI', 'prompt', '对话', 'chatbot', '助手'],
    '开发工具/脚手架': ['模板', '脚手架', '开发工具', '生成器', 'boilerplate', 'starter', 'template', 'cli', '命令行', '构建工具'],
    '内容管理系统': ['CMS', '博客', '内容管理', 'headless', 'blog', '内容发布'],
    '电商平台': ['电商', '购物', '支付', '订单', 'e-commerce', 'store', '商城', '零售'],
    '数据可视化/BI': ['数据可视化', '仪表盘', 'dashboard', '图表', '分析', '报表', '数据', '可视化', '图表'],
    '金融/交易': ['金融', '交易', '区块链', '加密货币', '股票', '支付', '钱包', 'DeFi', 'blockchain', 'crypto', 'bitcoin'],
    '医疗健康': ['医疗', '健康', '医院', '兽医', '药品', '诊断', '健康', '病历', '临床'],
    '教育学习': ['教育', '学习', '课程', '教学', '学生', '考试', '学习', '培训', 'tutorial'],
    '企业管理': ['管理', 'CRM', 'ERP', '后台', 'admin', 'SaaS', '企业', '系统管理', '办公', '工作流'],
    '游戏/娱乐': ['游戏', 'game', '娱乐', 'gaming', 'play', '休闲'],
    '媒体/视频': ['视频', '媒体', '音频', '直播', '影视', 'video', 'audio', '播放器'],
    '社交/社区': ['社交', '社区', '聊天', '论坛', 'social', 'chat', '通讯'],
    '物联网/硬件': ['物联网', 'IoT', '硬件', '机器人', '嵌入式', 'robot', '传感器', '设备'],
    '设计工具': ['设计', 'UI', '原型', 'Figma', 'design', 'design system', '创意', '图像编辑'],
    '网站/门户': ['网站', '官网', '门户', 'web', 'landing page', 'homepage', '展示', '作品集'],
    '自动化/工作流': ['自动化', '工作流', 'workflow', 'automation', '脚本', '定时任务', '批处理'],
    '编译器/开发环境': ['编译器', 'IDE', '编辑器', '开发环境', 'compiler', '解释器', '语言'],
    '代理/网关': ['代理', '网关', 'gateway', 'proxy', '路由', '中间件', 'API网关'],
    '安全/隐私': ['安全', '隐私', '加密', '认证', '密码', '防火墙', '保护'],
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

def get_typical_projects(items, domain, max_examples=3):
    """获取某个领域下的典型案例"""
    # 筛选属于该领域的项目
    domain_items = []
    for item in items:
        domains = extract_domains(item['core_intent'], item['analytical_insight'], item.get('description', ''))
        if domain in domains:
            domain_items.append(item)
    
    if not domain_items:
        return []
    
    # 按stars排序，取前max_examples个
    sorted_items = sorted(domain_items, key=lambda x: x['stars'], reverse=True)[:max_examples]
    
    return [(item['repo_name'], item['repo_url'], item['stars'], item['core_intent']) 
            for item in sorted_items]

# 创建输出目录
output_dir = 'micro'
os.makedirs(output_dir, exist_ok=True)

# 分析每个类别
results = {}
all_domain_cases = []  # 用于汇总所有案例

for scenario in ['效率工具', '技术基础设施', '企业商业应用', '个人生活', '娱乐媒体', '教育学习', '健康医疗', '社交社区']:
    items = groups[scenario]
    
    # 统计各领域的项目
    domain_items_map = defaultdict(list)
    for item in items:
        domains = extract_domains(item['core_intent'], item['analytical_insight'], item.get('description', ''))
        for domain in domains:
            domain_items_map[domain].append(item)
    
    # 获取各领域案例
    domain_cases = {}
    domain_counts = Counter()
    
    for domain, domain_items in domain_items_map.items():
        count = len(domain_items)
        domain_counts[domain] = count
        cases = get_typical_projects(items, domain, max_examples=2)
        domain_cases[domain] = cases
        
        # 记录到汇总列表
        for case in cases:
            all_domain_cases.append({
                'micro_scenario': scenario,
                'domain': domain,
                'repo_name': case[0],
                'repo_url': case[1],
                'stars': case[2],
                'core_intent': case[3]
            })
    
    # 获取总体代表性项目（按stars排序）
    sorted_items = sorted(items, key=lambda x: x['stars'], reverse=True)[:5]
    
    results[scenario] = {
        'count': len(items),
        'domains': domain_counts.most_common(8),
        'domain_cases': domain_cases,
        'examples': [(item['repo_name'], item['repo_url'], item['stars'], item['core_intent']) 
                     for item in sorted_items]
    }
    
    print(f'\n{"="*80}')
    print(f'【{scenario}】 共 {len(items)} 个项目')
    print(f'{"="*80}')
    print('\n高频应用领域及典型案例:')
    
    for domain, count in domain_counts.most_common(8):
        pct = count / len(items) * 100
        cases = domain_cases.get(domain, [])
        print(f'\n  【{domain}】: {count} ({pct:.1f}%)')
        if cases:
            for name, url, stars, intent in cases:
                print(f'      - {name} (stars:{stars})')
                print(f'        {intent[:60]}...' if len(intent) > 60 else f'        {intent}')
                print(f'        {url}')

# 生成CSV - 每个类别的领域分布（带案例）
for scenario in results:
    csv_path = os.path.join(output_dir, f'micro_scenario_{scenario}_domains_with_cases.csv')
    with open(csv_path, 'w', encoding='utf-8-sig') as f:
        f.write('应用领域,项目数,占比,典型案例1名称,典型案例1_stars,典型案例1链接,典型案例1描述,典型案例2名称,典型案例2_stars,典型案例2链接,典型案例2描述\n')
        
        for domain, count in results[scenario]['domains']:
            pct = count / results[scenario]['count'] * 100
            cases = results[scenario]['domain_cases'].get(domain, [])
            
            # 准备案例数据
            case1_data = ['', '', '', '']  # 名称, stars, 链接, 描述
            case2_data = ['', '', '', '']
            
            if len(cases) >= 1:
                case1_data = [cases[0][0], str(cases[0][2]), cases[0][1], cases[0][3].replace(',', '，')]
            if len(cases) >= 2:
                case2_data = [cases[1][0], str(cases[1][2]), cases[1][1], cases[1][3].replace(',', '，')]
            
            row = f'{domain},{count},{pct:.1f}%,{case1_data[0]},{case1_data[1]},{case1_data[2]},"{case1_data[3]}",{case2_data[0]},{case2_data[1]},{case2_data[2]},"{case2_data[3]}"\n'
            f.write(row)
    
    print(f'[OK] 已生成: {csv_path}')

# 生成汇总CSV - 所有细分领域的典型案例
summary_csv = os.path.join(output_dir, 'all_domain_typical_cases.csv')
with open(summary_csv, 'w', encoding='utf-8-sig') as f:
    f.write('Micro-Scenario,应用领域,项目名称,Stars,核心意图,GitHub链接\n')
    for case in all_domain_cases:
        intent_clean = case['core_intent'].replace(',', '，').replace('"', '""')
        f.write(f"{case['micro_scenario']},{case['domain']},{case['repo_name']},{case['stars']},\"{intent_clean}\",{case['repo_url']}\n")

print(f'[OK] 已生成汇总: {summary_csv}')

# 生成Markdown报告
md_path = os.path.join(output_dir, 'micro_scenario_analysis_report.md')
with open(md_path, 'w', encoding='utf-8') as f:
    f.write('# 📊 Vibe Coding 8大Micro-Scenario类别深度分析报告\n\n')
    f.write('> 数据来源：`vibe_coding_analysis_8cat.jsonl`  \n')
    f.write(f'> 总项目数：{len(records)}  \n')
    f.write('> 分析日期：2026-02-11\n\n')
    f.write('---\n\n')
    
    # 总体分布
    f.write('## 📈 总体分布\n\n')
    f.write('| Micro-Scenario | 项目数 | 占比 |\n')
    f.write('|---------------|--------|------|\n')
    for scenario in ['效率工具', '技术基础设施', '企业商业应用', '个人生活', '娱乐媒体', '教育学习', '健康医疗', '社交社区']:
        count = results[scenario]['count']
        pct = count / len(records) * 100
        f.write(f'| {scenario} | {count} | {pct:.1f}% |\n')
    f.write('\n---\n\n')
    
    # 每个类别的详细分析
    scenario_names = {
        '效率工具': '1. 效率工具',
        '技术基础设施': '2. 技术基础设施',
        '企业商业应用': '3. 企业商业应用',
        '个人生活': '4. 个人生活',
        '娱乐媒体': '5. 娱乐媒体',
        '教育学习': '6. 教育学习',
        '健康医疗': '7. 健康医疗',
        '社交社区': '8. 社交社区'
    }
    
    for scenario in ['效率工具', '技术基础设施', '企业商业应用', '个人生活', '娱乐媒体', '教育学习', '健康医疗', '社交社区']:
        data = results[scenario]
        f.write(f'## {scenario_names[scenario]}\n\n')
        f.write(f'**项目数量：{data["count"]} ({data["count"]/len(records)*100:.1f}%)**\n\n')
        
        f.write('### 应用领域分布及典型案例\n\n')
        f.write('| 应用领域 | 项目数 | 占比 | 典型案例 | Stars | 核心意图 |\n')
        f.write('|---------|--------|------|---------|-------|---------|\n')
        
        for domain, count in data['domains']:
            pct = count / data['count'] * 100
            cases = data['domain_cases'].get(domain, [])
            
            if cases:
                for i, (name, url, stars, intent) in enumerate(cases):
                    intent_short = intent[:40] + '...' if len(intent) > 40 else intent
                    if i == 0:
                        f.write(f'| {domain} | {count} | {pct:.1f}% | [{name}]({url}) | {stars} | {intent_short} |\n')
                    else:
                        f.write(f'| | | | [{name}]({url}) | {stars} | {intent_short} |\n')
            else:
                f.write(f'| {domain} | {count} | {pct:.1f}% | - | - | - |\n')
        
        f.write('\n')
    
    # 特别对比分析
    f.write('---\n\n')
    f.write('## 🔍 特别对比：效率工具 vs 技术基础设施 中的 AI/LLM工具\n\n')
    f.write('两个类别的头号细分领域都是 AI/LLM工具，但侧重点明显不同：\n\n')
    
    # 效率工具的AI案例
    f.write('### 效率工具 - AI/LLM工具 典型案例\n\n')
    f.write('| 项目名称 | Stars | 核心意图 | 特点 |\n')
    f.write('|---------|-------|---------|------|\n')
    for case in results['效率工具']['domain_cases'].get('AI/LLM工具', [])[:5]:
        name, url, stars, intent = case
        # 提取特点
        feature = "用户端应用"
        if "浏览器" in intent or "界面" in intent:
            feature = "AI交互界面"
        elif "工作流" in intent or "管理" in intent:
            feature = "AI工作流编排"
        elif "数据" in intent or "恢复" in intent:
            feature = "AI数据服务"
        f.write(f'| [{name}]({url}) | {stars} | {intent} | {feature} |\n')
    
    f.write('\n**特点总结**：偏向**终端用户应用**，关注如何让普通用户更方便地使用AI，强调交互体验和实用性。\n\n')
    
    # 技术基础设施的AI案例
    f.write('### 技术基础设施 - AI/LLM工具 典型案例\n\n')
    f.write('| 项目名称 | Stars | 核心意图 | 特点 |\n')
    f.write('|---------|-------|---------|------|\n')
    for case in results['技术基础设施']['domain_cases'].get('AI/LLM工具', [])[:5]:
        name, url, stars, intent = case
        feature = "底层服务"
        if "客户端" in intent or "UI" in intent:
            feature = "AI客户端基础设施"
        elif "安全" in intent or "沙箱" in intent:
            feature = "AI安全基础设施"
        elif "内核" in intent:
            feature = "系统级AI支持"
        f.write(f'| [{name}]({url}) | {stars} | {intent} | {feature} |\n')
    
    f.write('\n**特点总结**：偏向**底层基础设施和开发者工具**，关注如何为AI应用提供支撑，强调安全性、性能和可扩展性。\n\n')
    
    f.write('### 核心区别\n\n')
    f.write('| 维度 | 效率工具-AI/LLM | 技术基础设施-AI/LLM |\n')
    f.write('|------|----------------|---------------------|\n')
    f.write('| **目标用户** | 终端用户、普通开发者 | 开发者、系统架构师 |\n')
    f.write('| **产品形态** | 应用、插件、界面 | 框架、库、中间件 |\n')
    f.write('| **关注重点** | 易用性、交互体验 | 性能、安全、可扩展性 |\n')
    f.write('| **技术深度** | 应用层集成 | 系统层/内核层支持 |\n')
    f.write('| **典型场景** | AI助手、智能写作、自动化 | AI代理框架、安全沙箱、路由网关 |\n')
    f.write('\n---\n\n')
    
    f.write('## 📌 关键洞察\n\n')
    f.write('1. **AI/LLM工具贯穿所有类别**：从效率工具(48.7%)到健康医疗(57.9%)，AI技术已成为Vibe Coding的核心驱动力\n\n')
    f.write('2. **效率工具和技术基础设施占主导**：两者合计占比超过55%，反映了开发者对提升开发效率和构建基础能力的强烈需求\n\n')
    f.write('3. **企业商业应用以管理类为主**：69%涉及企业管理，包括CRM、ERP、后台管理系统等\n\n')
    f.write('4. **娱乐媒体聚焦游戏领域**：76.2%的项目与游戏相关，表明游戏是Vibe Coding的重要应用场景\n\n')
    f.write('5. **健康医疗虽然数量少但AI渗透率高**：57.9%的健康医疗项目使用AI/LLM技术，体现了AI在专业垂直领域的深度应用\n\n')
    f.write('6. **细分领域案例揭示应用深度**：同一领域在不同类别中呈现不同的应用层次（用户端vs基础设施）\n\n')

print(f'[OK] 已生成报告: {md_path}')

# 保存详细结果JSON
import json
json_path = os.path.join(output_dir, 'micro_scenario_analysis.json')
with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f'[OK] 已生成JSON: {json_path}')
print('\n分析完成！')
