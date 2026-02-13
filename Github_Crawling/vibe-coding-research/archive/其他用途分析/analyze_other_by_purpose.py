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

# 从用途类型维度重新分类
purpose_categories = {
    # 可能是现有分类遗漏的用途类型
    'infrastructure_devtool': [],  # 基础设施/开发工具
    'hardware_iot': [],            # 硬件/IoT
    'cms_headless': [],            # CMS/内容管理
    'developer_service': [],       # 开发者服务
    'system_tool': [],             # 系统工具
    'data_platform': [],           # 数据平台
    'documentation_site': [],      # 文档站
    'unknown_unclear': [],         # 信息不足无法判断
    'genuinely_other': [],         # 确实不属于现有分类
}

for item in other_items:
    intent = item.get('core_intent', '')
    insight = item.get('analytical_insight', '')
    macro = item.get('macro_category', '')
    full_text = (intent + ' ' + insight).lower()
    
    # 硬件相关
    if any(k in full_text for k in ['解锁手机', '固件', '硬件', '驱动', '路由器', '机械臂', 'dvb', '嵌入式']):
        purpose_categories['hardware_iot'].append(item)
    # CMS/Headless内容管理
    elif any(k in full_text for k in ['cms', '内容管理', 'headless', 'content management']):
        purpose_categories['cms_headless'].append(item)
    # 开发工具/基础设施
    elif any(k in full_text for k in ['编译时', 'source generator', '脚手架', '组件库', '设计系统', '代理', 'proxy', 'monorepo', '插件']):
        purpose_categories['infrastructure_devtool'].append(item)
    # 开发者服务
    elif any(k in full_text for k in ['api服务', '后端服务', '提供接口', 'gateway']):
        purpose_categories['developer_service'].append(item)
    # 系统工具
    elif any(k in full_text for k in ['shell脚本', '操作系统', '内核', '驱动程序', '系统']):
        purpose_categories['system_tool'].append(item)
    # 数据平台
    elif any(k in full_text for k in ['数据', 'analytics', '监控']):
        purpose_categories['data_platform'].append(item)
    # 文档站
    elif any(k in full_text for k in ['文档', 'documentation']):
        purpose_categories['documentation_site'].append(item)
    # 信息不足
    elif any(k in full_text for k in ['未知', '信息不足', '占位符', '信息缺失']):
        purpose_categories['unknown_unclear'].append(item)
    else:
        purpose_categories['genuinely_other'].append(item)

# 统计
print("=== 按用途类型重新分类 ===\n")
for cat, items in sorted(purpose_categories.items(), key=lambda x: -len(x[1])):
    if len(items) > 0:
        pct = len(items) / len(other_items) * 100
        print(f"{cat}: {len(items)} ({pct:.1f}%)")
        # 显示前2个示例
        for i, item in enumerate(items[:2]):
            print(f"  - {item.get('repo_name')}: {item.get('core_intent')[:70]}")
        print()

# 重点分析 genuinely_other
print("\n=== 深度分析 genuinely_other ===")
genuinely = purpose_categories['genuinely_other']
print(f"数量: {len(genuinely)}\n")

# 分析这些项目的关键词
words = Counter()
for item in genuinely:
    text = (item.get('core_intent', '') + ' ' + item.get('analytical_insight', '')).lower()
    for word in ['官网', '网站', 'web', '平台', '应用', '服务', '工具', '管理', '系统', '原型', '模板']:
        if word in text:
            words[word] += 1

print("高频词:")
for w, c in words.most_common(10):
    print(f"  {w}: {c}")

# 保存详细分析
with open('other_purpose_analysis.txt', 'w', encoding='utf-8') as f:
    f.write(f"从用途类型维度分析 'other' 分类 ({len(other_items)} items)\n")
    f.write("="*60 + "\n\n")
    
    for cat, items in sorted(purpose_categories.items(), key=lambda x: -len(x[1])):
        if len(items) > 0:
            f.write(f"\n## {cat}: {len(items)} items\n\n")
            for i, item in enumerate(items[:10]):
                f.write(f"{i+1}. {item.get('repo_name')}\n")
                f.write(f"   Intent: {item.get('core_intent')}\n")
                f.write(f"   Macro: {item.get('macro_category')}\n\n")

print("\n详细分析已保存到: other_purpose_analysis.txt")
