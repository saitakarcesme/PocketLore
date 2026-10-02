package org.pocketlore.app;
import android.app.*;import android.os.*;import android.content.*;import android.graphics.*;import android.text.*;import android.text.style.*;import android.view.*;import android.widget.*;import java.io.*;import java.nio.file.*;import java.nio.charset.StandardCharsets;import java.util.*;import java.util.function.*;import org.json.*;
public final class FederatedInstrumentation extends Instrumentation {
 JSONObject report=new JSONObject();JSONArray checks=new JSONArray(),outputs=new JSONArray(),screens=new JSONArray();String run,source,mode;File dir;MainActivity main;
 void ok(boolean b,String label){if(!b)throw new AssertionError(label);checks.put(label);}
 void await(BooleanSupplier b,String label)throws Exception{long end=SystemClock.elapsedRealtime()+30000;while(!b.getAsBoolean()&&SystemClock.elapsedRealtime()<end)Thread.sleep(30);ok(b.getAsBoolean(),label);}
 static Object field(Object o,String name){try{java.lang.reflect.Field f=o.getClass().getDeclaredField(name);f.setAccessible(true);return f.get(o);}catch(Exception e){throw new RuntimeException(e);}}
 byte[] bytes(File f)throws Exception{return Files.readAllBytes(f.toPath());}
 public void onCreate(Bundle b){run=b.getString("run_id");source=b.getString("source_hash");mode=b.getString("mode","install");start();}
 void capture(String name)throws Exception{Bitmap b=getUiAutomation().takeScreenshot();try(OutputStream o=new FileOutputStream(new File(dir,mode+"-"+name+".png"))){ok(b.compress(Bitmap.CompressFormat.PNG,100,o),"screenshot "+name);}StringBuilder nodes=new StringBuilder();nodes(getUiAutomation().getRootInActiveWindow(),nodes);Files.write(new File(dir,mode+"-"+name+".txt").toPath(),nodes.toString().getBytes(StandardCharsets.UTF_8));screens.put(mode+"-"+name);}
 void nodes(android.view.accessibility.AccessibilityNodeInfo n,StringBuilder out){if(n==null)return;android.graphics.Rect b=new android.graphics.Rect();n.getBoundsInScreen(b);out.append(n.getClassName()).append(' ').append(n.getText()).append(' ').append(n.getContentDescription()).append(' ').append(b).append('\n');for(int i=0;i<n.getChildCount();i++)nodes(n.getChild(i),out);}
 void reject(Runnable r,String name){try{r.run();}catch(IllegalArgumentException|java.util.concurrent.CancellationException e){ok(true,name);return;}throw new AssertionError(name);}
 boolean clickNode(android.view.accessibility.AccessibilityNodeInfo n,String label){if(n==null)return false;if(label.contentEquals(n.getText()==null?"":n.getText())&&n.isClickable())return n.performAction(android.view.accessibility.AccessibilityNodeInfo.ACTION_CLICK);for(int i=0;i<n.getChildCount();i++)if(clickNode(n.getChild(i),label))return true;return false;}
 void tap(String label)throws Exception{long end=SystemClock.elapsedRealtime()+10000;while(SystemClock.elapsedRealtime()<end){if(clickNode(getUiAutomation().getRootInActiveWindow(),label)){waitForIdleSync();return;}Thread.sleep(50);}throw new AssertionError("Missing actionable control: "+label);}
 static long meter()throws Exception{try(ResourceStorage.Reservation r=ResourceStorage.reserve(0)){return r.projectedBytes-held();}}
 static long held()throws Exception{java.lang.reflect.Field f=ResourceStorage.class.getDeclaredField("appLedger");f.setAccessible(true);return ((ResourceStorage.Ledger)f.get(null)).reservedBytes();}
 JSONObject external()throws Exception{
  android.content.pm.ApplicationInfo a=getTargetContext().getApplicationInfo();List<String> roots=new ArrayList<>(Arrays.asList(a.dataDir,a.sourceDir));
  if(new File(a.nativeLibraryDir).exists())roots.add(new File(a.nativeLibraryDir).getCanonicalPath());if(a.splitSourceDirs!=null)roots.addAll(Arrays.asList(a.splitSourceDirs));
  Set<String> seen=new HashSet<>();long logical=0,allocated=0,covered=0;JSONArray rows=new JSONArray();
  // Independent executable observations, without shell parsing or UiAutomation teardown.
  for(String root:roots){
   List<String> paths=new ArrayList<>();try(java.util.stream.Stream<java.nio.file.Path> walk=Files.walk(java.nio.file.Path.of(root))){Iterator<java.nio.file.Path> iterator=walk.iterator();while(iterator.hasNext()){if(paths.size()>=200000)throw new IOException("Independent traversal bound");paths.add(iterator.next().toString());}}
   for(int offset=0;offset<paths.size();offset+=64){
    List<String> command=new ArrayList<>(Arrays.asList("/system/bin/stat","-c","%d %i %s %b"));command.addAll(paths.subList(offset,Math.min(offset+64,paths.size())));
    java.lang.Process process=new ProcessBuilder(command).redirectErrorStream(true).start();
    try(BufferedReader reader=new BufferedReader(new InputStreamReader(process.getInputStream()))){String line;while((line=reader.readLine())!=null){
     String[] x=line.trim().split(" +");if(x.length!=4||!line.matches("[0-9 ]+"))throw new IOException("Independent stat failed: "+line);
     long size=Long.parseLong(x[2]),blocks=Long.parseLong(x[3])*512;rows.put(line);if(seen.add(x[0]+":"+x[1])){logical+=size;allocated+=blocks;covered+=Math.max(size,blocks);}
    }}if(process.waitFor()!=0)throw new IOException("Independent stat process failed");
   }
  }
  return new JSONObject().put("logical",logical).put("allocated",allocated).put("covered",covered).put("unique_inodes",seen.size()).put("stat_rows",rows);
 }
 void measurePackLifecycle(PackLibrary library,File pack,File catalog)throws Exception {
  byte[] saved=bytes(catalog);JSONObject measurements=new JSONObject();
  ok(held()==0,"initial staging reservation released");measurements.put("before",external().put("reserved",held()).put("meter",meter()));
  final boolean[] sampled={false};final long[] count={0};
  try(InputStream original=new FileInputStream(pack);InputStream observed=new FilterInputStream(original){
   @Override public int read(byte[] b,int off,int len)throws IOException{
    if(count[0]>=65536&&!sampled[0]){sampled[0]=true;try{
     long reserved=held();ok(reserved==ResourceStorage.stagePeak(pack.length()+2L*BroadPack.MAX_DATABASE+16L*1024*1024),"real pack stage reservation held");
     measurements.put("during",external().put("reserved",reserved).put("meter",meter()).put("copied_bytes_before_next_read",count[0]));
    }catch(Exception e){throw new IOException("Stage observation failed",e);}}
    int n=super.read(b,off,Math.min(len,65536));if(n>0)count[0]+=n;return n;
   }
  }){library.install(observed,()->false,pack.length());}
  ok(sampled[0]&&held()==0,"real pack staging sampled and released");
  measurements.put("after",external().put("reserved",held()).put("meter",meter()));
  ok(Arrays.equals(saved,bytes(catalog)),"measured repeat import retains exact catalog");
  report.put("storage_lifecycle",measurements);
 }
 public void onStart(){Bundle result=new Bundle();try{
  File files=getTargetContext().getFilesDir();dir=new File(files,"federated-"+run);report.put("run_id",run).put("source_hash",source).put("mode",mode);
  PackLibrary lib=new PackLibrary(files);PackLibrary.Snapshot prior=lib.load();Set<String> retained=new HashSet<>();for(PackLibrary.Entry e:prior.entries)retained.add(e.hash);
  File expanded=new File(dir,"expanded.plpack"),science=new File(dir,"science.plpack");
  String expandedHash=KnowledgePack.hash(bytes(expanded)),scienceHash=KnowledgePack.hash(bytes(science));
  JSONObject protocol=new JSONObject(new String(bytes(new File(dir,"development.json")),StandardCharsets.UTF_8));
  if(mode.equals("install")){
   try(InputStream in=new FileInputStream(expanded)){lib.install(in,()->false,expanded.length());}
   String personalId="personal-"+KnowledgePack.hash(protocol.getString("personal_fixture").getBytes(StandardCharsets.UTF_8)).substring(0,24);if(prior.entries.stream().noneMatch(e->e.id.equals(personalId))) {
   byte[] personal=PersonalDocuments.convert(new ByteArrayInputStream(protocol.getString("personal_fixture").getBytes(StandardCharsets.UTF_8)),"Observing notebook.txt","Public development fixture, not a real person's data","2026-10-02","Task490 frozen constructed fixture",getTargetContext().getCacheDir(),()->false);
   Files.write(new File(dir,"personal.plpack").toPath(),personal);try(InputStream in=new ByteArrayInputStream(personal)){lib.install(in,()->false,personal.length);}
   }
  }
  main=(MainActivity)startActivitySync(new Intent(getTargetContext(),MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK).putExtra("reload_library",true));
  await(()->!(Boolean)field(main,"importing")&&((Button)field(main,"briefButton")).isEnabled(),"library ready");
  runOnMainSync(()->((NativePanel)field(main,"nativePanel")).lowMemory());await(main::resourceIdle,"model unloaded");
  if(mode.equals("install")){
   android.net.Uri uri=android.net.Uri.parse("content://org.pocketlore.fixture.reference/"+run+"/science.plpack");
   runOnMainSync(()->main.onActivityResult(411,Activity.RESULT_OK,new Intent().setData(uri)));tap("Import");
   await(()->!(Boolean)field(main,"importing")&&((TextView)field(main,"answer")).getText().toString().contains("Collection retained"),"actual science Activity import");
  }
  PackLibrary.Snapshot installed=lib.load();for(String h:retained)ok(installed.entries.stream().anyMatch(e->e.hash.equals(h)),"retained existing collection");
  ok(installed.entries.stream().anyMatch(e->e.hash.equals(expandedHash)&&e.active)&&installed.entries.stream().anyMatch(e->e.hash.equals(scienceHash)&&e.active),"reviewed and science selected together");
  ResearchEngine single;try(InputStream in=new FileInputStream(expanded)){single=KnowledgePack.read(in,true).engine;}
  ResearchEngine engine=installed.engine;JSONArray questions=protocol.getJSONArray("questions");
  for(int i=0;i<questions.length();i++){
   String q=questions.getString(i);if(i>0)runOnMainSync(()->((Button)field(main,"editQuestion")).performClick());
   long begin=SystemClock.elapsedRealtimeNanos();runOnMainSync(()->{((EditText)field(main,"question")).setText(q);((Button)field(main,"briefButton")).performClick();});
   await(()->!(Boolean)field(main,"searching")&&((TextView)field(main,"answer")).getText().toString().startsWith("Source-backed research brief"),"UI research "+i);
   long elapsed=SystemClock.elapsedRealtimeNanos()-begin;ResearchWorkspace.Result expected=ResearchWorkspace.create(q,engine,()->false);
   String rendered=((TextView)field(main,"answer")).getText().toString();ok(rendered.equals(expected.brief.text),"UI exact controller output "+i);
   JSONArray quotes=new JSONArray();for(ResearchBrief.Quote quote:expected.brief.quotes){quote.verify(quote.source);ok(rendered.substring(quote.displayStart,quote.displayEnd).equals(quote.source.text),"exact UTF16 quote");quotes.put(new JSONObject().put("id",quote.source.id).put("text",quote.source.text).put("title",quote.source.title).put("url",quote.source.url).put("provenance",quote.source.collectionProvenance).put("sha256",quote.sha256).put("start",quote.displayStart).put("end",quote.displayEnd));}
   if(i==0){Set<String> editions=new HashSet<>();for(ResearchBrief.Quote quote:expected.brief.quotes)editions.add(quote.source.id.split("_",2)[0]);ok(editions.size()>=3,"one request spans reviewed science and personal editions");}
   if(i==5||i==6)ok(quotes.length()==0,"private or live request withheld");
   outputs.put(new JSONObject().put("question",q).put("rendered",rendered).put("quotes",quotes).put("ui_ns",elapsed).put("single_pack_baseline",ResearchWorkspace.create(q,single,()->false).brief.text).put("generated",false));
   if(i==0){capture("federated");Spannable displayed=(Spannable)((TextView)field(main,"answer")).getText();ClickableSpan[] links=displayed.getSpans(0,displayed.length(),ClickableSpan.class);ok(links.length==quotes.length(),"typed source links");ActivityMonitor monitor=addMonitor(SourceReaderActivity.class.getName(),null,false);runOnMainSync(()->links[0].onClick((TextView)field(main,"answer")));Activity a=waitForMonitorWithTimeout(monitor,10000);removeMonitor(monitor);if(a instanceof SourceReaderActivity){SourceReaderActivity reader=(SourceReaderActivity)a;await(()->reader.entry!=null&&reader.content!=null,"source snapshot ready");ok(reader.entry.body.contains(expected.brief.quotes.get(0).source.text),"reader exact snapshot");report.put("reader_route","saved snapshot");}else{tap("Read without saving");StringBuilder visible=new StringBuilder();nodes(getUiAutomation().getRootInActiveWindow(),visible);ok(visible.toString().contains(expected.brief.quotes.get(0).source.text)&&visible.toString().contains(expected.brief.quotes.get(0).source.id),"unsaved reader exact quote and citation");report.put("reader_route","existing unsaved reader; notebook full");}capture("reader");sendKeyDownUpSync(android.view.KeyEvent.KEYCODE_BACK);await(main::hasWindowFocus,"Back returns");}
  }
  final int[] calls={0};reject(()->engine.sourceResearch("DNA earthquake astronomy",()->++calls[0]>8),"cancellation within retrieval");ok(calls[0]>8,"cancellation polled inside retrieval");ok(!engine.sourceResearch("DNA").hits.isEmpty(),"retry after cancellation");
  Set<String> active=new HashSet<>();for(PackLibrary.Entry e:installed.entries)if(e.active)active.add(e.hash);
  Set<String> disabled=new HashSet<>(active);disabled.remove(scienceHash);
  try{PackLibrary.Snapshot without=lib.select(disabled);for(ResearchEngine.Hit h:without.engine.sourceResearch("DNA").hits)ok(!h.passage.id.startsWith("p"+scienceHash+"_"),"disabled science excluded");}finally{lib.select(active);}
  runOnMainSync(()->((Button)field(main,"collections")).performClick());capture("collection-controls");tap("Cancel");ok(lib.load().entries.stream().filter(e->e.active).count()==active.size(),"selection cancel retained");
  // Isolated library tests delete only invocation-owned copies, never real user collections.
  File isolated=new File(dir,"isolated");isolated.mkdirs();PackLibrary sandbox=new PackLibrary(isolated);try(InputStream in=new FileInputStream(science)){sandbox.install(in,()->false,science.length());}sandbox.remove(scienceHash);ok(sandbox.load().engine.sourceResearch("DNA").hits.isEmpty(),"deleted source absent in rebuilt catalog");
  List<ResearchEngine.Passage> collision=new ArrayList<>();collision.add(new ResearchEngine.Passage(new String[]{"paaa_same","Condition","fixture://scope","2025","Constructed test","Clear weather is required."},"Collection: a"));collision.add(new ResearchEngine.Passage(new String[]{"pbbb_same","Condition","fixture://scope","2026","Constructed test","Rain postpones observing."},"Collection: b"));
  ResearchEngine synthetic=new ResearchEngine(collision);ResearchEngine.Result ranked=synthetic.sourceResearch("Condition");ok(ranked.hits.size()==2&&!ranked.hits.get(0).passage.id.equals(ranked.hits.get(1).passage.id),"colliding local IDs retain qualified source editions");ok(ranked.hits.stream().anyMatch(h->h.passage.text.contains("Rain"))&&ranked.hits.stream().anyMatch(h->h.passage.text.contains("Clear")),"conflicting conditions preserved verbatim");
  List<ResearchEngine.Hit> duplicated=new ArrayList<>();duplicated.add(ranked.hits.get(0));duplicated.add(ranked.hits.get(0));ok(ResearchEngine.diverse(duplicated).size()==1,"duplicate citation candidate suppressed");
  ResearchEngine.Passage bad=new ResearchEngine.Passage(new String[]{ranked.hits.get(0).passage.id,"Wrong","fixture://wrong","2026","Constructed test","Wrong source identity."},"Collection: wrong");
  reject(()->ResearchEngine.diverse(new ArrayList<>(Arrays.asList(ranked.hits.get(0),new ResearchEngine.Hit(bad,1)))),"conflicting full citation identity rejected");
  ResearchEngine.Passage shared=new ResearchEngine.Passage(new String[]{"paaa_shared","Shared condition","fixture://shared","2026","Constructed test","Clear weather is required."},"Collection: first\nEdition SHA-256: aaaa\nAlso retained in:\nCollection: second\nEdition SHA-256: bbbb");
  ResearchEngine.Result sharedResult=new ResearchEngine(Arrays.asList(shared)).sourceResearch("Shared condition");ok(sharedResult.collectionCandidates.size()==2&&sharedResult.hits.size()==1,"deduplicated source reports both collections once");
  JSONArray catalog=new JSONArray();for(PackLibrary.Entry e:lib.load().entries)catalog.put(new JSONObject().put("id",e.id).put("hash",e.hash).put("active",e.active));report.put("catalog",catalog);
  Debug.MemoryInfo memory=new Debug.MemoryInfo();Debug.getMemoryInfo(memory);report.put("pss_kib",memory.getTotalPss()).put("documents",installed.distinctDocuments).put("passages",engine.size()).put("status","PASS");
 }catch(Throwable e){try{report.put("status","FAIL").put("error",android.util.Log.getStackTraceString(e));if(main!=null)report.put("pack_status",((TextView)field(main,"packStatus")).getText().toString());capture("failure");}catch(Exception ignored){}}
 finally{if(main!=null)runOnMainSync(main::finish);try{report.put("outputs",outputs).put("checks",checks).put("screens",screens);Files.write(new File(dir,mode+".json").toPath(),report.toString(2).getBytes(StandardCharsets.UTF_8));result.putString("receipt",new JSONObject().put("run_id",run).put("source_hash",source).put("report_sha256",KnowledgePack.hash(bytes(new File(dir,mode+".json")))).toString());}catch(Exception e){result.putString("error",e.toString());}finish(report.optString("status").equals("PASS")?-1:1,result);}}
}
