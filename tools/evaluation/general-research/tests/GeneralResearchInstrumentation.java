package org.pocketlore.app;
import android.app.*;import android.os.*;import android.content.*;import android.graphics.*;import android.text.*;import android.text.style.*;import android.view.*;import android.widget.*;import java.io.*;import java.nio.file.*;import java.nio.charset.StandardCharsets;import java.util.*;import java.util.function.*;import org.json.*;
public final class GeneralResearchInstrumentation extends Instrumentation {
 JSONObject report=new JSONObject();JSONArray checks=new JSONArray(),outputs=new JSONArray(),screens=new JSONArray();String run,source,mode;File dir;MainActivity main;
 void ok(boolean b,String label){if(!b)throw new AssertionError(label);checks.put(label);}
 void await(BooleanSupplier b,String label)throws Exception{long end=SystemClock.elapsedRealtime()+30000;while(!b.getAsBoolean()&&SystemClock.elapsedRealtime()<end)Thread.sleep(30);ok(b.getAsBoolean(),label);}
 static Object field(Object o,String name){try{java.lang.reflect.Field f=o.getClass().getDeclaredField(name);f.setAccessible(true);return f.get(o);}catch(Exception e){throw new RuntimeException(e);}}
 byte[] bytes(File f)throws Exception{return Files.readAllBytes(f.toPath());}
 public void onCreate(Bundle b){run=b.getString("run_id");source=b.getString("source_hash");mode=b.getString("mode","install");start();}
 void capture(String name)throws Exception{Bitmap b=getUiAutomation().takeScreenshot();try(OutputStream o=new FileOutputStream(new File(dir,mode+"-"+name+".png"))){ok(b.compress(Bitmap.CompressFormat.PNG,100,o),"screenshot "+name);}StringBuilder nodes=new StringBuilder();nodes(getUiAutomation().getRootInActiveWindow(),nodes);Files.write(new File(dir,mode+"-"+name+".txt").toPath(),nodes.toString().getBytes(StandardCharsets.UTF_8));screens.put(mode+"-"+name);}
 void nodes(android.view.accessibility.AccessibilityNodeInfo n,StringBuilder out){if(n==null)return;android.graphics.Rect b=new android.graphics.Rect();n.getBoundsInScreen(b);out.append(n.getClassName()).append(' ').append(n.getText()).append(' ').append(n.getContentDescription()).append(' ').append(b).append('\n');for(int i=0;i<n.getChildCount();i++)nodes(n.getChild(i),out);}
 void reject(Runnable r,String name){try{r.run();}catch(IllegalArgumentException|java.util.concurrent.CancellationException e){ok(true,name);return;}throw new AssertionError(name);}
 public void onStart(){Bundle result=new Bundle();try{
  dir=new File(getTargetContext().getFilesDir(),"general-research-"+run);ok(dir.isDirectory(),"owned run directory");report.put("run_id",run).put("source_hash",source).put("mode",mode);
  File files=getTargetContext().getFilesDir();PackLibrary lib=new PackLibrary(files);PackLibrary.Snapshot before=lib.load();Set<String> oldHashes=new HashSet<>();for(PackLibrary.Entry e:before.entries)oldHashes.add(e.hash);
  File pack=new File(dir,"valid.plpack");String hash=KnowledgePack.hash(bytes(pack));report.put("pack_sha256",hash);
  long began=SystemClock.elapsedRealtime();PackLibrary.Snapshot installed;
  if(mode.equals("install"))try(InputStream in=new FileInputStream(pack)){installed=lib.install(in,()->false,pack.length());}else installed=lib.load();
  report.put("import_or_reload_ms",SystemClock.elapsedRealtime()-began);ok(installed.entries.stream().anyMatch(e->e.hash.equals(hash)&&e.active),"real reviewed edition active");for(String h:oldHashes)ok(installed.entries.stream().anyMatch(e->e.hash.equals(h)),"retained prior collection");
  byte[] catalog=bytes(new File(files,"pack-library/catalog.json"));
  if(mode.equals("install")){
   for(String name:new String[]{"corrupt","rights","offset"}){boolean denied=false;try(InputStream in=new FileInputStream(new File(dir,name+".plpack"))){lib.install(in,()->false);}catch(Exception e){denied=true;}ok(denied&&Arrays.equals(catalog,bytes(new File(files,"pack-library/catalog.json"))),"real import rollback "+name);}
   boolean cancelled=false;try(InputStream in=new FileInputStream(pack)){lib.install(in,()->true);}catch(InterruptedIOException e){cancelled=true;}ok(cancelled&&Arrays.equals(catalog,bytes(new File(files,"pack-library/catalog.json"))),"cancelled import retains catalog");
  }
  ResearchEngine engine=installed.engine;
  reject(()->ResearchWorkspace.create("Longitude",engine,()->true),"cancel before selection");
  final int[] ticks={0};reject(()->ResearchWorkspace.create("Longitude; Inflation",engine,()->++ticks[0]>4),"cancel during selection without partial result");
  reject(()->ResearchWorkspace.plan("a;b;c;d;e;f;g"),"six part bound");
  ResearchWorkspace.Result retry=ResearchWorkspace.create("Longitude",engine,()->false);ok(!retry.brief.quotes.isEmpty(),"retry produces source quotation");
  ResearchBrief.Quote bound=retry.brief.quotes.get(0);ResearchEngine.Passage p=bound.source;
  reject(()->bound.verify(null),"missing source binding");reject(()->bound.verify(new ResearchEngine.Passage(new String[]{p.id,p.title,p.url,p.sourceDate,p.license,p.text+" fabricated tail"},p.collectionProvenance)),"changed factual tail binding");
  reject(()->bound.verify(new ResearchEngine.Passage(new String[]{"other-edition",p.title,p.url,p.sourceDate,p.license,p.text},p.collectionProvenance)),"changed namespace binding");
  main=(MainActivity)startActivitySync(new Intent(getTargetContext(),MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));runOnMainSync(()->((NativePanel)field(main,"nativePanel")).lowMemory());await(main::resourceIdle,"unloaded research ready");ok(!main.modelReady(),"no loaded model required");await(()->((Button)field(main,"briefButton")).isEnabled(),"installed collection and brief control ready");
  JSONArray cases=new JSONArray(new String(bytes(new File(dir,"cases.json")),StandardCharsets.UTF_8));
  for(int i=0;i<cases.length();i++){
   if(mode.equals("restart")&&i>0)break;
   JSONObject c=cases.getJSONObject(i);String q=c.getString("question");
   long start=SystemClock.elapsedRealtime();ResearchBrief.Brief baseline=ResearchBrief.create(q,engine.research(q),()->false);long baselineMs=SystemClock.elapsedRealtime()-start;
   if(i>0)runOnMainSync(()->((Button)field(main,"editQuestion")).performClick());
   runOnMainSync(()->{((EditText)field(main,"question")).setText(q);((Button)field(main,"briefButton")).performClick();});
   await(()->!(Boolean)field(main,"searching")&&((TextView)field(main,"answer")).getText().toString().contains("Source-backed research brief"),"actual brief UI completed "+c.getString("id"));
   long elapsed=SystemClock.elapsedRealtime()-start-baselineMs;
   ResearchWorkspace.Result expected=ResearchWorkspace.create(q,engine,()->false);String rendered=((TextView)field(main,"answer")).getText().toString();ok(rendered.equals(expected.brief.text),"real rendered output equals controller "+c.getString("id"));
   Spannable displayed=(Spannable)((TextView)field(main,"answer")).getText();ClickableSpan[] links=displayed.getSpans(0,displayed.length(),ClickableSpan.class);ok(links.length==expected.brief.quotes.size(),"typed quote links only");
   JSONArray quotes=new JSONArray(),sections=new JSONArray();for(ResearchBrief.Quote quote:expected.brief.quotes){quote.verify(quote.source);ok(rendered.substring(quote.displayStart,quote.displayEnd).equals(quote.source.text),"literal UTF16 rendering");ok(!quote.source.collectionProvenance.contains("Generation disabled:"),"unreviewed broad source denied");quotes.put(new JSONObject().put("id",quote.source.id).put("title",quote.source.title).put("url",quote.source.url).put("date",quote.source.sourceDate).put("rights",quote.source.license).put("text",quote.source.text).put("sha256",quote.sha256).put("metadata_hash",quote.metadataHash).put("display_start",quote.displayStart).put("display_end",quote.displayEnd));}
   for(ResearchWorkspace.Section section:expected.sections)sections.put(new JSONObject().put("question",section.question).put("scope",section.availability.name()).put("quote_count",section.quotes.size()).put("missing_terms",new JSONArray(section.missingTerms)));
   if(c.getBoolean("absent"))ok(quotes.length()==0,"absent request no attributed quotes "+c.getString("id"));
   JSONObject row=new JSONObject().put("id",c.getString("id")).put("question",q).put("rendered",rendered).put("quotes",quotes).put("sections",sections).put("baseline_rendered",baseline.text).put("baseline_quotes",baseline.quotes.size()).put("baseline_ms",baselineMs).put("ui_total_ms",elapsed).put("generated",false);outputs.put(row);
   if(i==0||i==19||i==20||i==23)capture(c.getString("id"));
   if(links.length>0&&i==0){ActivityMonitor monitor=addMonitor(SourceReaderActivity.class.getName(),null,false);runOnMainSync(()->links[0].onClick((TextView)field(main,"answer")));Activity a=waitForMonitorWithTimeout(monitor,15000);removeMonitor(monitor);ok(a instanceof SourceReaderActivity,"real citation opens source reader");SourceReaderActivity reader=(SourceReaderActivity)a;await(()->reader.content!=null,"source reader ready");ok(reader.entry.body.contains(expected.brief.quotes.get(0).source.text)&&reader.entry.body.contains(hash)&&reader.entry.body.contains("Attribution-ShareAlike 4.0 International"),"exact edition passage and offline license inspected");row.put("inspected_source",reader.entry.body);capture("source-reader");runOnMainSync(reader::finish);waitForIdleSync();}
  }
  Debug.MemoryInfo memory=new Debug.MemoryInfo();Debug.getMemoryInfo(memory);report.put("pss_kib",memory.getTotalPss()).put("app_logical_bytes",SharedShardUpdate.uniqueBytes(new File(getTargetContext().getApplicationInfo().dataDir))).put("collections",installed.entries.size()).put("documents",installed.distinctDocuments).put("passages",installed.engine.size()).put("status","PASS");
 }catch(Throwable e){try{report.put("status","FAIL").put("error",android.util.Log.getStackTraceString(e));if(main!=null){report.put("failure_ui_status",((TextView)field(main,"status")).getText().toString()).put("failure_answer",((TextView)field(main,"answer")).getText().toString());capture("failure");}}catch(Exception ignored){}}
 finally{if(main!=null)runOnMainSync(main::finish);try{report.put("outputs",outputs).put("checks",checks).put("screens",screens);Files.write(new File(dir,mode+".json").toPath(),report.toString(2).getBytes(StandardCharsets.UTF_8));result.putString("receipt",new JSONObject().put("status",report.optString("status")).put("run_id",run).put("source_hash",source).put("mode",mode).put("report_sha256",KnowledgePack.hash(bytes(new File(dir,mode+".json")))).toString());}catch(Exception e){result.putString("error",e.toString());}finish(report.optString("status").equals("PASS")?-1:1,result);}}
}
