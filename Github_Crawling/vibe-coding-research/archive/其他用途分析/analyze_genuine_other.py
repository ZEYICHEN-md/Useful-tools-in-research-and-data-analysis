import json
import re

# 读取other项
other_items = []
with open('other_items.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        try:
            data = json.loads(line)
            other_items.append(data)
        except:
            pass

# 先排除已经识别出的有明确用途的项目
infrastructure_items = []
hardware_items = []
cms_items = []
devservice_items = []
system_items = []
data_items = []
docs_items = []
unknown_items = []
remaining = []

for item in other_items:
    intent = item.get('core_intent', '')
    insight = item.get('analytical_insight', '')
    full_text = (intent + ' ' + insight).lower()
    
    if any(k in full_text for k in ['编译时', 'source generator', '脚手架', '组件库', '设计系统', '代理', 'proxy', 'monorepo', '插件', 'figma']):
        infrastructure_items.append(item)
    elif any(k in full_text for k in ['解锁手机', '固件', '硬件', '驱动', '路由器', '机械臂', 'dvb', '嵌入式']):
        hardware_items.append(item)
    elif any(k in full_text for k in ['cms', '内容管理', 'headless', 'content management']):
        cms_items.append(item)
    elif any(k in full_text for k in ['api服务', '后端服务', '提供接口', 'gateway']):
        devservice_items.append(item)
    elif any(k in full_text for k in ['shell脚本', '操作系统', '内核', '驱动程序']):
        system_items.append(item)
    elif any(k in full_text for k in ['数据', 'analytics', '监控']):
        data_items.append(item)
    elif any(k in full_text for k in ['文档', 'documentation']):
        docs_items.append(item)
    elif any(k in full_text for k in ['未知', '信息不足', '占位符', '信息缺失']):
        unknown_items.append(item)
    else:
        remaining.append(item)

print(f"Remaining after excluding known categories: {len(remaining)}\n")

# 从用途角度分析这些remaining项目
purposes = {
    # 游戏相关
    'gaming': [],
    # 营销/推广
    'marketing': [],
    # 信息展示/官网
    'showcase': [],
    # 创意/艺术
    'creative': [],
    # 社区/活动
    'community': [],
    # 生活服务
    'lifestyle': [],
    # 非营利/公益
    'nonprofit': [],
    # 真正的其他
    'truly_other': []
}

for item in remaining:
    intent = item.get('core_intent', '')
    desc = item.get('description', '') or ''
    full_text = (intent + ' ' + desc).lower()
    repo_name = item.get('repo_name', '').lower()
    
    # 游戏相关
    if any(k in full_text for k in ['游戏', 'game', 'puzzle', 'minesweeper', '扫雷', 'chess', '棋牌']):
        purposes['gaming'].append(item)
    # 营销/推广/着陆页
    elif any(k in full_text for k in ['营销', '推广', 'landing', '着陆页', '官网', '展示', '介绍']):
        purposes['marketing'].append(item)
    # 创意/艺术
    elif any(k in full_text for k in ['艺术', 'creative', '音乐', '画廊', 'portfolio', '作品集']):
        purposes['creative'].append(item)
    # 社区/活动
    elif any(k in full_text for k in ['社区', '活动', 'event', '聚会', 'church', '教堂']):
        purposes['community'].append(item)
    # 生活服务
    elif any(k in full_text for k in ['餐厅', 'food', '旅行', '旅游', '天气', '生活']):
        purposes['lifestyle'].append(item)
    # 非营利
    elif any(k in full_text for k in ['公益', '非盈利', '慈善', '非营利']):
        purposes['nonprofit'].append(item)
    else:
        purposes['truly_other'].append(item)

# 统计
print("=== 用途类型分析（从 remaining 中识别）===\n")
for purpose, items in sorted(purposes.items(), key=lambda x: -len(x[1])):
    if len(items) > 0:
        pct = len(items) / len(remaining) * 100
        print(f"{purpose}: {len(items)} ({pct:.1f}% of remaining)")
        for i, item in enumerate(items[:3]):
            print(f"  - {item.get('repo_name')}: {item.get('core_intent')[:65]}")
        print()

# 重点看truly_other
truly = purposes['truly_other']
print(f"\n=== truly_other 详细分析 ({len(truly)} items) ===\n")

with open('truly_other_detail.txt', 'w', encoding='utf-8') as f:
    f.write(f"truly_other 项目详细列表 ({len(truly)} items)\n")
    f.write("="*60 + "\n\n")
    for i, item in enumerate(truly):
        f.write(f"{i+1}. {item.get('repo_name')}\n")
        f.write(f"   Intent: {item.get('core_intent')}\n")
        f.write(f"   Desc: {item.get('description') or 'N/A'}\n")
        f.write(f"   Macro: {item.get('macro_category')}\n\n")

print("详细列表已保存到: truly_other_detail.txt")
