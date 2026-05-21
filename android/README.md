# 🔩 有色金属AI交易 — Android APK 构建指南

## 📱 方式一：Android Studio（推荐）

1. **安装 Android Studio**  
   https://developer.android.com/studio

2. **打开项目**  
   `File → Open` → 选择 `android/` 目录

3. **配置 Streamlit Cloud URL**  
   打开 `app/build.gradle`，找到 `buildConfigField 'String', 'APP_URL'`  
   改成你部署后的 Streamlit Cloud 地址：
   ```gradle
   buildConfigField 'String', 'APP_URL', '"https://你的应用名.streamlit.app"'
   ```

4. **构建 APK**  
   `Build → Build Bundle(s) / APK(s) → Build APK(s)`  
   生成的 APK 在 `app/build/outputs/apk/release/app-release.apk`

5. **安装到手机**  
   - USB 连接手机 → 开启「开发者选项 → USB 调试」→ 点击 Run
   - 或把 APK 传到手机直接安装

## 🚀 方式二：命令行（需要 Gradle）

```bash
cd android
./gradlew assembleRelease   # macOS/Linux
# 或
gradlew.bat assembleRelease  # Windows
```

## 🔧 本地开发调试

调试版默认连接 `http://10.0.2.2:8501`（模拟器中指向宿主机 localhost）。

启动 Streamlit 本地服务：
```bash
cd Metal项目根目录
streamlit run streamlit_app.py
```

然后 Android Studio 中运行 debug 版本即可连接本地服务。

## 📦 首次部署 Streamlit Cloud

1. 将项目推送到 GitHub
2. 登录 https://share.streamlit.io
3. 点击 `New app` → 选择仓库
4. Main file path: `streamlit_app.py`
5. 在 Settings → Secrets 中添加：
   ```
   [llm]
   api_key = "你的DeepSeek API密钥"
   ```
6. 部署后复制 URL（格式: `https://xxx.streamlit.app`）
7. 更新 `app/build.gradle` 中的 `APP_URL`
8. 重新构建 APK

## 🎨 APK 功能

- ✅ 全屏 WebView 展示 Streamlit 仪表盘
- ✅ 下拉刷新
- ✅ 返回键双击退出 + WebView 内导航
- ✅ 网络断开自动显示离线提示
- ✅ 自适应图标（金色金属主题）
- ✅ 支持深色模式
- ✅ ProGuard 代码混淆（Release）
