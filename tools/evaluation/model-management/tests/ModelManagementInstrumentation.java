package org.pocketlore.app;
import android.app.*;import android.content.*;import android.net.Uri;import android.os.*;import android.view.*;import android.widget.*;import java.io.*;import java.nio.charset.StandardCharsets;import java.nio.file.*;import java.util.concurrent.atomic.*;import java.util.function.BooleanSupplier;import org.json.*;
/** Public model-management transport/resource fixtures; no answer quality scoring. */
public final class ModelManagementInstrumentation extends Instrumentation {
 String mode;MainActivity app;NativePanel panel;JSONArray checks=new JSONArray();JSONObject report=new JSONObject();
 public void onCreate(Bundle b){super.onCreate(b);mode=b.getString("mode","import");start();}
 void ok(boolean b,String s){if(!b)throw new AssertionError(s);checks.put(s);}
 void await(BooleanSupplier b)throws Exception{long end=SystemClock.elapsedRealtime()+120000;while(SystemClock.elapsedRealtime()<end){AtomicBoolean ready=new AtomicBoolean();runOnMainSync(()->ready.set(b.getAsBoolean()));if(ready.get())return;Thread.sleep(50);}throw new AssertionError("Timed out waiting for model operation");}
 View find(View v,String s){if(v instanceof TextView&&s.contentEquals(((TextView)v).getText()))return v;if(v instanceof ViewGroup)for(int i=0;i<((ViewGroup)v).getChildCount();i++){View f=find(((ViewGroup)v).getChildAt(i),s);if(f!=null)return f;}return null;}
 void click(String s){runOnMainSync(()->{View v=find(app.getWindow().getDecorView(),s);if(v==null)throw new AssertionError("Missing "+s);v.performClick();});}
 TextView state()throws Exception{java.lang.reflect.Field f=NativePanel.class.getDeclaredField("state");f.setAccessible(true);return (TextView)f.get(panel);}
 public void onStart(){Bundle out=new Bundle();try{
  File files=getTargetContext().getFilesDir();ModelCatalog lib=new ModelCatalog(files);String before=BroadPack.hash(lib.active);ok(before.equals(ModelCatalog.SPECS[0].hash),"Demo baseline begins selected");
  app=(MainActivity)startActivitySync(new Intent(getTargetContext(),MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));java.lang.reflect.Field field=MainActivity.class.getDeclaredField("nativePanel");field.setAccessible(true);panel=(NativePanel)field.get(app);await(()->!panel.isBusy());ok(panel.hasModel(),"Actual saved JNI model loads");runOnMainSync(app::showSettings);
  ok(find(app.getWindow().getDecorView(),"Model catalog and selection")!=null,"Catalog control is reachable");
  report.put("mode",mode).put("runtime",NativeRuntime.identity());
  if(mode.equals("import")){
   boolean rejected=false;try{ModelCatalog.identify("0".repeat(64),ModelCatalog.SPECS[0].bytes);}catch(IOException e){rejected=true;}ok(rejected,"Changed identity rejected");
   rejected=false;try{ModelCatalog.admit(ModelCatalog.HARD-100,1000,Long.MAX_VALUE);}catch(IOException e){rejected=true;}ok(rejected,"Hard joint budget rejects transaction");ok(ModelCatalog.admit(ModelCatalog.TARGET,0,Long.MAX_VALUE)>ModelCatalog.TARGET,"Target exceedance is distinct from hard cap");
   File stage=new File(files,"model.partial");try{ModelImport.copy(new ByteArrayInputStream("GGUF".getBytes()),stage,4,Long.MAX_VALUE,()->true);throw new AssertionError("Cancellation accepted");}catch(InterruptedIOException expected){}ok(!stage.exists(),"Cancelled stage removed");
   // Drive the existing import operation with the actual local-provider bytes; UI picker is Android-owned.
   java.lang.reflect.Method method=NativePanel.class.getDeclaredMethod("importModel",Uri.class,long.class);method.setAccessible(true);
   runOnMainSync(()->{try{method.invoke(panel,Uri.parse("content://org.pocketlore.fixture.model/baseline"),ModelCatalog.SPECS[0].bytes);}catch(Exception e){throw new RuntimeException(e);}});await(()->!panel.isBusy());
   ok(panel.hasModel()&&state().getText().toString().startsWith("Selected:"),"Pinned provider import loads before selection");ok(BroadPack.hash(lib.active).equals(before),"Import retains exact baseline identity");ok(Files.isSameFile(lib.active.toPath(),lib.object(ModelCatalog.SPECS[0]).toPath()),"Active selection uses retained object without duplicate bytes");
  }else{
   long start=SystemClock.elapsedRealtime();runOnMainSync(()->panel.selectInstalled(ModelCatalog.SPECS[1]));await(()->!panel.isBusy());report.put("optional_load_ms",SystemClock.elapsedRealtime()-start).put("optional_state",state().getText());
   ok(panel.hasModel()&&BroadPack.hash(lib.active).equals(ModelCatalog.SPECS[1].hash),"Optional pinned model actually loads and becomes selected");report.put("native_resources",new JSONArray(NativeRuntime.resourceState()));
   // One bounded token verifies the newly selected model can execute; not a supported answer or quality score.
   java.lang.reflect.Field sf=NativePanel.class.getDeclaredField("session");sf.setAccessible(true);long session=sf.getLong(panel);ByteArrayOutputStream tokens=new ByteArrayOutputStream();NativeRuntime.reset(session);int count=NativeRuntime.generateChat(session,"Answer briefly.".getBytes(StandardCharsets.UTF_8),"Hello".getBytes(StandardCharsets.UTF_8),1,b->{try{tokens.write(b);}catch(IOException e){throw new RuntimeException(e);}});ok(count>=0,"Selected JNI performs bounded token execution");report.put("unverified_token_output",tokens.toString("UTF-8"));
   runOnMainSync(()->panel.selectInstalled(ModelCatalog.SPECS[0]));await(()->!panel.isBusy());ok(panel.hasModel()&&BroadPack.hash(lib.active).equals(before),"Baseline reselection restores native model and identity");
   // A missing catalog object is a real failed selection: current alias and native capability must survive.
   runOnMainSync(()->panel.selectInstalled(ModelCatalog.SPECS[2]));await(()->!panel.isBusy());ok(panel.hasModel()&&BroadPack.hash(lib.active).equals(before)&&state().getText().toString().contains("failed"),"Failed selection reloads previous model without alias mutation");
   lib.remove(ModelCatalog.SPECS[1]);ok(!lib.object(ModelCatalog.SPECS[1]).exists(),"Inactive model deletion works");
  }
  report.put("app_data_unique_bytes",SharedShardUpdate.uniqueBytes(new File(getTargetContext().getApplicationInfo().dataDir)));android.os.Debug.MemoryInfo memory=new android.os.Debug.MemoryInfo();android.os.Debug.getMemoryInfo(memory);report.put("pss_kib",memory.getTotalPss());ok(BroadPack.hash(lib.active).equals(before),"Final saved model identity preserved");report.put("status","PASS");
 }catch(Throwable e){try{report.put("status","FAIL").put("error",android.util.Log.getStackTraceString(e));}catch(Exception ignored){}}
 finally{if(app!=null){runOnMainSync(app::finish);waitForIdleSync();}try{report.put("checks",checks);File f=new File(getTargetContext().getFilesDir(),"model-management-"+mode+".json");Files.write(f.toPath(),report.toString(2).getBytes(StandardCharsets.UTF_8));out.putString("report",report.toString());}catch(Exception e){out.putString("error",e.toString());}finish(report.optString("status").equals("PASS")?-1:1,out);}}
}
