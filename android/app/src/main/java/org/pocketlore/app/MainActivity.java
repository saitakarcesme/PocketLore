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
    private ResearchEngine.Result latestEvidence;
    private NativePanel nativePanel;
    private EditText question;
    private TextView answer, status;
    private LinearLayout sourceList;
    private Button search, importPack;
    private TextView packStatus;
    private volatile boolean importing, cancelPack;
    private volatile Thread packThread;
    private static final ExecutorService packWorker=Executors.newSingleThreadExecutor();
    private static final int PICK_PACK = 411;
    private final ExecutorService worker = Executors.newSingleThreadExecutor();
    private volatile boolean destroyed;

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
        layout.addView(text("Offline research • local library", 16));
        layout.addView(text("Source-backed passages · Import a knowledge pack or local model", 14));
        Button travel = new Button(this); travel.setText("Offline travel and tools"); layout.addView(travel);
        travel.setOnClickListener(v -> startActivity(new android.content.Intent(this, TravelActivity.class)));
        packStatus = text("Bundled water-science starter pack", 14); layout.addView(packStatus);
        importPack = new Button(this); importPack.setText("Import knowledge pack"); layout.addView(importPack);
        importPack.setOnClickListener(v -> {
            android.content.Intent intent = new android.content.Intent(android.content.Intent.ACTION_OPEN_DOCUMENT);
            intent.addCategory(android.content.Intent.CATEGORY_OPENABLE); intent.setType("*/*");
            startActivityForResult(intent, PICK_PACK);
        });
        Button cancelImport=new Button(this);cancelImport.setText("Cancel pack import");layout.addView(cancelImport);cancelImport.setOnClickListener(v->{cancelPack=true;if(packThread!=null)packThread.interrupt();});
        question = new EditText(this);
        question.setHint("Ask about an installed source");
        question.setMinLines(2); question.setMaxLines(5); question.setTextSize(18);
        question.setContentDescription("Research question"); layout.addView(question);
        search = new Button(this); search.setText("Answer offline"); layout.addView(search);
        LinearLayout actions = new LinearLayout(this); actions.setOrientation(LinearLayout.VERTICAL); layout.addView(actions);
        status = text("Loading installed knowledge pack…", 14); status.setContentDescription("Answer status"); layout.addView(status);
        answer = text("Ask a question to inspect evidence stored on this device. The bundled starter covers water science. Imported packs are dated references, not current travel or medical advice.", 17);
        answer.setTextIsSelectable(true); answer.setContentDescription("Offline answer"); layout.addView(answer);
        sourceList = new LinearLayout(this); sourceList.setOrientation(LinearLayout.VERTICAL); layout.addView(sourceList);
        nativePanel = new NativePanel(this, layout, actions, answer, status, busy -> {
            search.setEnabled(engine != null && !busy && !importing); question.setEnabled(!busy && !importing); importPack.setEnabled(!busy && !importing);
        }, id -> { if(latestEvidence!=null) for(ResearchEngine.Hit hit:latestEvidence.hits) if(hit.passage.id.equals(id)) inspect(hit); });
        search.setEnabled(false);
        search.setOnClickListener(v -> runSearch());
        packWorker.execute(() -> {
            try {
                ResourceStorage.cleanupPackStages(getFilesDir());
                java.io.File installed = new java.io.File(getFilesDir(), "knowledge.plpack");
                KnowledgePack pack = installed.exists() ? KnowledgePack.load(installed) : null;
                ResearchEngine loaded = pack != null ? pack.engine : new ResearchEngine(new InputStreamReader(getAssets().open("water-science.tsv"), StandardCharsets.UTF_8));
                runOnUiThread(() -> { if (destroyed) return; engine = loaded; search.setEnabled(!nativePanel.isBusy());
                    if (pack != null) packStatus.setText(pack.id + " · " + pack.engine.size() + " passages\n" + pack.warning + "\nSHA-256: " + pack.sha256);
                    status.setText(engine.size() + " passages installed · No network permission");
                    if (state != null) question.setText(state.getString("question", ""));
                });
            } catch (Exception | OutOfMemoryError error) {
                runOnUiThread(() -> { if (!destroyed) status.setText("The installed pack could not be loaded. Reinstall the app. " + error.getMessage()); });
            }
        });
    }
    private void runSearch() {
        if (nativePanel.isBusy() || importing || engine == null) return;
        String query = question.getText().toString().trim();
        if (query.isEmpty()) { question.setError("Enter a research question"); return; }
        ((InputMethodManager)getSystemService(Context.INPUT_METHOD_SERVICE)).hideSoftInputFromWindow(question.getWindowToken(), 0);
        nativePanel.clearAnswer(); sourceList.removeAllViews();
        search.setEnabled(false); status.setText("Searching installed passages…");
        worker.execute(() -> {
            long start = System.nanoTime();
            ResearchEngine.Result result = engine.research(query);
            double millis = (System.nanoTime() - start) / 1_000_000.0;
            runOnUiThread(() -> {
                if (destroyed) return;

                status.setText(String.format(Locale.ROOT, "%d passages retrieved · %.1f ms on this device · Offline", result.hits.size(), millis));
                sourceList.removeAllViews();
                for (ResearchEngine.Hit hit : result.hits) {
                    Button source = new Button(this);
                    source.setText("Inspect [" + hit.passage.id + "] " + hit.passage.title);
                    source.setAllCaps(false);
                    source.setOnClickListener(v -> inspect(hit));
                    sourceList.addView(source);
                }
                latestEvidence=result;nativePanel.answer(query, result);
            });
        });
    }
    AnswerEngine.Outcome latestAnswer() { return nativePanel.outcome(); }
    boolean modelReady() { return nativePanel.hasModel() && !nativePanel.isBusy(); }
    private void inspect(ResearchEngine.Hit hit) {
        ResearchEngine.Passage p = hit.passage;
        TextView detail = text(p.text + "\n\nSource document: " + p.title + "\n" + p.url
            + "\n\nSource date / retrieval: " + p.sourceDate + "\nRights: " + p.license
            + (p.id.startsWith("water-") ? "\n\nPack text is a verbatim USGS paragraph with whitespace normalized." : "\n\nPack text is selected source text with whitespace normalized.") + " Source URLs are provenance labels; the app does not open them."
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
        if (request == PICK_PACK && result == RESULT_OK && data != null && data.getData() != null) {
            android.net.Uri uri = data.getData();
            importing = true; cancelPack=false; search.setEnabled(false); question.setEnabled(false); importPack.setEnabled(false);
            packStatus.setText("Validating knowledge pack…");
            packWorker.execute(() -> {
                packThread=Thread.currentThread();
                try (java.io.InputStream in = getContentResolver().openInputStream(uri)) {
                    KnowledgePack pack = KnowledgePack.install(in, getFilesDir(),()->cancelPack || destroyed);
                    runOnUiThread(() -> { if (destroyed) return; engine = pack.engine;
                        answer.setText("Pack imported. Ask a question to inspect its sources."); sourceList.removeAllViews();
                        packStatus.setText(pack.id + " · " + engine.size() + " passages\n" + pack.warning + "\nSHA-256: " + pack.sha256);
                    });
                } catch (Exception | OutOfMemoryError error) {
                    runOnUiThread(() -> { if (!destroyed) packStatus.setText("Pack rejected; previous library retained. " + error.getMessage()); });
                } finally {
                    packThread=null;Thread.interrupted();
                    runOnUiThread(() -> { if (destroyed) return; importing = false; question.setEnabled(!nativePanel.isBusy());
                        search.setEnabled(engine != null && !nativePanel.isBusy()); importPack.setEnabled(!nativePanel.isBusy()); });
                }
            });
        }
        if (request == NativePanel.PICK_MODEL && result == RESULT_OK && data != null) nativePanel.selected(data.getData());
    }
    void releaseForMemoryPressure(){cancelPack=true;if(packThread!=null)packThread.interrupt();latestEvidence=null;if(nativePanel!=null)nativePanel.lowMemory();}
    void reloadSavedModel(){nativePanel.reloadSaved();}
    @Override public void onTrimMemory(int level){super.onTrimMemory(level);if(level>=android.content.ComponentCallbacks2.TRIM_MEMORY_RUNNING_LOW)releaseForMemoryPressure();}
    @Override public void onLowMemory(){super.onLowMemory();releaseForMemoryPressure();}
    @Override protected void onDestroy() { destroyed = true;cancelPack=true;if(packThread!=null)packThread.interrupt(); if (nativePanel != null) nativePanel.destroy(); worker.shutdownNow(); super.onDestroy(); }
}
