package org.pocketlore.app;

import android.app.Activity;
import android.app.AlertDialog;
import android.os.Bundle;
import android.view.View;
import android.view.inputmethod.InputMethodManager;
import android.content.Context;
import android.widget.Button;
import android.widget.Spinner;
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
    private ScrollView[] screenViews;
    private LinearLayout answerActions, homeCollections, recentResearch, intro, composer;
    private TextView resultQuestion;
    private Button editQuestion;
    private Button compareAction;
    private TextView historyState;
    private String activeQuestion="",restoredAnswer="";
    private AnswerEngine.Outcome savedOutcome;
    private int selectedScreen;
    private ResearchEngine engine;
    private PackLibrary library;
    private PackLibrary.Snapshot catalog;
    private Button collections, reloadLibrary, removeCollection;
    private boolean searching, restoredEditing, hasSnapshot;
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
        if(state!=null){restoredAnswer=state.getString("answerSnapshot","");hasSnapshot=!restoredAnswer.isEmpty();activeQuestion=state.getString("answerQuestion","");restoredEditing=state.getBoolean("editing",false);}
        LinearLayout root=ReaderUi.shell(this,"Research");
        android.widget.FrameLayout pages=new android.widget.FrameLayout(this);root.addView(pages,1,new LinearLayout.LayoutParams(-1,0,1));
        LinearLayout research=ReaderUi.column(this),layout=ReaderUi.column(this);
        LinearLayout[] bodies={research,layout};screenViews=new ScrollView[2];
        for(int i=0;i<2;i++){screenViews[i]=new ScrollView(this);screenViews[i].setFillViewport(true);screenViews[i].addView(bodies[i]);pages.addView(screenViews[i]);}
        selectedScreen=state==null?0:state.getInt("screen",0);setScreen(getIntent().getBooleanExtra("settings",false)?1:selectedScreen);
        ReaderUi.button(this,layout,"Return to research",this::showResearch);
        TextView storageTitle=text("Storage & settings",24);ReaderUi.heading(storageTitle);layout.addView(storageTitle);
        layout.addView(text("Device free space: "+android.text.format.Formatter.formatFileSize(this,getFilesDir().getUsableSpace())+" at screen creation. Import checks run again before copying.",14));
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
        Button cancelImport=new Button(this);cancelImport.setText("Cancel pack import");layout.addView(cancelImport);ReaderUi.status(packStatus);cancelImport.setOnClickListener(v->{cancelPack=true;if(packThread!=null)packThread.interrupt();});
        intro=new LinearLayout(this);intro.setOrientation(1);research.addView(intro);ReaderUi.title(this,intro,"A little curiosity.\nA deeper understanding.","Your offline research notebook");
        composer=new LinearLayout(this);composer.setOrientation(1);ReaderUi.card(this,composer);LinearLayout.LayoutParams cp=new LinearLayout.LayoutParams(-1,-2);cp.topMargin=dp(20);cp.bottomMargin=dp(16);research.addView(composer,cp);
        question = new EditText(this);
        ReaderUi.label(this,composer,question,"Your question");
        question.setHint("What would you like to understand?");
        question.setInputType(android.text.InputType.TYPE_CLASS_TEXT|android.text.InputType.TYPE_TEXT_FLAG_MULTI_LINE);
        question.setMinLines(2); question.setMaxLines(6); question.setTextSize(20);question.setBackgroundTintList(android.content.res.ColorStateList.valueOf(ReaderUi.TEAL));
        question.setContentDescription("Research question"); composer.addView(question);
        search = new Button(this); search.setText("Research offline  →"); ReaderUi.styleButton(this,search,true);LinearLayout.LayoutParams submit=new LinearLayout.LayoutParams(-1,-2);submit.topMargin=dp(12);composer.addView(search,submit);
        resultQuestion=text("",28);resultQuestion.setTypeface(android.graphics.Typeface.create("serif",0));ReaderUi.heading(resultQuestion);research.addView(resultQuestion);resultQuestion.setVisibility(View.GONE);
        editQuestion=ReaderUi.button(this,research,"Edit question",()->{editResearch();question.requestFocus();screenViews[0].smoothScrollTo(0,0);});editQuestion.setVisibility(View.GONE);
        answerActions = new LinearLayout(this); LinearLayout actions=answerActions; actions.setOrientation(LinearLayout.VERTICAL); research.addView(actions);
        status = text("Loading installed knowledge pack…", 14); status.setTag("Answer status"); research.addView(status);
        answer = text("", 18);answer.setVisibility(View.GONE);
        ReaderUi.status(status); answer.setLineSpacing(dp(4),1.12f); ReaderUi.card(this,answer); answer.setTextIsSelectable(true); answer.setTag("Offline answer"); research.addView(answer);
        sourceList = new LinearLayout(this); sourceList.setOrientation(LinearLayout.VERTICAL); research.addView(sourceList);
        nativePanel = new NativePanel(this, layout, actions, answer, status, busy -> {
            updateControls(); captureCompleted();
        }, id -> { if(latestEvidence!=null) for(ResearchEngine.Hit hit:latestEvidence.hits) if(hit.passage.id.equals(id)) inspect(hit); });
        briefButton=ReaderUi.button(this,composer,"Research brief · source quotations",this::runBrief);
        ReaderUi.button(this,actions,"Cancel research brief",()->cancelBrief=true);
        ReaderUi.button(this,composer,"Photo text and speech input",()->{if(!importing&&!searching&&!nativePanel.isBusy())startActivityForResult(new android.content.Intent(this,AttachmentsActivity.class),340);});
        ReaderUi.button(this,layout,"Personal documents and collection export",()->{if(!importing&&!searching&&!nativePanel.isBusy())startActivityForResult(new android.content.Intent(this,PersonalDocumentsActivity.class),330);});
        historyState=text("",16);research.addView(historyState);historyState.setVisibility(View.GONE);
        compareAction=ReaderUi.button(this,research,"Compare retrieved sources",this::compareSources);compareAction.setVisibility(View.GONE);
        homeCollections=new LinearLayout(this);homeCollections.setOrientation(1);research.addView(homeCollections);
        recentResearch=new LinearLayout(this);recentResearch.setOrientation(1);research.addView(recentResearch);refreshRecent();
        search.setEnabled(false);
        search.setOnClickListener(v -> runSearch());
        question.setText(state!=null?state.getString("question", ""):getPreferences(0).getString("draft",""));
        try{library=new PackLibrary(getFilesDir());loadLibrary();}
        catch(Exception e){status.setText("Library unavailable: "+e.getMessage());}
    }
    private void editResearch(){resultMode(false);answer.setVisibility(View.GONE);sourceList.setVisibility(View.GONE);compareAction.setVisibility(View.GONE);historyState.setVisibility(View.GONE);status.setText("Edit your question, then research again");}
    private void resultMode(boolean result){
        intro.setVisibility(result?View.GONE:View.VISIBLE);composer.setVisibility(result?View.GONE:View.VISIBLE);resultQuestion.setText(activeQuestion.isEmpty()?question.getText():activeQuestion);resultQuestion.setVisibility(result?View.VISIBLE:View.GONE);editQuestion.setVisibility(result?View.VISIBLE:View.GONE);if(homeCollections!=null)homeCollections.setVisibility(result?View.GONE:View.VISIBLE);if(recentResearch!=null)recentResearch.setVisibility(result?View.GONE:View.VISIBLE);
    }
    private void showHomeCollections(){
        homeCollections.removeAllViews();TextView title=text("On your bookshelf",22);ReaderUi.heading(title);homeCollections.addView(title);
        if(catalog!=null&&!catalog.entries.isEmpty())for(PackLibrary.Entry e:catalog.entries)ReaderUi.entry(this,homeCollections,e.id.replace('-',' '),e.active?"Active collection · Edition details":"Installed collection · Inactive",()->new AlertDialog.Builder(this).setTitle(e.id.replace('-',' ')).setMessage("Installed edition: "+e.hash+"\n\n"+(e.active?"Included when researching across active collections. Open citations in a result to read its exact sources.":"This collection is inactive. Enable it in Settings to include it in research.")).setPositiveButton("Close",null).setNeutralButton("Collection settings",(d,w)->showSettings()).show());
        else ReaderUi.entry(this,homeCollections,"Water science","Bundled USGS source passages",()->ReaderUi.navigate(this,"Library"));
    }
    @Override protected void onResume(){super.onResume();refreshRecent();}
    private void refreshRecent(){
        if(recentResearch==null)return;NotebookActivity.IO.execute(()->{try(NotebookStore store=new NotebookStore(this)){java.util.List<NotebookStore.Entry> entries=store.list("",false);runOnUiThread(()->{if(destroyed)return;recentResearch.removeAllViews();TextView title=text("Pick up where you left off",22);ReaderUi.heading(title);recentResearch.addView(title);int count=0;for(NotebookStore.Entry e:entries){if(!e.kind.equals("research"))continue;ReaderUi.entry(this,recentResearch,e.title,android.text.format.DateFormat.format("MMM d · HH:mm",e.created).toString()+(e.bookmark?" · Bookmarked":" · Research"),()->startActivity(new android.content.Intent(this,SourceReaderActivity.class).putExtra("record",e.id)));if(++count==3)break;}if(count==0)recentResearch.addView(text("Your completed research will appear here. Start with a question above.",16));});}catch(Exception e){runOnUiThread(()->{if(!destroyed)recentResearch.addView(text("Saved research could not be read. Open Saved to retry.",16));});}});
    }
    private void updateControls(){
        if(nativePanel==null)return;if(answerActions!=null)answerActions.setVisibility(nativePanel.isBusy()||searching?View.VISIBLE:View.GONE);boolean ready=!nativePanel.isBusy()&&!importing&&!searching;
        search.setEnabled(ready&&engine!=null&&engine.size()>0);if(briefButton!=null)briefButton.setEnabled(ready&&engine!=null&&engine.size()>0);question.setEnabled(ready);importPack.setEnabled(ready);
        collections.setEnabled(ready&&catalog!=null&&!catalog.entries.isEmpty());removeCollection.setEnabled(ready&&catalog!=null&&!catalog.entries.isEmpty());reloadLibrary.setEnabled(ready);
    }
    private void showLibrary(PackLibrary.Snapshot next){
        catalog=next;engine=next.engine;latestEvidence=null;nativePanel.clearEvidence();sourceList.removeAllViews();
        packStatus.setText(next.description()+" · "+next.archiveBytes+" installed archive/index bytes"+(ImportRecovery.pending(getFilesDir(),"pack")?"\nPrevious import interrupted or failed. Installed editions retained; select the original file to restart verification.":""));status.setText("Ready to research offline");showHomeCollections();updateControls();
    }
    private void loadLibrary(){
        if(importing||searching)return;
        importing=true;cancelPack=false;long epoch=++libraryEpoch;updateControls();status.setText("Loading active collections…");
        packWorker.execute(()->{packThread=Thread.currentThread();try{
            PackLibrary.Snapshot next=library.loadMigrating(new java.io.File(getFilesDir(),"knowledge.plpack"));
            ResearchEngine starter=next.entries.isEmpty()?new ResearchEngine(new InputStreamReader(getAssets().open("water-science.tsv"),StandardCharsets.UTF_8)):null;
            runOnUiThread(()->{if(destroyed||epoch!=libraryEpoch)return;showLibrary(next);if(starter!=null){engine=starter;packStatus.setText("Bundled water-science starter · Import collections to build your library");}if(starter!=null)showHomeCollections();if(!restoredAnswer.isEmpty()){answer.setVisibility(View.VISIBLE);answer.setText(restoredAnswer);resultMode(true);status.setText("Restored snapshot · Open last saved research for source details");restoredAnswer="";if(restoredEditing)editResearch();}else answer.setVisibility(View.GONE);});
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
        if (nativePanel.isBusy() || importing || searching || engine == null) return;
        String query = question.getText().toString().trim(); activeQuestion=query;
        if (query.isEmpty()) { question.setError("Enter a research question"); return; }
        ((InputMethodManager)getSystemService(Context.INPUT_METHOD_SERVICE)).hideSoftInputFromWindow(question.getWindowToken(), 0);
        resultMode(true);sourceList.setVisibility(View.VISIBLE);screenViews[0].smoothScrollTo(0,0);hasSnapshot=false;nativePanel.clearAnswer(); answer.setVisibility(View.VISIBLE);sourceList.removeAllViews();compareAction.setVisibility(View.GONE);
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
                    LinearLayout sourceCard=new LinearLayout(this);sourceCard.setOrientation(1);ReaderUi.card(this,sourceCard);LinearLayout.LayoutParams sourceParams=new LinearLayout.LayoutParams(-1,-2);sourceParams.topMargin=dp(16);sourceList.addView(sourceCard,sourceParams);
                    Button source = new Button(this);
                    TextView quote=text("Source excerpt\n"+hit.passage.text,16);quote.setMaxLines(4);quote.setEllipsize(android.text.TextUtils.TruncateAt.END);sourceCard.addView(quote);
                    source.setText("Inspect source: " + hit.passage.title);
                    source.setAllCaps(false);ReaderUi.styleButton(this,source,false);
                    source.setOnClickListener(v -> inspect(hit));
                    sourceCard.addView(source);
                }
                latestEvidence=result;compareAction.setVisibility(result.hits.size()>=2?View.VISIBLE:View.GONE);nativePanel.answer(query, result);screenViews[0].post(()->answer.requestRectangleOnScreen(new android.graphics.Rect(0,0,answer.getWidth(),Math.min(answer.getHeight(),dp(120))),false));
            });
        });
    }
    private void runBrief() {
        if(nativePanel.isBusy()||importing||searching||engine==null)return;
        String query=question.getText().toString().trim();
        if(query.isEmpty()){question.setError("Enter a research question");return;}
        activeQuestion=query;resultMode(true);answer.setVisibility(View.VISIBLE);sourceList.setVisibility(View.VISIBLE);hasSnapshot=false;compareAction.setVisibility(View.GONE);cancelBrief=false;searching=true;updateControls();nativePanel.clearAnswer();sourceList.removeAllViews();
        status.setText("Selecting exact source quotations…");
        ResearchEngine selected=engine;long epoch=libraryEpoch;
        worker.execute(()->{try{
            ResearchEngine.Result result=EvidenceAvailability.scope(query)==EvidenceAvailability.Scope.REFERENCE
                ? selected.research(query)
                : new ResearchEngine.Result(java.util.Collections.emptyList(),java.util.Collections.emptySet(),"Evidence unavailable");
            ResearchBrief.Brief brief=ResearchBrief.create(query,result,()->cancelBrief||destroyed);
            runOnUiThread(()->{if(destroyed||epoch!=libraryEpoch||cancelBrief)return;
                latestEvidence=result;
                android.text.SpannableString rendered=new android.text.SpannableString(brief.text);
                for(ResearchBrief.Quote quote:brief.quotes){
                    rendered.setSpan(new android.text.style.ClickableSpan(){public void onClick(View view){
                        quote.verify(quote.source);inspect(new ResearchEngine.Hit(quote.source,0));
                    }},quote.displayStart,quote.displayEnd,android.text.Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
                }
                hasSnapshot=true;answer.setText(rendered);answer.setMovementMethod(android.text.method.LinkMovementMethod.getInstance());
                saveBrief(query,brief);
                status.setText(brief.availability==EvidenceAvailability.Scope.REFERENCE ? brief.quotes.size()+" source quotations · coverage unverified · no generated answer" : EvidenceAvailability.reason(brief.availability));
            });
        }catch(Exception e){runOnUiThread(()->{if(!destroyed)status.setText("Research brief unavailable: "+e.getMessage());});}
        finally{runOnUiThread(()->{if(!destroyed){searching=false;nativePanel.finishResearchBrief();if(cancelBrief)status.setText("Research brief cancelled; no partial result");updateControls();}});}});
    }
    private void saveBrief(String query,ResearchBrief.Brief brief){
        StringBuilder detail=new StringBuilder("Result label: SOURCE_BRIEF (extractive, not generated). Coverage is unverified.\n");
        for(ResearchBrief.Quote quote:brief.quotes)detail.append(sourceDetail(new ResearchEngine.Hit(quote.source,0))).append("\n\n");
        NotebookActivity.IO.execute(()->{try(NotebookStore store=new NotebookStore(this)){long id=store.add("research",query,query,brief.text,detail.toString(),false);getPreferences(0).edit().putLong("lastRecord",id).apply();runOnUiThread(()->{if(!destroyed){historyState.setText("Source brief saved to your notebook");historyState.setVisibility(View.VISIBLE);refreshRecent();}});}catch(Exception e){runOnUiThread(()->{if(!destroyed){historyState.setText("Brief was not saved: "+e.getMessage());historyState.setVisibility(View.VISIBLE);}});}});
    }
    AnswerEngine.Outcome latestAnswer() { return nativePanel.outcome(); }
    boolean modelReady() { return nativePanel.hasModel() && !nativePanel.isBusy(); }
    private String sourceDetail(ResearchEngine.Hit hit){
        ResearchEngine.Passage p=hit.passage;
        return p.text+"\n\nSource document: "+p.title+"\n"+p.url+"\nSource date / retrieval: "+known(p.sourceDate)+"\nRights: "+known(p.license)+"\nCitation: ["+p.id+"]\n"+p.collectionProvenance+"\n\n"+(p.url.startsWith("personal://")?"Personal document text preserves exact extracted offsets; PDF extraction order may differ from visual layout.":p.id.startsWith("water-")?"Pack text is a verbatim USGS paragraph with whitespace normalized.":"Pack text is selected source text with whitespace normalized.")+" URLs are provenance labels, not network links."+String.format(Locale.ROOT,"\nRetrieval rank score: %.3f (not confidence)",hit.score);
    }
    private void inspect(ResearchEngine.Hit hit) {
        String detail=sourceDetail(hit);
        if(hit.passage.id.matches("p[0-9a-f]{64}_wiki-.*"))try{detail+="\n\nOffline license\n"+BroadPack.licenseText(getFilesDir(),hit.passage.id);}catch(Exception e){detail+="\nSaved license unavailable: "+e.getMessage();}
        ReaderUi.openSource(this,hit.passage.title,detail,"Retrieved passage only. Coverage is limited to active installed editions. Source date and rights are supplied above; Unknown means unavailable.");
    }
    private void captureCompleted(){
        if(nativePanel==null||nativePanel.isBusy())return;AnswerEngine.Outcome result=nativePanel.outcome();
        if(result==null||result==savedOutcome||result.kind==AnswerEngine.Kind.CANCELLED)return;savedOutcome=result;
        String q=activeQuestion;StringBuilder sources=new StringBuilder("Result label: "+result.kind+"\nReason: "+result.reason+"\nSaved sources are snapshots, not proof of answer quality.\n\n");
        if(latestEvidence!=null)for(ResearchEngine.Hit hit:latestEvidence.hits)sources.append(sourceDetail(hit)).append("\n\n");
        NotebookActivity.IO.execute(()->{try(NotebookStore store=new NotebookStore(this)){long id=store.add("research",q,q,result.text,sources.toString(),false);getPreferences(0).edit().putLong("lastRecord",id).apply();runOnUiThread(()->{if(!destroyed){historyState.setVisibility(View.VISIBLE);historyState.setText("Saved to your notebook");refreshRecent();}});}catch(Exception e){runOnUiThread(()->{if(!destroyed){historyState.setVisibility(View.VISIBLE);historyState.setText("Research was not saved: "+e.getMessage());}});}});
    }
    private void compareSources(){
        if(latestEvidence==null||latestEvidence.hits.size()<2){historyState.setText("At least two real retrieved sources are required. You can also compare two records in Saved.");return;}
        java.util.List<ResearchEngine.Hit> hits=latestEvidence.hits;String[] titles=new String[hits.size()];boolean[] checked=new boolean[hits.size()];for(int i=0;i<titles.length;i++)titles[i]=hits.get(i).passage.title;
        new AlertDialog.Builder(this).setTitle("Choose two source passages").setMultiChoiceItems(titles,checked,(d,i,on)->checked[i]=on).setNegativeButton("Cancel",null).setPositiveButton("Compare",(d,w)->{
            java.util.List<ResearchEngine.Hit> selected=new java.util.ArrayList<>();for(int i=0;i<checked.length;i++)if(checked[i])selected.add(hits.get(i));if(selected.size()!=2){historyState.setText("Select exactly two sources.");return;}
            NotebookActivity.IO.execute(()->{try(NotebookStore store=new NotebookStore(this)){long first=store.add("source",selected.get(0).passage.title,activeQuestion,sourceDetail(selected.get(0)),"Retrieved passage; no new inference or verification.",false);long second=store.add("source",selected.get(1).passage.title,activeQuestion,sourceDetail(selected.get(1)),"Retrieved passage; no new inference or verification.",false);runOnUiThread(()->startActivity(new android.content.Intent(this,SourceReaderActivity.class).putExtra("record",first).putExtra("compare",second)));}catch(Exception e){runOnUiThread(()->historyState.setText("Comparison unavailable: "+e.getMessage()));}});
        }).show();
    }
    private static String known(String value){return value==null||value.trim().isEmpty()?"Unknown":value;}
    private TextView text(String value, int size) {
        return ReaderUi.text(this,value,size);
    }
    private int dp(int value) { return Math.round(value * getResources().getDisplayMetrics().density); }
    @Override protected void onSaveInstanceState(Bundle state) { super.onSaveInstanceState(state); state.putString("question", question.getText().toString()); state.putInt("screen",selectedScreen);state.putString("answerQuestion",activeQuestion);state.putBoolean("editing",composer.getVisibility()==View.VISIBLE);if(nativePanel!=null&&(hasSnapshot||nativePanel.outcome()!=null||status.getText().toString().startsWith("Restored snapshot"))&&answer.length()<128000)state.putString("answerSnapshot",answer.getText().toString()); }
    private void setScreen(int screen){selectedScreen=screen==1?1:0;for(int i=0;i<screenViews.length;i++)screenViews[i].setVisibility(i==selectedScreen?View.VISIBLE:View.GONE);}
    void showResearch(){setScreen(0);}
    void showSettings(){setScreen(1);}
    @Override protected void onNewIntent(android.content.Intent intent){super.onNewIntent(intent);setIntent(intent);setScreen(intent.getBooleanExtra("settings",false)?1:0);}
    @Override protected void onPause(){super.onPause();if(question!=null)getPreferences(0).edit().putString("draft",question.getText().toString()).apply();}
    @Override public void onBackPressed(){if(selectedScreen!=0)showResearch();else super.onBackPressed();}
    @Override protected void onActivityResult(int request, int result, android.content.Intent data) {
        super.onActivityResult(request, result, data);
        if(request==340&&result==RESULT_OK&&data!=null){editResearch();question.setText(data.getStringExtra("recognized_text"));status.setText("Recognized input requires review; it is not source evidence.\n"+data.getStringExtra("recognition_receipt"));return;}
        if(request==330){loadLibrary();return;}
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
