package org.pocketlore.app;
import android.app.Instrumentation;import android.os.Bundle;import android.os.Debug;import android.system.Os;import java.io.*;import java.nio.file.*;import java.nio.charset.StandardCharsets;import java.util.*;import org.json.*;
/** Rolling real-shard compatibility experiment, never simultaneous full installation. */
public final class ShardSweepInstrumentation extends Instrumentation {
 Bundle args;
 public void onCreate(Bundle b){super.onCreate(b);args=b;start();}
 public void onStart(){Bundle result=new Bundle();File fifo=null;
  try{
   String label=args.getString("label");ScaleLibrary.check(label!=null&&label.matches("[a-z0-9-]{1,80}"),"Invalid sweep label");
   File files=getTargetContext().getFilesDir(),scope=new File(files,"sweep-owned");ScaleLibrary.check(scope.isDirectory()||scope.mkdir(),"Sweep directory");
   ScaleLibrary library=new ScaleLibrary(scope);fifo=new File(files,"sweep-input");ScaleLibrary.check(!fifo.exists(),"Previous FIFO still present");Os.mkfifo(fifo.getPath(),0600);
   long before=SharedShardUpdate.uniqueBytes(scope),start=System.nanoTime();ScaleLibrary.Entry e;
   try(InputStream in=new FileInputStream(fifo)){e=library.install(in,()->false);}Files.delete(fifo.toPath());fifo=null;
   JSONObject r=new JSONObject().put("status","PASS").put("label",label).put("manifest",e.id).put("pid",android.os.Process.myPid()).put("kind",e.kind()).put("shards",e.manifest.getJSONArray("shards")).put("metadata_only",e.manifest.optBoolean("metadata_only",false)).put("import_ms",(System.nanoTime()-start)/1e6).put("owned_before",before).put("owned_after",SharedShardUpdate.uniqueBytes(scope)).put("observed_precommit",library.lastPhysicalPeak).put("new_bytes_written",library.lastTemporaryPeak).put("usable_bytes",scope.getUsableSpace());
   if(!e.manifest.optBoolean("metadata_only",false)&&!"true".equals(args.getString("smoke"))){
    JSONObject p=e.manifest.getJSONObject("probe");long t=System.nanoTime();
    if(e.kind().equals("wiki")){
     List<ScaleWiki.Hit> hits=ScaleWiki.search(e,p.getString("title"),()->false);ScaleLibrary.check(!hits.isEmpty()&&hits.get(0).id.equals(p.getString("id")),"Frozen exact title probe failed");
     ScaleWiki.Hit h=hits.get(0);ScaleWiki.Read read=ScaleWiki.read(h,getTargetContext().getCacheDir(),()->false);ScaleLibrary.check(!read.text.isEmpty()&&!h.mayGenerate(),"Source read/rights failure");r.put("source_identity",h.identity()).put("source_sha256",h.sourceHash).put("source_preview",read.text.substring(0,Math.min(2000,read.text.length()))).put("documents",e.manifest.getLong("documents"));
    }else{
     List<ScalePlaces.Hit> hits=ScalePlaces.nearby(e,p.getDouble("lat"),p.getDouble("lon"),0.1,null,()->false);ScaleLibrary.check(!hits.isEmpty(),"Frozen spatial probe failed");
     r.put("nearby_count",hits.size()).put("source_identity",hits.get(0).identity()).put("source",ScalePlaces.detail(hits.get(0),()->false)).put("source_records",e.manifest.getLong("source_records"));
    }
    r.put("query_and_inspect_ms",(System.nanoTime()-t)/1e6);
   }
   r.put("pss_kib",Debug.getPss());ScaleLibrary.write(new File(files,"sweep-result.json"),r.toString(2).getBytes(StandardCharsets.UTF_8));result.putString("result",r.toString());finish(-1,result);
  }catch(Throwable error){if(fifo!=null)try{Files.deleteIfExists(fifo.toPath());}catch(Exception ignored){}result.putString("failure",android.util.Log.getStackTraceString(error));finish(1,result);}
 }
}
