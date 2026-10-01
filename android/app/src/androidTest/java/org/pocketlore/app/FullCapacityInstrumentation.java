package org.pocketlore.app;

import android.app.Instrumentation;
import android.os.*;
import android.system.Os;
import java.io.*;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import org.json.*;

/** Full simultaneous residency on the dedicated capacity emulator; no inference. */
public final class FullCapacityInstrumentation extends Instrumentation {
    Bundle args;
    static void check(boolean yes,String why)throws IOException {ScaleLibrary.check(yes,why);}
    static JSONObject read(File f)throws Exception{return new JSONObject(new String(Files.readAllBytes(f.toPath()),StandardCharsets.UTF_8));}
    static String hash(File f)throws Exception{return ScaleLibrary.hash(f,()->false);}
    public void onCreate(Bundle b){super.onCreate(b);args=b;start();}
    volatile boolean sampling;long logicalPeak,allocatedPeak,pssPeak;String sampleFailure;
    void sample(File root)throws Exception {
        long logical=SharedShardUpdate.uniqueBytes(root),allocated=0;
        try(java.util.stream.Stream<Path> walk=Files.walk(root.toPath())){
            for(Iterator<Path> it=walk.iterator();it.hasNext();){Path p=it.next();try{allocated+=Os.stat(p.toString()).st_blocks*512;}catch(android.system.ErrnoException e){if(e.errno!=android.system.OsConstants.ENOENT)throw e;}}
        }
        logicalPeak=Math.max(logicalPeak,logical);allocatedPeak=Math.max(allocatedPeak,allocated);pssPeak=Math.max(pssPeak,Debug.getPss());
    }
    public void onStart(){Bundle report=new Bundle();File fifo=null;Thread sampler=null;JSONObject r=new JSONObject();
        try {
            File files=getTargetContext().getFilesDir(),app=files.getParentFile();String mode=args.getString("mode");
            r.put("mode",mode).put("pid",android.os.Process.myPid()).put("platform","emulator-5562 API35 x86_64; CPU; no inference");
            sampling=true;sampler=new Thread(()->{while(sampling){try{sample(app);Thread.sleep(250);}catch(java.nio.file.NoSuchFileException e){/* Concurrent committed cleanup; next sample retries. */}catch(java.io.UncheckedIOException e){if(!(e.getCause() instanceof java.nio.file.NoSuchFileException)){sampleFailure=e.toString();break;}}catch(Exception e){sampleFailure=e.toString();break;}}},"capacity-sampler");sampler.start();
            if(mode.equals("seed")){
                PackLibrary packs=new PackLibrary(files);
                for(String name:new String[]{"reference.plpack","science.plpack","broad.plpack"}){File f=new File(files,"capacity-seed/"+name);try(InputStream in=new FileInputStream(f)){packs.install(in,()->false,f.length());}Files.delete(f.toPath());}
                PackLibrary.Snapshot s=packs.load();check(s.entries.size()==3,"Three reviewed collections required");r.put("reviewed_documents",s.distinctDocuments).put("reviewed_passages",s.engine.size());
            }else if(mode.equals("import")||mode.equals("cancel")||mode.equals("corrupt")){
                ScaleLibrary lib=new ScaleLibrary(files);File catalog=new File(lib.root,"catalog.json");String prior=catalog.exists()?hash(catalog):"";long before=SharedShardUpdate.uniqueBytes(files);String priorModel=hash(new File(files,"model.gguf"));
                fifo=new File(files,"capacity-input");check(!fifo.exists(),"Previous input remains");Os.mkfifo(fifo.getPath(),0600);long start=System.nanoTime();final long[] read={0};boolean rejected=false;
                try(InputStream raw=new FileInputStream(fifo);InputStream in=new FilterInputStream(raw){public int read(byte[] b,int off,int len)throws IOException{int n=super.read(b,off,len);if(n>0)read[0]+=n;return n;}}){
                    ScaleLibrary.Entry e=lib.install(in,()->mode.equals("cancel")&&read[0]>1048576);
                    check(mode.equals("import"),"Invalid update accepted");r.put("manifest",e.id).put("shards",e.manifest.getJSONArray("shards")).put("kind",e.kind());
                }catch(IOException e){if(mode.equals("import"))throw e;rejected=true;r.put("rejection",e.toString());}
                Files.delete(fifo.toPath());fifo=null;
                r.put("elapsed_ms",(System.nanoTime()-start)/1e6).put("read_bytes",read[0]).put("files_before",before).put("files_after",SharedShardUpdate.uniqueBytes(files)).put("precommit_files_bytes",lib.lastPhysicalPeak).put("admission_bytes",lib.lastAdmissionPeak).put("new_bytes_written",lib.lastTemporaryPeak);
                if(!mode.equals("import")){check(rejected&&hash(catalog).equals(prior),"Rollback catalog changed");check(before==SharedShardUpdate.uniqueBytes(files),"Rollback leaked staging");r.put("rollback",true);}
                check(priorModel.equals(hash(new File(files,"model.gguf"))),"Saved model changed");
             }else if(mode.equals("redirect")){
                check(ScaleWiki.aliasShardName("000_00000.parquet").equals("000_00000")&&ScaleWiki.aliasShardName("000_00000.sqlite").equals("000_00000")&&ScaleWiki.aliasShardName("000_00000").equals("000_00000")&&ScaleWiki.aliasShardName("000_00000.parquet.extra").equals("000_00000.parquet.extra"),"Terminal shard extension normalization");
                ScaleLibrary lib=new ScaleLibrary(files);ScaleLibrary.Entry wiki=null;int shards=0;
                for(ScaleLibrary.Entry e:lib.entries()){shards+=e.manifest.getJSONArray("shards").length();if(e.kind().equals("wiki"))wiki=e;}
                check(shards==31&&wiki!=null,"Full retained catalog required");JSONArray cases=read(new File(files,"capacity-redirect.json")).getJSONArray("cases"),out=new JSONArray();
                for(int i=0;i<cases.length();i++){
                    JSONObject c=cases.getJSONObject(i);long t=System.nanoTime();List<ScaleWiki.Hit> hits=ScaleWiki.search(wiki,c.getString("query"),()->false);check(!hits.isEmpty(),"Missing redirect");ScaleWiki.Hit h=hits.get(0);
                    check(h.id.equals(c.getString("id"))&&h.shard.equals(c.getString("shard"))&&h.title.equals(c.getString("title"))&&!h.mayGenerate(),"Redirect source binding mismatch");ScaleWiki.Read read=ScaleWiki.read(h,getTargetContext().getCacheDir(),()->false);
                    out.put(new JSONObject().put("query",c.getString("query")).put("title",h.title).put("id",h.id).put("shard",h.shard).put("source",ScaleWiki.detail(h,read)).put("ms",(System.nanoTime()-t)/1e6));
                }r.put("queries",out).put("simultaneous_shards",shards);
            }else if(mode.equals("reconcile")){
                ScaleLibrary lib=new ScaleLibrary(files);JSONObject expected=read(new File(files,"capacity-reconcile.json"));String id=hash(new File(files,"capacity-reconcile.json"));ScaleLibrary.Entry found=null;
                for(ScaleLibrary.Entry e:lib.entries())if(e.id.equals(id))found=e;
                check(found!=null,"Failed measurement did not commit expected collection");ScaleLibrary.verifySchema(found.directory,found.manifest,()->false);
                r.put("manifest",id).put("kind",found.kind()).put("shards",found.manifest.getJSONArray("shards")).put("files_after",SharedShardUpdate.uniqueBytes(files)).put("reconciled_import",true).put("measurement_limit","Import committed before sampler failure; original peak and elapsed fields were not persisted, not reconstructed");
            }else if(mode.equals("hash")){
                ScaleLibrary lib=new ScaleLibrary(files);JSONArray rows=new JSONArray();Set<String> seen=new HashSet<>();
                for(ScaleLibrary.Entry e:lib.entries())for(int i=0;i<e.manifest.getJSONArray("files").length();i++){
                    JSONObject spec=e.manifest.getJSONArray("files").getJSONObject(i);if(!seen.add(spec.getString("sha256")))continue;File f=ScaleLibrary.resolve(e.directory,spec.getString("path"));String digest=hash(f);check(digest.equals(spec.getString("sha256")),"Installed object hash mismatch");rows.put(new JSONObject().put("sha256",digest).put("bytes",f.length()).put("path",spec.getString("path")));
                }
                File aux=new File(files,"capacity-aux");for(File f:Objects.requireNonNull(aux.listFiles()))rows.put(new JSONObject().put("sha256",hash(f)).put("bytes",f.length()).put("path","capacity-aux/"+f.getName()));r.put("objects",rows);
            }else if(mode.equals("disable")||mode.equals("enable")||mode.equals("restart")){
                ScaleLibrary lib=new ScaleLibrary(files);Set<String> active=new HashSet<>();for(ScaleLibrary.Entry e:lib.entries())if(mode.equals("enable")||e.kind().equals("places"))active.add(e.id);
                if(!mode.equals("restart"))lib.select(active);
                else for(ScaleLibrary.Entry e:lib.entries())check(e.active==e.kind().equals("places"),"Selection did not survive process restart");
                r.put("catalog",new JSONArray(new String(Files.readAllBytes(new File(lib.root,"catalog.json").toPath()),StandardCharsets.UTF_8)));
            }else if(mode.equals("inspect")){
                ScaleLibrary lib=new ScaleLibrary(files);List<ScaleLibrary.Entry> es=lib.entries();check(es.size()==2,"Two simultaneous bulk collections required");ScaleLibrary.Entry wiki=null,places=null;
                for(ScaleLibrary.Entry e:es){check(e.active&&!e.mayGenerate(),"Active/browse-only state");if(e.kind().equals("wiki"))wiki=e;else places=e;}
                check(wiki!=null&&places!=null&&wiki.manifest.getJSONArray("shards").length()==15&&places.manifest.getJSONArray("shards").length()==16,"All thirty-one shards must be simultaneous");
                ScaleLibrary.verifySchema(wiki.directory,wiki.manifest,()->false);ScaleLibrary.verifySchema(places.directory,places.manifest,()->false);
                r.put("wiki_documents",wiki.manifest.getLong("documents")).put("wiki_full",wiki.manifest.getLong("full_articles")).put("wiki_leads",wiki.manifest.getLong("leads")).put("places_source_records",places.manifest.getLong("source_records"));
                JSONObject protocol=read(new File(files,"capacity-protocol.json"));JSONArray qs=new JSONArray();
                for(String group:new String[]{"wiki_queries","redirects"})for(int i=0;i<protocol.getJSONArray(group).length();i++){
                    String q=protocol.getJSONArray(group).getString(i);long t=System.nanoTime();List<ScaleWiki.Hit> hs=ScaleWiki.search(wiki,q,()->false);check(!hs.isEmpty(),"Missing wiki query "+q);if(group.equals("wiki_queries"))check(hs.get(0).title.equals(q),"Exact title missed");
                    ScaleWiki.Hit h=hs.get(0);ScaleWiki.Read source=ScaleWiki.read(h,getTargetContext().getCacheDir(),()->false);Set<String> shards=new HashSet<>();for(ScaleWiki.Hit x:hs)shards.add(x.shard);
                    qs.put(new JSONObject().put("query",q).put("title",h.title).put("shards_in_top12",shards.size()).put("ms",(System.nanoTime()-t)/1e6).put("source",ScaleWiki.detail(h,source)).put("raw_block_bytes",source.rawBlockBytes).put("temporary_bytes",source.temporaryBytes));
                }r.put("wiki_queries",qs);JSONArray cities=new JSONArray();
                for(int i=0;i<protocol.getJSONArray("cities").length();i++){
                    String name=protocol.getJSONArray("cities").getString(i);long t=System.nanoTime();List<ScalePlaces.City> cs=ScalePlaces.cities(places,name,()->false);check(!cs.isEmpty(),"City missing");ScalePlaces.City c=cs.get(0);List<ScalePlaces.Hit> hs=ScalePlaces.nearby(places,c.lat,c.lon,1,"restaurant",()->false);
                    JSONObject q=new JSONObject().put("city",name).put("count",hs.size()).put("lat",c.lat).put("lon",c.lon).put("ms",(System.nanoTime()-t)/1e6);if(!hs.isEmpty())q.put("source",ScalePlaces.detail(hs.get(0),()->false));cities.put(q);
                }r.put("cities",cities);check(ScalePlaces.nearby(places,19.4326,-99.1332,1,"pocketlore nonexistent category 300",()->false).isEmpty(),"Absent category leak");r.put("absent_category_withheld",true);
                final ScaleLibrary.Entry w=wiki;boolean cancelled=false;try{ScaleWiki.search(w,"Acid",()->true);}catch(InterruptedIOException expected){cancelled=true;}check(cancelled,"Query cancellation");r.put("query_cancelled",true);
                PackLibrary.Snapshot small=new PackLibrary(files).load();check(small.entries.size()==3,"Reviewed collection retention");r.put("reviewed_documents",small.distinctDocuments).put("reviewed_collections",small.entries.size());
            }else throw new IOException("Unknown mode");
            sampling=false;sampler.join();sample(app);check(sampleFailure==null,"Sampler failure: "+sampleFailure);
            r.put("status","PASS").put("sampled_app_logical_peak",logicalPeak).put("sampled_app_allocated_peak",allocatedPeak).put("sampled_pss_peak_kib",pssPeak).put("app_logical_bytes",SharedShardUpdate.uniqueBytes(app)).put("model_sha256",hash(new File(files,"model.gguf"))).put("proc_status",new String(Files.readAllBytes(Paths.get("/proc/self/status")),StandardCharsets.UTF_8));
            ScaleLibrary.write(new File(files,"capacity-result.json"),r.toString(2).getBytes(StandardCharsets.UTF_8));report.putString("result","capacity-result.json");finish(-1,report);
        }catch(Throwable e){report.putString("failure",android.util.Log.getStackTraceString(e));finish(1,report);}
        finally{sampling=false;if(fifo!=null)try{Files.deleteIfExists(fifo.toPath());}catch(Exception ignored){}}
    }
}
