package org.pocketlore.app;

import android.app.Activity;
import android.app.AlertDialog;
import android.graphics.Color;
import android.os.Bundle;
import android.view.View;
import android.view.WindowInsets;
import android.view.inputmethod.InputMethodManager;
import android.content.Context;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public final class MainActivity extends Activity {
    private ResearchEngine engine;
    private NativePanel nativePanel;
    private EditText question;
    private TextView answer, status;
    private LinearLayout sourceList;
    private Button search;
    private final ExecutorService worker = Executors.newSingleThreadExecutor();
    private boolean destroyed;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR | View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR);
        getWindow().setStatusBarColor(Color.rgb(239, 244, 237));
        getWindow().setNavigationBarColor(Color.rgb(239, 244, 237));
        ScrollView scroll = new ScrollView(this);
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setPadding(dp(22), dp(20), dp(22), dp(24));
        layout.setBackgroundColor(Color.rgb(239, 244, 237));
        scroll.addView(layout);
        setContentView(scroll);
        scroll.setOnApplyWindowInsetsListener((view, insets) -> {
            if (android.os.Build.VERSION.SDK_INT >= 30) {
                android.graphics.Insets bars = insets.getInsets(WindowInsets.Type.systemBars());
                view.setPadding(bars.left, bars.top, bars.right, bars.bottom);
            } else {
                view.setPadding(insets.getSystemWindowInsetLeft(), insets.getSystemWindowInsetTop(),
                    insets.getSystemWindowInsetRight(), insets.getSystemWindowInsetBottom());
            }
            return insets;
        });
        TextView title = text("PocketLore", 32); title.setTextColor(Color.rgb(22, 67, 45)); layout.addView(title);
        layout.addView(text("Offline research • starter library", 16));
        layout.addView(text("Water science pack · Source-backed passages\nInspect passages or import an optional local model", 14));
        question = new EditText(this);
        question.setHint("Ask about evaporation or groundwater");
        question.setMinLines(2); question.setMaxLines(5); question.setTextSize(18);
        question.setContentDescription("Research question"); layout.addView(question);
        search = new Button(this); search.setText("Find evidence"); layout.addView(search);
        status = text("Loading installed knowledge pack…", 14); layout.addView(status);
        answer = text("Ask a question to inspect evidence stored on this device. This starter pack covers only water science; it does not provide current travel or medical advice.", 17);
        answer.setTextIsSelectable(true); layout.addView(answer);
        sourceList = new LinearLayout(this); sourceList.setOrientation(LinearLayout.VERTICAL); layout.addView(sourceList);
        nativePanel = new NativePanel(this, layout);
        search.setEnabled(false);
        search.setOnClickListener(v -> runSearch());
        worker.execute(() -> {
            try {
                ResearchEngine loaded = new ResearchEngine(new InputStreamReader(getAssets().open("water-science.tsv"), StandardCharsets.UTF_8));
                runOnUiThread(() -> { if (destroyed) return; engine = loaded; search.setEnabled(true);
                    status.setText(engine.size() + " passages installed · No network permission");
                    if (state != null) question.setText(state.getString("question", ""));
                });
            } catch (Exception error) {
                runOnUiThread(() -> { if (!destroyed) status.setText("The installed pack could not be loaded. Reinstall the app. " + error.getMessage()); });
            }
        });
    }
    private void runSearch() {
        String query = question.getText().toString().trim();
        if (query.isEmpty()) { question.setError("Enter a research question"); return; }
        ((InputMethodManager)getSystemService(Context.INPUT_METHOD_SERVICE)).hideSoftInputFromWindow(question.getWindowToken(), 0);
        search.setEnabled(false); status.setText("Searching installed passages…");
        worker.execute(() -> {
            long start = System.nanoTime();
            ResearchEngine.Result result = engine.research(query);
            double millis = (System.nanoTime() - start) / 1_000_000.0;
            runOnUiThread(() -> {
                if (destroyed) return;
                answer.setText(result.answer);
                nativePanel.evidence(query, result);
                status.setText(String.format(Locale.ROOT, "%d passages retrieved · %.1f ms on this device · Offline", result.hits.size(), millis));
                sourceList.removeAllViews();
                for (ResearchEngine.Hit hit : result.hits) {
                    Button source = new Button(this);
                    source.setText("Inspect [" + hit.passage.id + "] " + hit.passage.title);
                    source.setAllCaps(false);
                    source.setOnClickListener(v -> inspect(hit));
                    sourceList.addView(source);
                }
                search.setEnabled(true);
            });
        });
    }
    private void inspect(ResearchEngine.Hit hit) {
        ResearchEngine.Passage p = hit.passage;
        TextView detail = text(p.text + "\n\nSource: U.S. Geological Survey, Water Science School\n" + p.url
            + "\n\nRetrieved: " + p.sourceDate + "\nRights: " + p.license
            + "\n\nPack text is a verbatim USGS paragraph with whitespace normalized. Source URLs are provenance labels; the app does not open them."
            + String.format(Locale.ROOT, "\n\nBM25 rank score: %.3f (not confidence)", hit.score), 16);
        detail.setTextIsSelectable(true); detail.setPadding(dp(20), dp(10), dp(20), dp(10));
        ScrollView scroll = new ScrollView(this); scroll.addView(detail);
        new AlertDialog.Builder(this).setTitle("[" + p.id + "] " + p.title).setView(scroll).setPositiveButton("Close", null).show();
    }
    private TextView text(String value, int size) {
        TextView view = new TextView(this); view.setText(value); view.setTextSize(size);
        view.setTextColor(Color.rgb(30, 43, 36)); view.setPadding(0, dp(8), 0, dp(8)); return view;
    }
    private int dp(int value) { return Math.round(value * getResources().getDisplayMetrics().density); }
    @Override protected void onSaveInstanceState(Bundle state) { super.onSaveInstanceState(state); state.putString("question", question.getText().toString()); }
    @Override protected void onActivityResult(int request, int result, android.content.Intent data) {
        super.onActivityResult(request, result, data);
        if (request == NativePanel.PICK_MODEL && result == RESULT_OK && data != null) nativePanel.selected(data.getData());
    }
    @Override protected void onDestroy() { destroyed = true; if (nativePanel != null) nativePanel.destroy(); worker.shutdownNow(); super.onDestroy(); }
}
