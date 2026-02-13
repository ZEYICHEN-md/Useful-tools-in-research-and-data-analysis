# -*- coding: utf-8 -*-
"""
V4版本：更细粒度的用途分类，避免"通用工具"等过于宽泛的分类
"""
import json
import sys
import os
import re
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

def extract_domains(core_intent, analytical_insight, description):
    """提取项目所属的领域"""
    text = f'{core_intent} {analytical_insight} {description if description else ""}'
    domains = []
    
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

def classify_specific_use_case(core_intent, description, domain):
    """
    根据用途/功能进行更具体的分类
    避免使用"通用工具"等过于宽泛的分类
    """
    text = f'{core_intent} {description if description else ""}'
    text_lower = text.lower()
    
    # AI/LLM工具的细粒度分类
    if domain == 'AI/LLM工具':
        if any(kw in text for kw in ['聊天', 'chat', '对话', '界面', 'UI', '前端', '浏览器']):
            return 'AI聊天界面'
        if any(kw in text for kw in ['代码', '编程', 'IDE', '开发辅助', 'copilot']):
            return 'AI编程助手'
        if any(kw in text for kw in ['视频', '视觉', '特效', '生成视频']):
            return 'AI视频生成'
        if any(kw in text for kw in ['写作', '文案', '内容生成', '生成文章']):
            return 'AI写作助手'
        if any(kw in text for kw in ['图像', '图片', '绘画', '生成图']):
            return 'AI图像生成'
        if any(kw in text for kw in ['代理', 'agent', '智能体', '自主', '自动化工作流']):
            return 'AI代理框架'
        if any(kw in text for kw in ['安全', '沙箱', '防护', '隐私保护']):
            return 'AI安全沙箱'
        if any(kw in text for kw in ['分析', '预测', '洞察', '数据']):
            return 'AI数据分析'
        if any(kw in text for kw in ['客服', '客服机器人', '自动回复']):
            return 'AI客服系统'
        if any(kw in text for kw in ['路由', '网关', 'API管理']):
            return 'AI路由网关'
        return 'AI其他应用'
    
    # 开发工具/脚手架的细粒度分类
    if domain == '开发工具/脚手架':
        if any(kw in text for kw in ['Next.js', 'React', 'Vue', 'Angular']):
            return '前端框架模板'
        if any(kw in text for kw in ['命令行', 'CLI', '终端', 'shell']):
            return 'CLI命令行工具'
        if any(kw in text for kw in ['API', '接口封装', 'SDK']):
            return 'API封装工具'
        if any(kw in text for kw in ['构建', '打包', '编译', 'build']):
            return '构建工具'
        if any(kw in text for kw in ['代码生成', '自动生成', 'scaffold']):
            return '代码生成器'
        if any(kw in text for kw in ['测试', '调试', 'debug']):
            return '测试调试工具'
        return '开发工具其他'
    
    # 自动化/工作流的细粒度分类
    if domain == '自动化/工作流':
        if any(kw in text for kw in ['CI/CD', '部署', '持续集成']):
            return 'CI/CD自动化'
        if any(kw in text for kw in ['数据处理', 'ETL', '同步']):
            return '数据处理自动化'
        if any(kw in text for kw in ['定时任务', '调度', 'cron']):
            return '定时任务调度'
        if any(kw in text for kw in ['工作流引擎', '流程编排', 'pipeline']):
            return '工作流引擎'
        return '自动化其他'
    
    # 设计工具的细粒度分类
    if domain == '设计工具':
        if any(kw in text for kw in ['UI', 'UX', '界面设计', '原型']):
            return 'UI/UX设计工具'
        if any(kw in text for kw in ['图形', '图像处理', '图片编辑']):
            return '图形图像工具'
        if any(kw in text for kw in ['设计系统', '组件库', '样式']):
            return '设计系统构建'
        if any(kw in text for kw in ['3D', '建模', '渲染']):
            return '3D设计工具'
        return '设计工具其他'
    
    # 企业管理的细粒度分类
    if domain == '企业管理':
        if any(kw in text for kw in ['订单', '点餐', '外卖']):
            return '订单管理系统'
        if any(kw in text for kw in ['库存', '仓储', '供应链']):
            return '库存管理系统'
        if any(kw in text for kw in ['客户', 'CRM', '销售']):
            return 'CRM客户管理'
        if any(kw in text for kw in ['员工', '人事', 'HR', '招聘']):
            return '人力资源系统'
        if any(kw in text for kw in ['财务', '会计', '发票', '报销']):
            return '财务管理系统'
        if any(kw in text for kw in ['后台', 'admin', '管理面板']):
            return '后台管理系统'
        if any(kw in text for kw in ['项目', '任务', '协作']):
            return '项目管理系统'
        return '企业管理其他'
    
    # 网站/门户的细粒度分类
    if domain == '网站/门户':
        if any(kw in text for kw in ['博客', 'blog', '个人网站']):
            return '个人博客网站'
        if any(kw in text for kw in ['作品集', 'portfolio', '展示']):
            return '作品集展示站'
        if any(kw in text for kw in ['企业', '公司', '品牌', '官网']):
            return '企业官网'
        if any(kw in text for kw in ['电商', '商城', '商店']):
            return '电商网站'
        if any(kw in text for kw in ['落地页', 'landing page', '营销']):
            return '营销落地页'
        return '网站其他'
    
    # 数据可视化/BI的细粒度分类
    if domain == '数据可视化/BI':
        if any(kw in text for kw in ['仪表盘', 'dashboard', '面板']):
            return '数据仪表盘'
        if any(kw in text for kw in ['图表', '报表', '统计']):
            return '图表报表工具'
        if any(kw in text for kw in ['监控', '实时', '告警']):
            return '实时监控面板'
        if any(kw in text for kw in ['分析', 'BI', '商业智能']):
            return '商业分析工具'
        return '数据可视化其他'
    
    # 游戏/娱乐的细粒度分类
    if domain == '游戏/娱乐':
        if any(kw in text for kw in ['Minecraft', '游戏mod', '插件']):
            return '游戏Mod/插件'
        if any(kw in text for kw in ['游戏引擎', 'framework']):
            return '游戏引擎框架'
        if any(kw in text for kw in ['休闲', '小游戏']):
            return '休闲小游戏'
        if any(kw in text for kw in ['RPG', '角色扮演']):
            return 'RPG游戏'
        if any(kw in text for kw in ['策略', '模拟']):
            return '策略模拟游戏'
        return '游戏其他'
    
    # 媒体/视频的细粒度分类
    if domain == '媒体/视频':
        if any(kw in text for kw in ['播放器', 'player']):
            return '媒体播放器'
        if any(kw in text for kw in ['编辑', '剪辑', '后期']):
            return '视频编辑工具'
        if any(kw in text for kw in ['直播', 'stream', '流媒体']):
            return '直播流媒体'
        if any(kw in text for kw in ['IPTV', '电视']):
            return 'IPTV播放器'
        return '媒体其他'
    
    # 社交/社区的细粒度分类
    if domain == '社交/社区':
        if any(kw in text for kw in ['聊天', '消息', 'IM']):
            return '即时通讯'
        if any(kw in text for kw in ['论坛', '社区', '讨论']):
            return '论坛社区'
        if any(kw in text for kw in ['社交', '网络', '好友']):
            return '社交网络'
        if any(kw in text for kw in ['约会', '匹配']):
            return '约会匹配平台'
        return '社交其他'
    
    # 医疗健康的细粒度分类
    if domain == '医疗健康':
        if any(kw in text for kw in ['病历', '电子病历']):
            return '电子病历系统'
        if any(kw in text for kw in ['诊断', '辅助诊断']):
            return '辅助诊断工具'
        if any(kw in text for kw in ['医院', '门诊', 'HIS']):
            return '医院管理系统'
        if any(kw in text for kw in ['健康', '监测', '追踪']):
            return '健康监测应用'
        if any(kw in text for kw in ['药品', '药房', '处方']):
            return '药品管理系统'
        if any(kw in text for kw in ['兽医', '宠物医疗']):
            return '兽医医疗系统'
        return '医疗其他'
    
    # 教育学习的细粒度分类
    if domain == '教育学习':
        if any(kw in text for kw in ['课程', '学习管理', 'LMS']):
            return '课程管理系统'
        if any(kw in text for kw in ['编程', '代码', '算法']):
            return '编程学习平台'
        if any(kw in text for kw in ['考试', '测验', '评测']):
            return '考试评测系统'
        if any(kw in text for kw in ['笔记', '知识', 'wiki']):
            return '知识管理工具'
        return '教育其他'
    
    # 金融/交易的细粒度分类
    if domain == '金融/交易':
        if any(kw in text for kw in ['支付', '付款', '收银']):
            return '支付系统'
        if any(kw in text for kw in ['交易', '股票', '投资']):
            return '交易投资平台'
        if any(kw in text for kw in ['区块链', 'crypto', '比特币']):
            return '加密货币/DeFi'
        if any(kw in text for kw in ['分析', '风控']):
            return '金融分析工具'
        return '金融其他'
    
    # 安全/隐私的细粒度分类
    if domain == '安全/隐私':
        if any(kw in text for kw in ['认证', '授权', '登录', '身份']):
            return '身份认证系统'
        if any(kw in text for kw in ['加密', '解密', '密码学']):
            return '加密解密工具'
        if any(kw in text for kw in ['代理', 'VPN', '隧道']):
            return '代理VPN工具'
        if any(kw in text for kw in ['防火墙', '防护']):
            return '安全防护工具'
        return '安全其他'
    
    # 代理/网关的细粒度分类
    if domain == '代理/网关':
        if any(kw in text for kw in ['API网关', 'gateway']):
            return 'API网关'
        if any(kw in text for kw in ['反向代理', '负载均衡']):
            return '反向代理'
        if any(kw in text for kw in ['AI路由']):
            return 'AI模型路由'
        return '网关其他'
    
    # 对于其他domain，根据文本内容提取更具体的分类
    if '管理' in text:
        if '用户' in text:
            return '用户管理系统'
        if '内容' in text:
            return '内容管理系统'
        return '管理系统'
    
    if '分析' in text or '分析工具' in text:
        return '数据分析工具'
    
    if '生成' in text or '创建' in text:
        if '网站' in text or 'web' in text_lower:
            return '网站生成器'
        if '代码' in text:
            return '代码生成器'
        return '内容生成器'
    
    if '监控' in text:
        return '监控工具'
    
    if '平台' in text:
        return '应用平台'
    
    # 提取核心动词+名词作为最后的分类
    # 如果都没匹配上，返回"其他"+domain名称
    return f'{domain}其他'

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
        use_case = classify_specific_use_case(item['core_intent'], item.get('description', ''), domain)
        use_case_groups[use_case].append(item)
    
    # 从每个用途类别中选择一个代表性项目（优先stars高的）
    selected_examples = []
    used_projects = set()
    
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
    csv_path = os.path.join(output_dir, f'micro_scenario_{scenario}_domains_with_cases_v4.csv')
    with open(csv_path, 'w', encoding='utf-8-sig') as f:
        f.write('应用领域,项目数,占比,典型案例1_用途,典型案例1_名称,典型案例1_stars,典型案例1链接,典型案例1描述,典型案例2_用途,典型案例2_名称,典型案例2_stars,典型案例2链接,典型案例2描述,典型案例3_用途,典型案例3_名称,典型案例3_stars,典型案例3链接,典型案例3描述\n')
        
        for domain, count in results[scenario]['domains']:
            pct = count / results[scenario]['count'] * 100
            cases = results[scenario]['domain_cases'].get(domain, [])
            
            # 准备案例数据
            case_data = []
            for i in range(3):
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
summary_csv = os.path.join(output_dir, 'all_domain_typical_cases_v4.csv')
with open(summary_csv, 'w', encoding='utf-8-sig') as f:
    f.write('Micro-Scenario,应用领域,用途分类,项目名称,Stars,核心意图,GitHub链接\n')
    for case in all_domain_cases:
        intent_clean = case['core_intent'].replace(',', '，').replace('"', '""')
        f.write(f"{case['micro_scenario']},{case['domain']},{case['use_case']},{case['repo_name']},{case['stars']},\"{intent_clean}\",{case['repo_url']}\n")

