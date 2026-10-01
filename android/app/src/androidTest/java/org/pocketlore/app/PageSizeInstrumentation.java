package org.pocketlore.app;
import android.app.Instrumentation;import android.os.*;import android.system.*;import android.database.sqlite.SQLiteDatabase;import java.io.*;import java.nio.charset.StandardCharsets;import java.nio.file.*;import java.security.*;import java.util.*;import java.util.concurrent.atomic.*;import org.json.*;
/** Bounded real baseline JNI on a 16KB emulator; not answer quality or phone evidence. */
public final class PageSizeInstrumentation extends Instrumentation {
 static void check(boolean b,String message){if(!b)throw new AssertionError(message);}
 static byte[] bytes(String s){return s.getBytes(StandardCharsets.UTF_8);}
 @Override public void onCreate(Bundle args){super.onCreate(args);start();}
 @Override public void onStart(){Bundle result=new Bundle();JSONObject r=new JSONObject();long session=0;AtomicBoolean sampling=new AtomicBoolean(true);AtomicLong peak=new AtomicLong();Thread memory=new Thread(()->{while(sampling.get()){Debug.MemoryInfo m=new Debug.MemoryInfo();Debug.getMemoryInfo(m);peak.accumulateAndGet(m.getTotalPss(),Math::max);try{Thread.sleep(100);}catch(InterruptedException e){return;}}});memory.start();
 try{
  long page=Os.sysconf(OsConstants._SC_PAGESIZE);check(page==16384,"Process libc page size is not16384");check(Build.VERSION.SDK_INT==37,"API37 required");
  r.put("page_size",page).put("sdk",Build.VERSION.SDK_INT).put("fingerprint",Build.FINGERPRINT).put("abi",Build.SUPPORTED_ABIS[0]);
  File model=new File(getTargetContext().getFilesDir(),"page-size-test/model.gguf");MessageDigest digest=MessageDigest.getInstance("SHA-256");try(InputStream in=new FileInputStream(model)){byte[] b=new byte[65536];int n;while((n=in.read(b))!=-1)digest.update(b,0,n);}StringBuilder hash=new StringBuilder();for(byte b:digest.digest())hash.append(String.format(Locale.ROOT,"%02x",b&255));
  check(hash.toString().equals("74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db"),"Baseline model hash mismatch");r.put("model_sha256",hash).put("model_bytes",model.length());
  r.put("runtime",NativeRuntime.identity()).put("index_runtime",NativeIndex.identity());
  File db=new File(getTargetContext().getCacheDir(),"page-size-test.sqlite");try(SQLiteDatabase sql=SQLiteDatabase.openOrCreateDatabase(db,null)){sql.execSQL("CREATE TABLE IF NOT EXISTS fixture(value TEXT)");sql.execSQL("DELETE FROM fixture");sql.execSQL("INSERT INTO fixture VALUES ('alignment fixture')");}
  JSONArray rows=NativeIndex.rows(db.getPath(),"SELECT value FROM fixture",new String[0],1,()->false);check(rows.getJSONArray(0).getString(0).equals("alignment fixture"),"Actual native SQLite query failed");r.put("index_query",rows);
  session=NativeRuntime.create();long begin=System.nanoTime();NativeRuntime.load(session,bytes(model.getPath()));r.put("load_ms",(System.nanoTime()-begin)/1e6);
  NativeRuntime.cancel(session);int cancelled=NativeRuntime.generate(session,bytes("Hello"),8,piece->{});check(cancelled<0,"Cancellation failed");NativeRuntime.reset(session);
  String system="Reply concisely in English.",prompt="Say hello in a short sentence.";r.put("system_prompt",system).put("prompt",prompt).put("max_tokens",24).put("prompt_tokens",NativeRuntime.countChatTokens(session,bytes(system),bytes(prompt)));
  ByteArrayOutputStream output=new ByteArrayOutputStream();AtomicLong first=new AtomicLong();begin=System.nanoTime();int tokens=NativeRuntime.generateChat(session,bytes(system),bytes(prompt),24,piece->{first.compareAndSet(0,System.nanoTime());output.write(piece,0,piece.length);});long end=System.nanoTime();String text=output.toString("UTF-8");check(tokens>0&&tokens<=24&&!text.trim().isEmpty(),"Real generation empty/invalid");
  r.put("tokens",tokens).put("output",text).put("first_token_ms",(first.get()-begin)/1e6).put("generation_ms",(end-begin)/1e6).put("resource_state",new JSONArray(NativeRuntime.resourceState()));
  r.put("maps",new String(Files.readAllBytes(Paths.get("/proc/self/maps")),StandardCharsets.UTF_8));
  NativeRuntime.close(session);session=0;session=NativeRuntime.create();begin=System.nanoTime();NativeRuntime.load(session,bytes(model.getPath()));r.put("reload_ms",(System.nanoTime()-begin)/1e6);NativeRuntime.close(session);session=0;
  r.put("checks",new JSONArray(Arrays.asList("process_page_size","both_jni_loads","native_index_query","baseline_model_hash","real_load","cancel_before_generation","real_generation_after_cancel","close_reload"))).put("status","pass");
 }catch(Throwable t){try{r.put("status","fail").put("error",android.util.Log.getStackTraceString(t));}catch(Exception ignored){}}finally{if(session!=0)NativeRuntime.close(session);sampling.set(false);try{memory.join(1000);r.put("sampled_peak_pss_kib",peak.get());Files.write(new File(getTargetContext().getFilesDir(),"page-size-test/result.json").toPath(),r.toString(2).getBytes(StandardCharsets.UTF_8));result.putString("stream",r.toString(2)+"\n");}catch(Exception e){result.putString("stream",android.util.Log.getStackTraceString(e));}finish("pass".equals(r.optString("status"))?-1:1,result);}}
}
