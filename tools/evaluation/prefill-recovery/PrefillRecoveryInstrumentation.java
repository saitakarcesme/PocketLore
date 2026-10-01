package org.pocketlore.app;

import android.app.Instrumentation;
import android.os.Bundle;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;
import org.json.*;

/** Actual JNI lifecycle tests. Diagnostics observe execution; no artificial native pause or failure injection. */
public final class PrefillRecoveryInstrumentation extends Instrumentation {
    private String mode;private File dir,model;private JSONObject report=new JSONObject();
    private final ExecutorService worker=Executors.newSingleThreadExecutor();
    private long session;private MainActivity activity;
    static byte[] bytes(String x){return x.getBytes(StandardCharsets.UTF_8);}
    static double ms(long start){return (System.nanoTime()-start)/1e6;}
    static void check(boolean b,String why){if(!b)throw new AssertionError(why);}
    void save()throws Exception{Files.write(new File(dir,mode+".json").toPath(),bytes(report.toString(2)));}
    long[] awaitPhase(int wanted,int counter,Future<?> work)throws Exception{
        long deadline=System.nanoTime()+TimeUnit.SECONDS.toNanos(20);
        while(System.nanoTime()<deadline){long[] s=NativeRuntime.operationState();if(s[0]==wanted&&s[counter]>0&&!work.isDone())return s;if(work.isDone())throw new AssertionError("Operation ended before phase "+wanted+": "+work.get());Thread.sleep(1);}
        throw new AssertionError("Phase "+wanted+" not observed");
    }
    void load()throws Exception{session=NativeRuntime.create();long start=System.nanoTime();NativeRuntime.load(session,bytes(model.getAbsolutePath()));report.put("load_ms",ms(start)).put("after_load",new JSONArray(NativeRuntime.operationState()));}
    JSONObject generateAfterRecovery()throws Exception{
        NativeRuntime.reset(session);StringBuilder raw=new StringBuilder();long start=System.nanoTime();int n=NativeRuntime.generate(session,bytes("Water is"),8,b->raw.append(new String(b,StandardCharsets.UTF_8)));
        check(n>0&&raw.length()>0,"No real generation after recovery");check(NativeRuntime.resourceState()[1]==0,"Context remained after recovery generation");
        return new JSONObject().put("tokens",n).put("raw_output",raw.toString()).put("elapsed_ms",ms(start));
    }
    @Override public void onCreate(Bundle args){super.onCreate(args);mode=args.getString("mode","lifecycle");start();}
    @Override public void onStart(){Bundle output=new Bundle();
        try{
            File root=getTargetContext().getFilesDir();dir=new File(root,"prefill-recovery-tests");dir.mkdirs();model=new File(root,"model.gguf");
            JSONObject spec=new JSONObject(new String(Files.readAllBytes(new File(dir,"cases.json").toPath()),StandardCharsets.UTF_8));
            report.put("pid",android.os.Process.myPid()).put("mode",mode).put("runtime",NativeRuntime.identity()).put("initial_resources",new JSONArray(NativeRuntime.resourceState()));
            check(NativeRuntime.resourceState()[0]==0&&NativeRuntime.resourceState()[1]==0,"Native state survived prior process/session");
            String prompt=spec.getString("prompt").repeat(spec.getInt("prompt_repetitions"));report.put("prompt",prompt);save();
            if(mode.equals("restart")){
                activity=(MainActivity)startActivitySync(new android.content.Intent(getTargetContext(),MainActivity.class).addFlags(android.content.Intent.FLAG_ACTIVITY_NEW_TASK));
                long end=System.nanoTime()+TimeUnit.SECONDS.toNanos(20);while(!activity.modelReady()&&System.nanoTime()<end)Thread.sleep(10);check(activity.modelReady(),"Saved model not ready after restart");
                end=System.nanoTime()+TimeUnit.SECONDS.toNanos(10);while(new File(root,"pack-140000.partial").exists()&&System.nanoTime()<end)Thread.sleep(10);
                check(!new File(root,"model.partial").exists()&&!new File(root,"pack-140000.partial").exists(),"Orphan stages not cleaned");
                check(new String(Files.readAllBytes(new File(root,"prefill-notes.partial").toPath()),StandardCharsets.UTF_8).equals("unrelated fixture retained"),"Unrelated file changed");
                report.put("activity_saved_model_ready",true).put("orphan_stages_removed",true).put("unrelated_preserved",true);
                // Release the Activity's model before exercising a fresh direct session in this process.
                runOnMainSync(activity::releaseForMemoryPressure);end=System.nanoTime()+TimeUnit.SECONDS.toNanos(10);while(NativeRuntime.resourceState()[0]!=0&&System.nanoTime()<end)Thread.sleep(5);
                check(NativeRuntime.resourceState()[0]==0,"Activity did not release session");load();report.put("restart_generation",generateAfterRecovery());
            }else{
                load();AtomicInteger callbacks=new AtomicInteger();long id=session;long prefillStart=System.nanoTime();
                Future<Integer> generating=worker.submit(()->NativeRuntime.generate(id,bytes(prompt),spec.getInt("max_output_tokens"),b->callbacks.incrementAndGet()));
                long[] observed=awaitPhase(4,2,generating);check(callbacks.get()==0&&observed[3]>=1700,"Did not observe long prefill before first token");
                report.put("prefill_observed",new JSONArray(observed)).put("prefill_observation_ms",ms(prefillStart)).put("token_callbacks_before_cancel",callbacks.get());
                if(mode.equals("kill-ready")){
                    for(String name:new String[]{"model.partial","pack-140000.partial"}){File f=new File(root,name);check(!f.exists(),"Refuse to overwrite preexisting stage");Files.write(f.toPath(),bytes("seeded interrupted-import stage"),StandardOpenOption.CREATE_NEW);}
                    Files.write(new File(root,"prefill-notes.partial").toPath(),bytes("unrelated fixture retained"));
                    report.put("status","READY_FOR_SIGKILL");save();
                    generating.get(120,TimeUnit.SECONDS);throw new AssertionError("Host did not kill during prefill");
                }
                long start=System.nanoTime();NativeRuntime.cancel(session);int result=generating.get(5,TimeUnit.SECONDS);double cancelMs=ms(start);
                report.put("prefill_cancel_ms",cancelMs).put("prefill_result",result).put("token_callbacks_after_cancel",callbacks.get()).put("resources_after_cancel",new JSONArray(NativeRuntime.resourceState()));
                check(result==-1&&callbacks.get()==0&&cancelMs<spec.getDouble("cancel_deadline_ms")&&NativeRuntime.resourceState()[1]==0,"Prefill cancellation failed");
                report.put("reuse_after_prefill",generateAfterRecovery());NativeRuntime.close(session);session=0;
                // Close only after the real weight loader's progress callback has run, before load returns.
                session=NativeRuntime.create();long loadingId=session;Future<String> loading=worker.submit(()->{try{NativeRuntime.load(loadingId,bytes(model.getAbsolutePath()));return "loaded";}catch(IllegalStateException e){return e.getMessage();}});
                long[] loadObserved=awaitPhase(2,1,loading);report.put("load_observed",new JSONArray(loadObserved));start=System.nanoTime();NativeRuntime.close(session);session=0;
                String closed=loading.get(5,TimeUnit.SECONDS);double closeMs=ms(start);report.put("close_load_ms",closeMs).put("closed_load_result",closed).put("resources_after_close_load",new JSONArray(NativeRuntime.resourceState()));
                check(closed.equals("Cancelled")&&closeMs<5000&&NativeRuntime.resourceState()[0]==0,"Close during load did not cancel/release");
                load();report.put("reuse_after_close_load",generateAfterRecovery());NativeRuntime.close(session);session=0;
                File bad=new File(dir,"truncated.gguf");Files.write(bad.toPath(),bytes("GGUF"));session=NativeRuntime.create();String failure="";try{NativeRuntime.load(session,bytes(bad.getAbsolutePath()));}catch(IllegalStateException expected){failure=expected.getMessage();}
                check(!failure.isEmpty()&&NativeRuntime.resourceState()[1]==0,"Malformed load accepted/leaked");report.put("invalid_model_failure",failure);
            }
            NativeRuntime.close(session);session=0;report.put("final_operation",new JSONArray(NativeRuntime.operationState())).put("final_resources",new JSONArray(NativeRuntime.resourceState())).put("status","PASS");save();finish(-1,output);
        }catch(Throwable e){try{report.put("status","FAIL").put("failure",e.toString());save();}catch(Exception ignored){}output.putString("failure",e.toString());finish(1,output);}
        finally{if(session!=0)NativeRuntime.close(session);worker.shutdownNow();if(activity!=null)runOnMainSync(activity::finish);}
    }
}
