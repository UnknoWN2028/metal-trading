@echo off
chcp 65001 >nul
title 有色金属AI交易 - 一键部署与构建

echo.
echo ╔══════════════════════════════════════════════╗
echo ║  🔩 有色金属回收倒卖AI系统 v3                  ║
echo ║  一键部署 + APK 构建向导                       ║
echo ╚══════════════════════════════════════════════╝
echo.
echo  请选择操作:
echo.
echo   [1] 测试本地运行 (streamlit run)
echo   [2] 部署到 Streamlit Cloud (需要 GitHub 仓库)
echo   [3] 构建 Android APK
echo   [4] 完整流程指引
echo   [0] 退出
echo.

set /p choice="请输入选项 (0-4): "

if "%choice%"=="1" goto local_run
if "%choice%"=="2" goto cloud_deploy
if "%choice%"=="3" goto build_apk
if "%choice%"=="4" goto full_guide
if "%choice%"=="0" goto end

echo 无效选项，请重新运行
pause
goto end

:local_run
echo.
echo ═══════════════════════════════════════════════
echo   🚀 本地运行测试
echo ═══════════════════════════════════════════════
echo.

:: 检查虚拟环境
if not exist "venv\Scripts\python.exe" (
    echo 🔧 创建虚拟环境...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ❌ 创建虚拟环境失败，请安装 Python 3.9+
        pause
        goto end
    )
    echo 📦 安装依赖...
    venv\Scripts\pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
)

echo.
echo 🚀 启动 Streamlit Web 界面...
echo 📱 浏览器将打开 http://localhost:8501
echo 💡 按 Ctrl+C 停止
echo.

venv\Scripts\streamlit run streamlit_app.py --server.port 8501
goto end

:cloud_deploy
echo.
echo ═══════════════════════════════════════════════
echo   ☁️  Streamlit Cloud 部署指引
echo ═══════════════════════════════════════════════
echo.
echo  前提条件:
echo   1. 拥有 GitHub 账号 (https://github.com)
echo   2. 拥有 Streamlit Cloud 账号 (https://share.streamlit.io)
echo.
echo  步骤:
echo.
echo  📌 步骤 1: 初始化 Git 仓库
echo     git init
echo     git add .
echo     git commit -m "Metal Trading AI v3 - Initial commit"
echo.
echo  📌 步骤 2: 创建 GitHub 仓库并推送
echo     在 GitHub 创建新仓库 (如: metal-trading-ai)
echo     git remote add origin https://github.com/YOUR_USER/metal-trading-ai.git
echo     git push -u origin main
echo.
echo  📌 步骤 3: 部署到 Streamlit Cloud
echo     访问 https://share.streamlit.io
echo     → New App → 选择仓库 → Main file: streamlit_app.py → Deploy!
echo.
echo  📌 步骤 4: 获取部署 URL
echo     例如: https://metal-trading-ai.streamlit.app
echo.
echo  📌 步骤 5: 更新 APK 中的 URL
echo     编辑 android\app\src\main\java\com\metal\trading\MainActivity.java
echo     修改 APP_URL 为你的部署地址
echo.
echo  详细说明见: APK_BUILD_GUIDE.md
echo.
pause
goto end

:build_apk
echo.
echo ═══════════════════════════════════════════════
echo   📱 构建 Android APK
echo ═══════════════════════════════════════════════
echo.
echo   ⚠️  请先完成云部署，并更新 APP_URL！
echo.
echo   开始构建...
cd android
call build_apk.bat
cd ..
goto end

:full_guide
echo.
echo ═══════════════════════════════════════════════
echo   📖 完整流程指引
echo ═══════════════════════════════════════════════
echo.
echo  完整流程分为两大步:
echo.
echo  ┌─────────────────────────────────────────────────┐
echo  │ 第一步: 部署到 Streamlit Cloud (免费云服务器)      │
echo  │                                                  │
echo  │  1. 将代码推送到 GitHub                           │
echo  │  2. 在 share.streamlit.io 创建 App               │
echo  │  3. 获取部署 URL (如 xxx.streamlit.app)          │
echo  │  4. 用手机浏览器访问测试                           │
echo  └─────────────────────────────────────────────────┘
echo                          ↓
echo  ┌─────────────────────────────────────────────────┐
echo  │ 第二步: 构建 Android APK                          │
echo  │                                                  │
echo  │  1. 安装 Android Studio                          │
echo  │  2. 打开 android/ 项目                            │
echo  │  3. 修改 APP_URL 为部署地址                        │
echo  │  4. Build → Build APK                            │
echo  │  5. 安装到手机                                    │
echo  └─────────────────────────────────────────────────┘
echo.
echo  📄 详细说明: APK_BUILD_GUIDE.md
echo.
pause
goto end

:end
echo.
echo  再见！🔩
exit /b 0
