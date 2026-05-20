package com.metal.trading;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.Context;
import android.graphics.Bitmap;
import android.net.ConnectivityManager;
import android.net.NetworkInfo;
import android.os.Build;
import android.os.Bundle;
import android.view.KeyEvent;
import android.view.View;
import android.view.WindowManager;
import android.webkit.CookieManager;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.ProgressBar;
import android.widget.Toast;
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout;

public class MainActivity extends Activity {

    // ═══════════════════════════════════════
    //  ⚠️ 部署后修改此 URL
    // ═══════════════════════════════════════
    // Streamlit Cloud 部署后的 URL 格式：
    // https://你的应用名.streamlit.app
    private static final String APP_URL = "https://YOUR_APP_NAME.streamlit.app";

    private WebView webView;
    private ProgressBar progressBar;
    private SwipeRefreshLayout swipeRefresh;

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        // 初始化视图
        webView = findViewById(R.id.webView);
        progressBar = findViewById(R.id.progressBar);
        swipeRefresh = findViewById(R.id.swipeRefresh);

        // 配置 WebView
        configureWebView();

        // 下拉刷新
        swipeRefresh.setColorSchemeResources(
                R.color.primary, R.color.accent, R.color.primary_dark
        );
        swipeRefresh.setOnRefreshListener(() -> webView.reload());

        // 检查网络并加载
        if (isNetworkAvailable()) {
            webView.loadUrl(APP_URL);
        } else {
            showOfflinePage();
        }
    }

    @SuppressLint("SetJavaScriptEnabled")
    private void configureWebView() {
        WebSettings settings = webView.getSettings();

        // 基础设置
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(false);

        // 缓存策略（有网络时用网络，无网络时用缓存）
        settings.setCacheMode(WebSettings.LOAD_DEFAULT);
        settings.setAppCacheEnabled(true);
        settings.setAppCachePath(getCacheDir().getAbsolutePath());

        // 自适应屏幕
        settings.setUseWideViewPort(true);
        settings.setLoadWithOverviewMode(true);
        settings.setBuiltInZoomControls(true);
        settings.setDisplayZoomControls(false);

        // 混合内容 (HTTPS 页面加载 HTTP 资源)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            settings.setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);
        }

        // Cookie 管理
        CookieManager.getInstance().setAcceptThirdPartyCookies(webView, true);

        // WebViewClient
        webView.setWebViewClient(new WebViewClient() {
            @Override
            public void onPageStarted(WebView view, String url, Bitmap favicon) {
                super.onPageStarted(view, url, favicon);
                progressBar.setVisibility(View.VISIBLE);
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                super.onPageFinished(view, url);
                progressBar.setVisibility(View.GONE);
                swipeRefresh.setRefreshing(false);
            }

            @Override
            public void onReceivedError(WebView view, WebResourceRequest request,
                                        WebResourceError error) {
                super.onReceivedError(view, request, error);
                if (request.isForMainFrame()) {
                    showOfflinePage();
                }
            }
        });

        // WebChromeClient
        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onProgressChanged(WebView view, int newProgress) {
                super.onProgressChanged(view, newProgress);
                progressBar.setProgress(newProgress);
            }
        });
    }

    /**
     * 处理返回键 - WebView 内导航优先
     */
    @Override
    public boolean onKeyDown(int keyCode, KeyEvent event) {
        if (keyCode == KeyEvent.KEYCODE_BACK && webView.canGoBack()) {
            webView.goBack();
            return true;
        }
        // 双击退出提示
        if (keyCode == KeyEvent.KEYCODE_BACK) {
            if (System.currentTimeMillis() - lastBackPressTime > 2000) {
                Toast.makeText(this, "再按一次退出", Toast.LENGTH_SHORT).show();
                lastBackPressTime = System.currentTimeMillis();
                return true;
            }
        }
        return super.onKeyDown(keyCode, event);
    }

    private long lastBackPressTime = 0;

    /**
     * 检查网络连接
     */
    private boolean isNetworkAvailable() {
        ConnectivityManager cm = (ConnectivityManager)
                getSystemService(Context.CONNECTIVITY_SERVICE);
        if (cm != null) {
            NetworkInfo activeNetwork = cm.getActiveNetworkInfo();
            return activeNetwork != null && activeNetwork.isConnected();
        }
        return false;
    }

    /**
     * 显示离线页面
     */
    private void showOfflinePage() {
        progressBar.setVisibility(View.GONE);
        swipeRefresh.setRefreshing(false);
        String offlineHtml = "<html><body style='background:#F5F6FA;display:flex;" +
                "align-items:center;justify-content:center;height:100vh;" +
                "flex-direction:column;font-family:sans-serif;text-align:center;'>" +
                "<div style='font-size:3rem;margin-bottom:16px;'>🔩</div>" +
                "<h2 style='color:#1A1D26;margin:0;'>有色金属AI交易</h2>" +
                "<p style='color:#6B7280;margin:12px 0;'>网络连接失败</p>" +
                "<p style='color:#9CA3AF;font-size:0.85rem;'>请检查网络后下拉刷新</p>" +
                "</body></html>";
        webView.loadDataWithBaseURL(null, offlineHtml,
                "text/html", "UTF-8", null);
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
        if (webView != null) {
            webView.destroy();
        }
        super.onDestroy();
    }
}
