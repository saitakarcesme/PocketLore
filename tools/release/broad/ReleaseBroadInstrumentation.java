package org.pocketlore.app;
import android.app.*;import android.content.*;import android.os.*;import android.widget.*;import android.view.accessibility.AccessibilityNodeInfo;import java.io.*;import java.nio.file.*;import java.nio.charset.StandardCharsets;import java.util.*;import org.json.*;
/** Supplemental actual source-button check; no model generation and no generated-link credit. */
public final class ReleaseBroadInstrumentation extends Instrumentation {
 static Object reflect(Object o,String n){try{java.lang.reflect.Field f=o.getClass().getDeclaredField(n);f.setAccessible(true);return f.get(o);}catch(Exception e){throw new RuntimeException(e);}}
 long opened; String mode; MainActivity a;File root;JSONObject report=new JSONObject();JSONArray dialogs=new JSONArray();
 Object field(Object o,String n){return reflect(o,n);}void check(boolean b,String m){if(!b)throw new AssertionError(m);}
 void await(java.util.function.BooleanSupplier f)throws Exception{long end=System.nanoTime()+180_000_000_000L;while(!f.getAsBoolean()&&System.nanoTime()<end)Thread.sleep(20);check(f.getAsBoolean(),"UI timeout");}
 void ready()throws Exception{waitForIdleSync();await(()->{boolean[] b={false};runOnMainSync(()->b[0]=!(Boolean)field(a,"searching")&&!(Boolean)field(a,"importing")&&a.resourceIdle());return b[0];});}
 void click(Object o,String n){runOnMainSync(()->{Button b=(Button)field(o,n);check(b.isEnabled(),"Disabled "+n);b.performClick();});}
 String visible(AccessibilityNodeInfo n){if(n==null)return "";String s=n.getText()==null?"":n.getText()+"\n";for(int i=0;i<n.getChildCount();i++)s+=visible(n.getChild(i));return s;}
 boolean tap(AccessibilityNodeInfo n,String label){if(n==null)return false;if(n.getText()!=null&&n.getText().toString().equalsIgnoreCase(label)){while(n!=null){if(n.isClickable())return n.performAction(AccessibilityNodeInfo.ACTION_CLICK);n=n.getParent();}return false;}for(int i=0;i<n.getChildCount();i++)if(tap(n.getChild(i),label))return true;return false;}
 void tap(String s)throws Exception{await(()->visible(getUiAutomation().getRootInActiveWindow()).toLowerCase(Locale.ROOT).contains(s.toLowerCase(Locale.ROOT)));check(tap(getUiAutomation().getRootInActiveWindow(),s),"Cannot click "+s);getUiAutomation().waitForIdle(100,3000);}
 void search(String question,boolean disabled)throws Exception{
  runOnMainSync(()->((EditText)field(a,"question")).setText(question));click(a,"search");ready();check(!a.latestAnswer().invokedModel,"Unexpected model invocation");ResearchEngine.Result r=(ResearchEngine.Result)field(a,"latestEvidence");Set<String> editions=new HashSet<>();
  for(int i=0;i<r.hits.size();i++){ResearchEngine.Passage p=r.hits.get(i).passage;editions.add(p.id.split("_")[0]);if(disabled)check(!p.id.contains("c69f31299553f4a1168eaa0400129fd5e41f21b4354248a0e2b97a87546ff274"),"Disabled source leaked");final int j=i;runOnMainSync(()->((LinearLayout)field(a,"sourceList")).getChildAt(j).performClick());await(()->visible(getUiAutomation().getRootInActiveWindow()).contains(p.text));String text=visible(getUiAutomation().getRootInActiveWindow());check(text.contains(p.id)&&text.contains(p.url)&&text.contains(p.sourceDate)&&text.contains(p.license)&&text.contains(p.collectionProvenance),"Dialog provenance mismatch");String name=dialogs.length()+"-"+(disabled?"disabled-":"combined-")+i;android.graphics.Bitmap image=getUiAutomation().takeScreenshot();check(image!=null,"No screenshot");try(FileOutputStream out=new FileOutputStream(new File(root,name+".png"))){image.compress(android.graphics.Bitmap.CompressFormat.PNG,100,out);}image.recycle();dialogs.put(new JSONObject().put("file",name+".png").put("citation",p.id).put("disabled_science",disabled).put("visible",text).put("route",a.latestAnswer().kind.name()).put("invoked",false));if(p.id.startsWith("pb8d188")){tap("License");String legal=visible(getUiAutomation().getRootInActiveWindow());check(legal.contains("Attribution")||legal.contains("Creative Commons"),"Offline license missing");report.put("broad_license_visible",legal);tap("Close");}else tap("Close");}
  check(!editions.isEmpty(),"No inspected source");
 }
 @Override public void onCreate(Bundle b){super.onCreate(b);mode=b.getString("mode","fresh");start();}
 @Override public void onStart(){Bundle b=new Bundle();try{
  opened=SystemClock.elapsedRealtime();root=new File(getTargetContext().getFilesDir(),"release-tests");root.mkdirs();getUiAutomation();a=(MainActivity)startActivitySync(new Intent(getTargetContext(),MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TASK));ready();report.put("opening_ms",SystemClock.elapsedRealtime()-opened);Debug.MemoryInfo memory=new Debug.MemoryInfo();Debug.getMemoryInfo(memory);report.put("opening_pss_kib",memory.getTotalPss());report.put("pid",android.os.Process.myPid()).put("mode",mode);
  File saved=new File(getTargetContext().getFilesDir(),"model.gguf");PackLibrary.Snapshot cat=(PackLibrary.Snapshot)field(a,"catalog");
  if(mode.equals("fresh")){
   check(!saved.exists()&&!a.modelReady(),"Restored model in fresh install");check(cat.entries.isEmpty(),"Restored catalog in fresh install");report.put("empty_model_and_catalog",true);
  }else{
   check(a.modelReady()&&saved.length()==491400032L,"Saved model not loaded");check(cat.entries.size()==3,"Expected both retained editions");
   if(mode.equals("disabled")){
    check(cat.engine.size()==210&&cat.entries.stream().filter(e->e.active).count()==2,"Disabled selection not persistent");for(ResearchEngine.Hit h:cat.engine.research("Acid").hits)check(!h.passage.id.startsWith("pb8d188"),"Disabled broad leaked");report.put("disabled_persisted",true);
    click(a,"collections");tap("broad reference rendered 20261001 v2 · edition b8d18801");tap("Apply");ready();
   }else{
    check(cat.engine.size()==40891&&cat.distinctDocuments==1113&&cat.entries.stream().allMatch(e->e.active),"Combined selection not persistent");
    runOnMainSync(()->((EditText)field(a,"question")).setText("Why are headlamps recommended for lighting at night?"));click(a,"search");ready();AnswerEngine.Outcome o=a.latestAnswer();check(o.invokedModel&&o.tokens>0,"No real JNI answer");report.put("answer",new JSONObject().put("question","Why are headlamps recommended for lighting at night?").put("route",o.kind.name()).put("raw",o.rawDraft).put("text",o.text).put("prompt",o.prompt).put("tokens",o.tokens).put("first_token_ms",o.firstTokenMs).put("total_ms",o.totalMs));
    check(o.kind==AnswerEngine.Kind.GENERATED,"Generated navigation requires published model output");android.text.Spanned rendered=(android.text.Spanned)((TextView)field(a,"answer")).getText();android.text.style.ClickableSpan[] spans=rendered.getSpans(0,rendered.length(),android.text.style.ClickableSpan.class);check(spans.length>0,"No rendered citation spans");runOnMainSync(()->spans[0].onClick((TextView)field(a,"answer")));await(()->visible(getUiAutomation().getRootInActiveWindow()).contains("hands-free"));String linked=visible(getUiAutomation().getRootInActiveWindow());check(linked.contains(o.citedIds.iterator().next()),"Wrong citation target");report.put("generated_navigation",new JSONObject().put("visible",linked).put("citation",o.citedIds.iterator().next()).put("span_count",spans.length));tap("Close");
    // Source buttons are independent of generation acceptance, and are labeled as such.
    click(field(a,"nativePanel"),"unload");ready();search("magma lava",false);search("Acid",false);
    if(mode.equals("combined")){click(a,"collections");tap("broad reference rendered 20261001 v2 · edition b8d18801");tap("Apply");ready();}
   }
   cat=(PackLibrary.Snapshot)field(a,"catalog");report.put("collections",cat.entries.size()).put("passages",cat.engine.size()).put("documents",cat.distinctDocuments).put("saved_model_bytes",saved.length());
  }
  Debug.MemoryInfo endMemory=new Debug.MemoryInfo();Debug.getMemoryInfo(endMemory);report.put("end_pss_kib",endMemory.getTotalPss()).put("proc_status",new String(Files.readAllBytes(new File("/proc/self/status").toPath()),StandardCharsets.UTF_8));report.put("status","PASS");
 }catch(Throwable e){try{report.put("status","FAIL").put("failure",e.toString());}catch(Exception ignored){}b.putString("failure",e.toString());}
 finally{try{if(a!=null){ready();runOnMainSync(a::finish);}report.put("dialogs",dialogs);Files.write(new File(root,mode+".json").toPath(),report.toString(2).getBytes(StandardCharsets.UTF_8));}catch(Throwable e){try{report.put("status","FAIL");}catch(Exception ignored){}b.putString("cleanup_failure",e.toString());}}
 finish(report.optString("status").equals("PASS")?-1:1,b);
 }
}
