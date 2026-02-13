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

# 从真实用途维度分析
usage_types = {
    # 模板/脚手架/初始化（开发阶段产物，非用途）
    'template_starter': [],
    # 硬件/IoT/嵌入式
    'hardware_iot': [],
    # 系统工具/OS/底层
    'system_os': [],
    # 开发者工具/DevOps/基础设施
    'dev_tool': [],
    # CMS/内容管理
    'cms_content': [],
    # 数据平台/分析
    'data_platform': [],
    # 网络安全/安全工具
    'security': [],
    # 游戏
    'gaming': [],
    # 信息不足
    'insufficient_info': [],
    # 难以归类
    'hard_to_classify': []
}

for item in other_items:
    intent = item.get('core_intent', '')
    desc = item.get('description', '') or ''
    insight = item.get('analytical_insight', '')
    full_text = (intent + ' ' + desc + ' ' + insight).lower()
    
    # 模板/脚手架
    if any(k in full_text for k in ['模板', '脚手架', 'starter', 'boilerplate', '默认项目', '初始化', '基础框架']):
        usage_types['template_starter'].append(item)
    # 硬件/IoT
    elif any(k in full_text for k in ['解锁', '固件', '硬件', '驱动', '路由器', '嵌入式', 'dvb', 'iot', '设备']):
        usage_types['hardware_iot'].append(item)
    # 系统/OS/底层工具
    elif any(k in full_text for k in ['操作系统', '内核', 'shell', '终端', '系统', 'linux', 'kernel']):
        usage_types['system_os'].append(item)
    # 开发者工具
    elif any(k in full_text for k in ['编译时', 'source generator', '组件库', '设计系统', 'figma', '代理', 'proxy', 'monorepo', '插件', '脚手架']):
        usage_types['dev_tool'].append(item)
    # CMS/内容管理
    elif any(k in full_text for k in ['cms', '内容管理', 'headless']):
        usage_types['cms_content'].append(item)
    # 数据平台
    elif any(k in full_text for k in ['数据', 'analytics', '分析']):
        usage_types['data_platform'].append(item)
    # 安全
    elif any(k in full_text for k in ['安全', '认证', 'auth', '加密', 'security']):
        usage_types['security'].append(item)
    # 游戏
    elif any(k in full_text for k in ['游戏', 'game', 'puzzle', 'chess', '扫雷']):
        usage_types['gaming'].append(item)
    # 信息不足
    elif any(k in full_text for k in ['未知', '信息不足', '占位符', '信息缺失', '仅含仓库名']):
        usage_types['insufficient_info'].append(item)
    else:
        usage_types['hard_to_classify'].append(item)

# 统计
print("=== 从真实用途维度分析 'other' 类别 ===\n")
total_accounted = 0
for usage, items in sorted(usage_types.items(), key=lambda x: -len(x[1])):
    if len(items) > 0:
        pct = len(items) / len(other_items) * 100
        total_accounted += len(items)
        print(f"{usage}: {len(items)} ({pct:.1f}%)")
        # 显示前2个示例
        for i, item in enumerate(items[:2]):
            print(f"  - {item.get('repo_name')}: {item.get('core_intent')[:60]}")
        print()

print(f"已分类: {total_accounted} / {len(other_items)} ({total_accounted/len(other_items)*100:.1f}%)\n")

# 深度分析 hard_to_classify
hard = usage_types['hard_to_classify']
print(f"=== 深度分析 hard_to_classify ({len(hard)} items) ===\n")

with open('hard_to_classify_detail.txt', 'w', encoding='utf-8') as f:
    f.write(f"难以归类项目详细列表 ({len(hard)} items)\n")
    f.write("="*60 + "\n\n")
    for i, item in enumerate(hard):
        f.write(f"{i+1}. {item.get('repo_name')}\n")
        f.write(f"   Intent: {item.get('core_intent')}\n")
        f.write(f"   Desc: {item.get('description') or 'N/A'}\n")
        f.write(f"   Insight: {item.get('analytical_insight')[:100]}...\n\n")

print("详细列表已保存到: hard_to_classify_detail.txt")

# 输出结论
print("\n" + "="*60)
print("结论与建议")
print("="*60)

template_count = len(usage_types['template_starter'])
hardware_count = len(usage_types['hardware_iot'])
system_count = len(usage_types['system_os'])
devtool_count = len(usage_types['dev_tool'])
info_count = len(usage_types['insufficient_info'])

print(f"""
1. 模板/脚手架类项目: {template_count}个 ({template_count/len(other_items)*100:.1f}%)
   - 这些是开发阶段产物，不是真实用途
   - 建议: 在数据预处理阶段过滤掉这类项目
   
2. 硬件/IoT类: {hardware_count}个 ({hardware_count/len(other_items)*100:.1f}%)
   - 现有micro_scenario确实未覆盖此用途类型
   - 建议: 考虑新增 'hardware_iot' 分类
   
3. 系统/OS/底层工具: {system_count}个 ({system_count/len(other_items)*100:.1f}%)
   - 现有分类未覆盖操作系统、内核等场景
   - 建议: 考虑新增 'system_infrastructure' 分类
   
4. 开发者工具: {devtool_count}个 ({devtool_count/len(other_items)*100:.1f}%)
   - 现有分类已覆盖(macro_category中有基础设施)
   - 但micro_scenario缺乏对应细分
   
5. 信息不足: {info_count}个 ({info_count/len(other_items)*100:.1f}%)
   - 这些项目确实无法判断用途
   - 建议: 保持'other'分类

是否需要重新跑DeepSeek?
- 如果过滤掉模板/脚手架项目，other比例会从21.9%降至约{((len(other_items)-template_count)/1531*100):.1f}%
- 硬件和系统类是否需要新增分类取决于你的研究目标
""")
