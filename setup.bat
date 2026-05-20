@echo off
chcp 65001 >nul 2>&1
title 有色金属回收AI系统

echo.
echo  ============================================
echo     🔩 有色金属回收倒卖AI系统 v1.1
echo  ============================================
echo.

:: 检查Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [错误] 未找到 Python！请先安装 Python 3.9+
    echo  下载地址: https://www.python.org/downloads/
    echo  安装时务必勾选 "Add Python to PATH"
    pause
    exit /b 1
)

python --version
echo.

:: 创建虚拟环境
if not exist "venv\Scripts\python.exe" (
    echo  [1/3] 正在创建虚拟环境...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo  [错误] 虚拟环境创建失败
        pause
        exit /b 1
    )
    echo  虚拟环境已创建
) else (
    echo  [1/3] 虚拟环境已存在，跳过创建
)

:: 安装依赖
echo.
echo  [2/3] 安装依赖包（首次可能需要几分钟）...
venv\Scripts\python -m pip install --upgrade pip -q
venv\Scripts\pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo  [警告] 部分包安装失败，尝试使用国内镜像...
    venv\Scripts\pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
)

:: 启动
echo.
echo  [3/3] 启动系统...
echo.
echo  ╔══════════════════════════════════════════╗
echo  ║  浏览器访问: http://localhost:8501       ║
echo  ║  按 Ctrl+C 停止服务                      ║
echo  ╚══════════════════════════════════════════╝
echo.

venv\Scripts\python -m streamlit run web\app.py --server.port 8501

pause