print(f'[OK] 已生成汇总: {summary_csv}')

# 生成Markdown报告
md_path = os.path.join(output_dir, 'micro_scenario_analysis_report_v4.md')
with open(md_path, 'w', encoding='utf-8') as f:
    f.write('# 📊 Vibe Coding 8大Micro-Scenario类别深度分析报告 (V4)\n\n')
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
        f.write('| 应用领域 | 项目数 | 占比 | 具体用途 | 典型案例 | Stars |\n')
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
    f.write('| 具体用途 | 项目名称 | Stars | 核心意图 |\n')
    f.write('|---------|---------|-------|---------|\n')
    for case in results['效率工具']['domain_cases'].get('AI/LLM工具', []):
        intent_short = case['intent'][:50] + '...' if len(case['intent']) > 50 else case['intent']
        f.write(f'| {case["use_case"]} | [{case["name"]}]({case["url"]}) | {case["stars"]} | {intent_short} |\n')
    
    f.write('\n**特点总结**：偏向**终端用户应用**，关注如何让普通用户更方便地使用AI，强调交互体验和实用性。\n\n')
    
    # 技术基础设施的AI案例
    f.write('### 技术基础设施 - AI/LLM工具 典型案例\n\n')
    f.write('| 具体用途 | 项目名称 | Stars | 核心意图 |\n')
    f.write('|---------|---------|-------|---------|\n')
    for case in results['技术基础设施']['domain_cases'].get('AI/LLM工具', []):
        intent_short = case['intent'][:50] + '...' if len(case['intent']) > 50 else case['intent']
        f.write(f'| {case["use_case"]} | [{case["name"]}]({case["url"]}) | {case["stars"]} | {intent_short} |\n')
    
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
print('\n分析完成！')
