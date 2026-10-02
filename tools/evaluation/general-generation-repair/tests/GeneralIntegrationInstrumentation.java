package org.pocketlore.app;
import android.app.*;import android.os.*;import android.content.*;import android.widget.*;import java.io.*;import java.nio.file.*;import org.json.*;
public final class GeneralIntegrationInstrumentation extends Instrumentation {
 String run,source;public void onCreate(Bundle b){run=b.getString("run_id");source=b.getString("source_hash");start();}
 static Object field(Object o,String n)throws Exception{java.lang.reflect.Field f=o.getClass().getDeclaredField(n);f.setAccessible(true);return f.get(o);}
 public void onStart(){Bundle result=new Bundle();try{
 MainActivity a=(MainActivity)startActivitySync(new Intent(getTargetContext(),MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));long end=SystemClock.elapsedRealtime()+30000;
 while((field(a,"engine")==null||!a.resourceIdle())&&SystemClock.elapsedRealtime()<end)Thread.sleep(50);
 if(field(a,"engine")==null||!a.resourceIdle())throw new AssertionError("App startup not ready");
 runOnMainSync(()->{try{((EditText)field(a,"question")).setText("Compare mulch and crop rotation");((Button)field(a,"search")).performClick();}catch(Exception e){throw new RuntimeException(e);}});
 end=SystemClock.elapsedRealtime()+30000;while(a.latestAnswer()==null&&SystemClock.elapsedRealtime()<end)Thread.sleep(50);
 AnswerEngine.Outcome o=a.latestAnswer();if(o==null||o.kind!=AnswerEngine.Kind.ABSTAINED||o.invokedModel||!o.text.contains("independent whole-answer support verification"))throw new AssertionError("Missing fail-closed general path");
 File dir=new File(getTargetContext().getFilesDir(),"general-generation-repair/"+run);dir.mkdirs();org.json.JSONObject report=new JSONObject().put("run_id",run).put("source_hash",source).put("status","PASS").put("scope","Actual API37 research control reaches general unavailable-verifier route; no model inference or selected-model proof").put("kind",o.kind.name()).put("invoked_model",o.invokedModel).put("visible_text",o.text).put("api",Build.VERSION.SDK_INT);
 Files.writeString(new File(dir,"report.json").toPath(),report.toString(2));try(OutputStream out=new FileOutputStream(new File(dir,"screen.png"))){if(!getUiAutomation().takeScreenshot().compress(android.graphics.Bitmap.CompressFormat.PNG,100,out))throw new AssertionError("screenshot");}
 result.putString("status","PASS");finish(-1,result);
 }catch(Throwable e){result.putString("failure",e.toString());finish(1,result);}}
}
