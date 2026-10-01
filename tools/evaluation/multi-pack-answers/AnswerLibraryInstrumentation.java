package org.pocketlore.app;
import android.app.*;
import android.os.*;
import android.content.*;
import android.widget.*;
import android.text.Spanned;
import android.text.style.ClickableSpan;
import android.view.accessibility.AccessibilityNodeInfo;
import java.io.*;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import org.json.*;

/** Real Activity/JNI revalidation, one resident production model and serial requests. */
public final class AnswerLibraryInstrumentation extends Instrumentation {
    private MainActivity activity;private File root;private JSONObject report=new JSONObject(),protocol;
    private JSONArray rows=new JSONArray(),samples=new JSONArray();private volatile boolean sampling;private volatile String phase="startup";private Thread sampler;private volatile Throwable sampleFailure;
    static Object field(Object o,String n){try{java.lang.reflect.Field f=o.getClass().getDeclaredField(n);f.setAccessible(true);return f.get(o);}catch(Exception e){throw new RuntimeException(e);}}
    static void check(boolean b,String why){if(!b)throw new AssertionError(why);}
    static byte[] bytes(String s){return s.getBytes(StandardCharsets.UTF_8);}
    static double ms(long t){return (System.nanoTime()-t)/1e6;}
    private void save()throws Exception{String serialized;synchronized(samples){report.put("samples",samples);serialized=report.toString(2);}Files.write(new File(root,"results.json").toPath(),bytes(serialized));}
    private void await(java.util.function.BooleanSupplier f,String why)throws Exception{long end=System.nanoTime()+180_000_000_000L;while(!f.getAsBoolean()&&System.nanoTime()<end)Thread.sleep(20);check(f.getAsBoolean(),why);}
    private void ready()throws Exception{await(()->{boolean[] idle={false};runOnMainSync(()->idle[0]=!(Boolean)field(activity,"importing")&&!(Boolean)field(activity,"searching")&&activity.resourceIdle());return idle[0];},"Activity idle timeout: "+phase);}
    private PackLibrary.Snapshot catalog(){return (PackLibrary.Snapshot)field(activity,"catalog");}
    private Object panel(){return field(activity,"nativePanel");}
    private void click(Object o,String field)throws Exception{runOnMainSync(()->{Button b=(Button)field(o,field);check(b.isEnabled(),"Disabled button "+field);b.performClick();});}
    private static String visible(AccessibilityNodeInfo n){if(n==null)return "";StringBuilder s=new StringBuilder();if(n.getText()!=null)s.append(n.getText()).append('\n');for(int i=0;i<n.getChildCount();i++)s.append(visible(n.getChild(i)));return s.toString();}
    private boolean clickText(AccessibilityNodeInfo n,String label){if(n==null)return false;if(n.getText()!=null&&n.getText().toString().equalsIgnoreCase(label)){AccessibilityNodeInfo p=n;while(p!=null){if(p.isClickable())return p.performAction(AccessibilityNodeInfo.ACTION_CLICK);p=p.getParent();}}for(int i=0;i<n.getChildCount();i++)if(clickText(n.getChild(i),label))return true;return false;}
    private void dialogClick(String label)throws Exception{await(()->visible(getUiAutomation().getRootInActiveWindow()).toLowerCase(Locale.ROOT).contains(label.toLowerCase(Locale.ROOT)),"Missing dialog "+label);check(clickText(getUiAutomation().getRootInActiveWindow(),label),"Cannot click "+label);getUiAutomation().waitForIdle(100,3000);}
    private void select(boolean science,boolean duplicate)throws Exception{
        click(activity,"collections");await(()->visible(getUiAutomation().getRootInActiveWindow()).contains("Search these collections"),"Collection dialog missing");
        for(PackLibrary.Entry e:catalog().entries){boolean on=e.id.startsWith("science-")?science:e.id.startsWith("duplicate-")?duplicate:true;if(e.active!=on)dialogClick(e.id.replace('-',' ')+" · edition "+e.hash.substring(0,8));}
        dialogClick("Apply");ready();
    }
    private void screenshot(String name)throws Exception{android.graphics.Bitmap b=getUiAutomation().takeScreenshot();check(b!=null,"Screenshot unavailable");try(FileOutputStream out=new FileOutputStream(new File(root,name+".png"))){b.compress(android.graphics.Bitmap.CompressFormat.PNG,100,out);}b.recycle();}
    private void sample()throws Exception{
        android.os.Debug.MemoryInfo m=new android.os.Debug.MemoryInfo();android.os.Debug.getMemoryInfo(m);JSONObject s=new JSONObject().put("phase",phase).put("uptime_ms",SystemClock.elapsedRealtime()).put("pss_kib",m.getTotalPss()).put("java_used_bytes",Runtime.getRuntime().totalMemory()-Runtime.getRuntime().freeMemory()).put("java_max_bytes",Runtime.getRuntime().maxMemory()).put("native",new JSONArray(NativeRuntime.resourceState())).put("operation",new JSONArray(NativeRuntime.operationState()));
        for(String line:Files.readAllLines(Paths.get("/proc/self/status")))if(line.startsWith("VmRSS:")||line.startsWith("VmSwap:")||line.startsWith("VmHWM:")){String[] parts=line.trim().split("\\s+");s.put(parts[0].replace(":",""),Long.parseLong(parts[1]));}
        synchronized(samples){samples.put(s);}
    }
    private JSONArray sources(ResearchEngine.Result evidence,int limit)throws Exception{JSONArray result=new JSONArray();for(ResearchEngine.Hit hit:evidence.hits){ResearchEngine.Passage p=hit.passage;result.put(new JSONObject().put("id",p.id).put("text",p.text).put("excerpt",EvidencePrompt.excerpt(hit,limit)).put("title",p.title).put("url",p.url).put("date",p.sourceDate).put("rights",p.license).put("provenance",p.collectionProvenance).put("score",hit.score));}return result;}
    private JSONObject record(String id,String question,long start)throws Exception{
        AnswerEngine.Outcome a=activity.latestAnswer();check(a!=null,"Missing completed outcome "+id);ResearchEngine.Result evidence=(ResearchEngine.Result)field(activity,"latestEvidence");
        ResearchEngine.Result selected=EvidencePrompt.select(question,evidence);int limit=900;
        while(!a.prompt.isEmpty()&&limit>200&&!EvidencePrompt.build(question,selected,limit).equals(a.prompt))limit-=100;
        long session=(Long)field(panel(),"session");int promptTokens=a.prompt.isEmpty()?0:NativeRuntime.countChatTokens(session,bytes(EvidencePrompt.SYSTEM),bytes(a.prompt));
        JSONArray active=new JSONArray();for(PackLibrary.Entry e:catalog().entries)if(e.active)active.put(e.hash);
        JSONObject row=new JSONObject().put("id",id).put("question",question).put("active",active).put("passages",catalog().engine.size()).put("documents",catalog().distinctDocuments).put("index_counts",new JSONArray(catalog().engine.resourceCounts())).put("route",a.kind.name()).put("invoked",a.invokedModel).put("reason",a.reason).put("text",a.text).put("raw",a.rawDraft).put("resolved_raw",EvidencePrompt.resolve(a.rawDraft,selected)).put("prompt",a.prompt).put("system",EvidencePrompt.SYSTEM).put("prompt_tokens",promptTokens).put("tokens",a.tokens).put("first_token_ms",a.firstTokenMs).put("controller_total_ms",a.totalMs).put("ui_wall_ms",ms(start)).put("retrieved",sources(evidence,900)).put("selected",sources(selected,limit)).put("native_after",new JSONArray(NativeRuntime.resourceState()));
        rows.put(row);report.put("rows",rows);Files.write(new File(root,id+".json").toPath(),bytes(row.toString(2)));save();
        check(promptTokens+256<=2048&&a.tokens<=256,"Context/output budget exceeded");check(NativeRuntime.resourceState()[1]==0,"Context retained after request");
        return row;
    }
    private void startQuery(String question)throws Exception{runOnMainSync(()->((EditText)field(activity,"question")).setText(question));click(activity,"search");}
    private void inspectLink(String id)throws Exception{
        AnswerEngine.Outcome outcome=activity.latestAnswer();if(outcome.kind!=AnswerEngine.Kind.GENERATED)return;
        final String[] cited={null};runOnMainSync(()->{TextView view=(TextView)field(activity,"answer");check(view.getText() instanceof Spanned,"Generated answer has no spans");Spanned text=(Spanned)view.getText();ClickableSpan[] spans=text.getSpans(0,text.length(),ClickableSpan.class);check(spans.length>0,"Generated citations not clickable");int start=text.getSpanStart(spans[0]),end=text.getSpanEnd(spans[0]);cited[0]=text.subSequence(start+1,end-1).toString();spans[0].onClick(view);});
        ResearchEngine.Result evidence=(ResearchEngine.Result)field(activity,"latestEvidence");ResearchEngine.Hit expected=null;for(ResearchEngine.Hit h:evidence.hits)if(h.passage.id.equals(cited[0]))expected=h;check(expected!=null,"Link not in retrieved evidence");final ResearchEngine.Passage p=expected.passage;
        await(()->visible(getUiAutomation().getRootInActiveWindow()).contains(p.text),"Citation dialog not shown");String text=visible(getUiAutomation().getRootInActiveWindow());check(text.contains(p.id)&&text.contains(p.url)&&text.contains(p.sourceDate)&&text.contains(p.license)&&text.contains(p.collectionProvenance),"Wrong source/edition dialog");
        JSONObject link=new JSONObject().put("case",id).put("citation",p.id).put("visible",text);report.getJSONArray("links").put(link);screenshot(id+"-citation");dialogClick("Close");save();
    }
    private JSONObject answer(JSONObject c)throws Exception{phase=c.getString("id");Files.write(new File(root,"active-case.txt").toPath(),bytes(phase));long t=System.nanoTime();startQuery(c.getString("question"));ready();JSONObject r=record(phase,c.getString("question"),t);inspectLink(phase);return r;}
    private void importDuplicate()throws Exception{
        IntentFilter f=new IntentFilter(Intent.ACTION_OPEN_DOCUMENT);f.addCategory(Intent.CATEGORY_OPENABLE);f.addDataType("*/*");ActivityMonitor monitor=addMonitor(f,new ActivityResult(Activity.RESULT_OK,new Intent().setData(android.net.Uri.fromFile(new File(root,"duplicate.plpack")))),true);long epoch=(Long)field(activity,"libraryEpoch");
        try{click(activity,"importPack");await(()->(Long)field(activity,"libraryEpoch")>epoch,"No duplicate import result");ready();check(monitor.getHits()==1&&catalog().entries.size()==3&&catalog().engine.size()==210,"Duplicate import changed index coverage");}finally{removeMonitor(monitor);}
    }
    @Override public void onCreate(Bundle args){super.onCreate(args);start();}
    @Override public void onStart(){Bundle result=new Bundle();File catalogFile=new File(getTargetContext().getFilesDir(),"pack-library/catalog.json");byte[] original=null;
        try{
            root=new File(getTargetContext().getFilesDir(),"multi-pack-answer-tests");root.mkdirs();original=Files.readAllBytes(catalogFile.toPath());protocol=new JSONObject(new String(Files.readAllBytes(new File(root,"protocol.json").toPath()),StandardCharsets.UTF_8));report.put("rows",rows).put("links",new JSONArray()).put("pid",android.os.Process.myPid());save();
            sampling=true;sampler=new Thread(()->{try{while(sampling){sample();Thread.sleep(250);}}catch(InterruptedException done){}catch(Throwable e){sampleFailure=e;}},"answer-memory-samples");sampler.start();
            getUiAutomation();long t=System.nanoTime();activity=(MainActivity)startActivitySync(new Intent(getTargetContext(),MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TASK));ready();check(activity.modelReady(),"Pinned model not loaded");check(catalog().entries.size()==2&&catalog().engine.size()==210,"Expected two active pinned editions");
            report.put("startup_ready_ms",ms(t)).put("runtime",NativeRuntime.identity()).put("model",protocol.getJSONObject("model"));save();
            JSONArray cases=protocol.getJSONArray("cases");JSONObject reference=null;
            for(int i=0;i<6;i++){
                JSONObject c=cases.getJSONObject(i);String id=c.getString("id");if(id.equals("disabled-science"))select(false,false);if(id.equals("absent"))select(true,false);if(id.equals("duplicate"))importDuplicate();
                JSONObject row=answer(c);if(id.equals("reference"))reference=row;
                if(id.equals("cross-pack")){Set<String> editions=new HashSet<>();JSONArray hits=row.getJSONArray("retrieved");for(int j=0;j<hits.length();j++)editions.add(hits.getJSONObject(j).getString("id").split("_")[0]);check(editions.size()==2,"Cross-pack retrieval did not include both editions");}
                if(id.equals("disabled-science")){check(!row.getBoolean("invoked")&&row.getString("route").equals("ABSTAINED"),"Disabled science unexpectedly answered");check(!row.toString().contains("c69f31299553f4a1168eaa0400129fd5e41f21b4354248a0e2b97a87546ff274"),"Disabled edition leaked into answer evidence");}
                if(id.equals("absent"))check(!row.getBoolean("invoked")&&row.getString("route").equals("ABSTAINED"),"Absent fact not withheld");
                if(id.equals("duplicate")){check(row.getString("prompt").equals(reference.getString("prompt")),"Duplicate changed production prompt");report.put("duplicate_raw_equal",row.getString("raw").equals(reference.getString("raw")));select(true,false);}
            }
            phase="cancel-prefill";t=System.nanoTime();String q=protocol.getJSONObject("cancellation").getString("question");startQuery(q);await(()->NativeRuntime.operationState()[0]==4,"No actual native prefill reached");long[] observed=NativeRuntime.operationState();long cancel=System.nanoTime();click(panel(),"cancel");ready();JSONObject cancelled=record("cancel-prefill",q,t);check(cancelled.getString("route").equals("CANCELLED"),"Cancelled request published");report.put("cancellation",new JSONObject().put("observed_operation",new JSONArray(observed)).put("click_to_idle_ms",ms(cancel)));save();
            answer(cases.getJSONObject(6));phase="unload";click(panel(),"unload");ready();check(NativeRuntime.resourceState()[0]==0&&!activity.modelReady(),"Model lease survived unload");sample();
            phase="reload";t=System.nanoTime();click(panel(),"reload");ready();check(activity.modelReady()&&NativeRuntime.resourceState()[0]==1,"Reload failed");report.put("reload_ready_ms",ms(t));answer(cases.getJSONObject(7));
            JSONObject repair=new JSONObject(new String(Files.readAllBytes(new File(root,"link-repair-protocol.json").toPath()),StandardCharsets.UTF_8));
            for(int i=0;i<repair.getJSONArray("cases").length();i++)answer(repair.getJSONArray("cases").getJSONObject(i));
            check(report.getJSONArray("links").length()>0,"No generated answer available to exercise actual citation links");report.put("status","PASS");
        }catch(Throwable e){try{report.put("status","FAIL").put("failure",e.toString());}catch(Exception ignored){}result.putString("failure",e.toString());}
        finally{
            sampling=false;if(sampler!=null){sampler.interrupt();try{sampler.join(5000);}catch(Exception ignored){}}
            try{
                if(activity!=null){ready();runOnMainSync(activity::finish);}
                if(original!=null){File stage=new File(root,"restore-catalog.json");Files.write(stage.toPath(),original);Files.move(stage.toPath(),catalogFile.toPath(),StandardCopyOption.ATOMIC_MOVE,StandardCopyOption.REPLACE_EXISTING);new PackLibrary(getTargetContext().getFilesDir()).load();check(Arrays.equals(original,Files.readAllBytes(catalogFile.toPath())),"Catalog restore mismatch");report.put("catalog_restored",true);}
                if(sampleFailure!=null)report.put("status","FAIL").put("sampler_failure",sampleFailure.toString());save();
            }catch(Throwable e){try{report.put("status","FAIL").put("cleanup_failure",e.toString());save();}catch(Exception ignored){}result.putString("cleanup_failure",e.toString());}
        }
        finish(report.optString("status").equals("PASS")?-1:1,result);
    }
}
