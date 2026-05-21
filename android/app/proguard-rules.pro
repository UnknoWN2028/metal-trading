# ProGuard 规则 — 有色金属AI交易 APK

# 保留 JS 桥接接口（不被混淆）
-keepclassmembers class com.metal.trading.MainActivity$AndroidBridge {
    public *;
}
-keep class com.metal.trading.MainActivity$AndroidBridge { *; }

# 保留 WebView 相关
-keepclassmembers class * {
    @android.webkit.JavascriptInterface <methods>;
}

# 保留 BuildConfig（URL读取用）
-keep class com.metal.trading.BuildConfig { *; }

# 通用优化
-optimizations !code/simplification/arithmetic,!field/*,!class/merging/*
-keepattributes SourceFile,LineNumberTable
