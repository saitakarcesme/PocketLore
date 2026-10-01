package org.pocketlore.app;
import android.app.*;
import android.os.*;
import android.content.*;
import android.widget.*;
import android.view.accessibility.AccessibilityNodeInfo;
import java.io.*;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import org.json.*;

/** Public-fixture catalog/UI tests; no generated-answer rating and no user asset replacement. */
public final class LibraryInstrumentation extends Instrumentation {
    private File root;private String mode;private JSONObject report=new JSONObject();private MainActivity activity;
    private static void check(boolean ok,String why){if(!ok)throw new AssertionError(why);}
    private static Object field(Object o,String n){try{java.lang.reflect.Field f=o.getClass().getDeclaredField(n);f.setAccessible(true);return f.get(o);}catch(Exception e){throw new RuntimeException(e);}}
    private void save()throws Exception{Files.write(new File(root,mode+".json").toPath(),report.toString(2).getBytes(StandardCharsets.UTF_8));}
    private static void await(java.util.function.BooleanSupplier f,String why)throws Exception{long end=System.nanoTime()+60_000_000_000L;while(!f.getAsBoolean()&&System.nanoTime()<end)Thread.sleep(30);check(f.getAsBoolean(),why);}
    private void ready()throws Exception{await(()->{final boolean[] idle={false};runOnMainSync(()->idle[0]=!(Boolean)field(activity,"importing")&&!(Boolean)field(activity,"searching")&&activity.resourceIdle());return idle[0];},"Activity did not become idle");}
    private void button(String n)throws Exception{runOnMainSync(()->{Button b=(Button)field(activity,n);check(b.isEnabled(),"Control disabled: "+n);check(b.performClick(),"Control not clicked: "+n);});getUiAutomation().waitForIdle(50,3000);}
    private static String visible(AccessibilityNodeInfo node){if(node==null)return "";StringBuilder s=new StringBuilder();if(node.getText()!=null)s.append(node.getText()).append('\n');for(int i=0;i<node.getChildCount();i++)s.append(visible(node.getChild(i)));return s.toString();}
    private boolean clickText(AccessibilityNodeInfo node,String text){if(node==null)return false;if(node.getText()!=null&&node.getText().toString().equalsIgnoreCase(text)){AccessibilityNodeInfo at=node;while(at!=null){if(at.isClickable())return at.performAction(AccessibilityNodeInfo.ACTION_CLICK);at=at.getParent();}}for(int i=0;i<node.getChildCount();i++)if(clickText(node.getChild(i),text))return true;return false;}
    private void dialogClick(String text)throws Exception{getUiAutomation().waitForIdle(100,3000);await(()->visible(getUiAutomation().getRootInActiveWindow()).toLowerCase(Locale.ROOT).contains(text.toLowerCase(Locale.ROOT)),"Dialog did not appear: "+text);check(clickText(getUiAutomation().getRootInActiveWindow(),text),"Missing dialog control: "+text);Thread.sleep(100);}
    private PackLibrary.Snapshot current(){return (PackLibrary.Snapshot)field(activity,"catalog");}
    private JSONObject memory(String name)throws Exception{android.os.Debug.MemoryInfo m=new android.os.Debug.MemoryInfo();android.os.Debug.getMemoryInfo(m);JSONObject o=new JSONObject().put("phase",name).put("pss_kib",m.getTotalPss()).put("java_used_bytes",Runtime.getRuntime().totalMemory()-Runtime.getRuntime().freeMemory()).put("java_max_bytes",Runtime.getRuntime().maxMemory());for(String l:Files.readAllLines(Paths.get("/proc/self/status")))if(l.startsWith("VmRSS:")||l.startsWith("VmSwap:")){String[] v=l.trim().split("\\s+");o.put(v[0].replace(":",""),Long.parseLong(v[1]));}return o;}
    private PackLibrary.Snapshot install(PackLibrary lib,String name)throws Exception{try(InputStream in=new FileInputStream(new File(root,name+".plpack"))){return lib.install(in,()->false);}}
    private void assertions()throws Exception{
        File isolated=new File(root,"isolated-"+android.os.Process.myPid());isolated.mkdirs();PackLibrary lib=new PackLibrary(isolated);JSONArray tests=new JSONArray();report.put("tests",tests);
        PackLibrary.Snapshot first=install(lib,"reference"),both=install(lib,"science");check(both.entries.size()==2&&both.engine.size()==210&&both.distinctDocuments==18,"Combined collection counts");tests.put("two-real-editions");
        check(install(lib,"reference").entries.size()==2,"Exact reimport duplicated edition");tests.put("idempotent-import");
        PackLibrary.Snapshot dup=install(lib,"duplicate");check(dup.entries.size()==3&&dup.engine.size()==210&&dup.distinctDocuments==18,"Duplicate document expanded index");
        check(dup.engine.research("headlamps").hits.get(0).passage.collectionProvenance.contains("Also retained in"),"Duplicate provenance lost");tests.put("duplicate-document-provenance");
        PackLibrary.Snapshot same=install(lib,"same-name");check(same.entries.size()==4&&same.engine.size()==210&&same.distinctDocuments==18,"Same-name edition identity collision");tests.put("same-name-distinct-edition");
        Set<String> active=new HashSet<>();active.add(first.entries.get(0).hash);PackLibrary.Snapshot disabled=lib.select(active);check(disabled.engine.size()==186,"Disabled edition indexed");for(ResearchEngine.Hit h:disabled.engine.research("magma lava").hits)check(!h.passage.collectionProvenance.contains("science-supplement"),"Disabled science hit");tests.put("disabled-pack");
        check(lib.select(Collections.emptySet()).engine.size()==0,"All-disabled not empty");tests.put("all-disabled");
        active.add(both.entries.get(1).hash);lib.select(active);File catalog=new File(isolated,"pack-library/catalog.json");byte[] old=Files.readAllBytes(catalog.toPath());JSONArray rejected=new JSONArray();report.put("rejections",rejected);
        for(String name:new String[]{"conflicting-id","corrupt"}){String failure="";try{install(lib,name);}catch(Exception e){failure=e.toString();}check(!failure.isEmpty()&&Arrays.equals(old,Files.readAllBytes(catalog.toPath())),"Integrity rollback "+name);rejected.put(new JSONObject().put("case",name).put("failure",failure));}
        for(boolean before:new boolean[]{true,false}){final boolean[] cancelled={before};InputStream original=new FileInputStream(new File(root,"science.plpack"));InputStream stream=new FilterInputStream(original){public int read(byte[] b,int o,int l)throws IOException{int n=super.read(b,o,Math.min(l,128));cancelled[0]=true;return n;}};long t=System.nanoTime();String failure="";try(InputStream in=stream){lib.install(in,()->cancelled[0]);}catch(Exception e){failure=e.toString();}check(!failure.isEmpty()&&Arrays.equals(old,Files.readAllBytes(catalog.toPath())),"Cancellation rollback");rejected.put(new JSONObject().put("case",before?"cancel-before":"cancel-during").put("failure",failure).put("latency_ms",(System.nanoTime()-t)/1e6));}
        // Each padded manifest is valid alone, but both together exceed aggregate admission.
        KnowledgePack.load(new File(root,"large-a.plpack"));KnowledgePack.load(new File(root,"large-b.plpack"));
        install(lib,"large-a");old=Files.readAllBytes(catalog.toPath());String fail="";try{install(lib,"large-b");}catch(Exception e){fail=e.toString();}check(fail.contains("Combined collection storage limit")&&Arrays.equals(old,Files.readAllBytes(catalog.toPath())),"Combined manifest admission rollback");rejected.put(new JSONObject().put("case","combined-admission").put("failure",fail));
        long[][] limits={{PackLibrary.MAX_ARCHIVES+1,0,0,0,0,0,0,0},{0,PackLibrary.MAX_EXPANDED+1,0,0,0,0,0,0},{0,0,PackLibrary.MAX_MANIFESTS+1,0,0,0,0,0},{0,0,0,1001,0,0,0,0},{0,0,0,0,9,0,0,0},{0,0,0,0,0,5001,0,0},{0,0,0,0,0,0,1000001,0},{0,0,0,0,0,0,0,200001}};
        for(long[] v:limits){boolean rejectedLimit=false;try{PackLibrary.admit(v[0],v[1],v[2],v[3],v[4],v[5],v[6],v[7]);}catch(IOException e){rejectedLimit=true;}check(rejectedLimit,"Policy admitted over-limit");}tests.put("eight-admission-boundaries");
        boolean lowHeap=false;try{PackLibrary.admitHeap(1024,32L*1024*1024);}catch(IOException e){lowHeap=true;}check(lowHeap,"Insufficient heap policy admitted");PackLibrary.admitHeap(1024,32L*1024*1024+1024);tests.put("heap-reserve-boundary");
        check(new File(isolated,"pack-library").listFiles((d,n)->n.endsWith(".partial")).length==0,"Import stages remain");tests.put("staging-cleanup");save();
    }
    private void importUI(String name)throws Exception{
        // The actual button/framework result path is exercised with a deterministic
        // pinned fixture result. Provider browsing itself is outside this catalog test.
        IntentFilter filter=new IntentFilter(Intent.ACTION_OPEN_DOCUMENT);filter.addCategory(Intent.CATEGORY_OPENABLE);filter.addDataType("*/*");
        ActivityMonitor monitor=addMonitor(filter,new ActivityResult(Activity.RESULT_OK,new Intent().setData(android.net.Uri.fromFile(new File(root,name+".plpack")))),true);
        long epoch=(Long)field(activity,"libraryEpoch");
        try{button("importPack");await(()->(Long)field(activity,"libraryEpoch")>epoch,"Import result not delivered");ready();check(monitor.getHits()==1,"Import control did not request document picker");}
        finally{removeMonitor(monitor);}
    }
    private void selectScience(boolean on)throws Exception{
        button("collections");await(()->visible(getUiAutomation().getRootInActiveWindow()).contains("Search these collections"),"Collection dialog not visible");report.put("collection_controls",visible(getUiAutomation().getRootInActiveWindow()));screenshot("collections-dialog");PackLibrary.Entry entry=current().entries.stream().filter(e->e.id.startsWith("science-")).findFirst().get();
        if(entry.active!=on)dialogClick(entry.id.replace('-',' ')+" · edition "+entry.hash.substring(0,8));dialogClick("Apply");ready();
    }
    private JSONArray researchUI(String query)throws Exception{
        runOnMainSync(()->((EditText)field(activity,"question")).setText(query));button("search");ready();ResearchEngine.Result result=(ResearchEngine.Result)field(activity,"latestEvidence");check(result!=null&&!result.hits.isEmpty(),"No actual UI search result");JSONArray hits=new JSONArray();for(ResearchEngine.Hit h:result.hits)hits.put(new JSONObject().put("id",h.passage.id).put("text",h.passage.text).put("provenance",h.passage.collectionProvenance).put("url",h.passage.url).put("date",h.passage.sourceDate).put("rights",h.passage.license));return hits;
    }
    private void screenshot(String name)throws Exception{android.graphics.Bitmap b=getUiAutomation().takeScreenshot();check(b!=null,"Screenshot missing");try(FileOutputStream out=new FileOutputStream(new File(root,name+".png"))){b.compress(android.graphics.Bitmap.CompressFormat.PNG,100,out);}b.recycle();}
    private void inspectUI(String query,String marker,String name)throws Exception{
        JSONArray hits=researchUI(query);JSONObject hit=hits.getJSONObject(0);check(hit.getString("provenance").contains(marker),"Wrong edition at first hit");
        runOnMainSync(()->((Button)((LinearLayout)field(activity,"sourceList")).getChildAt(0)).performClick());getUiAutomation().waitForIdle(100,3000);await(()->visible(getUiAutomation().getRootInActiveWindow()).contains(hit.optString("text")),"Source dialog not visible");String text=visible(getUiAutomation().getRootInActiveWindow());
        check(text.contains(hit.getString("text"))&&text.contains(hit.getString("rights"))&&text.contains(hit.getString("url"))&&text.contains(hit.getString("date"))&&text.contains("Source SHA-256:")&&text.contains("Edition SHA-256:")&&text.contains(marker),"Displayed provenance missing");
        report.put(name,new JSONObject().put("hits",hits).put("visible_dialog",text).put("answer",activity.latestAnswer().text).put("route",activity.latestAnswer().kind.toString()));screenshot(name);dialogClick("Close");save();
    }
    @Override public void onCreate(Bundle args){super.onCreate(args);mode=args.getString("mode","exercise");start();}
    @Override public void onStart(){Bundle result=new Bundle();try{
        root=new File(getTargetContext().getFilesDir(),"multi-pack-tests");root.mkdirs();report.put("mode",mode).put("pid",android.os.Process.myPid());
        if(mode.equals("exercise"))assertions();
        getUiAutomation();
        activity=(MainActivity)startActivitySync(new Intent(getTargetContext(),MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));ready();
        // Actual unload control keeps retrieval evaluation separate from generated-answer quality.
        runOnMainSync(()->((Button)field(field(activity,"nativePanel"),"unload")).performClick());ready();
        if(mode.equals("exercise")){
            check(current().entries.size()==1,"Expected migrated pinned reference fixture only");report.put("memory_before_import",memory("before-import"));long importStart=System.nanoTime();importUI("science");report.put("import_ui_wall_ms",(System.nanoTime()-importStart)/1e6);check(current().entries.size()==2&&current().engine.size()==210&&current().distinctDocuments==18,"Actual import replaces collection");
            report.put("combined",current().description()).put("archive_bytes",current().archiveBytes).put("index_counts",new JSONArray(current().engine.resourceCounts())).put("memory_combined",memory("combined"));
            JSONArray both=researchUI("magma headlamps");Set<String> editions=new HashSet<>();for(int i=0;i<both.length();i++){String id=both.getJSONObject(i).getString("id");editions.add(id.substring(0,id.indexOf('_')));}check(editions.size()==2,"Cross-pack query did not retrieve both");report.put("cross_pack",both);
            inspectUI("What is the difference between magma and lava?","science-supplement","science-dialog");inspectUI("What navigation backups should I bring?","english-reference","reference-dialog");
            selectScience(false);check(current().engine.size()==186,"Disabled UI selection not applied");report.put("disabled_status",current().description());selectScience(true);
            String catalogHash=KnowledgePack.hash(Files.readAllBytes(new File(getTargetContext().getFilesDir(),"pack-library/catalog.json").toPath()));importUI("corrupt");check(KnowledgePack.hash(Files.readAllBytes(new File(getTargetContext().getFilesDir(),"pack-library/catalog.json").toPath())).equals(catalogHash),"UI corrupt import changed catalog");report.put("ui_corrupt_status",((TextView)field(activity,"packStatus")).getText().toString());selectScience(false);report.put("selection_before_restart",current().description());
        }else{
            check(current().entries.size()==2&&current().engine.size()==186,"Cold restart lost disabled selection");report.put("restart_status",current().description());selectScience(true);check(current().engine.size()==210,"Re-enable science failed after restart");
            report.put("memory_before_trim",memory("before-platform-trim"));save();Files.write(new File(root,"ready-memory").toPath(),new byte[]{1});
            await(()->field(activity,"engine")==null,"Platform trim did not release index");ready();report.put("memory_released",memory("after-platform-trim"));button("reloadLibrary");ready();check(current().engine.size()==210&&current().entries.size()==2,"Active reload failed");
            report.put("memory_reloaded",memory("after-active-reload")).put("reload_status",current().description());inspectUI("What is the difference between magma and lava?","science-supplement","reload-dialog");
        }
        report.put("status","PASS");save();
    }catch(Throwable e){try{report.put("status","FAIL").put("failure",e.toString()).put("failure_memory",memory("failure"));save();}catch(Exception ignored){}result.putString("failure",e.toString());}
        finish(report.optString("status").equals("PASS")?-1:1,result);
    }
}
