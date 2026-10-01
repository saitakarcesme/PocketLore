package org.pocketlore.app;
import android.app.Instrumentation;
import android.os.Bundle;
import org.json.*;
import java.nio.file.*;
import java.util.*;
/** Public fixture replay through the actual Android controller; no generation. */
public final class BriefInstrumentation extends Instrumentation {
 @Override public void onCreate(Bundle b){super.onCreate(b);start();}
 @Override public void onStart(){Bundle result=new Bundle();try{
  JSONArray sources=new JSONArray(new String(Files.readAllBytes(Path.of("/data/local/tmp/pocketlore-brief226/sources.json")),java.nio.charset.StandardCharsets.UTF_8));
  JSONArray cases=new JSONArray(new String(Files.readAllBytes(Path.of("/data/local/tmp/pocketlore-brief226/cases.json")),java.nio.charset.StandardCharsets.UTF_8));
  List<ResearchEngine.Passage> ps=new ArrayList<>();
  for(int i=0;i<sources.length();i++){JSONObject s=sources.getJSONObject(i);ps.add(new ResearchEngine.Passage(new String[]{s.getString("id"),s.getString("title"),s.getString("url"),s.getString("date"),s.getString("rights"),s.getString("text")},"Edition SHA-256: "+s.getString("edition_sha256")+"; passage SHA-256: "+s.getString("sha256")));}
  ResearchEngine engine=new ResearchEngine(ps);JSONArray rows=new JSONArray();long started=System.nanoTime();
  for(int i=0;i<cases.length();i++){JSONObject c=cases.getJSONObject(i);String q=c.getString("question");long start=System.nanoTime();ResearchBrief.Brief b=ResearchBrief.create(q,engine.research(q),()->false);
   JSONObject row=new JSONObject();row.put("id",c.getString("id"));row.put("rendered_sha256",ResearchBrief.hash(b.text));row.put("total_ns",System.nanoTime()-start);row.put("generated",b.generated);row.put("availability",b.availability.name());
   if(c.optBoolean("absent",false) && (!b.quotes.isEmpty()||b.availability==EvidenceAvailability.Scope.REFERENCE))throw new AssertionError("Absent request not withheld");
   if(c.has("scope")&&!b.availability.name().equals(c.getString("scope").toUpperCase(java.util.Locale.ROOT)))throw new AssertionError("Supplementary scope mismatch");row.put("quotes",b.quotes.size());
   for(ResearchBrief.Quote quote:b.quotes){quote.verify(quote.source);if(!b.text.substring(quote.displayStart,quote.displayEnd).equals(quote.source.text))throw new AssertionError("UTF-16 quote mismatch");}rows.put(row);
  }
  try{ResearchBrief.create("cancel",engine.research("DNA"),()->true);throw new AssertionError("Cancellation accepted");}catch(java.util.concurrent.CancellationException expected){}
  JSONObject out=new JSONObject();out.put("environment","AOSP emulator Android controller; no inference or phone measurement");out.put("rows",rows);out.put("total_ns",System.nanoTime()-started);out.put("java_used_bytes",Runtime.getRuntime().totalMemory()-Runtime.getRuntime().freeMemory());
  Files.write(getTargetContext().getFilesDir().toPath().resolve("brief226-results.json"),out.toString(2).getBytes(java.nio.charset.StandardCharsets.UTF_8));result.putString("stream","36 Android quote replays and cancellation passed\n");finish(-1,result);
 }catch(Throwable error){result.putString("stream",android.util.Log.getStackTraceString(error));finish(1,result);}}
}
