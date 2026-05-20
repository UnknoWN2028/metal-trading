# 🔩 有色金属回收倒卖AI系统 v3 — 移动端打包指南

## 📋 方案概述

将 Streamlit Web 应用封装为 Android APK 分两步：

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│  Streamlit App  │ ──▶  │ Streamlit Cloud  │ ──▶  │  Android APK    │
│   (Python源码)   │      │   (免费云部署)     │      │  (WebView封装)   │
└─────────────────┘      └──────────────────┘      └─────────────────┘
```

---

## 🚀 第一步：部署到 Streamlit Cloud（免费）

### 1.1 准备工作

你的项目已经准备好了 Cloud 部署入口文件 `streamlit_app.py`。

### 1.2 推送到 GitHub

```bash
# 在 G:/Metal 目录下
git init
git add .
git commit -m "Initial commit - Metal Trading AI v3"

# 创建 GitHub 仓库后
git remote add origin https://github.com/你的用户名/metal-trading-ai.git
git push -u origin main
```

### 1.3 部署到 Streamlit Cloud

1. 访问 [https://share.streamlit.io](https://share.streamlit.io)
2. 点击 "New app"
3. 选择你的 GitHub 仓库
4. Main file path 填写: `streamlit_app.py`
5. 点击 "Deploy!"

部署成功后，你会得到一个 URL，例如：
```
https://你的应用名.streamlit.app
```

### 1.4 测试手机访问

用手机浏览器打开部署后的 URL，确认一切正常。
Streamlit 的 UI 已经做了移动端响应式适配，手机使用体验良好！

---

## 📱 第二步：构建 Android APK

### 方案 A：使用 Android Studio（推荐）

#### 1. 安装 Android Studio
下载：https://developer.android.com/studio

#### 2. 打开项目
1. 启动 Android Studio
2. 选择 "Open" → 打开 `G:/Metal/android` 目录
3. 等待 Gradle 同步完成

#### 3. 修改 URL
编辑 `app/src/main/java/com/metal/trading/MainActivity.java`：

```java
// 将这一行：
private static final String APP_URL = "https://YOUR_APP_NAME.streamlit.app";
// 改为你的实际 URL：
private static final String APP_URL = "https://你的应用名.streamlit.app";
```

#### 4. 构建 APK
- **菜单栏**: Build → Build Bundle(s) / APK(s) → Build APK(s)
- APK 输出路径: `android/app/build/outputs/apk/debug/app-debug.apk`

#### 5. 安装到手机
将 APK 文件传到手机，直接安装即可。

---

### 方案 B：命令行构建（无需 Android Studio）

如果你已安装 JDK 17+ 和 Android SDK：

```bash
cd android

# Linux/Mac
./gradlew assembleDebug

# Windows
gradlew.bat assembleDebug
```

APK 路径: `app/build/outputs/apk/debug/app-debug.apk`

---

### 方案 C：在线 APK 构建器（最简单，无需开发环境）

如果不想安装任何开发工具，可以使用在线服务：

1. **WebIntoApp** (https://www.webintoapp.com)
   - 输入你的 Streamlit Cloud URL
   - 上传图标
   - 自动生成 APK

2. **PWABuilder** (https://pwabuilder.com)
   - 输入 URL 生成 Android 包

⚠️ 注意：在线工具生成的 APK 功能有限，推荐使用 Android Studio。

---

## 🎨 自定义 APK 信息

### 修改应用名称
编辑 `android/app/src/main/res/values/strings.xml`：
```xml
<string name="app_name">有色金属AI交易</string>
```

### 修改包名
编辑 `android/app/build.gradle`：
```gradle
applicationId "com.yourcompany.yourapp"
```

### 修改应用图标
替换以下文件（推荐 1024x1024 PNG）：
- `drawable/ic_launcher_foreground.xml`（矢量图标）
- 或使用 Android Studio 的 Image Asset Studio 生成

---

## 📦 生成正式发布版 APK（带签名）

### 1. 创建签名密钥
```bash
keytool -genkey -v -keystore metal-trading.keystore \
  -alias metal-trading -keyalg RSA -keysize 2048 -validity 10000
```

### 2. 配置签名
在 `android/app/build.gradle` 的 `android` 块中添加：
```gradle
signingConfigs {
    release {
        storeFile file("metal-trading.keystore")
        storePassword "你的密码"
        keyAlias "metal-trading"
        keyPassword "你的密码"
    }
}
buildTypes {
    release {
        signingConfig signingConfigs.release
        // ...
    }
}
```

### 3. 构建
```bash
./gradlew assembleRelease
```

---

## ⚙️ 技术细节

### Android 项目结构
```
android/
├── build.gradle              # 项目级构建配置
├── settings.gradle           # 项目设置
├── gradle.properties         # Gradle 属性
├── gradle/wrapper/           # Gradle Wrapper
└── app/
    ├── build.gradle          # App 构建配置
    ├── proguard-rules.pro    # 混淆规则
    └── src/main/
        ├── AndroidManifest.xml
        ├── java/com/metal/trading/
        │   └── MainActivity.java   # WebView 主活动
        └── res/
            ├── layout/activity_main.xml
            ├── drawable/            # 图标资源
            ├── mipmap-anydpi-v26/   # 自适应图标
            ├── values/              # 主题/颜色/字符串
            └── xml/                 # 网络安全配置
```

### 功能特性
- ✅ 全屏 WebView 封装
- ✅ 下拉刷新
- ✅ 加载进度条
- ✅ 离线提示页
- ✅ 双击退出
- ✅ HTTPS 支持
- ✅ Cookie 持久化
- ✅ 响应式适配
- ✅ Streamlit 兼容

---

## ❓ 常见问题

### Q: 为什么需要云服务器，不能完全离线？
A: Streamlit 是 Python Web 框架，需要服务器运行。WebView APK 是将网页"装进"原生应用壳中。

### Q: 可以不用 GitHub 部署吗？
A: 可以部署到任何支持 Python 的服务器（Railway、Render、阿里云等），然后将 URL 填入 APK。

### Q: 如何更新 APP 内容？
A: 只需更新 Streamlit Cloud 上的代码，APK 无需重新安装即可获取最新内容。

### Q: Debug APK 和 Release APK 区别？
A: Debug 可直接安装测试；Release 需签名，适合分发。

---

## 📞 支持

需要帮助？检查：
1. Streamlit Cloud 日志：https://share.streamlit.io
2. Android Studio 构建输出
3. 确保 `requirements.txt` 中所有依赖都兼容云端环境
