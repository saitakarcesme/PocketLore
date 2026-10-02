package org.pocketlore.app;
import android.app.*;import android.os.*;import android.content.*;import android.system.Os;
import java.io.*;import java.nio.file.*;import java.util.*;import java.util.concurrent.*;import java.util.concurrent.atomic.*;import org.json.*;

/** Tiny invocation-owned fixtures; no native load, inference or recognition. */
public final class StorageMeterInstrumentation extends Instrumentation {
 Bundle args;File fixture;JSONObject report=new JSONObject();JSONArray checks=new JSONArray();
 interface Action{void run()throws Exception;}
 void ok(boolean b,String name){if(!b)throw new AssertionError(name);checks.put(name);}
 void reject(Action a,String name)throws Exception{try{a.run();}catch(IOException e){checks.put(name);return;}throw new AssertionError(name);}
 public void onCreate(Bundle b){args=b;start();}
 static long meter()throws Exception{try(ResourceStorage.Reservation r=ResourceStorage.reserve(0)){return r.projectedBytes;}}
 static long held()throws Exception{java.lang.reflect.Field f=ResourceStorage.class.getDeclaredField("appLedger");f.setAccessible(true);return ((ResourceStorage.Ledger)f.get(null)).reservedBytes();}
 JSONObject external()throws Exception{
  android.content.pm.ApplicationInfo a=getTargetContext().getApplicationInfo();List<String> roots=new ArrayList<>(Arrays.asList(a.dataDir,a.sourceDir));
  if(new File(a.nativeLibraryDir).exists())roots.add(new File(a.nativeLibraryDir).getCanonicalPath());if(a.splitSourceDirs!=null)roots.addAll(Arrays.asList(a.splitSourceDirs));
  Set<String> seen=new HashSet<>();long logical=0,allocated=0,covered=0;JSONArray rows=new JSONArray();
  for(String root:roots){java.lang.Process p=new ProcessBuilder("/system/bin/sh","-c","find \"$1\" -exec stat -c '%d %i %s %b' {} +","meter",root).redirectErrorStream(true).start();
   try(BufferedReader reader=new BufferedReader(new InputStreamReader(p.getInputStream()))){String line;while((line=reader.readLine())!=null){String[] x=line.trim().split(" +");if(x.length!=4)throw new IOException("Independent stat failed: "+line);long size=Long.parseLong(x[2]),blocks=Long.parseLong(x[3])*512;rows.put(line);if(seen.add(x[0]+":"+x[1])){logical+=size;allocated+=blocks;covered+=Math.max(size,blocks);}}}if(p.waitFor()!=0)throw new IOException("Independent find/stat failed");}
  return new JSONObject().put("logical",logical).put("allocated",allocated).put("covered",covered).put("unique_inodes",seen.size()).put("stat_rows",rows);
 }
 void reconcile(String name)throws Exception{long before=meter();JSONObject observed=external();long after=meter();ok(before==after&&after==observed.getLong("covered"),name+"_independent_stat_exact");report.put(name,observed.put("meter",after));}
 void remove(File f)throws IOException{if(Files.isSymbolicLink(f.toPath())){Files.delete(f.toPath());return;}if(f.isDirectory()){File[] children=f.listFiles();if(children==null)throw new IOException("Cannot enumerate own fixture");for(File c:children)remove(c);}Files.delete(f.toPath());}
 public void onStart(){boolean pass=false;try{
  String id=args.getString("run_id");if(id==null||!id.matches("[A-Za-z0-9-]+"))throw new IOException("Invalid invocation");report.put("run_id",id).put("source_manifest_sha256",args.getString("source_manifest_sha256")).put("sdk",Build.VERSION.SDK_INT).put("page_size",Os.sysconf(android.system.OsConstants._SC_PAGESIZE));
  ok(getTargetContext().getApplicationContext() instanceof StorageApplication,"actual_storage_application_started");ok(held()==0,"startup_zero_reservations");
  fixture=new File(getTargetContext().getFilesDir(),"storage-meter-"+id);ok(fixture.mkdir(),"fresh_owned_fixture");
  reconcile("before");File stage=new File(fixture,"model.partial"),kept=new File(fixture,"kept.gguf");Files.write(kept.toPath(),"GGUFretained fixture".getBytes());byte[] retained=Files.readAllBytes(kept.toPath());
  byte[] data=new byte[8192];data[0]='G';data[1]='G';data[2]='U';data[3]='F';
  AtomicBoolean observed=new AtomicBoolean();InputStream inspected=new ByteArrayInputStream(data){public synchronized int read(byte[] b,int o,int n){if(pos>0&&!observed.getAndSet(true))try{ok(held()==ResourceStorage.stagePeak(data.length),"during_copy_reservation_held");reconcile("during");}catch(Exception e){throw new RuntimeException(e);}return super.read(b,o,Math.min(n,4096));}};
  ModelImport.copy(inspected,stage,data.length,fixture.getUsableSpace(),()->false);ok(held()==0,"copy_success_release");ok(Arrays.equals(retained,Files.readAllBytes(kept.toPath())),"selected_fixture_retained");
  Files.createLink(new File(fixture,"hardlink").toPath(),stage.toPath());reconcile("hardlink");
  File bad=new File(fixture,"unknown-link");Files.createSymbolicLink(bad.toPath(),kept.toPath());try{reject(()->meter(),"unknown_symlink_denied");}finally{Files.delete(bad.toPath());}
  // Exact same measured process meter, no virtual disk override or real large allocation.
  long available=fixture.getUsableSpace();long used=meter();long budget=Math.min(available-ResourceStorage.RESERVE_BYTES,ResourceStorage.TARGET_BYTES-used)-1024*1024;ok(budget>0,"bounded_reservation_allowance");
  CountDownLatch start=new CountDownLatch(1),attempted=new CountDownLatch(2),release=new CountDownLatch(1);AtomicInteger admitted=new AtomicInteger(),denied=new AtomicInteger();AtomicReference<Throwable> error=new AtomicReference<>();
  Runnable job=()->{ResourceStorage.Reservation token=null;try{start.await();try{token=ResourceStorage.reserve(budget);admitted.incrementAndGet();}catch(IOException e){denied.incrementAndGet();}finally{attempted.countDown();}release.await();}catch(Throwable e){error.set(e);}finally{if(token!=null)token.close();}};
  Thread a=new Thread(job),b=new Thread(job);a.start();b.start();start.countDown();try{ok(attempted.await(30,TimeUnit.SECONDS),"concurrent_completed");ok(admitted.get()==1&&denied.get()==1,"concurrent_one_admitted");}finally{release.countDown();a.join(30000);b.join(30000);}ok(error.get()==null&&held()==0,"concurrent_release");report.put("reserved_virtual_only_bytes",budget);
  reject(()->ModelImport.copy(new ByteArrayInputStream(data),stage,data.length,fixture.getUsableSpace(),()->true),"copy_cancelled");ok(!stage.exists()&&held()==0,"cancel_cleanup_release");
  InputStream failed=new InputStream(){public int read()throws IOException{throw new IOException("fixture provider failure");}};
  reject(()->ModelImport.copy(failed,stage,8192,fixture.getUsableSpace(),()->false),"copy_failure");ok(!stage.exists()&&held()==0,"failure_cleanup_release");
  ModelImport.copy(new ByteArrayInputStream(data),stage,data.length,fixture.getUsableSpace(),()->false);ok(stage.length()==8192&&held()==0,"same_process_retry");
  byte[] pack=PersonalDocuments.convert(new ByteArrayInputStream("Orchid fixture reference.".getBytes()),"fixture.txt","Task430 fixture","2026-10-02","fixture://task430",fixture,()->false);
  PackLibrary lib=new PackLibrary(fixture);PackLibrary.Snapshot installed=lib.install(new ByteArrayInputStream(pack),()->false,pack.length);ByteArrayOutputStream exported=new ByteArrayOutputStream();lib.exportCollection(installed.entries.get(0).hash,exported,()->false);ok(Arrays.equals(pack,exported.toByteArray()),"personal_import_export_startup");ok(held()==0,"personal_release");
  reject(()->AttachmentAssets.install(fixture,false,new ByteArrayInputStream(new byte[8]),()->false),"optional_invalid_asset_denied");ok(!AttachmentAssets.file(fixture,false).exists()&&held()==0,"optional_failure_release");
  reconcile("after");ok(Arrays.equals(retained,Files.readAllBytes(kept.toPath())),"retained_fixture_final");pass=true;
 }catch(Throwable e){try{report.put("error",android.util.Log.getStackTraceString(e));}catch(Exception ignored){}}
 finally{try{if(fixture!=null&&fixture.exists())remove(fixture);ok(fixture!=null&&!fixture.exists(),"owned_fixture_removed");ok(held()==0,"final_zero_reservations");}catch(Throwable e){pass=false;try{report.put("cleanup_error",e.toString());}catch(Exception ignored){}}
  try{report.put("checks",checks).put("status",pass?"PASS":"FAIL");Bundle result=new Bundle();result.putString("storage_receipt",report.toString());finish(pass?Activity.RESULT_OK:Activity.RESULT_CANCELED,result);}catch(Exception e){finish(Activity.RESULT_CANCELED,new Bundle());}}
 }
}
