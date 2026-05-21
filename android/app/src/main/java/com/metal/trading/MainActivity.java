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
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout;

public class MainActivity extends Activity {

    private static final String PREFS_NAME = "metal_prefs";
    private static final String KEY_URL = "server_url";

    private WebView webView;
    private ProgressBar progressBar;
    private SwipeRefreshLayout swipeRefresh;
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
        swipeRefresh = findViewById(R.id.swipeRefresh);

        configureWebView();

        swipeRefresh.setColorSchemeResources(
                R.color.primary, R.color.accent, R.color.primary_dark);
        swipeRefresh.setOnRefreshListener(() -> {
            pageFinished = false;
            webView.clearCache(true);
            webView.reload();
        });

        // 长按弹出修改地址
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
        // 开启 WebView 远程调试（Chrome inspect）
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.KITKAT) {
            WebView.setWebContentsDebuggingEnabled(true);
        }

        WebSettings settings = webView.getSettings();

        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(false);
        settings.setCacheMode(WebSettings.LOAD_DEFAULT);
        settings.setUseWideViewPort(true);
        settings.setLoadWithOverviewMode(true);
        settings.setBuiltInZoomControls(true);
        settings.setDisplayZoomControls(false);
        settings.setTextZoom(100);
        // 关键：允许跨域访问（Streamlit 内部 iframe 需要）
        settings.setSupportMultipleWindows(false);
        settings.setBlockNetworkLoads(false);
        settings.setBlockNetworkImage(false);
        // 自定义 User-Agent，避免 Streamlit Cloud 拒绝 WebView
        String userAgent = settings.getUserAgentString()
                .replace("; wv", "")  // 移除 WebView 标记
                .replace("Version/", "Chrome/");  // 伪装成 Chrome
        settings.setUserAgentString(userAgent);

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            settings.setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);
        }

        CookieManager.getInstance().setAcceptThirdPartyCookies(webView, true);

        // 暴露接口给网页调用
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
                swipeRefresh.setRefreshing(false);
            }

            @Override
            public void onReceivedError(WebView view, WebResourceRequest request,
                                        WebResourceError error) {
                // 只对主框架错误做处理，忽略子资源错误
                if (request.isForMainFrame() && !pageFinished) {
                    // 延迟判断：如果 20 秒内还没加载成功才显示离线页
                    handler.postDelayed(() -> {
                        if (!pageFinished) {
                            showOfflinePage();
                        }
                    }, 20000);
                }
            }

            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                // 所有 URL 在 WebView 内打开
                return false;
            }
        });

        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onProgressChanged(WebView view, int newProgress) {
                super.onProgressChanged(view, newProgress);
                progressBar.setProgress(newProgress);
            }
        });
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
        swipeRefresh.setRefreshing(false);
        String html = "<!DOCTYPE html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'></head>"
                + "<body style='background:#F5F6FA;display:flex;align-items:center;justify-content:center;"
                + "height:100vh;flex-direction:column;font-family:sans-serif;text-align:center;padding:20px;box-sizing:border-box;'>"
                + "<div style='font-size:3rem;margin-bottom:16px;'>&#x1F529;</div>"
                + "<h2 style='color:#1A1D26;margin:0;'>有色金属AI交易</h2>"
                + "<p style='color:#6B7280;margin:12px 0;'>无法连接到服务器</p>"
                + "<p style='color:#9CA3AF;font-size:0.85rem;'>下拉刷新重试 · 长按修改地址</p>"
                + "<button onclick='location.reload()' style='margin-top:16px;padding:14px 32px;"
                + "background:#C8923A;color:white;border:none;border-radius:10px;font-size:1rem;'>🔄 重试连接</button>"
                + "<p style='color:#9CA3AF;font-size:0.72rem;margin-top:12px;word-break:break-all;'>"
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
