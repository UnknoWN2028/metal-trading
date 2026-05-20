# ProGuard 规则
-keepattributes *Annotation*
-keepattributes SourceFile,LineNumberTable
-keep public class * extends android.app.Activity
-keep public class * extends android.app.Application
-keep public class * extends android.app.Service
-keep public class * extends android.content.BroadcastReceiver

# WebView
-keepclassmembers class * {
    @android.webkit.JavascriptInterface <methods>;
}
