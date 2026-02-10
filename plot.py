import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from matplotlib.patches import FancyBboxPatch
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os

# 设置中文字体为微软雅黑，避免中文标题无法显示
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

# ==========================================
# 1. 数据准备
# ==========================================
data = [
    {"name": "Gemini 3\nPro",             "score": 1293, "color": "#34A853"},  # Google绿 (SOTA)
    {"name": "GPT-5.2",                   "score": 1253, "color": "#1A1A1A"},  # OpenAI黑 (SOTA)
    {"name": "Kimi K2.5",                 "score": 1249, "color": "#007AFF"},  # Kimi蓝 (SOTA - 全球第三)
    {"name": "Ernie 5.0",                 "score": 1219, "color": "#2932E1"},  # 百度蓝 (SOTA - 新入榜)
    {"name": "Qwen3 VL",                  "score": 1209, "color": "#FF8C00"},  # 通义橙 (SOTA)
    {"name": "Claude Sonnet 4",           "score": 1206, "color": "#D97757"},  # Claude肉粉 (SOTA)
    {"name": "Hunyuan Vision 1.5",        "score": 1187, "color": "#0052D9"}, # 腾讯蓝 (SOTA - 新入榜)
    {"name": "Grok 4",                    "score": 1182, "color": "#7B68EE"},  # Grok紫 (SOTA)
]

names = [d["name"] for d in data]
scores = [d["score"] for d in data]
base_colors = [d["color"] for d in data]

# 视觉上压缩柱形高度，减小头部差距（标签仍显示原始分数）
min_score = min(scores)
max_score = max(scores)
score_range = max_score - min_score if max_score != min_score else 1
visual_scores = [
    ((score - min_score) / score_range) ** 0.3 * 40 + 20
    for score in scores
]

# ==========================================
# 2. 核心逻辑：设置高亮 (透明度控制)
# ==========================================
# 如果名字里包含 'Kimi'，透明度为 1.0 (不透明)，否则为 0.3 (半透明)
alphas = [1.0 if "Kimi" in name else 0.3 for name in names]

# 将 Hex 颜色转换为 Matplotlib 可识别的 RGBA 格式
from matplotlib.colors import to_rgba
bar_colors = [to_rgba(c, alpha=a) for c, a in zip(base_colors, alphas)]

# ==========================================
# 3. 辅助函数：生成简单的圆形占位 Logo
#    (为了让你能直接运行，不用下载图片，我用代码画圆代替)
# ==========================================
def create_dummy_logo(color, text_char):
    # 创建一个透明背景的图
    size = (100, 100)
    img = Image.new("RGBA", size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # 画一个圆
    draw.ellipse((0, 0, 100, 100), fill=color)
    
    # 稍微处理一下颜色用来写字 (如果是深色背景用白色字)
    text_color = "white"
    
    # 画一个简单的字母在中间
    # 这里为了通用不加载特殊字体，只画个简单的形状示意
    # 实际使用时，你可以把这里替换为 img = Image.open("logo.png")
    return img

# ==========================================
# 4. 开始绘图
# ==========================================
fig, ax = plt.subplots(figsize=(14, 6), dpi=150) # 高清设置

# 绘制柱状图（圆角）
x_positions = np.arange(len(names))
bar_width = 0.6
bars = []
for i, (score, color) in enumerate(zip(visual_scores, bar_colors)):
    left = x_positions[i] - bar_width / 2
    rounded_bar = FancyBboxPatch(
        (left, 0),
        bar_width,
        score,
        boxstyle="round,pad=0,rounding_size=0.20",
        linewidth=0,
        facecolor=color,
        mutation_aspect=0.5,
    )
    ax.add_patch(rounded_bar)
    bars.append((left, bar_width, score))

ax.set_xlim(-0.5, len(names) - 0.5)
ax.set_ylim(0, max(visual_scores) + 10)

# 设置样式
ax.set_title("模型视觉理解能力众测排名", fontsize=18, pad=20, loc='center', color='black')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.yaxis.set_visible(False) # 隐藏Y轴，因为数据在柱子上
ax.grid(axis='y', linestyle='--', alpha=0.3)

# 添加数值标签
for (left, width, score), raw_score, is_target in zip(bars, scores, alphas):
    # 所有数值稍微加粗，Kimi 更加突出
    font_weight = 'bold' if is_target == 1.0 else 'semibold'
    
    ax.text(
        left + width / 2,
        score + 3,  # 放在柱顶上方一点点
        f"{raw_score}", 
        ha='center', va='bottom', 
        color='black', fontsize=12, fontweight=font_weight
    )

# ==========================================
# 5. 添加 Logo 和 调整 X 轴标签
# ==========================================
# 隐藏原本的 X 轴标签，我们自己手动画，为了放 Logo
ax.set_xticklabels([]) 
ax.tick_params(axis='x', length=0) # 隐藏刻度线

for i, (name, color) in enumerate(zip(names, base_colors)):
    # 1. 获取（生成）Logo
    logo_img = create_dummy_logo(color, name[0])
    
    # 2. 创建 ImageBox
    imagebox = OffsetImage(logo_img, zoom=0.25) # zoom控制 Logo 大小
    
    # 3. 放置 Logo (y坐标设为负数，放在 X 轴下方)
    ab = AnnotationBbox(imagebox, (i, -2.5), frameon=False, boxcoords="data", pad=0)
    ax.add_artist(ab)
    
    # 4. 放置文字标签 (在 Logo 下方)
    # 所有文字标签使用深色
    text_color = "black"
    font_weight = "bold" if "Kimi" in name else "normal"
    
    ax.text(
        i, -5, # Y 坐标继续往下移
        name, 
        ha='center', va='top', 
        rotation=35, 
        fontsize=12, 
        color=text_color,
        fontweight=font_weight
    )

# 调整布局，防止下方文字被切掉
plt.tight_layout()
plt.subplots_adjust(bottom=0.26) # 底部留白给 Logo 和文字

# 保存或显示
output_path = os.path.join(os.path.dirname(__file__), "chart_with_logo_visual_LM.png")
plt.savefig(output_path, bbox_inches='tight')
plt.show()