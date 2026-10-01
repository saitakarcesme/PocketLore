package org.pocketlore.app;
import android.app.Instrumentation;import android.os.Bundle;import java.io.*;import java.nio.file.*;import java.util.*;import org.json.*;
/** Real source subset transactions in isolated test-owned directory; no full inventory claim. */
public final class ShardUpdateInstrumentation extends Instrumentation {
 static void check(boolean b,String s){if(!b)throw new AssertionError(s);}
 interface Work{void run()throws Exception;}
 static void reject(Work w)throws Exception{try{w.run();throw new AssertionError("Invalid update accepted");}catch(IOException expected){}}
 public void onCreate(Bundle b){super.onCreate(b);start();}
 public void onStart(){Bundle report=new Bundle();File scope=null;
 try{
  File files=getTargetContext().getFilesDir(),input=new File(files,"shard-fixtures");
  scope=Files.createTempDirectory(files.toPath(),"shard-test-").toFile();ScaleLibrary lib=new ScaleLibrary(scope);
  String modelBefore=ScaleLibrary.hash(new File(files,"model.gguf"),()->false);
  ScaleLibrary.Entry base;try(InputStream in=new FileInputStream(new File(input,"base.plscale"))){base=lib.install(in,()->false);}
  String catalog=ScaleLibrary.hash(new File(lib.root,"catalog.json"),()->false);long before=SharedShardUpdate.uniqueBytes(scope);
  reject(()->{try(InputStream in=new FileInputStream(new File(input,"corrupt.plscale"))){lib.install(in,()->false);}});
  check(ScaleLibrary.hash(new File(lib.root,"catalog.json"),()->false).equals(catalog),"Corruption changed catalog");
  reject(()->{try(InputStream in=new FileInputStream(new File(input,"update.plscale"))){lib.install(in,()->true);}});
  final int[] reads={0};long cancelStart=System.nanoTime();
  reject(()->{try(InputStream in=new FileInputStream(new File(input,"update.plscale"))){lib.install(in,()->++reads[0]>15);}});
  long cancelNs=System.nanoTime()-cancelStart;
  check(ScaleLibrary.hash(new File(lib.root,"catalog.json"),()->false).equals(catalog),"Cancel changed catalog");
  check(SharedShardUpdate.uniqueBytes(scope)==before,"Failed update leaked files");
  File retained=ScaleLibrary.resolve(base.directory,"NOTICE.txt");
  File object=ScaleLibrary.resolve(base.directory,"NOTICE.txt");byte[] original=Files.readAllBytes(object.toPath());byte[] changed=original.clone();changed[0]^=1;Files.write(object.toPath(),changed);
  reject(()->{try(InputStream in=new FileInputStream(new File(input,"update.plscale"))){lib.install(in,()->false);}});Files.write(object.toPath(),original);
  File hidden=new File(scope,"hidden-object");Files.move(object.toPath(),hidden.toPath());
  reject(()->{try(InputStream in=new FileInputStream(new File(input,"update.plscale"))){lib.install(in,()->false);}});Files.move(hidden.toPath(),object.toPath());
  File interrupted=new File(lib.root,"pending-simulated-crash");check(interrupted.mkdir(),"Create interrupted stage");Files.write(new File(interrupted,"partial").toPath(),new byte[1024]);
  check(new ScaleLibrary(scope).entries().size()==1&&!interrupted.exists(),"Interrupted stage recovery");
  lib.select(Collections.emptySet());ScaleLibrary.Entry updated;
  long start=System.nanoTime();try(InputStream in=new FileInputStream(new File(input,"update.plscale"))){updated=lib.install(in,()->false);}
  long elapsed=System.nanoTime()-start;
  check(!updated.active,"Update lost disabled selection");check(retained.equals(ScaleLibrary.resolve(updated.directory,"NOTICE.txt")),"Notice copied instead of shared");
  check(!base.directory.exists(),"Old directory retained");
  List<ScaleLibrary.Entry> restored=new ScaleLibrary(scope).entries();check(restored.size()==1&&restored.get(0).id.equals(updated.id),"Restart changed update");
  lib.select(Collections.singleton(updated.id));JSONArray hits=new JSONArray();
  for(String q:new String[]{"Acid","Cooking"}){List<ScaleWiki.Hit> hs=ScaleWiki.search(updated,q,()->false);check(!hs.isEmpty()&&hs.get(0).title.equals(q),"Exact cross-shard title missed");ScaleWiki.Read r=ScaleWiki.read(hs.get(0),getTargetContext().getCacheDir(),()->false);check(!r.text.isEmpty()&&!hs.get(0).mayGenerate(),"Source read/rights");hits.put(new JSONObject().put("query",q).put("identity",hs.get(0).identity()).put("preview",r.text));}
  List<ScaleWiki.Hit> diverse=ScaleWiki.search(updated,"acid cooking",()->false);Set<String> ss=new HashSet<>();for(ScaleWiki.Hit h:diverse)ss.add(h.shard);check(ss.size()==2,"Cross-shard diversity");
  reject(()->SharedShardUpdate.admit(ScaleLibrary.HARD-1,1,1,Long.MAX_VALUE));
  reject(()->SharedShardUpdate.admit(1,1,1,1));
  reject(()->{try(InputStream in=new FileInputStream(new File(input,"update.plscale"))){new ScaleLibrary(Files.createTempDirectory(getTargetContext().getCacheDir().toPath(),"missing-base-").toFile()).install(in,()->false);}});
  long wikiPeak=lib.lastTemporaryPeak,wikiAdmission=lib.lastAdmissionPeak,wikiPhysicalPeak=lib.lastPhysicalPeak,wikiAfter=SharedShardUpdate.uniqueBytes(scope);
  ScaleLibrary.Entry places;try(InputStream in=new FileInputStream(new File(input,"places.plscale"))){places=lib.install(in,()->false);}
  JSONArray cityResults=new JSONArray();
  for(String name:new String[]{"London","Mexico City"}){long t=System.nanoTime();List<ScalePlaces.City> cs=ScalePlaces.cities(places,name,()->false);check(!cs.isEmpty(),"City alias missing");ScalePlaces.City city=cs.get(0);List<ScalePlaces.Hit> ps=ScalePlaces.nearby(places,city.lat,city.lon,1,null,()->false);check(!ps.isEmpty(),"Positive place coverage missing");String detail=ScalePlaces.detail(ps.get(0),()->false);check(detail.contains("unknown")&&detail.contains("Routing unavailable"),"Live disclosure lost");List<ScalePlaces.Hit> cats=ScalePlaces.nearby(places,city.lat,city.lon,1,"restaurant",()->false);cityResults.put(new JSONObject().put("city",name).put("count",ps.size()).put("restaurant_count",cats.size()).put("ms",(System.nanoTime()-t)/1e6).put("source",detail));}
  check(ScalePlaces.nearby(places,19.4326,-99.1332,1,"pocketlore nonexistent category 300",()->false).isEmpty(),"Absent category leak");
  check(ScaleLibrary.hash(new File(files,"model.gguf"),()->false).equals(modelBefore),"Model changed");
  JSONObject result=new JSONObject().put("status","PASS").put("platform","emulator-5560 x86_64, real source subset only").put("before_bytes",before).put("after_bytes",SharedShardUpdate.uniqueBytes(scope)).put("wiki_after_bytes",wikiAfter).put("wiki_observed_precommit_bytes",wikiPhysicalPeak).put("new_temporary_peak",wikiPeak).put("admission_peak_with_reserve",wikiAdmission).put("update_ms",elapsed/1e6).put("cancel_ms",cancelNs/1e6).put("shared_object",true).put("changed_missing_shared_object_rejected",true).put("interrupted_stage_recovery",true).put("corrupt_cancel_rollback",true).put("restart_selection",true).put("model_sha256",modelBefore).put("cities",cityResults).put("hits",hits).put("pss_kib",android.os.Debug.getPss());
  ScaleLibrary.write(new File(files,"shard-update-result.json"),result.toString(2).getBytes(java.nio.charset.StandardCharsets.UTF_8));report.putString("result",result.toString());finish(-1,report);
 }catch(Throwable e){report.putString("failure",android.util.Log.getStackTraceString(e));finish(1,report);}finally{if(scope!=null)try{ScaleLibrary.removeTree(scope);}catch(Exception ignored){}}
 }
}
