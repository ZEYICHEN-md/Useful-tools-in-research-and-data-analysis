#!/bin/bash

echo "========================================"
echo "Vibe Coding 双模式爬虫"
echo "========================================"
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未找到 Python3"
    exit 1
fi

# 检查 .env
if [ ! -f .env ]; then
    echo "[提示] 未找到 .env 文件，从示例创建..."
    cp .env.example .env
    echo "       请编辑 .env 文件添加 GITHUB_TOKEN"
    echo ""
fi

# 安装依赖
echo "[1/2] 安装依赖..."
pip3 install -q -r requirements.txt

# 运行爬虫
echo "[2/2] 启动双模式爬虫..."
echo ""
echo "  模式A: 关键词搜索"
echo "  模式B: 配置文件搜索 (高置信度)"
echo ""

python3 vibe_coding_crawler_v2.py

echo ""
echo "========================================"
echo "爬取完成！"
echo "========================================"
echo ""

# 查找高置信度文件
MODEB_FILE=$(ls -t vibe_coding_modeB_highconf_*.csv 2>/dev/null | head -1)
if [ -n "$MODEB_FILE" ]; then
    echo "推荐查看: $MODEB_FILE"
    echo "          (高置信度 Vibe Coding 项目)"
fi
echo ""
