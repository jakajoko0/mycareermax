package com.mycareermax.mycareermax;

import android.app.DownloadManager;
import android.content.Context;
import android.content.Intent;
import android.graphics.Bitmap;
import android.net.Uri;
import android.os.Bundle;
import android.os.Environment;
import android.view.Gravity;
import android.view.MenuItem;
import android.view.View;
import android.webkit.DownloadListener;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.URLUtil;

import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.appcompat.app.ActionBarDrawerToggle;
import androidx.appcompat.app.AppCompatActivity;
import androidx.drawerlayout.widget.DrawerLayout;

import com.google.android.gms.ads.AdRequest;
import com.google.android.gms.ads.AdView;
import com.google.android.gms.ads.MobileAds;
import com.google.android.material.navigation.NavigationView;

public class MainActivity extends AppCompatActivity {

    private WebView myWebView;
    private ValueCallback<Uri[]> uploadMessage;
    private DrawerLayout drawerLayout;
    private ActionBarDrawerToggle actionBarDrawerToggle;
    private AdView mAdView;
    private AdView mAdViewTop;
    ActivityResultLauncher<Intent> activityResultLauncher;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        // Initialize AdMob
        MobileAds.initialize(this, initializationStatus -> {});

        // Initialize bottom AdView and load ad
        mAdView = findViewById(R.id.adViewBottom);
        AdRequest adRequestBottom = new AdRequest.Builder().build();
        mAdView.loadAd(adRequestBottom);

        // Initialize top AdView and load ad
        mAdViewTop = findViewById(R.id.adViewTop);
        AdRequest adRequestTop = new AdRequest.Builder().build();
        mAdViewTop.loadAd(adRequestTop);

        drawerLayout = findViewById(R.id.drawer_layout);
        actionBarDrawerToggle = new ActionBarDrawerToggle(this, drawerLayout, R.string.drawer_open, R.string.drawer_close);
        drawerLayout.addDrawerListener(actionBarDrawerToggle);
        actionBarDrawerToggle.syncState();
        getSupportActionBar().setDisplayHomeAsUpEnabled(true);

        // Initialize ActivityResultLauncher for file uploads
        activityResultLauncher = registerForActivityResult(
                new ActivityResultContracts.StartActivityForResult(),
                result -> {
                    if (uploadMessage != null) {
                        Uri[] results = null;
                        if (result.getResultCode() == RESULT_OK) {
                            if (result.getData() != null) {
                                results = new Uri[]{result.getData().getData()};
                            }
                        }
                        uploadMessage.onReceiveValue(results);
                        uploadMessage = null;
                    }
                }
        );

        NavigationView navigationView = findViewById(R.id.nav_view);
        navigationView.setNavigationItemSelectedListener(new NavigationView.OnNavigationItemSelectedListener() {
            @Override
            public boolean onNavigationItemSelected(MenuItem item) {
                int id = item.getItemId();
                if (id == R.id.nav_dashboard) {
                    myWebView.loadUrl("https://app.mycareermax.com/dashboard");
                } else if (id == R.id.nav_careerclick) {
                    myWebView.loadUrl("https://app.mycareermax.com/careerclick");
                } else if (id == R.id.nav_tools_create) {
                    myWebView.loadUrl("https://app.mycareermax.com/tools");
                } else if (id == R.id.nav_resume_scanner) {
                    myWebView.loadUrl("https://app.mycareermax.com/resume-enhancer");
                } else if (id == R.id.nav_interview_prep) {
                    myWebView.loadUrl("https://app.mycareermax.com/interview-prep");
                } else if (id == R.id.nav_max) {
                    myWebView.loadUrl("https://app.mycareermax.com/careerbot");
                } else if (id == R.id.nav_login) {
                    myWebView.loadUrl("https://app.mycareermax.com/login");
                } else if (id == R.id.nav_logout) {
                    myWebView.loadUrl("https://app.mycareermax.com/logout");
                } else if (id == R.id.nav_delete_account) {
                    myWebView.loadUrl("https://app.mycareermax.com/delete_account");
                }
                drawerLayout.closeDrawer(Gravity.LEFT);
                return true;
            }
        });

        myWebView = findViewById(R.id.webview);
        WebSettings webSettings = myWebView.getSettings();
        webSettings.setJavaScriptEnabled(true);

        // WebChromeClient for file uploads
        myWebView.setWebChromeClient(new WebChromeClient() {
            public boolean onShowFileChooser(WebView webView, ValueCallback<Uri[]> filePathCallback, WebChromeClient.FileChooserParams fileChooserParams) {
                uploadMessage = filePathCallback;
                Intent intent = fileChooserParams.createIntent();
                activityResultLauncher.launch(intent);
                return true;
            }
        });

        // DownloadListener for file downloads
        myWebView.setDownloadListener(new DownloadListener() {
            @Override
            public void onDownloadStart(String url, String userAgent, String contentDisposition, String mimeType, long contentLength) {
                DownloadManager.Request request = new DownloadManager.Request(Uri.parse(url));
                request.setMimeType(mimeType);
                String cookies = android.webkit.CookieManager.getInstance().getCookie(url);
                request.addRequestHeader("cookie", cookies);
                request.addRequestHeader("User-Agent", userAgent);
                request.setDescription("Downloading file...");
                request.setTitle(URLUtil.guessFileName(url, contentDisposition, mimeType));
                request.allowScanningByMediaScanner();
                request.setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED);
                request.setDestinationInExternalFilesDir(MainActivity.this, Environment.DIRECTORY_DOWNLOADS, ".pdf");
                DownloadManager dm = (DownloadManager) getSystemService(Context.DOWNLOAD_SERVICE);
                dm.enqueue(request);
                android.widget.Toast.makeText(getApplicationContext(), "Downloading File", android.widget.Toast.LENGTH_LONG).show();
            }
        });

        myWebView.setWebViewClient(new WebViewClient() {
            @Override
            public void onPageStarted(WebView view, String url, Bitmap favicon) {
                super.onPageStarted(view, url, favicon);
                if (url.contains("login")) {
                    // Hide AdViews when on login page
                    mAdView.setVisibility(View.GONE);
                    mAdViewTop.setVisibility(View.GONE);
                } else {
                    // Show AdViews on other pages
                    mAdView.setVisibility(View.VISIBLE);
                    mAdViewTop.setVisibility(View.VISIBLE);
                }
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                // JavaScript to hide the navbar
                view.loadUrl("javascript:(function() { " +
                        "document.getElementsByClassName('navbar')[0].style.display='none'; " +
                        "})()");
            }
        });

        myWebView.loadUrl("https://app.mycareermax.com");
    }

    @Override
    public boolean onOptionsItemSelected(MenuItem item) {
        if (actionBarDrawerToggle.onOptionsItemSelected(item)) {
            return true;
        }
        return super.onOptionsItemSelected(item);
    }

    @Override
    public void onBackPressed() {
        // Check if the WebView can navigate back
        if (myWebView.canGoBack()) {
            // Navigate back to the previous page
            myWebView.goBack();
        } else {
            // If the WebView can't go back, then call the superclass implementation
            super.onBackPressed();
        }
    }
}