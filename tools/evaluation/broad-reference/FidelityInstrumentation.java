package org.pocketlore.app;
import android.app.*;import android.content.*;import android.os.*;import android.widget.*;import android.view.accessibility.AccessibilityNodeInfo;import java.io.*;import java.nio.file.*;import java.nio.charset.StandardCharsets;import org.json.*;
/** Actual source dialogs for the critic's missing-formula and missing-unit cases. */
public final class FidelityInstrumentation extends Instrumentation {
 MainActivity activity;File root;JSONObject report=new JSONObject();
 Object field(Object o,String n){try{java.lang.reflect.Field f=o.getClass().getDeclaredField(n);f.setAccessible(true);return f.get(o);}catch(Exception e){throw new RuntimeException(e);}}
 void check(boolean b,String m){if(!b)throw new AssertionError(m);}
 void await(java.util.function.BooleanSupplier f)throws Exception{long end=System.nanoTime()+60_000_000_000L;while(!f.getAsBoolean()&&System.nanoTime()<end)Thread.sleep(20);check(f.getAsBoolean(),"UI timeout");}
 void ready()throws Exception{await(()->{boolean[] b={false};runOnMainSync(()->b[0]=!(Boolean)field(activity,"searching")&&!(Boolean)field(activity,"importing")&&activity.resourceIdle());return b[0];});}
 String visible(AccessibilityNodeInfo n){if(n==null)return "";String s=n.getText()==null?"":n.getText()+"\n";for(int i=0;i<n.getChildCount();i++)s+=visible(n.getChild(i));return s;}
 @Override public void onCreate(Bundle b){super.onCreate(b);start();}
 @Override public void onStart(){Bundle result=new Bundle();try{
  root=new File(getTargetContext().getFilesDir(),"broad-tests");getUiAutomation();activity=(MainActivity)startActivitySync(new Intent(getTargetContext(),MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TASK));ready();
  runOnMainSync(()->((Button)field(field(activity,"nativePanel"),"unload")).performClick());ready();JSONArray fixtures=new JSONObject(new String(Files.readAllBytes(new File(root,"fidelity.json").toPath()),StandardCharsets.UTF_8)).getJSONArray("cases"),rows=new JSONArray();
  for(int i=0;i<fixtures.length();i++){
   JSONObject test=fixtures.getJSONObject(i);String q=test.getString("question"),expected=test.getString("citation"),body=test.getString("text");runOnMainSync(()->{((EditText)field(activity,"question")).setText(q);((Button)field(activity,"search")).performClick();});ready();ResearchEngine.Result evidence=(ResearchEngine.Result)field(activity,"latestEvidence");int found=-1;for(int j=0;j<evidence.hits.size();j++)if(evidence.hits.get(j).passage.id.equals(expected))found=j;check(found>=0,"Expected fidelity passage absent: "+q);final int ix=found;runOnMainSync(()->((LinearLayout)field(activity,"sourceList")).getChildAt(ix).performClick());await(()->visible(getUiAutomation().getRootInActiveWindow()).contains(body));String v=visible(getUiAutomation().getRootInActiveWindow());check(v.contains(expected)&&v.contains(test.getString("required")),"Source fidelity not visible");Thread.sleep(400);android.graphics.Bitmap bitmap=getUiAutomation().takeScreenshot();String name="fidelity-"+i+".png";try(FileOutputStream out=new FileOutputStream(new File(root,name))){bitmap.compress(android.graphics.Bitmap.CompressFormat.PNG,100,out);}bitmap.recycle();rows.put(new JSONObject().put("question",q).put("citation",expected).put("visible",v).put("route",activity.latestAnswer().kind.name()).put("invoked",activity.latestAnswer().invokedModel).put("screenshot",name));getUiAutomation().performGlobalAction(android.accessibilityservice.AccessibilityService.GLOBAL_ACTION_BACK);Thread.sleep(200);
  }
  report.put("cases",rows).put("status","PASS");
 }catch(Throwable e){try{report.put("status","FAIL").put("failure",e.toString());}catch(Exception ignored){}result.putString("failure",e.toString());}
 finally{try{if(activity!=null){ready();runOnMainSync(activity::finish);}Files.write(new File(root,"fidelity-result.json").toPath(),report.toString(2).getBytes(StandardCharsets.UTF_8));}catch(Exception e){result.putString("cleanup",e.toString());}}
 finish(report.optString("status").equals("PASS")?-1:1,result);
 }
}
