@echo off
chcp 65001 >nul
echo ========================================
echo Vibe Coding 双模式爬虫
echo ========================================
echo.

:: 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请安装 Python 3.8+
    pause
    exit /b 1
)

:: 检查 .env
if not exist .env (
    echo [提示] 未找到 .env 文件，从示例创建...
    copy .env.example .env >nul
    echo       请编辑 .env 文件添加 GITHUB_TOKEN
    echo.
)

:: 安装依赖
echo [1/2] 安装依赖...
pip install -q -r requirements.txt

:: 运行爬虫
echo [2/2] 启动双模式爬虫...
echo.
echo   模式A: 关键词搜索
echo   模式B: 配置文件搜索 ^(高置信度^)
echo.

python vibe_coding_crawler_v2.py

echo.
echo ========================================
echo 爬取完成！
echo ========================================
echo.
if exist vibe_coding_modeB_highconf_*.csv (
    echo 推荐查看: vibe_coding_modeB_highconf_*.csv
    echo           ^(高置信度 Vibe Coding 项目^)
)
echo.
pause
