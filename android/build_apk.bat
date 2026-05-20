@echo off
chcp 65001 >nul
title 有色金属AI交易 - APK 构建工具

echo.
echo ╔══════════════════════════════════════════════╗
echo ║   🔩 有色金属回收倒卖AI系统                    ║
echo ║   Android APK 一键构建工具                      ║
echo ╚══════════════════════════════════════════════╝
echo.

:: 检查 Java
java -version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 未检测到 Java JDK！
    echo    请安装 JDK 17+: https://adoptium.net
    echo.
    pause
    exit /b 1
)
echo ✅ Java 已就绪

:: 检查 Android SDK
if "%ANDROID_HOME%"=="" (
    if "%ANDROID_SDK_ROOT%"=="" (
        echo ⚠️  未设置 ANDROID_HOME 环境变量
        echo    请安装 Android Studio 或 Android SDK 命令行工具
        echo    下载: https://developer.android.com/studio
        echo.
        echo    安装后设置环境变量:
        echo    set ANDROID_HOME=C:\Users\你的用户名\AppData\Local\Android\Sdk
        echo.
        pause
        exit /b 1
    ) else (
        set "ANDROID_HOME=%ANDROID_SDK_ROOT%"
    )
)
echo ✅ ANDROID_HOME=%ANDROID_HOME%

:: 进入 Android 项目目录
cd /d "%~dp0android"

:: 检查 Gradle Wrapper
if not exist "gradlew.bat" (
    echo.
    echo ❌ 未找到 gradlew.bat
    echo    请确保在项目 android/ 目录中运行此脚本
    pause
    exit /b 1
)

echo.
echo ═══════════════════════════════════════════════
echo   📱 开始构建 Debug APK ...
echo ═══════════════════════════════════════════════
echo.
echo   提示: 首次构建会下载 Gradle 和依赖，需要 5-15 分钟
echo.

call gradlew.bat assembleDebug

if %errorlevel% neq 0 (
    echo.
    echo ❌ 构建失败！
    echo    常见原因:
    echo    1. 网络问题导致依赖下载失败 - 请检查网络或配置代理
    echo    2. JDK 版本不兼容 - 需要 JDK 17+
    echo    3. Android SDK 缺少组件 - 请用 Android Studio SDK Manager 安装
    echo       Platform: Android 34, Build-Tools: 34.0.0+
    pause
    exit /b 1
)

echo.
echo ═══════════════════════════════════════════════
echo   ✅ APK 构建成功！
echo ═══════════════════════════════════════════════
echo.
echo   📦 输出路径:
echo   app\build\outputs\apk\debug\app-debug.apk
echo.
echo   📲 安装方式:
echo   1. 将 APK 文件传到手机
echo   2. 在手机上打开文件管理器
echo   3. 点击 APK 文件安装
echo   4. 如提示"未知来源"，请在设置中允许
echo.
echo   ⚠️  注意: 部署 Streamlit Cloud 后，
echo   请修改 MainActivity.java 中的 APP_URL！
echo.

:: 询问是否打开输出文件夹
set /p open="是否打开 APK 所在文件夹？(Y/N): "
if /i "%open%"=="Y" (
    start "" "%~dp0android\app\build\outputs\apk\debug"
)

pause
