# -*- coding: utf-8 -*-
"""
V3版本：根据用途/功能归类典型案例，避免重复，每个案例代表不同用途方向
"""
import json
import sys
import os
import re
from collections import defaultdict, Counter
from difflib import SequenceMatcher

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

# 定义用途/功能分类关键词
USE_CASE_PATTERNS = {
    'AI/LLM工具': {
        'AI交互界面': ['界面', '浏览器', 'UI', '前端', '交互', 'chat', '对话', '界面'],
        'AI代理/智能体': ['代理', 'agent', '智能体', '自主', '自动化', '工作流'],
        'AI内容生成': ['生成', '写作', '内容', '文案', '创作', '图像', '视频'],
        'AI数据分析': ['分析', '数据', '预测', '洞察', '报表', '智能分析'],
        'AI辅助编程': ['编程', '代码', '开发辅助', 'IDE', '插件'],
        'AI安全/沙箱': ['安全', '沙箱', '保护', '防护', '隐私'],
        'AI模型训练': ['训练', '微调', '模型', 'fine-tune', '深度学习'],
        'AI API/服务': ['API', '服务', '接口', '后端', 'provider'],
    },
    '开发工具/脚手架': {
        '项目模板': ['模板', 'template', 'starter', 'boilerplate', '初始化'],
        'CLI工具': ['命令行', 'cli', '终端', 'shell', '命令'],
        '代码生成器': ['生成器', '生成', 'scaffold', '自动生成'],
        '构建工具': ['构建', '打包', '编译', 'build', 'bundle'],
        '开发框架': ['框架', 'framework', '库', 'library'],
        '测试工具': ['测试', 'test', '调试', 'debug'],
    },
    '自动化/工作流': {
        '数据处理自动化': ['数据处理', 'ETL', '同步', '迁移', '转换'],
        '任务自动化': ['任务', '定时', '调度', 'cron', '自动化'],
        '工作流引擎': ['工作流', 'workflow', '流程', 'pipeline', '编排'],
        'CI/CD自动化': ['CI/CD', '部署', '集成', '持续'],
    },
    '设计工具': {
        'UI/UX设计': ['UI', 'UX', '界面设计', '原型', 'prototype'],
        '图形/视觉': ['图形', '视觉', '图像', '图片', 'icon', 'logo'],
        '设计系统': ['设计系统', 'design system', '组件库', '样式'],
        '3D/动画': ['3D', '动画', '动效', '建模', '渲染'],
    },
    '企业管理': {
        'CRM/客户管理': ['CRM', '客户', '销售', '营销'],
        'ERP/资源管理': ['ERP', '资源', '库存', '供应链'],
        '项目管理': ['项目', '任务', '协作', 'team', '管理'],
        '后台管理系统': ['后台', 'admin', 'dashboard', '管理面板'],
        '人力资源': ['HR', '人事', '招聘', '员工'],
        '财务/会计': ['财务', '会计', '发票', '报销', '预算'],
    },
    '网站/门户': {
        '个人网站/博客': ['个人', '博客', 'blog', 'portfolio', '作品集'],
        '企业官网': ['企业', '官网', '公司', '品牌'],
        '电商网站': ['电商', '商城', '商店', '产品展示'],
        '内容站点': ['内容', '资讯', '新闻', '文档'],
        '落地页': ['落地页', 'landing page', '营销页', '推广'],
    },
    '数据可视化/BI': {
        '仪表盘/Dashboard': ['仪表盘', 'dashboard', '面板', 'overview'],
        '图表/报表': ['图表', '报表', 'chart', 'graph', '统计'],
        '实时监控': ['监控', '实时', '告警', '指标', 'metrics'],
        '数据探索': ['探索', '查询', '分析工具', 'BI工具'],
    },
    '游戏/娱乐': {
        '游戏引擎/框架': ['引擎', 'framework', '游戏框架', 'game engine'],
        '游戏Mod/插件': ['mod', '插件', '扩展', '增强'],
        '游戏工具': ['游戏工具', '辅助', '外挂', '工具'],
        '休闲游戏': ['休闲', '小游戏', '轻量'],
        'RPG/冒险': ['RPG', '冒险', '角色扮演'],
        '策略/模拟': ['策略', '模拟', '经营', '建造'],
    },
    '媒体/视频': {
        '视频播放器': ['播放器', 'player', '视频播放'],
        '视频编辑': ['编辑', '剪辑', '后期', '特效'],
        '直播/流媒体': ['直播', 'stream', '流媒体', 'broadcast'],
        '音频处理': ['音频', '音乐', 'sound', 'voice'],
        '转码/处理': ['转码', '压缩', '格式', '处理'],
    },
    '社交/社区': {
        '即时通讯': ['聊天', '消息', 'IM', '即时通讯'],
        '论坛/社区': ['论坛', '社区', '讨论', '帖子'],
        '社交网络': ['社交', '网络', '关系', '好友'],
        '内容分享': ['分享', '发布', '动态', 'feed'],
    },
    '医疗健康': {
        '医疗管理': ['管理', '系统', 'HIS', '医院管理'],
        '诊断/辅助': ['诊断', '辅助', '决策支持', 'AI诊断'],
        '健康监测': ['监测', '追踪', '健康数据', '可穿戴'],
        '医学教育': ['医学教育', '培训', '模拟', '学习'],
        '药品/药房': ['药品', '药房', '处方', '药物'],
    },
    '教育学习': {
        '课程管理': ['课程', '学习管理', 'LMS', '教学'],
        '编程学习': ['编程', '代码', '算法', '练习'],
        '知识管理': ['知识', '笔记', 'wiki', '文档'],
        '考试/评测': ['考试', '评测', '测验', '评估'],
        '教育游戏': ['教育游戏', '寓教于乐', '游戏化'],
    },
    '金融/交易': {
        '支付系统': ['支付', '付款', '收银', '支付网关'],
        '交易/投资': ['交易', '投资', '股票', '证券'],
        '加密货币': ['区块链', 'crypto', '比特币', '以太坊', 'DeFi'],
        '金融分析': ['分析', '风控', '信用', '评估'],
        '银行/账户': ['银行', '账户', '钱包', '余额'],
    },
    '安全/隐私': {
        '认证/授权': ['认证', '授权', '登录', '身份', 'auth'],
        '加密/解密': ['加密', '解密', '密码学', 'crypto'],
        '代理/VPN': ['代理', 'proxy', 'VPN', '隧道'],
        '防火墙/防护': ['防火墙', '防护', 'WAF', '安全'],
    },
    '代理/网关': {
        'API网关': ['API', '网关', 'gateway', '路由'],
        '反向代理': ['反向代理', '负载均衡', 'nginx'],
        'AI路由/代理': ['AI路由', '模型路由', '负载均衡'],
    },
}

