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
    private PackLibrary library;
    private PackLibrary.Snapshot catalog;
    private Button collections, reloadLibrary, removeCollection;
    private boolean searching;
    private long libraryEpoch;
    private ResearchEngine.Result latestEvidence;
    private NativePanel nativePanel;
    private EditText question;
    private TextView answer, status;
    private LinearLayout sourceList;
    private Button search, importPack, briefButton;
    private volatile boolean cancelBrief;
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
        Button bulk = new Button(this); bulk.setText("Reference and world places"); layout.addView(bulk); bulk.setOnClickListener(v -> startActivity(new android.content.Intent(this, ScaleActivity.class)));
        Button travel = new Button(this); travel.setText("Offline travel and tools"); layout.addView(travel);
        travel.setOnClickListener(v -> startActivity(new android.content.Intent(this, TravelActivity.class)));
        packStatus = text("Bundled water-science starter pack", 14); layout.addView(packStatus);
        importPack = new Button(this); importPack.setText("Import knowledge pack"); layout.addView(importPack);
        importPack.setOnClickListener(v -> {
            android.content.Intent intent = new android.content.Intent(android.content.Intent.ACTION_OPEN_DOCUMENT);
            intent.addCategory(android.content.Intent.CATEGORY_OPENABLE); intent.setType("*/*"); intent.putExtra(android.content.Intent.EXTRA_LOCAL_ONLY,true);
            startActivityForResult(intent, PICK_PACK);
        });
        collections=new Button(this);collections.setText("Choose collections");layout.addView(collections);collections.setOnClickListener(v->chooseCollections());
        removeCollection=new Button(this);removeCollection.setText("Remove a collection");layout.addView(removeCollection);removeCollection.setOnClickListener(v->removeCollection());
        layout.addView(text("Setup: obtain packs and GGUF files before going offline. Imports retain the original file and need free space for a full copy plus 256 MiB. Large SQLite packs also need space for their expanded index. Unsupported pack formats are rejected. Source rights and dates must be inspected for each edition.",14));
        reloadLibrary=new Button(this);reloadLibrary.setText("Reload library");layout.addView(reloadLibrary);reloadLibrary.setOnClickListener(v->loadLibrary());
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
            updateControls();
        }, id -> { if(latestEvidence!=null) for(ResearchEngine.Hit hit:latestEvidence.hits) if(hit.passage.id.equals(id)) inspect(hit); });
        briefButton = new Button(this); briefButton.setText("Research brief · source quotations"); actions.addView(briefButton);
        briefButton.setOnClickListener(v -> runBrief());
        Button stopBrief=new Button(this); stopBrief.setText("Cancel research brief"); actions.addView(stopBrief);
        stopBrief.setOnClickListener(v -> cancelBrief=true);
        search.setEnabled(false);
        search.setOnClickListener(v -> runSearch());
        if (state != null) question.setText(state.getString("question", ""));
        try{library=new PackLibrary(getFilesDir());loadLibrary();}
        catch(Exception e){status.setText("Library unavailable: "+e.getMessage());}
    }
    private void updateControls(){
        if(nativePanel==null)return;boolean ready=!nativePanel.isBusy()&&!importing&&!searching;
        search.setEnabled(ready&&engine!=null&&engine.size()>0);if(briefButton!=null)briefButton.setEnabled(ready&&engine!=null&&engine.size()>0);question.setEnabled(ready);importPack.setEnabled(ready);
        collections.setEnabled(ready&&catalog!=null&&!catalog.entries.isEmpty());removeCollection.setEnabled(ready&&catalog!=null&&!catalog.entries.isEmpty());reloadLibrary.setEnabled(ready);
    }
    private void showLibrary(PackLibrary.Snapshot next){
        catalog=next;engine=next.engine;latestEvidence=null;nativePanel.clearEvidence();sourceList.removeAllViews();
        packStatus.setText(next.description()+" · "+next.archiveBytes+" installed archive/index bytes"+(ImportRecovery.pending(getFilesDir(),"pack")?"\nPrevious import interrupted or failed. Installed editions retained; select the original file to restart verification.":""));status.setText("Active collections ready · No network permission");updateControls();
    }
    private void loadLibrary(){
        if(importing||searching)return;
        importing=true;cancelPack=false;long epoch=++libraryEpoch;updateControls();status.setText("Loading active collections…");
        packWorker.execute(()->{packThread=Thread.currentThread();try{
            PackLibrary.Snapshot next=library.loadMigrating(new java.io.File(getFilesDir(),"knowledge.plpack"));
            ResearchEngine starter=next.entries.isEmpty()?new ResearchEngine(new InputStreamReader(getAssets().open("water-science.tsv"),StandardCharsets.UTF_8)):null;
            runOnUiThread(()->{if(destroyed||epoch!=libraryEpoch)return;showLibrary(next);if(starter!=null){engine=starter;packStatus.setText("Bundled water-science starter · Import collections to build your library");}answer.setText("Select active collections, then ask a question to inspect their sources.");});
        }catch(Exception|OutOfMemoryError e){runOnUiThread(()->{if(!destroyed)status.setText("Library could not be loaded; saved collections retained. "+e.getMessage());});}
        finally{packThread=null;Thread.interrupted();runOnUiThread(()->{if(!destroyed){importing=false;updateControls();}});}});
    }
    private void chooseCollections(){
        if(catalog==null||importing||nativePanel.isBusy()||searching)return;
        final java.util.List<PackLibrary.Entry> entries=catalog.entries;String[] labels=new String[entries.size()];boolean[] checked=new boolean[entries.size()];
        for(int i=0;i<entries.size();i++){PackLibrary.Entry e=entries.get(i);labels[i]=e.id.replace('-', ' ')+" · edition "+e.hash.substring(0,8);checked[i]=e.active;}
        new AlertDialog.Builder(this).setTitle("Search these collections").setMultiChoiceItems(labels,checked,(d,i,on)->checked[i]=on)
            .setNegativeButton("Cancel",null).setPositiveButton("Apply",(d,w)->{
                java.util.Set<String> active=new java.util.HashSet<>();for(int i=0;i<checked.length;i++)if(checked[i])active.add(entries.get(i).hash);
                importing=true;long epoch=++libraryEpoch;updateControls();packWorker.execute(()->{packThread=Thread.currentThread();try{PackLibrary.Snapshot next=library.select(active);
                    runOnUiThread(()->{if(!destroyed&&epoch==libraryEpoch){showLibrary(next);answer.setText(active.isEmpty()?"No collections selected. Choose at least one to search.":"Active collections updated. Ask a new question.");}});
                }catch(Exception|OutOfMemoryError e){runOnUiThread(()->{if(!destroyed)status.setText("Selection not changed: "+e.getMessage());});}
                finally{packThread=null;Thread.interrupted();runOnUiThread(()->{if(!destroyed){importing=false;updateControls();}});}});
            }).show();
    }
    private void removeCollection() {
        if(catalog==null||importing||searching||nativePanel.isBusy())return;
        final java.util.List<PackLibrary.Entry> entries=catalog.entries;
        String[] labels=new String[entries.size()];for(int i=0;i<labels.length;i++)labels[i]=entries.get(i).id+" · "+entries.get(i).hash.substring(0,12);
        new AlertDialog.Builder(this).setTitle("Remove an installed edition").setItems(labels,(dialog,index)->{
            PackLibrary.Entry entry=entries.get(index);
            new AlertDialog.Builder(this).setTitle("Remove "+entry.id+"?").setMessage("Edition SHA-256: "+entry.hash+"\nDeletes this app's archive and index. The original import file remains. This edition will no longer be searched.")
                .setNegativeButton("Keep",null).setPositiveButton("Remove",(d,w)->{
                    if(importing||searching||nativePanel.isBusy())return;
                    importing=true;long epoch=++libraryEpoch;updateControls();
                    packWorker.execute(()->{try{PackLibrary.Snapshot next=library.remove(entry.hash);
                        runOnUiThread(()->{if(!destroyed&&epoch==libraryEpoch){showLibrary(next);answer.setText("Collection removed. Import or select a collection to continue.");}});
                    }catch(Exception e){runOnUiThread(()->{if(!destroyed)status.setText("Removal failed: "+e.getMessage());});}
                    finally{runOnUiThread(()->{if(!destroyed){importing=false;updateControls();}});}});
                }).show();
        }).setNegativeButton("Cancel",null).show();
    }
    private void runSearch() {
        if (nativePanel.isBusy() || importing || engine == null) return;
        String query = question.getText().toString().trim();
        if (query.isEmpty()) { question.setError("Enter a research question"); return; }
        ((InputMethodManager)getSystemService(Context.INPUT_METHOD_SERVICE)).hideSoftInputFromWindow(question.getWindowToken(), 0);
        nativePanel.clearAnswer(); sourceList.removeAllViews();
        searching=true;updateControls();status.setText("Searching active collections…");
        final ResearchEngine selectedEngine=engine;final long epoch=libraryEpoch;
        worker.execute(() -> {
            long start = System.nanoTime();
            ResearchEngine.Result result;
            try { result = selectedEngine.research(query); }
            catch(Exception | OutOfMemoryError error) {
                runOnUiThread(()->{if(!destroyed){searching=false;if(epoch==libraryEpoch){nativePanel.searchFailed();status.setText("Search failed; saved sources retained. "+error.getMessage());}updateControls();}});
                return;
            }
            double millis = (System.nanoTime() - start) / 1_000_000.0;
            runOnUiThread(() -> {
                searching=false;if (destroyed || epoch!=libraryEpoch){updateControls();return;}

                status.setText(String.format(Locale.ROOT, "%d passages retrieved · %.1f ms on this device · Offline", result.hits.size(), millis));
                sourceList.removeAllViews();
                for (ResearchEngine.Hit hit : result.hits) {
                    Button source = new Button(this);
                    source.setText("Inspect source: " + hit.passage.title);
                    source.setAllCaps(false);
                    source.setOnClickListener(v -> inspect(hit));
                    sourceList.addView(source);
                }
                latestEvidence=result;nativePanel.answer(query, result);
            });
        });
    }
    private void runBrief() {
        if(nativePanel.isBusy()||importing||searching||engine==null)return;
        String query=question.getText().toString().trim();
        if(query.isEmpty()){question.setError("Enter a research question");return;}
        cancelBrief=false;searching=true;updateControls();nativePanel.clearAnswer();sourceList.removeAllViews();
        status.setText("Selecting exact source quotations…");
        ResearchEngine selected=engine;long epoch=libraryEpoch;
        worker.execute(()->{try{
            ResearchEngine.Result result=selected.research(query);
            ResearchBrief.Brief brief=ResearchBrief.create(query,result,()->cancelBrief||destroyed);
            runOnUiThread(()->{if(destroyed||epoch!=libraryEpoch||cancelBrief)return;
                latestEvidence=result;
                android.text.SpannableString rendered=new android.text.SpannableString(brief.text);
                for(ResearchBrief.Quote quote:brief.quotes){
                    rendered.setSpan(new android.text.style.ClickableSpan(){public void onClick(View view){
                        quote.verify(quote.source);inspect(new ResearchEngine.Hit(quote.source,0));
                    }},quote.displayStart,quote.displayEnd,android.text.Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
                }
                answer.setText(rendered);answer.setMovementMethod(android.text.method.LinkMovementMethod.getInstance());
                status.setText(brief.quotes.size()+" source quotations · coverage unverified · no generated answer");
            });
        }catch(Exception e){runOnUiThread(()->{if(!destroyed)status.setText("Research brief unavailable: "+e.getMessage());});}
        finally{runOnUiThread(()->{if(!destroyed){searching=false;if(cancelBrief)status.setText("Research brief cancelled; no partial result");updateControls();}});}});
    }
    AnswerEngine.Outcome latestAnswer() { return nativePanel.outcome(); }
    boolean modelReady() { return nativePanel.hasModel() && !nativePanel.isBusy(); }
    private void inspect(ResearchEngine.Hit hit) {
        ResearchEngine.Passage p = hit.passage;
        TextView detail = text(p.text + "\n\nSource document: " + p.title + "\n" + p.url
            + "\n\nSource date / retrieval: " + known(p.sourceDate) + "\nRights: " + known(p.license)
            + "\n\nCitation: [" + p.id + "]\n" + p.collectionProvenance
            + (p.id.startsWith("water-") ? "\n\nPack text is a verbatim USGS paragraph with whitespace normalized." : "\n\nPack text is selected source text with whitespace normalized.") + " Source URLs are provenance labels; the app does not open them."
            + String.format(Locale.ROOT, "\n\nRetrieval rank score: %.3f (not confidence)", hit.score), 16);
        detail.setTextIsSelectable(true); detail.setPadding(dp(20), dp(10), dp(20), dp(10));
        ScrollView scroll = new ScrollView(this); scroll.addView(detail);
        AlertDialog.Builder dialog=new AlertDialog.Builder(this).setTitle(p.title).setView(scroll).setPositiveButton("Close", null);
        if(p.id.matches("p[0-9a-f]{64}_wiki-.*"))dialog.setNeutralButton("License",(d,w)->{
            try{TextView license=text(BroadPack.licenseText(getFilesDir(),p.id),14);ScrollView view=new ScrollView(this);view.addView(license);new AlertDialog.Builder(this).setTitle("CC BY-SA 4.0 · offline license").setView(view).setPositiveButton("Close",null).show();}
            catch(Exception e){new AlertDialog.Builder(this).setMessage("Cannot read saved license: "+e.getMessage()).setPositiveButton("Close",null).show();}
        });dialog.show();
    }
    private static String known(String value){return value==null||value.trim().isEmpty()?"Unknown":value;}
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
            long bytes=-1;
            try(android.database.Cursor cursor=getContentResolver().query(uri,new String[]{android.provider.OpenableColumns.SIZE},null,null,null)){
                if(cursor!=null&&cursor.moveToFirst()&&!cursor.isNull(0))bytes=cursor.getLong(0);
            }catch(Exception error){packStatus.setText("Cannot inspect pack: "+error.getMessage());return;}
            if(bytes<=0||bytes>BroadPack.MAX_ARCHIVE){packStatus.setText("Pack requires a known size between 1 and "+BroadPack.MAX_ARCHIVE+" bytes. Other bulk schemas need a compatible reader.");return;}
            try{ResourceStorage.requireSpace(bytes,getFilesDir().getUsableSpace());}
            catch(Exception error){packStatus.setText(error.getMessage());return;}
            final long expected=bytes;
            new AlertDialog.Builder(this).setTitle("Import local collection?").setMessage("Archive: "+bytes+" bytes. Free storage: "+getFilesDir().getUsableSpace()+" bytes. Keep at least 256 MiB free after copying; SQLite expansion is checked separately. Internal content hashes are verified; they do not authenticate the publisher. The original file remains.")
                .setNegativeButton("Cancel",null).setPositiveButton("Import",(d,w)->importCollection(uri,expected)).show();
        }
        if (request == NativePanel.PICK_MODEL && result == RESULT_OK && data != null) nativePanel.selected(data.getData());
    }
    private void importCollection(android.net.Uri uri,long expected){
        if(importing||searching||nativePanel.isBusy())return;
            importing = true; cancelPack=false;++libraryEpoch;updateControls();
            packStatus.setText("Validating knowledge pack…");
            packWorker.execute(() -> {
                packThread=Thread.currentThread();
                try {
                    ImportRecovery.begin(getFilesDir(),"pack");
                    try (java.io.InputStream in = DocumentInput.open(getContentResolver(),uri,()->cancelPack || destroyed)) {
                    PackLibrary.Snapshot next = library.install(in,()->cancelPack || destroyed,expected);
                    ImportRecovery.finish(getFilesDir(),"pack");
                    runOnUiThread(() -> { if (destroyed || cancelPack) return;showLibrary(next);
                        answer.setText("Collection retained. Search all active collections or choose which to use.");
                    });
                    }
                } catch (Exception | OutOfMemoryError error) {
                    runOnUiThread(() -> { if (!destroyed) packStatus.setText("Pack rejected; previous library retained. " + error.getMessage()); });
                } finally {
                    packThread=null;Thread.interrupted();
                    runOnUiThread(() -> { if (destroyed) return; importing = false;updateControls(); });
                }
            });
    }
    void releaseForMemoryPressure(){cancelPack=true;++libraryEpoch;if(packThread!=null)packThread.interrupt();latestEvidence=null;engine=null;catalog=null;sourceList.removeAllViews();if(nativePanel!=null)nativePanel.lowMemory();status.setText("Memory released. Tap Reload library to search your saved active collections.");updateControls();}
    boolean resourceIdle(){return !nativePanel.isBusy();}
    void reloadSavedModel(){nativePanel.reloadSaved();}
    @Override public void onTrimMemory(int level){super.onTrimMemory(level);if(level==android.content.ComponentCallbacks2.TRIM_MEMORY_RUNNING_LOW || level==android.content.ComponentCallbacks2.TRIM_MEMORY_RUNNING_CRITICAL || level>=android.content.ComponentCallbacks2.TRIM_MEMORY_BACKGROUND)releaseForMemoryPressure();}
    @Override public void onLowMemory(){super.onLowMemory();releaseForMemoryPressure();}
    @Override protected void onDestroy() { destroyed = true;cancelPack=true;if(packThread!=null)packThread.interrupt(); if (nativePanel != null) nativePanel.destroy(); worker.shutdownNow(); super.onDestroy(); }
}
