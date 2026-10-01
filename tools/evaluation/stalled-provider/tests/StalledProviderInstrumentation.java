package org.pocketlore.app;

import android.app.Instrumentation;
import android.net.Uri;
import android.os.Bundle;
import android.provider.DocumentsContract;
import java.io.*;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;
import java.util.function.BooleanSupplier;
import org.json.*;

public final class StalledProviderInstrumentation extends Instrumentation {
    private boolean legacy;
    private final JSONArray rows=new JSONArray();
    private final ExecutorService worker=Executors.newSingleThreadExecutor();
    private final AtomicReference<Thread> importing=new AtomicReference<>();
    private File dir,output;
    private static String hash(File f)throws Exception{return KnowledgePack.hash(Files.readAllBytes(f.toPath()));}
    private Bundle provider(String method){return getContext().getContentResolver().call(Uri.parse("content://org.pocketlore.fixture.documents"),method,null,null);}
    private static void require(boolean b,String message){if(!b)throw new AssertionError(message);}
    private InputStream open(Uri uri,BooleanSupplier cancelled)throws Exception {
        if(legacy)return getTargetContext().getContentResolver().openInputStream(uri);
        try{return (InputStream)Class.forName("org.pocketlore.app.DocumentInput").getMethod("open",android.content.ContentResolver.class,Uri.class,BooleanSupplier.class).invoke(null,getTargetContext().getContentResolver(),uri,cancelled);}
        catch(java.lang.reflect.InvocationTargetException e){throw (Exception)e.getCause();}
    }
    private Future<String> submit(String kind,String mode,AtomicBoolean cancel){return worker.submit(()->{
        importing.set(Thread.currentThread());
        try(InputStream in=open(DocumentsContract.buildDocumentUri("org.pocketlore.fixture.documents",kind+"-"+mode),cancel::get)){
            if(kind.equals("model"))ModelImport.copy(in,new File(dir,"model.partial"),8,Long.MAX_VALUE,cancel::get);
            else KnowledgePack.install(in,dir,cancel::get);
            return "success";
        }catch(Exception e){return e.getClass().getSimpleName()+": "+e.getMessage();}
        finally{importing.set(null);Thread.interrupted();}
    });}
    private void waitFor(java.util.function.BooleanSupplier test,String why)throws Exception{long end=System.nanoTime()+TimeUnit.SECONDS.toNanos(5);while(!test.getAsBoolean()&&System.nanoTime()<end)Thread.sleep(5);require(test.getAsBoolean(),why);}
    private boolean stagesGone(){File[] fs=dir.listFiles((d,n)->n.endsWith(".partial"));return fs!=null&&fs.length==0;}
    private long staged(){long n=0;for(File f:dir.listFiles())if(f.getName().endsWith(".partial"))n+=f.length();return n;}
    private void save(JSONObject report)throws Exception{Files.write(output.toPath(),report.toString(2).getBytes(java.nio.charset.StandardCharsets.UTF_8));}
    @Override public void onCreate(Bundle args){super.onCreate(args);legacy="true".equals(args.getString("legacy"));start();}
    @Override public void onStart(){Bundle result=new Bundle();JSONObject report=new JSONObject();
        try {
            getContext().startActivity(new android.content.Intent().setClassName("org.pocketlore.app.test","org.pocketlore.app.FixtureGrantActivity").addFlags(android.content.Intent.FLAG_ACTIVITY_NEW_TASK));
            waitFor(()->{try{provider("status");return true;}catch(SecurityException e){return false;}},"fixture grants unavailable");
            dir=new File(getTargetContext().getFilesDir(),"stalled-provider-tests");dir.mkdirs();output=new File(dir,"results.json");
            File model=new File(dir,"model.gguf"),pack=new File(dir,"knowledge.plpack");
            Files.write(model.toPath(),"saved model sentinel".getBytes());
            Files.copy(new File(dir,"reference.plpack").toPath(),pack.toPath(),StandardCopyOption.REPLACE_EXISTING);
            String modelHash=hash(model),packHash=hash(pack);long threadId=-1;
            report.put("mode",legacy?"legacy-baseline":"repaired").put("pid",android.os.Process.myPid()).put("rows",rows);
            for(String kind:new String[]{"model","pack"}) {
                for(String scenario:new String[]{"cancel-before-open","stall-empty","stall-prefix"}) {
                    provider("reset");AtomicBoolean cancelled=new AtomicBoolean(scenario.equals("cancel-before-open"));
                    Future<String> task=submit(kind,scenario.equals("cancel-before-open")?"stall-empty":scenario,cancelled);
                    if(!scenario.equals("cancel-before-open")){
                        waitFor(()->"stalled".equals(provider("status").getString("state")),"provider did not stall");
                        waitFor(()->scenario.endsWith("prefix")?staged()>=4:!stagesGone(),"copy did not reach fixture");
                        Thread.sleep(250);require(!task.isDone(),"fixture did not block");
                    }
                    long start=System.nanoTime();cancelled.set(true);
                    Thread thread=importing.get();if(kind.equals("pack")&&thread!=null)thread.interrupt();
                    boolean returned=true;String outcome;
                    try{outcome=task.get(1500,TimeUnit.MILLISECONDS);}catch(TimeoutException timeout){returned=false;outcome="deadline exceeded";}
                    double latency=(System.nanoTime()-start)/1e6;
                    int opens=provider("status").getInt("opens");boolean cleanBeforeRelease=stagesGone();
                    provider("release");if(!returned)outcome=task.get(5,TimeUnit.SECONDS);
                    if(opens>0)waitFor(()->!"stalled".equals(provider("status").getString("state")),"provider writer did not finish");
                    String state=provider("status").getString("state");
                    boolean preserved=hash(model).equals(modelHash)&&hash(pack).equals(packHash);
                    JSONObject row=new JSONObject().put("kind",kind).put("case",scenario).put("returned_before_release",returned).put("cancel_ms",latency).put("outcome",outcome).put("opens",opens).put("clean_before_release",cleanBeforeRelease).put("saved_unchanged",preserved).put("provider_state_after_release",state);
                    rows.put(row);save(report);
                    require(stagesGone()&&preserved,"cancel lost saved bytes or left stage");
                    if(!legacy){require(returned&&latency<1500&&cleanBeforeRelease&&!outcome.equals("success"),"cancellation failed");require(scenario.equals("cancel-before-open")?opens==0:state.equals("reader-closed"),"descriptor remained open");}
                }
                provider("reset");String shortResult=submit(kind,"short",new AtomicBoolean()).get(5,TimeUnit.SECONDS);
                require(!shortResult.equals("success")&&stagesGone()&&hash(model).equals(modelHash)&&hash(pack).equals(packHash),"short stream accepted or saved bytes changed");
                rows.put(new JSONObject().put("kind",kind).put("case","short-read").put("outcome",shortResult).put("saved_unchanged",true).put("staging_removed",true));save(report);
                provider("reset");String retry=submit(kind,"retry",new AtomicBoolean()).get(10,TimeUnit.SECONDS);
                require(retry.equals("success"),"retry failed: "+retry);
                if(kind.equals("model")){require(hash(new File(dir,"model.partial")).equals(KnowledgePack.hash("GGUFtest".getBytes())),"retry staged wrong bytes");new File(dir,"model.partial").delete();}
                else require(hash(pack).equals(packHash),"retry installed wrong pack");
                require(hash(model).equals(modelHash)&&stagesGone(),"retry damaged saved model or left stage");
                long id=worker.submit(()->Thread.currentThread().getId()).get();if(threadId<0)threadId=id;require(threadId==id,"worker was replaced");
                rows.put(new JSONObject().put("kind",kind).put("case","retry").put("outcome",retry).put("worker_thread_id",id).put("saved_model_unchanged",true).put("staging_removed",true));save(report);
            }
            report.put("status",legacy?"BASELINE_FAILURE_REPRODUCED":"PASS");save(report);finish(-1,result);
        }catch(Throwable e){try{report.put("status","FAIL").put("failure",e.toString());save(report);}catch(Exception ignored){}result.putString("failure",e.toString());finish(1,result);}
        finally{provider("release");worker.shutdownNow();}
    }
}