def extract_domains(core_intent, analytical_insight, description):
    """提取项目所属的领域"""
    text = f'{core_intent} {analytical_insight} {description if description else ""}'
    domains = []
    
    # 简化的领域关键词映射
    domain_keywords = {
        'AI/LLM工具': ['AI', 'LLM', '人工智能', '大模型', 'GPT', 'Claude', '代理', 'agent', '智能体'],
        '开发工具/脚手架': ['模板', '脚手架', 'cli', '命令行', '生成器', 'boilerplate', 'starter'],
        '内容管理系统': ['CMS', '博客', '内容管理', 'headless'],
        '电商平台': ['电商', '购物', '支付', '订单', 'e-commerce', '商城'],
        '数据可视化/BI': ['可视化', '仪表盘', 'dashboard', '图表', '报表', '数据'],
        '金融/交易': ['金融', '交易', '区块链', '加密货币', '股票', '支付', 'DeFi'],
        '医疗健康': ['医疗', '健康', '医院', '兽医', '药品', '诊断'],
        '教育学习': ['教育', '学习', '课程', '教学', '学生', '考试'],
        '企业管理': ['管理', 'CRM', 'ERP', '后台', 'admin', 'SaaS', '企业'],
        '游戏/娱乐': ['游戏', 'game', '娱乐', 'gaming'],
        '媒体/视频': ['视频', '媒体', '音频', '直播', 'video', 'audio'],
        '社交/社区': ['社交', '社区', '聊天', '论坛', 'social', 'chat'],
        '物联网/硬件': ['物联网', 'IoT', '硬件', '机器人', '嵌入式'],
        '设计工具': ['设计', 'UI', '原型', 'Figma', 'design', '创意'],
        '网站/门户': ['网站', '官网', '门户', 'web', 'homepage'],
        '自动化/工作流': ['自动化', '工作流', 'workflow', 'automation'],
        '编译器/开发环境': ['编译器', 'IDE', '编辑器', 'compiler'],
        '代理/网关': ['代理', '网关', 'gateway', 'proxy'],
        '安全/隐私': ['安全', '隐私', '加密', '认证', '保护'],
    }
    
    for domain, keywords in domain_keywords.items():
        for kw in keywords:
            if kw.lower() in text.lower():
                domains.append(domain)
                break
    return domains if domains else ['其他']

