package com.metal.trading;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.app.AlertDialog;
import android.content.Context;
import android.content.SharedPreferences;
import android.graphics.Bitmap;
import android.net.ConnectivityManager;
import android.net.Network;
import android.net.NetworkCapabilities;
import android.net.NetworkInfo;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.KeyEvent;
import android.view.View;
import android.webkit.CookieManager;
import android.webkit.JavascriptInterface;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.EditText;
import android.widget.ProgressBar;
import android.widget.Toast;

public class MainActivity extends Activity {

    private static final String PREFS_NAME = "metal_prefs";
    private static final String KEY_URL = "server_url";

    private WebView webView;
    private ProgressBar progressBar;
    private String appUrl;
    private boolean pageFinished = false;
    private final Handler handler = new Handler(Looper.getMainLooper());

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        SharedPreferences prefs = getSharedPreferences(PREFS_NAME, MODE_PRIVATE);
        appUrl = prefs.getString(KEY_URL, BuildConfig.APP_URL);

        webView = findViewById(R.id.webView);
        progressBar = findViewById(R.id.progressBar);

        configureWebView();

        // 🆕 长按弹出修改地址
        webView.setOnLongClickListener(v -> {
            showUrlDialog();
            return true;
        });

        if (isNetworkAvailable()) {
            webView.loadUrl(appUrl);
        } else {
            showOfflinePage();
        }
    }

    @SuppressLint("SetJavaScriptEnabled")
    private void configureWebView() {
        WebSettings settings = webView.getSettings();

        // ── 基础设置 ──
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(false);

        // ── 🆕 性能优化 ──
        settings.setRenderPriority(WebSettings.RenderPriority.HIGH);
        settings.setCacheMode(WebSettings.LOAD_CACHE_ELSE_NETWORK);  // 优先缓存
        settings.setLoadsImagesAutomatically(true);
        settings.setBlockNetworkImage(false);
        // 🆕 启用硬件加速层
        webView.setLayerType(View.LAYER_TYPE_HARDWARE, null);

        // ── 视口 ──
        settings.setUseWideViewPort(true);
        settings.setLoadWithOverviewMode(true);
        settings.setBuiltInZoomControls(true);
        settings.setDisplayZoomControls(false);
        settings.setTextZoom(100);
        settings.setSupportMultipleWindows(false);
        settings.setBlockNetworkLoads(false);

        // ── User-Agent: 伪装Chrome避免Streamlit Cloud拒绝 ──
        String userAgent = settings.getUserAgentString()
                .replace("; wv", "")
                .replace("Version/", "Chrome/");
        settings.setUserAgentString(userAgent);

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            settings.setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);
        }

        CookieManager.getInstance().setAcceptThirdPartyCookies(webView, true);

        webView.addJavascriptInterface(new AndroidBridge(), "Android");

        webView.setWebViewClient(new WebViewClient() {

            @Override
            public void onPageStarted(WebView view, String url, Bitmap favicon) {
                super.onPageStarted(view, url, favicon);
                pageFinished = false;
                progressBar.setVisibility(View.VISIBLE);
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                super.onPageFinished(view, url);
                pageFinished = true;
                progressBar.setVisibility(View.GONE);
            }

            @Override
            public void onReceivedError(WebView view, WebResourceRequest request,
                                        WebResourceError error) {
                if (request.isForMainFrame() && !pageFinished) {
                    // 🆕 缩短超时：8s（原20s）
                    handler.postDelayed(() -> {
                        if (!pageFinished) {
                            showOfflinePage();
                        }
                    }, 8000);
                }
            }

            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                return false;
            }
        });

        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onProgressChanged(WebView view, int newProgress) {
                super.onProgressChanged(view, newProgress);
                progressBar.setProgress(newProgress);
                // 🆕 加载完成时触发一次 theme适配（注入暗色/亮色检测JS）
                if (newProgress == 100) {
                    injectThemeBridge();
                }
            }
        });
    }

    /**
     * 🆕 注入JS桥接：让Web页面感知Android环境，优化交互体验
     */
    private void injectThemeBridge() {
        String js = "javascript:(function(){"
                + "window.__isAndroidApp__=true;"
                + "window.__androidVersion__='1.0';"
                + "document.body.classList.add('android-app');"
                + "})()";
        webView.evaluateJavascript(js, null);
    }

    /**
     * Android 与网页 JS 桥接
     */
    class AndroidBridge {
        @JavascriptInterface
        public void showUrlDialog() {
            runOnUiThread(() -> MainActivity.this.showUrlDialog());
        }
    }

    @Override
    public boolean onKeyDown(int keyCode, KeyEvent event) {
        if (keyCode == KeyEvent.KEYCODE_BACK && webView.canGoBack()) {
            webView.goBack();
            return true;
        }
        if (keyCode == KeyEvent.KEYCODE_BACK) {
            if (System.currentTimeMillis() - lastBackPressTime > 2000) {
                Toast.makeText(this, "再按一次退出 | 长按屏幕修改地址", Toast.LENGTH_SHORT).show();
                lastBackPressTime = System.currentTimeMillis();
                return true;
            }
        }
        return super.onKeyDown(keyCode, event);
    }

    private long lastBackPressTime = 0;

    private boolean isNetworkAvailable() {
        ConnectivityManager cm = (ConnectivityManager)
                getSystemService(Context.CONNECTIVITY_SERVICE);
        if (cm == null) return false;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            Network network = cm.getActiveNetwork();
            if (network == null) return false;
            NetworkCapabilities caps = cm.getNetworkCapabilities(network);
            return caps != null && caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET);
        } else {
            NetworkInfo info = cm.getActiveNetworkInfo();
            return info != null && info.isConnected();
        }
    }

    private void showOfflinePage() {
        progressBar.setVisibility(View.GONE);
        String html = "<!DOCTYPE html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no'></head>"
                + "<body style='background:linear-gradient(180deg,#1A1D26,#0F1117);display:flex;align-items:center;justify-content:center;"
                + "height:100vh;flex-direction:column;font-family:-apple-system,BlinkMacSystemFont,sans-serif;text-align:center;padding:20px;box-sizing:border-box;margin:0;'>"
                + "<div style='width:64px;height:64px;border-radius:50%;background:linear-gradient(135deg,#D4A460,#C8923A);"
                + "display:flex;align-items:center;justify-content:center;margin-bottom:24px;box-shadow:0 4px 20px rgba(200,146,58,0.3);'>"
                + "<span style='font-size:28px;'>&#9889;</span></div>"
                + "<h2 style='color:#E4E7EB;margin:0 0 8px 0;font-size:20px;font-weight:700;'>有色金属AI交易</h2>"
                + "<p style='color:#9CA3AF;margin:0 0 24px 0;font-size:14px;'>无法连接到服务器</p>"
                + "<button onclick='location.reload()' style='padding:14px 48px;"
                + "background:linear-gradient(135deg,#C8923A,#D4832A);color:white;border:none;border-radius:12px;font-size:15px;"
                + "font-weight:600;box-shadow:0 2px 8px rgba(200,146,58,0.4);cursor:pointer;'>重新连接</button>"
                + "<p style='color:#6B7280;font-size:12px;margin-top:20px;'>下拉刷新 · 长按修改地址</p>"
                + "<p style='color:#4B5563;font-size:11px;margin-top:8px;word-break:break-all;max-width:280px;'>"
                + appUrl + "</p></body></html>";
        webView.loadDataWithBaseURL(null, html, "text/html", "UTF-8", null);
    }

    private void showUrlDialog() {
        AlertDialog.Builder builder = new AlertDialog.Builder(this);
        builder.setTitle("⚙️ 修改服务器地址");

        final EditText input = new EditText(this);
        input.setText(appUrl);
        input.setHint("http://192.168.x.x:8501");
        input.setSingleLine(true);
        builder.setView(input);

        builder.setPositiveButton("保存", (dialog, which) -> {
            String newUrl = input.getText().toString().trim();
            if (!newUrl.isEmpty()) {
                appUrl = newUrl;
                getSharedPreferences(PREFS_NAME, MODE_PRIVATE)
                        .edit().putString(KEY_URL, newUrl).apply();
                Toast.makeText(this, "✅ 已保存，重新连接...", Toast.LENGTH_SHORT).show();
                webView.clearCache(true);
                pageFinished = false;
                webView.loadUrl(appUrl);
            }
        });
        builder.setNeutralButton("重置默认", (dialog, which) -> {
            appUrl = BuildConfig.APP_URL;
            getSharedPreferences(PREFS_NAME, MODE_PRIVATE)
                    .edit().remove(KEY_URL).apply();
            Toast.makeText(this, "✅ 已重置", Toast.LENGTH_SHORT).show();
            webView.clearCache(true);
            pageFinished = false;
            webView.loadUrl(appUrl);
        });
        builder.setNegativeButton("取消", null);
        builder.show();
    }

    @Override
    protected void onResume() {
        super.onResume();
        webView.onResume();
    }

    @Override
    protected void onPause() {
        webView.onPause();
        super.onPause();
    }

    @Override
    protected void onDestroy() {
        handler.removeCallbacksAndMessages(null);
        if (webView != null) {
            webView.destroy();
        }
        super.onDestroy();
    }
}
