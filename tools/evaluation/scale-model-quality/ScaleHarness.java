package org.pocketlore.app;
import java.nio.file.*;import java.nio.charset.StandardCharsets;import java.io.*;import java.util.*;
/** Same frozen oracle evidence/new architecture for every model; one generation per case. */
public final class ScaleHarness {
 static byte[] b(String x){return x.getBytes(StandardCharsets.UTF_8);}
 static String q(String s){return "\""+s.replace("\\","\\\\").replace("\"","\\\"").replace("\n","\\n").replace("\r","\\r").replace("\t","\\t")+"\"";}
 static String decode(String x){return new String(Base64.getDecoder().decode(x),StandardCharsets.UTF_8);}
 public static void main(String[] args)throws Exception{
  Path input=Path.of(args[0]),out=Path.of(args[2]);Files.createDirectories(out);long session=NativeRuntime.create(),start=System.nanoTime();
  try{
   NativeRuntime.load(session,b(args[1]));Files.writeString(out.resolve("load.json"),"{\"identity\":"+q(NativeRuntime.identity())+",\"load_ms\":"+(System.nanoTime()-start)/1e6+",\"resources\":"+Arrays.toString(NativeRuntime.resourceState())+"}");
   for(String line:Files.readAllLines(input.resolve("cases.tsv"))){
    String[] c=line.split("\t");String id=c[0],question=decode(c[1]);Files.writeString(out.resolve("active-case.txt"),id);List<ResearchEngine.Hit> hits=new ArrayList<>();
    for(String source:Files.readAllLines(input.resolve(id+".tsv"))){String[] fields=source.split("\t");for(int i=0;i<fields.length;i++)fields[i]=decode(fields[i]);hits.add(new ResearchEngine.Hit(new ResearchEngine.Passage(fields),1));}
    NativeRuntime.reset(session);int excerpt=1200;String prompt=ObligationAnswer.prompt(question,hits,excerpt);int promptTokens=NativeRuntime.countChatTokens(session,b(ObligationAnswer.SYSTEM),b(prompt));
    while(promptTokens+512>4096&&excerpt>300){excerpt-=100;prompt=ObligationAnswer.prompt(question,hits,excerpt);promptTokens=NativeRuntime.countChatTokens(session,b(ObligationAnswer.SYSTEM),b(prompt));}
    if(promptTokens+512>4096)throw new IllegalStateException("Context admission failed");
    Files.writeString(out.resolve(id+".prompt.txt"),prompt);ByteArrayOutputStream buffer=new ByteArrayOutputStream();long begin=System.nanoTime();long[] first={0};long[] peaks=new long[5];int tokens=0;String error="";
    try{tokens=NativeRuntime.generateChat(session,b(ObligationAnswer.SYSTEM),b(prompt),512,piece->{if(first[0]==0)first[0]=System.nanoTime();buffer.write(piece,0,piece.length);long[] state=NativeRuntime.resourceState();for(int i=0;i<5;i++)peaks[i]=Math.max(peaks[i],state[i]);try{Files.writeString(out.resolve(id+".partial.txt"),buffer.toString(StandardCharsets.UTF_8));}catch(IOException e){throw new UncheckedIOException(e);}});}catch(RuntimeException e){error=e.toString();}
    double total=(System.nanoTime()-begin)/1e6;String raw=buffer.toString(StandardCharsets.UTF_8).trim();String failure=error.isEmpty()?ObligationAnswer.failure(question,raw,hits,excerpt,tokens,512):error;
    String record="{\"id\":"+q(id)+",\"question\":"+q(question)+",\"raw\":"+q(raw)+",\"resolved_raw\":"+q(ObligationAnswer.resolve(raw,hits))+",\"screen_route\":"+q(failure.isEmpty()?"CANDIDATE_FOR_SOURCE_REVIEW":"WITHHELD")+",\"failure\":"+q(failure)+",\"prompt_tokens\":"+promptTokens+",\"tokens\":"+tokens+",\"excerpt_limit\":"+excerpt+",\"first_token_ms\":"+(first[0]==0?0:(first[0]-begin)/1e6)+",\"total_ms\":"+total+",\"native_peaks\":"+Arrays.toString(peaks)+",\"native_after\":"+Arrays.toString(NativeRuntime.resourceState())+"}\n";
    Files.writeString(out.resolve(id+".json"),record,StandardOpenOption.CREATE_NEW);System.out.println(id+" "+tokens+" "+failure);System.out.flush();
   }
  }finally{NativeRuntime.close(session);}
 }
}