def classify_use_case(core_intent, description, domain):
    """根据用途/功能分类"""
    text = f'{core_intent} {description if description else ""}'
    
    # 获取该domain的用途分类模式
    patterns = USE_CASE_PATTERNS.get(domain, {})
    
    matches = []
    for use_case_type, keywords in patterns.items():
        for kw in keywords:
            if kw.lower() in text.lower():
                matches.append(use_case_type)
                break
    
    # 如果没有匹配到特定用途，则根据文本内容推断
    if not matches:
        # 提取核心动词+名词作为用途
        if '管理' in text:
            matches.append('管理系统')
        elif '分析' in text or '统计' in text:
            matches.append('分析工具')
        elif '生成' in text or '创建' in text:
            matches.append('生成工具')
        elif '监控' in text:
            matches.append('监控工具')
        else:
            matches.append('通用工具')
    
    return matches[0] if matches else '其他'

def get_diverse_examples(items, domain, max_examples=3):
    """获取多样化的典型案例，按用途分类，避免重复"""
    # 筛选属于该领域的项目
    domain_items = []
    for item in items:
        domains = extract_domains(item['core_intent'], item['analytical_insight'], item.get('description', ''))
        if domain in domains:
            domain_items.append(item)
    
    if not domain_items:
        return []
    
    # 按用途分类
    use_case_groups = defaultdict(list)
    for item in domain_items:
        use_case = classify_use_case(item['core_intent'], item.get('description', ''), domain)
        use_case_groups[use_case].append(item)
    
    # 从每个用途类别中选择一个代表性项目（优先stars高的）
    selected_examples = []
    used_projects = set()  # 记录已使用的项目
    
    for use_case, projects in sorted(use_case_groups.items(), key=lambda x: len(x[1]), reverse=True):
        if len(selected_examples) >= max_examples:
            break
        
        # 从未使用的项目中选择stars最高的
        available_projects = [p for p in projects if p['repo_name'] not in used_projects]
        if not available_projects:
            continue
            
        best_project = max(available_projects, key=lambda x: x['stars'])
        
        selected_examples.append({
            'name': best_project['repo_name'],
            'url': best_project['repo_url'],
            'stars': best_project['stars'],
            'intent': best_project['core_intent'],
            'use_case': use_case
        })
        used_projects.add(best_project['repo_name'])
    
    return selected_examples

# 创建输出目录
output_dir = 'micro'
os.makedirs(output_dir, exist_ok=True)

# 分析每个类别
results = {}
all_domain_cases = []

for scenario in ['效率工具', '技术基础设施', '企业商业应用', '个人生活', '娱乐媒体', '教育学习', '健康医疗', '社交社区']:
    items = groups[scenario]
    
    # 统计各领域的项目
    domain_items_map = defaultdict(list)
    for item in items:
        domains = extract_domains(item['core_intent'], item['analytical_insight'], item.get('description', ''))
        for domain in domains:
            domain_items_map[domain].append(item)
    
    # 获取各领域案例（多样化）
    domain_cases = {}
    domain_counts = Counter()
    
    for domain, domain_items in domain_items_map.items():
        count = len(domain_items)
        domain_counts[domain] = count
        
        # 获取多样化的案例
        examples = get_diverse_examples(items, domain, max_examples=3)
        domain_cases[domain] = examples
        
        # 记录到汇总列表
        for case in examples:
            all_domain_cases.append({
                'micro_scenario': scenario,
                'domain': domain,
                'use_case': case['use_case'],
                'repo_name': case['name'],
                'repo_url': case['url'],
                'stars': case['stars'],
                'core_intent': case['intent']
            })
    
    results[scenario] = {
        'count': len(items),
        'domains': domain_counts.most_common(8),
        'domain_cases': domain_cases,
    }
    
    print(f'\n{"="*100}')
    print(f'【{scenario}】 共 {len(items)} 个项目')
    print(f'{"="*100}')
    print('\n高频应用领域及典型案例:')
    
    for domain, count in domain_counts.most_common(8):
        pct = count / len(items) * 100
        cases = domain_cases.get(domain, [])
        print(f'\n  【{domain}】: {count} ({pct:.1f}%)')
        if cases:
            for case in cases:
                print(f'      [{case["use_case"]}] {case["name"]} (stars:{case["stars"]})')
                intent_display = case['intent'][:55] + '...' if len(case['intent']) > 55 else case['intent']
                print(f'      {intent_display}')
                print(f'      {case["url"]}')

