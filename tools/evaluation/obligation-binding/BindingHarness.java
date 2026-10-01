package org.pocketlore.app;
import java.nio.file.*;import java.nio.charset.StandardCharsets;import java.io.*;import java.util.*;
public final class BindingHarness {
 static byte[] b(String s){return s.getBytes(StandardCharsets.UTF_8);}static String q(String s){return ScaleHarness.q(s);}static String decode(String s){return ScaleHarness.decode(s);}
 static final class Stage {String raw="",failure="";int tokens,promptTokens;double firstMs,totalMs;long[] peak=new long[5];}
 static Stage generate(long session,String system,String prompt,int budget,Path path)throws Exception{
  Stage s=new Stage();s.promptTokens=NativeRuntime.countChatTokens(session,b(system),b(prompt));Files.writeString(Path.of(path+".prompt.txt"),system+"\n--- USER ---\n"+prompt,StandardOpenOption.CREATE_NEW);
  if(s.promptTokens+budget>4096){s.failure="Context admission failed";return s;}
  ByteArrayOutputStream buf=new ByteArrayOutputStream();long start=System.nanoTime();long[] first={0};NativeRuntime.reset(session);
  try{s.tokens=NativeRuntime.generateChat(session,b(system),b(prompt),budget,piece->{if(first[0]==0)first[0]=System.nanoTime();buf.write(piece,0,piece.length);long[] st=NativeRuntime.resourceState();for(int i=0;i<5;i++)s.peak[i]=Math.max(s.peak[i],st[i]);try{Files.writeString(Path.of(path+".partial.txt"),buf.toString(StandardCharsets.UTF_8));}catch(IOException e){throw new UncheckedIOException(e);}});}catch(RuntimeException e){s.failure=e.toString();}
  s.totalMs=(System.nanoTime()-start)/1e6;s.firstMs=first[0]==0?0:(first[0]-start)/1e6;s.raw=buf.toString(StandardCharsets.UTF_8).trim();return s;
 }
 static String json(Stage s){return "{\"raw\":"+q(s.raw)+",\"failure\":"+q(s.failure)+",\"tokens\":"+s.tokens+",\"prompt_tokens\":"+s.promptTokens+",\"first_token_ms\":"+s.firstMs+",\"total_ms\":"+s.totalMs+",\"native_peaks\":"+Arrays.toString(s.peak)+"}";}
 static String spans(BoundAnswer.Draft d){StringBuilder b=new StringBuilder("[");for(int i=0;i<d.claims.size();i++){if(i>0)b.append(',');BoundAnswer.Claim c=d.claims.get(i);b.append("{\"obligation\":").append(c.obligation).append(",\"subject\":").append(q(c.subject)).append(",\"qualifier\":").append(q(c.qualifier)).append(",\"text\":").append(q(c.text)).append(",\"references\":[");for(int n=0;n<c.references.size();n++){if(n>0)b.append(',');BoundAnswer.Span s=c.references.get(n);b.append("{\"edition\":").append(q(s.source.edition)).append(",\"passage\":").append(q(s.source.id)).append(",\"passage_sha256\":").append(q(s.source.hash)).append(",\"document_sha256\":").append(q(s.source.documentHash)).append(",\"label\":").append(q(s.label)).append(",\"start_utf16\":").append(s.start).append(",\"end_utf16\":").append(s.end).append(",\"text\":").append(q(s.text())).append('}');}b.append("]}");}return b.append(']').toString();}
 static BoundAnswer.Catalog catalog(Path input,String id,BoundAnswer.Cancel cancel)throws Exception{
  List<BoundAnswer.Source> sources=new ArrayList<>();for(String line:Files.readAllLines(input.resolve(id+".tsv"))){String[] f=line.split("\t");for(int i=0;i<f.length;i++)f[i]=decode(f[i]);sources.add(new BoundAnswer.Source(f[0],f[1],f[2],f[3],f[4],f[5],f[6],f[7]));}return new BoundAnswer.Catalog(sources,cancel);
 }
 public static void main(String[] args)throws Exception{
  Path input=Path.of(args[0]),out=Path.of(args[2]);Files.createDirectories(out);long session=NativeRuntime.create(),start=System.nanoTime();
  try{NativeRuntime.load(session,b(args[1]));Files.writeString(out.resolve("load.json"),"{\"identity\":"+q(NativeRuntime.identity())+",\"load_ms\":"+(System.nanoTime()-start)/1e6+"}",StandardOpenOption.CREATE_NEW);
   for(String row:Files.readAllLines(input.resolve("cases.tsv"))){String[] c=row.split("\t");String id=c[0],question=decode(c[1]);BoundAnswer.Cancel cancel=new BoundAnswer.Cancel();BoundAnswer.Catalog catalog=catalog(input,id,cancel);Files.writeString(out.resolve("active-case.txt"),id);
    Stage draft=generate(session,BoundAnswer.DRAFT_SYSTEM,BoundAnswer.prompt(question,catalog,cancel),320,out.resolve(id+".draft"));Stage audit=new Stage();String failure=draft.failure,rendered="",claims="[]";String auditStatus="NOT_RUN";
    if(failure.isEmpty())try{BoundAnswer.Draft parsed=BoundAnswer.parse(question,draft.raw,catalog,draft.tokens,cancel);claims=spans(parsed);audit=generate(session,BoundAnswer.AUDIT_SYSTEM,BoundAnswer.auditPrompt(parsed,cancel),192,out.resolve(id+".audit"));auditStatus="RUN";failure=audit.failure;if(failure.isEmpty()){failure=BoundAnswer.auditFailure(parsed,audit.raw,audit.tokens,cancel);if(failure.isEmpty())rendered=BoundAnswer.render(parsed,audit.raw,audit.tokens,cancel).text;}}catch(IllegalArgumentException e){failure=e.getMessage();}
    String result="{\"id\":"+q(id)+",\"question\":"+q(question)+",\"draft\":"+json(draft)+",\"audit\":"+json(audit)+",\"audit_status\":"+q(auditStatus)+",\"claims\":"+claims+",\"rendered\":"+q(rendered)+",\"failure\":"+q(failure)+",\"route\":"+q(failure.isEmpty()?"SCREEN_ELIGIBLE":"WITHHELD")+",\"native_after\":"+Arrays.toString(NativeRuntime.resourceState())+"}\n";
    Files.writeString(out.resolve(id+".json"),result,StandardOpenOption.CREATE_NEW);System.out.println(id+" "+(draft.tokens+audit.tokens)+" "+failure);System.out.flush();
   }
  }finally{NativeRuntime.close(session);}
 }
}
