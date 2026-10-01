package org.pocketlore.app;
import android.app.Instrumentation;
import android.os.*;
import java.io.*;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import org.json.*;

/** Real JNI and bounded duplication-only pack transitions; no fabricated output. */
public final class ScaleLatencyInstrumentation extends Instrumentation {
    private File root,install;private JSONObject report=new JSONObject();private JSONArray samples=new JSONArray();
    private volatile boolean sampling;private volatile String phase="baseline";private Thread sampler;private String mode;private int index;
    private KnowledgePack oldPack,newPack;private long session;private Throwable sampleFailure;
    static byte[] bytes(String s){return s.getBytes(StandardCharsets.UTF_8);}
    static double ms(long start){return (System.nanoTime()-start)/1e6;}
    static void check(boolean ok,String why){if(!ok)throw new AssertionError(why);}
    private void save()throws Exception{Files.write(new File(root,mode+"-"+index+".json").toPath(),bytes(report.toString(2)));}
    private void snapshot()throws Exception{
        Debug.MemoryInfo mem=new Debug.MemoryInfo();Debug.getMemoryInfo(mem);
        JSONObject s=new JSONObject().put("phase",phase).put("uptime_ms",SystemClock.elapsedRealtime()).put("pss_kib",mem.getTotalPss()).put("swap_pss_kib",mem.getTotalSwappedOutPss()).put("java_used_bytes",Runtime.getRuntime().totalMemory()-Runtime.getRuntime().freeMemory()).put("java_max_bytes",Runtime.getRuntime().maxMemory()).put("native_buffers",new JSONArray(NativeRuntime.resourceState()));
        for(String line:Files.readAllLines(Paths.get("/proc/self/status")))if(line.startsWith("VmRSS:")||line.startsWith("VmSwap:")||line.startsWith("VmHWM:")){String[] v=line.trim().split("\\s+");s.put(v[0].replace(":","")+"_kib",Long.parseLong(v[1]));}
        long stage=0,saved=0;if(install!=null){File[] fs=install.listFiles();if(fs!=null)for(File f:fs){if(f.getName().endsWith(".partial"))stage+=f.length();if(f.getName().equals("knowledge.plpack"))saved=f.length();}}
        s.put("stage_bytes",stage).put("saved_pack_bytes",saved);
        synchronized(samples){samples.put(s);}
    }
    private void steady(String name)throws Exception{phase=name;System.gc();Thread.sleep(150);snapshot();}
    @Override public void onCreate(Bundle args){super.onCreate(args);mode=args.getString("mode","warm");index=Integer.parseInt(args.getString("index","0"));start();}
    @Override public void onStart(){Bundle result=new Bundle();long ready=System.nanoTime();
        try{
            root=new File(getTargetContext().getFilesDir(),"scale-latency-tests");root.mkdirs();install=new File(root,"installed");install.mkdirs();
            report.put("mode",mode).put("index",index).put("pid",android.os.Process.myPid()).put("runtime",NativeRuntime.identity()).put("sampling_target_ms",250);
            JSONObject protocol=new JSONObject(new String(Files.readAllBytes(new File(root,"protocol.json").toPath()),StandardCharsets.UTF_8));
            snapshot();sampling=true;sampler=new Thread(()->{while(sampling){try{snapshot();Thread.sleep(250);}catch(InterruptedException e){return;}catch(Throwable e){sampleFailure=e;return;}}});sampler.start();
            phase="pack-load";long t=System.nanoTime();oldPack=KnowledgePack.load(new File(root,"reference.plpack"));report.put("pack_load_ms",ms(t));check(oldPack.sha256.equals(protocol.getString("pack_sha256")),"Pinned pack");
            phase="model-load";session=NativeRuntime.create();t=System.nanoTime();NativeRuntime.load(session,bytes(new File(getTargetContext().getFilesDir(),"model.gguf").getAbsolutePath()));report.put("model_load_ms",ms(t));final long id=session;
            if(mode.equals("scale")){
                JSONObject fixture=protocol.getJSONArray("fixtures").getJSONObject(index);File incoming=new File(root,fixture.getString("file"));
                check(KnowledgePack.hash(Files.readAllBytes(incoming.toPath())).equals(fixture.getString("sha256")),"Fixture hash");
                Files.copy(new File(root,"reference.plpack").toPath(),new File(install,"knowledge.plpack").toPath(),StandardCopyOption.REPLACE_EXISTING);
                steady("before-import");report.put("old_index_counts",new JSONArray(oldPack.engine.resourceCounts()));phase="import";t=System.nanoTime();boolean accepted=false;String failure="";
                try(InputStream in=new FileInputStream(incoming)){newPack=KnowledgePack.install(in,install);accepted=true;}
                catch(Exception|OutOfMemoryError e){failure=e.toString();}
                report.put("import_ms",ms(t)).put("accepted",accepted).put("failure",failure).put("fixture",fixture);save();
                check(accepted==fixture.getString("expected").equals("accept"),"Unexpected admission result: "+failure);
                check(oldPack.engine.size()==186&&!oldPack.engine.research(protocol.getJSONArray("questions").getString(0)).hits.isEmpty(),"Old live index damaged");
                check(install.listFiles((d,n)->n.endsWith(".partial")).length==0,"Stage remains");
                if(accepted){
                    check(newPack.engine.size()==fixture.getInt("passages"),"Index count");
                    check(KnowledgePack.hash(Files.readAllBytes(new File(install,"knowledge.plpack").toPath())).equals(fixture.getString("sha256")),"Saved replacement");
                    report.put("new_index_counts",new JSONArray(newPack.engine.resourceCounts()));steady("old-and-new-index-retained");
                    t=System.nanoTime();ResearchEngine.Result found=newPack.engine.research(protocol.getJSONArray("questions").getString(0));report.put("retrieval_ms",ms(t)).put("candidates_scored",found.candidatesScored);check(!found.hits.isEmpty(),"Stress index unusable");
                    oldPack=null;steady("new-index-only");
                }else{
                    check(KnowledgePack.hash(Files.readAllBytes(new File(install,"knowledge.plpack").toPath())).equals(protocol.getString("pack_sha256")),"Rejected pack replaced old");
                    steady("after-rejection");check(!failure.isEmpty(),"Missing failure");
                }
                report.put("stage_cleanup",true).put("old_index_survived",true);
            }else{
                AnswerEngine.Generator generator=new AnswerEngine.Generator(){
                    public int run(byte[] p,int limit,NativeRuntime.Sink sink){return NativeRuntime.generateChat(id,bytes(EvidencePrompt.SYSTEM),p,limit,sink);}
                    public int runWithSources(byte[] p,int limit,NativeRuntime.Sink sink,int count,boolean combined){return NativeRuntime.generateClaims(id,bytes(EvidencePrompt.SYSTEM),p,limit,sink,count,combined);}
                    public int countTokens(byte[] p){return NativeRuntime.countChatTokens(id,bytes(EvidencePrompt.SYSTEM),p);}
                };
                JSONArray rows=new JSONArray();report.put("rows",rows).put("system_prompt",EvidencePrompt.SYSTEM);
                int count=mode.equals("warm")?11:1;
                for(int i=0;i<count;i++){
                    String q=protocol.getJSONArray("questions").getString(mode.equals("warm")?i%2:index%2);
                    phase="answer-"+i;NativeRuntime.reset(id);t=System.nanoTime();ResearchEngine.Result evidence=oldPack.engine.research(q);double retrieval=ms(t);
                    AnswerEngine.Outcome a=AnswerEngine.answer(q,evidence,generator,part->{},()->false);double total=ms(t);
                    JSONArray sources=new JSONArray();for(ResearchEngine.Hit h:evidence.hits)sources.put(new JSONObject().put("id",h.passage.id).put("text",h.passage.text).put("url",h.passage.url).put("rights",h.passage.license));
                    rows.put(new JSONObject().put("question",q).put("sample",i).put("warmup",mode.equals("warm")&&i==0).put("kind",a.kind.toString()).put("text",a.text).put("raw_draft",a.rawDraft).put("prompt",a.prompt).put("sources",sources).put("reason",a.reason).put("invoked",a.invokedModel).put("tokens",a.tokens).put("retrieval_ms",retrieval).put("answer_first_token_ms",a.firstTokenMs).put("request_first_token_ms",a.firstTokenMs>0?retrieval+a.firstTokenMs:0).put("answer_total_ms",a.totalMs).put("request_total_ms",total).put("since_process_ready_ms",ms(ready)));
                    save();check(a.invokedModel&&a.tokens>0&&a.firstTokenMs>0&&!a.rawDraft.isEmpty(),"No real native output");
                    check(NativeRuntime.resourceState()[1]==0,"Native context retained");
                }
                steady("after-answers");
            }
            report.put("status","PASS");
        }catch(Throwable failure){try{report.put("status","FAIL").put("failure",failure.toString());}catch(Exception ignored){}result.putString("failure",failure.toString());}
        finally{
            sampling=false;if(sampler!=null){sampler.interrupt();try{sampler.join(5000);}catch(Exception ignored){}}
            try{if(session!=0)NativeRuntime.close(session);report.put("final_native",new JSONArray(NativeRuntime.resourceState()));synchronized(samples){report.put("samples",samples);}if(sampleFailure!=null)report.put("status","FAIL").put("sampler_failure",sampleFailure.toString());save();}catch(Exception error){result.putString("save_failure",error.toString());}
        }
        finish(report.optString("status").equals("PASS")?-1:1,result);
    }
}
