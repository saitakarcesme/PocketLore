package org.pocketlore.app;
import android.app.Instrumentation;import android.os.Bundle;import java.io.*;import java.nio.file.*;import java.util.*;import org.json.*;
/** Real source subset transactions in isolated test-owned directory; no full inventory claim. */
public final class ShardUpdateInstrumentation extends Instrumentation {
 static void check(boolean b,String s){if(!b)throw new AssertionError(s);}
 interface Work{void run()throws Exception;}
 static void reject(Work w)throws Exception{try{w.run();throw new AssertionError("Invalid update accepted");}catch(IOException expected){}}
 Bundle args;public void onCreate(Bundle b){super.onCreate(b);args=b;start();}
 public void onStart(){Bundle report=new Bundle();File scope=null;
 try{
  if("large-inspect".equals(args.getString("mode"))){
   File files=getTargetContext().getFilesDir();ScaleLibrary lib=new ScaleLibrary(files);check(lib.entries().size()==1,"Expected measured places collection");ScaleLibrary.Entry e=lib.entries().get(0);check(e.manifest.getJSONArray("shards").length()==2,"Expected two installed full shards");
   JSONObject protocol=new JSONObject(new String(Files.readAllBytes(new File(files,"shard-fixtures/protocol.json").toPath()),java.nio.charset.StandardCharsets.UTF_8));JSONArray queries=new JSONArray();
   for(int i=0;i<protocol.getJSONArray("cities").length();i++){String name=protocol.getJSONArray("cities").getString(i);long t=System.nanoTime();List<ScalePlaces.City> cities=ScalePlaces.cities(e,name,()->false);check(!cities.isEmpty(),"City alias missing");ScalePlaces.City c=cities.get(0);List<ScalePlaces.Hit> hits=ScalePlaces.nearby(e,c.lat,c.lon,1,null,()->false);JSONObject q=new JSONObject().put("city",name).put("count",hits.size()).put("query_ms",(System.nanoTime()-t)/1e6);if(!hits.isEmpty())q.put("source",ScalePlaces.detail(hits.get(0),()->false));queries.put(q);}
   JSONObject r=new JSONObject().put("status","PASS").put("pid",android.os.Process.myPid()).put("manifest",e.id).put("source_records",e.manifest.getLong("source_records")).put("queries",queries).put("pss_kib",android.os.Debug.getPss());ScaleLibrary.write(new File(files,"large-inspect.json"),r.toString(2).getBytes(java.nio.charset.StandardCharsets.UTF_8));report.putString("result",r.toString());finish(-1,report);return;
  }
  if(args.getString("mode","").startsWith("large-")){
   File files=getTargetContext().getFilesDir();ScaleLibrary lib=new ScaleLibrary(files);boolean first="large-base".equals(args.getString("mode"));
   if(first)check(lib.entries().isEmpty(),"Do not replace preexisting bulk data");else check(lib.entries().size()==1,"Large update base");
   String beforeModel=ScaleLibrary.hash(new File(files,"model.gguf"),()->false);File archive=new File(files,"shard-fixtures/large.plscale");long before=SharedShardUpdate.uniqueBytes(files),t=System.nanoTime();
   File cityBefore=first?null:ScaleLibrary.resolve(lib.entries().get(0).directory,"cities.sqlite");ScaleLibrary.Entry e;
   try(InputStream in=new FileInputStream(archive)){e=lib.install(in,()->false);}long ns=System.nanoTime()-t;
   check(first||cityBefore.equals(ScaleLibrary.resolve(e.directory,"cities.sqlite")),"Full shard duplicated shared cities");check(lib.entries().size()==1,"Update retained obsolete collection");
   JSONObject r=new JSONObject().put("status","PASS").put("mode",args.getString("mode")).put("pid",android.os.Process.myPid()).put("manifest",e.id).put("source_records",e.manifest.getLong("source_records")).put("shards",e.manifest.getJSONArray("shards")).put("archive_bytes",archive.length()).put("app_files_before",before).put("app_files_after",SharedShardUpdate.uniqueBytes(files)).put("observed_precommit_bytes",lib.lastPhysicalPeak).put("new_bytes_written",lib.lastTemporaryPeak).put("admission_peak",lib.lastAdmissionPeak).put("ms",ns/1e6).put("pss_kib",android.os.Debug.getPss()).put("shared_cities",!first).put("model_sha256",ScaleLibrary.hash(new File(files,"model.gguf"),()->false));check(r.getString("model_sha256").equals(beforeModel),"Large update model drift");
   ScaleLibrary.write(new File(files,args.getString("mode")+".json"),r.toString(2).getBytes(java.nio.charset.StandardCharsets.UTF_8));Files.delete(archive.toPath());report.putString("result",r.toString());finish(-1,report);return;
  }
  if("restart".equals(args.getString("mode"))){
   File files=getTargetContext().getFilesDir();JSONObject prior=new JSONObject(new String(Files.readAllBytes(new File(files,"shard-update-result.json").toPath()),java.nio.charset.StandardCharsets.UTF_8));
   File saved=new File(files,prior.getString("fixture_directory"));check(saved.getName().startsWith("shard-test-")&&saved.getCanonicalFile().getParentFile().equals(files.getCanonicalFile()),"Fixture path");
   ScaleLibrary loaded=new ScaleLibrary(saved);check(loaded.entries().size()==2,"Process restart lost collections");for(ScaleLibrary.Entry e:loaded.entries())check(e.active&&!e.mayGenerate(),"Restart selection/rights");
   JSONObject r=new JSONObject().put("status","PASS").put("pid",android.os.Process.myPid()).put("previous_pid",prior.getInt("pid")).put("collections",2).put("model_sha256",ScaleLibrary.hash(new File(files,"model.gguf"),()->false));check(r.getInt("pid")!=r.getInt("previous_pid"),"Same process restart");
   ScaleLibrary.write(new File(files,"shard-restart-result.json"),r.toString(2).getBytes(java.nio.charset.StandardCharsets.UTF_8));ScaleLibrary.removeTree(saved);report.putString("result",r.toString());finish(-1,report);return;
  }
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
  File obsolete=ScaleLibrary.resolve(updated.directory,updated.manifest.getJSONArray("shards").getString(0)+"/articles.blocks");
  try(InputStream in=new FileInputStream(new File(input,"remove-first.plscale"))){ScaleLibrary.Entry reduced=lib.install(in,()->false);check(reduced.manifest.getJSONArray("shards").length()==1&&!obsolete.exists(),"Removed shard not reclaimed");check(ScaleLibrary.resolve(reduced.directory,"NOTICE.txt").exists(),"Shared notice reclaimed");}
  ScaleLibrary.Entry places;try(InputStream in=new FileInputStream(new File(input,"places.plscale"))){places=lib.install(in,()->false);}
  JSONArray cityResults=new JSONArray();
  for(String name:new String[]{"London","Mexico City"}){long t=System.nanoTime();List<ScalePlaces.City> cs=ScalePlaces.cities(places,name,()->false);check(!cs.isEmpty(),"City alias missing");ScalePlaces.City city=cs.get(0);List<ScalePlaces.Hit> ps=ScalePlaces.nearby(places,city.lat,city.lon,1,null,()->false);check(!ps.isEmpty(),"Positive place coverage missing");String detail=ScalePlaces.detail(ps.get(0),()->false);check(detail.contains("unknown")&&detail.contains("Routing unavailable"),"Live disclosure lost");List<ScalePlaces.Hit> cats=ScalePlaces.nearby(places,city.lat,city.lon,1,"restaurant",()->false);cityResults.put(new JSONObject().put("city",name).put("count",ps.size()).put("restaurant_count",cats.size()).put("ms",(System.nanoTime()-t)/1e6).put("source",detail));}
  check(ScalePlaces.nearby(places,19.4326,-99.1332,1,"pocketlore nonexistent category 300",()->false).isEmpty(),"Absent category leak");
  check(ScaleLibrary.hash(new File(files,"model.gguf"),()->false).equals(modelBefore),"Model changed");
  JSONObject result=new JSONObject().put("status","PASS").put("platform","emulator-5560 x86_64, real source subset only").put("pid",android.os.Process.myPid()).put("fixture_directory",scope.getName()).put("before_bytes",before).put("after_bytes",SharedShardUpdate.uniqueBytes(scope)).put("wiki_after_bytes",wikiAfter).put("wiki_observed_precommit_bytes",wikiPhysicalPeak).put("new_temporary_peak",wikiPeak).put("admission_peak_with_reserve",wikiAdmission).put("update_ms",elapsed/1e6).put("cancel_ms",cancelNs/1e6).put("shared_object",true).put("removed_shard_reclaimed",true).put("changed_missing_shared_object_rejected",true).put("interrupted_stage_recovery",true).put("corrupt_cancel_rollback",true).put("restart_selection",true).put("model_sha256",modelBefore).put("cities",cityResults).put("hits",hits).put("pss_kib",android.os.Debug.getPss());
  ScaleLibrary.write(new File(files,"shard-update-result.json"),result.toString(2).getBytes(java.nio.charset.StandardCharsets.UTF_8));report.putString("result",result.toString());scope=null;finish(-1,report);
 }catch(Throwable e){report.putString("failure",android.util.Log.getStackTraceString(e));finish(1,report);}finally{if(scope!=null)try{ScaleLibrary.removeTree(scope);}catch(Exception ignored){}}
 }
}
