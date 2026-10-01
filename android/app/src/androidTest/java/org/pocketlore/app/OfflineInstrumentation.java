package org.pocketlore.app;

import android.app.*;
import android.content.*;
import android.content.pm.PackageManager;
import android.os.*;
import android.provider.Settings;
import android.view.*;
import android.widget.*;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.atomic.AtomicReference;
import java.util.function.BooleanSupplier;
import org.json.*;

/** Offline lifecycle checks require actual JNI invocation, not an answer-quality verdict. */
public final class OfflineInstrumentation extends Instrumentation {
    MainActivity activity;String mode;final JSONObject report=new JSONObject();final JSONArray checks=new JSONArray(),cases=new JSONArray();
    @Override public void onCreate(Bundle args){super.onCreate(args);mode=args.getString("mode","loaded");start();}
    void ok(boolean value,String name){if(!value)throw new AssertionError(name);checks.put(name);}
    View find(View v,String name){if(name.contentEquals(v.getContentDescription()==null?"":v.getContentDescription())||v instanceof TextView&&name.contentEquals(((TextView)v).getText()))return v;if(v instanceof ViewGroup){ViewGroup g=(ViewGroup)v;for(int i=0;i<g.getChildCount();i++){View r=find(g.getChildAt(i),name);if(r!=null)return r;}}return null;}
    View view(String name){View v=find(activity.getWindow().getDecorView(),name);if(v==null)throw new AssertionError("Missing UI: "+name);return v;}
    void await(BooleanSupplier condition,String label)throws Exception{long end=SystemClock.elapsedRealtime()+90000;while(SystemClock.elapsedRealtime()<end){AtomicReference<Boolean> done=new AtomicReference<>(false);runOnMainSync(()->done.set(condition.getAsBoolean()));if(done.get())return;Thread.sleep(50);}throw new AssertionError("Timed out: "+label);}
    void ask(String q){runOnMainSync(()->{((EditText)view("Research question")).setText(q);view("Answer offline").performClick();});}
    View source(View v){if(v instanceof Button&&((Button)v).getText().toString().startsWith("Inspect ["))return v;if(v instanceof ViewGroup){ViewGroup g=(ViewGroup)v;for(int i=0;i<g.getChildCount();i++){View r=source(g.getChildAt(i));if(r!=null)return r;}}return null;}
    JSONObject describe(String q,AnswerEngine.Outcome a)throws Exception{return new JSONObject().put("question",q).put("kind",a.kind.toString()).put("invoked_model",a.invokedModel).put("tokens",a.tokens).put("raw_draft",a.rawDraft).put("text",a.text).put("prompt",a.prompt).put("reason",a.reason).put("total_ms",a.totalMs).put("first_token_ms",a.firstTokenMs);}
    @Override public void onStart(){Bundle result=new Bundle();long start=SystemClock.elapsedRealtime();try{
        Context c=getTargetContext();File dir=c.getFilesDir();report.put("mode",mode).put("environment","AOSP x86_64 emulator; no physical/GrapheneOS acceptance").put("runtime",NativeRuntime.identity());
        ok(Settings.Global.getInt(c.getContentResolver(),Settings.Global.AIRPLANE_MODE_ON,0)==1,"airplane_mode_on");
        ok(c.checkSelfPermission("android.permission.INTERNET")==PackageManager.PERMISSION_DENIED,"internet_permission_denied");
        boolean denied=false;String denial="";try(Socket socket=new Socket()){socket.connect(new InetSocketAddress(InetAddress.getByAddress(new byte[]{127,0,0,1}),9),1000);}catch(SecurityException e){denied=true;denial=e.toString();}catch(SocketException e){denial=e.toString();denied=denial.contains("EPERM")||denial.contains("EACCES")||denial.toLowerCase(java.util.Locale.ROOT).contains("permission");}report.put("socket_probe",denial);ok(denied,"socket_denied_by_application_uid");
        if(mode.equals("fresh"))ok(!new File(dir,"model.gguf").exists()&&!new File(dir,"knowledge.plpack").exists(),"no_restored_model_or_pack");
        activity=(MainActivity)startActivitySync(new Intent(c,MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TASK));
        await(()->view("Answer offline").isEnabled()&&(mode.equals("fresh")||activity.modelReady()),"initial state");
        if(mode.equals("fresh")){
            ask("Compare evaporation and condensation");await(()->activity.latestAnswer()!=null,"no-model answer");AnswerEngine.Outcome a=activity.latestAnswer();cases.put(describe("Compare evaporation and condensation",a));ok(a.kind==AnswerEngine.Kind.FALLBACK&&!a.invokedModel,"fresh_no_model_labeled_fallback");
        }else{
            String[] queries={"Compare evaporation and condensation","What is groundwater?","quasar supernova","Does evaporation cure diabetes?"};
            for(int i=0;i<queries.length;i++){ask(queries[i]);await(()->activity.latestAnswer()!=null,"offline answer");AnswerEngine.Outcome a=activity.latestAnswer();cases.put(describe(queries[i],a));if(i<2)ok(a.invokedModel&&a.tokens>0&&!a.rawDraft.isEmpty()&&(a.kind==AnswerEngine.Kind.GENERATED||a.kind==AnswerEngine.Kind.FALLBACK),"real_offline_inference_"+i);else ok(a.kind==AnswerEngine.Kind.ABSTAINED&&!a.invokedModel,"unsupported_abstention_"+i);}
            ask(queries[0]);await(()->((TextView)view("Answer status")).getText().toString().contains("Citation checks pending"),"streamed token");long cancel=SystemClock.elapsedRealtime();runOnMainSync(()->view("Cancel current operation").performClick());await(()->activity.latestAnswer()!=null,"cancellation");ok(activity.latestAnswer().kind==AnswerEngine.Kind.CANCELLED,"cancel_discards_real_partial_draft");report.put("cancel_ms",SystemClock.elapsedRealtime()-cancel);
            ask(queries[0]);await(()->((TextView)view("Answer status")).getText().toString().contains("Citation checks pending"),"stream before recreation");ActivityMonitor monitor=addMonitor(MainActivity.class.getName(),null,false);runOnMainSync(activity::recreate);Activity recreated=waitForMonitorWithTimeout(monitor,30000);removeMonitor(monitor);ok(recreated instanceof MainActivity,"activity_recreated");activity=(MainActivity)recreated;await(()->activity.modelReady()&&view("Answer offline").isEnabled(),"reload after recreation");ok(activity.latestAnswer()==null,"recreation_discards_prior_draft");ask(queries[0]);await(()->activity.latestAnswer()!=null,"generation after recreation");ok(activity.latestAnswer().invokedModel,"inference_after_recreation");
        }
        runOnMainSync(()->{View button=source(activity.getWindow().getDecorView());if(button==null)throw new AssertionError("No source button");button.performClick();});waitForIdleSync();ok(true,"source_dialog_opened");
        report.put("status","PASS");
    }catch(Throwable error){try{report.put("status","FAIL").put("error",android.util.Log.getStackTraceString(error));}catch(Exception ignored){}}
    finally{try{report.put("checks",checks).put("cases",cases).put("elapsed_ms",SystemClock.elapsedRealtime()-start);try(FileOutputStream out=new FileOutputStream(new File(getTargetContext().getFilesDir(),"offline-result.json"))){out.write(report.toString(2).getBytes(StandardCharsets.UTF_8));}result.putString("report",report.toString());}catch(Exception e){result.putString("error",e.toString());}finish(report.optString("status").equals("PASS")?-1:1,result);}}
}