# 生成CSV - 每个类别的领域分布（带多样化案例）
for scenario in results:
    csv_path = os.path.join(output_dir, f'micro_scenario_{scenario}_domains_with_cases.csv')
    with open(csv_path, 'w', encoding='utf-8-sig') as f:
        f.write('应用领域,项目数,占比,典型案例1_用途,典型案例1_名称,典型案例1_stars,典型案例1链接,典型案例1描述,典型案例2_用途,典型案例2_名称,典型案例2_stars,典型案例2链接,典型案例2描述,典型案例3_用途,典型案例3_名称,典型案例3_stars,典型案例3链接,典型案例3描述\n')
        
        for domain, count in results[scenario]['domains']:
            pct = count / results[scenario]['count'] * 100
            cases = results[scenario]['domain_cases'].get(domain, [])
            
            # 准备案例数据
            case_data = []
            for i in range(3):  # 最多3个案例
                if i < len(cases):
                    case = cases[i]
                    case_data.extend([
                        case['use_case'],
                        case['name'],
                        str(case['stars']),
                        case['url'],
                        case['intent'].replace(',', '，').replace('"', '""')
                    ])
                else:
                    case_data.extend(['', '', '', '', ''])
            
            row = f'{domain},{count},{pct:.1f}%,{case_data[0]},{case_data[1]},{case_data[2]},{case_data[3]},"{case_data[4]}",{case_data[5]},{case_data[6]},{case_data[7]},{case_data[8]},"{case_data[9]}",{case_data[10]},{case_data[11]},{case_data[12]},{case_data[13]},"{case_data[14]}"\n'
            f.write(row)
    
    print(f'[OK] 已生成: {csv_path}')

# 生成汇总CSV
summary_csv = os.path.join(output_dir, 'all_domain_typical_cases.csv')
with open(summary_csv, 'w', encoding='utf-8-sig') as f:
    f.write('Micro-Scenario,应用领域,用途分类,项目名称,Stars,核心意图,GitHub链接\n')
    for case in all_domain_cases:
        intent_clean = case['core_intent'].replace(',', '，').replace('"', '""')
        f.write(f"{case['micro_scenario']},{case['domain']},{case['use_case']},{case['repo_name']},{case['stars']},\"{intent_clean}\",{case['repo_url']}\n")

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
        f.write('| 应用领域 | 项目数 | 占比 | 用途分类 | 典型案例 | Stars |\n')
        f.write('|---------|--------|------|---------|---------|-------|\n')
        
        for domain, count in data['domains']:
            pct = count / data['count'] * 100
            cases = data['domain_cases'].get(domain, [])
            
            if cases:
                for i, case in enumerate(cases):
                    intent_short = case['intent'][:35] + '...' if len(case['intent']) > 35 else case['intent']
                    if i == 0:
                        f.write(f'| {domain} | {count} | {pct:.1f}% | {case["use_case"]} | [{case["name"]}]({case["url"]}) | {case["stars"]} |\n')
                    else:
                        f.write(f'| | | | {case["use_case"]} | [{case["name"]}]({case["url"]}) | {case["stars"]} |\n')
            else:
                f.write(f'| {domain} | {count} | {pct:.1f}% | - | - | - |\n')
        
        f.write('\n')
    
    # 特别对比分析
    f.write('---\n\n')
    f.write('## 🔍 特别对比：效率工具 vs 技术基础设施 中的 AI/LLM工具\n\n')
    f.write('两个类别的头号细分领域都是 AI/LLM工具，但侧重点明显不同：\n\n')
    
    # 效率工具的AI案例
    f.write('### 效率工具 - AI/LLM工具 典型案例\n\n')
    f.write('| 用途分类 | 项目名称 | Stars | 核心意图 |\n')
    f.write('|---------|---------|-------|---------|\n')
    for case in results['效率工具']['domain_cases'].get('AI/LLM工具', []):
        intent_short = case['intent'][:50] + '...' if len(case['intent']) > 50 else case['intent']
        f.write(f'| {case["use_case"]} | [{case["name"]}]({case["url"]}) | {case["stars"]} | {intent_short} |\n')
    
    f.write('\n**特点总结**：偏向**终端用户应用**，关注如何让普通用户更方便地使用AI，强调交互体验和实用性。典型用途包括AI交互界面、内容生成、辅助编程等。\n\n')
    
    # 技术基础设施的AI案例
    f.write('### 技术基础设施 - AI/LLM工具 典型案例\n\n')
    f.write('| 用途分类 | 项目名称 | Stars | 核心意图 |\n')
    f.write('|---------|---------|-------|---------|\n')
    for case in results['技术基础设施']['domain_cases'].get('AI/LLM工具', []):
        intent_short = case['intent'][:50] + '...' if len(case['intent']) > 50 else case['intent']
        f.write(f'| {case["use_case"]} | [{case["name"]}]({case["url"]}) | {case["stars"]} | {intent_short} |\n')
    
    f.write('\n**特点总结**：偏向**底层基础设施和开发者工具**，关注如何为AI应用提供支撑，强调安全性、性能和可扩展性。典型用途包括AI代理框架、安全沙箱、API网关等。\n\n')
    
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
print('\n分析完成！')
