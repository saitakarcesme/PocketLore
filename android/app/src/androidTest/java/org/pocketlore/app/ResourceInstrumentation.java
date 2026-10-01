package org.pocketlore.app;

import android.app.*;
import android.os.*;
import android.content.Intent;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.concurrent.atomic.*;
import org.json.*;

/** Real JNI/memory sampling plus labeled injected storage and memory-pressure controls. */
public final class ResourceInstrumentation extends Instrumentation {
    final JSONObject report=new JSONObject();final JSONArray checks=new JSONArray(),samples=new JSONArray();
    volatile boolean sampling;volatile String phase="baseline";final AtomicLong peak=new AtomicLong();
    interface Action {void run()throws Exception;}
    void ok(boolean b,String name){if(!b)throw new AssertionError(name);checks.put(name);}
    void rejects(Action a,String name)throws Exception {try{a.run();}catch(Exception expected){checks.put(name);return;}throw new AssertionError(name);}
    static byte[] bytes(String s){return s.getBytes(StandardCharsets.UTF_8);}
    static String hash(File f)throws Exception {java.security.MessageDigest d=java.security.MessageDigest.getInstance("SHA-256");try(InputStream in=new FileInputStream(f)){byte[] b=new byte[65536];int n;while((n=in.read(b))!=-1)d.update(b,0,n);}StringBuilder s=new StringBuilder();for(byte b:d.digest())s.append(String.format(java.util.Locale.ROOT,"%02x",b&255));return s.toString();}
    void snapshot(){try{Debug.MemoryInfo m=new Debug.MemoryInfo();Debug.getMemoryInfo(m);long p=m.getTotalPss();peak.accumulateAndGet(p,Math::max);JSONObject s=new JSONObject().put("phase",phase).put("elapsed_ms",SystemClock.elapsedRealtime()).put("pss_kib",p).put("java_used_bytes",Runtime.getRuntime().totalMemory()-Runtime.getRuntime().freeMemory()).put("native_heap_allocated_bytes",Debug.getNativeHeapAllocatedSize());synchronized(samples){samples.put(s);}}catch(Exception e){throw new RuntimeException(e);}}
    void await(java.util.function.BooleanSupplier condition,String name)throws Exception{long end=SystemClock.elapsedRealtime()+90000;while(!condition.getAsBoolean()&&SystemClock.elapsedRealtime()<end)Thread.sleep(100);ok(condition.getAsBoolean(),name);}
    @Override public void onCreate(Bundle args){super.onCreate(args);start();}
    @Override public void onStart(){Bundle result=new Bundle();long session=0;Thread sampler=null;MainActivity activity=null;File dir=new File(getTargetContext().getFilesDir(),"resource-tests");dir.mkdirs();
        try{
            File root=getTargetContext().getFilesDir(),model=new File(root,"synthesis-tests/model.gguf"),packFile=new File(root,"synthesis-tests/reference.plpack");
            String modelHash=hash(model);ok(modelHash.equals("061b54daade076b5d3362dac252678d17da8c68f07560be70818cace6590cb1a"),"pinned_real_model");
            report.put("pid",android.os.Process.myPid());
            report.put("environment","AOSP x86_64 emulator, not physical Android").put("model_sha256",modelHash).put("model_bytes",model.length()).put("runtime",NativeRuntime.identity());
            ActivityManager.MemoryInfo available=new ActivityManager.MemoryInfo();getTargetContext().getSystemService(ActivityManager.class).getMemoryInfo(available);report.put("emulator_total_memory_bytes",available.totalMem).put("emulator_available_before_bytes",available.availMem).put("emulator_low_memory_before",available.lowMemory).put("java_max_heap_bytes",Runtime.getRuntime().maxMemory());
            sampling=true;sampler=new Thread(()->{while(sampling){snapshot();try{Thread.sleep(100);}catch(InterruptedException e){return;}}});sampler.start();
            // Injected storage failures run in an isolated directory; installed user assets stay intact.
            File old=new File(dir,"model.gguf"),stage=new File(dir,"model.partial");Files.write(old.toPath(),bytes("old model sentinel"));String oldHash=hash(old);
            rejects(()->ModelImport.copy(new ByteArrayInputStream(bytes("GGUFdata")),stage,8,8,()->false),"low_storage_rejected");
            AtomicBoolean cancelled=new AtomicBoolean();InputStream cancelInput=new ByteArrayInputStream(bytes("GGUFdata")){@Override public synchronized int read(byte[] b,int o,int n){int count=super.read(b,o,n);cancelled.set(true);return count;}};
            rejects(()->ModelImport.copy(cancelInput,stage,8,Long.MAX_VALUE,cancelled::get),"model_mid_copy_cancel");ok(!stage.exists()&&hash(old).equals(oldHash),"model_cancel_preserves_old");
            try{ModelImport.copy(new InputStream(){public int read(){throw new OutOfMemoryError("Injected allocation failure");}},stage,8,Long.MAX_VALUE,()->false);throw new AssertionError("OOM injection not raised");}catch(OutOfMemoryError expected){ok(!stage.exists()&&hash(old).equals(oldHash),"injected_model_oom_cleanup");}
            File pack=new File(dir,"knowledge.plpack");Files.copy(packFile.toPath(),pack.toPath(),StandardCopyOption.REPLACE_EXISTING);String packHash=hash(pack);
            rejects(()->KnowledgePack.install(new ByteArrayInputStream(bytes("invalid")),dir),"invalid_pack_preserves_old");
            AtomicBoolean pc=new AtomicBoolean();try(InputStream in=new FileInputStream(packFile){@Override public int read(byte[] b,int o,int n)throws IOException{int c=super.read(b,o,n);pc.set(true);return c;}}){rejects(()->KnowledgePack.install(in,dir,pc::get),"pack_mid_copy_cancel");}
            ok(hash(pack).equals(packHash),"pack_old_bytes_preserved");
            File orphan=new File(dir,"pack-123.partial"),unrelated=new File(dir,"notes.partial");Files.write(orphan.toPath(),bytes("orphan"));Files.write(stage.toPath(),bytes("orphan"));Files.write(unrelated.toPath(),bytes("retain"));
            ResourceStorage.cleanupPackStages(dir);ResourceStorage.cleanupModelStage(dir);ok(!orphan.exists()&&!stage.exists()&&unrelated.exists()&&old.exists()&&pack.exists(),"recognized_stage_recovery_only");
            phase="real_staging_copy";long freeBefore=dir.getUsableSpace(),copyStart=System.nanoTime();String copied;
            try(InputStream in=new FileInputStream(model)){copied=ModelImport.copy(in,stage,model.length(),freeBefore,()->false);}
            report.put("real_copy_ms",(System.nanoTime()-copyStart)/1e6).put("staged_model_bytes",stage.length()).put("staging_free_space_delta_bytes",freeBefore-dir.getUsableSpace());
            ok(copied.equals(modelHash)&&stage.length()==model.length(),"full_real_model_staged_hash");ok(stage.delete(),"full_stage_removed");
            phase="index";long indexStart=System.nanoTime();KnowledgePack indexed=KnowledgePack.load(packFile);report.put("index_load_ms",(System.nanoTime()-indexStart)/1e6).put("index_counts_passages_terms_postings_text_chars",new JSONArray(indexed.engine.resourceCounts())).put("persistent_index_bytes",0).put("persistent_inference_cache_bytes",0);snapshot();
            phase="model_load";long start=System.nanoTime();session=NativeRuntime.create();final long id=session;NativeRuntime.load(id,bytes(model.getAbsolutePath()));report.put("load_ms",(System.nanoTime()-start)/1e6);snapshot();
            rejects(()->NativeRuntime.create(),"second_resident_session_rejected");
            rejects(()->NativeRuntime.generate(id,bytes("water ".repeat(2200)),256,b->{}),"context_overflow_rejected");
            phase="generation";StringBuilder text=new StringBuilder();start=System.nanoTime();int tokens=NativeRuntime.generateChat(id,bytes("Answer in English."),bytes("Explain evaporation in one sentence."),32,b->text.append(new String(b,StandardCharsets.UTF_8)));report.put("generation_tokens",tokens).put("generation_text",text.toString()).put("generation_ms",(System.nanoTime()-start)/1e6);ok(tokens>0&&text.length()>0,"real_generation");ok(NativeRuntime.resourceState()[1]==0,"context_released_after_generation");
            phase="active_cancel";NativeRuntime.reset(id);AtomicLong cancelNs=new AtomicLong();AtomicBoolean held=new AtomicBoolean();int cancelledTokens=NativeRuntime.generate(id,bytes("Water is"),256,b->{if(NativeRuntime.resourceState()[1]!=1)throw new AssertionError("Expected one active context");cancelNs.compareAndSet(0,System.nanoTime());NativeRuntime.close(id);try{NativeRuntime.create();}catch(IllegalStateException expected){held.set(true);}});report.put("cancel_after_token_return_ms",(System.nanoTime()-cancelNs.get())/1e6);ok(cancelledTokens==-1&&cancelNs.get()>0&&held.get(),"close_cancels_and_holds_resident_lease_until_return");NativeRuntime.close(id);session=0;
            phase="unloaded";ok(NativeRuntime.resourceState()[0]==0&&NativeRuntime.resourceState()[1]==0,"no_native_lease_or_context_after_cancel");snapshot();long probe=NativeRuntime.create();NativeRuntime.close(probe);ok(true,"session_slot_recovered");
            // Actual Activity loads its existing saved model, receives a low-memory callback and reloads.
            phase="activity_saved_load";File saved=new File(root,"model.gguf");String savedHash=hash(saved);report.put("saved_model_sha256",savedHash).put("saved_model_bytes",saved.length());
            activity=(MainActivity)startActivitySync(new Intent(getTargetContext(),MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));final MainActivity a=activity;
            await(a::modelReady,"activity_saved_model_ready");phase="injected_trim";runOnMainSync(()->a.onTrimMemory(android.content.ComponentCallbacks2.TRIM_MEMORY_RUNNING_CRITICAL));
            await(()->!a.modelReady(),"trim_model_unavailable");
            // A new session is only possible after worker release, not merely after UI state changes.
            AtomicBoolean released=new AtomicBoolean();await(()->{try{long h=NativeRuntime.create();NativeRuntime.close(h);released.set(true);}catch(IllegalStateException busy){}return released.get();},"trim_released_native_lease");
            phase="activity_reload";runOnMainSync(a::reloadSavedModel);await(a::modelReady,"explicit_reload_after_trim");runOnMainSync(a::onLowMemory);
            released.set(false);await(()->{try{long h=NativeRuntime.create();NativeRuntime.close(h);released.set(true);}catch(IllegalStateException busy){}return released.get();},"low_memory_callback_releases");ok(hash(saved).equals(savedHash),"saved_model_unchanged_after_pressure");
            phase="final";snapshot();sampling=false;sampler.join(2000);report.put("status","PASS").put("checks",checks).put("sampled_peak_pss_kib",peak.get()).put("samples",samples).put("sampling_target_ms",100).put("limitations","Injected callbacks/allocation errors are controls, not actual OS OOM survival; sampled PSS can miss peaks and is not physical-device RAM.");
            try(FileOutputStream out=new FileOutputStream(new File(root,"resource-results.json"))){out.write(bytes(report.toString(2)));}result.putString("status","PASS");finish(-1,result);
        }catch(Throwable failure){sampling=false;if(sampler!=null)sampler.interrupt();try{report.put("status","FAIL").put("failure",failure.toString()).put("checks",checks).put("samples",samples);try(FileOutputStream out=new FileOutputStream(new File(getTargetContext().getFilesDir(),"resource-results.json"))){out.write(bytes(report.toString(2)));}}catch(Exception ignored){}result.putString("failure",failure.toString());finish(1,result);}
        finally{sampling=false;if(sampler!=null)sampler.interrupt();if(session!=0)NativeRuntime.close(session);if(activity!=null){MainActivity a=activity;runOnMainSync(a::finish);}}
    }
}
