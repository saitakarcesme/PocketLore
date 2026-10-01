package org.pocketlore.app;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.io.*;
import java.util.*;
/** Host execution of the unchanged production JNI and answer controller. */
public final class CompleteClaimHarness {
 static void writeText(Path p,String s,OpenOption... options)throws IOException {Files.write(p,s.getBytes(StandardCharsets.UTF_8),options);}
 static byte[] b(String x){return x.getBytes(StandardCharsets.UTF_8);}
 static String q(String s){return "\""+s.replace("\\","\\\\").replace("\"","\\\"").replace("\n","\\n").replace("\r","\\r").replace("\t","\\t")+"\"";}
 static void partial(Path out,String id,String text){try{writeText(out.resolve(id+".partial.txt"),text);}catch(IOException e){throw new UncheckedIOException(e);}}
 static String decode(String s){return new String(Base64.getDecoder().decode(s),StandardCharsets.UTF_8);}
 public static void main(String[] args)throws Exception {
  Path input=Paths.get(args[0]),out=Paths.get(args[2]);Files.createDirectories(out);
  long session=NativeRuntime.create();long start=System.nanoTime();
  try {
   NativeRuntime.load(session,b(args[1]));double load=(System.nanoTime()-start)/1e6;
   writeText(out.resolve("load.json"),"{\"identity\":"+q(NativeRuntime.identity())+",\"load_ms\":"+load+",\"resources\":"+Arrays.toString(NativeRuntime.resourceState())+"}\n");
   for(String line:Files.readAllLines(input.resolve("cases.tsv"))) {
    String[] c=line.split("\t");String id=c[0],question=decode(c[1]);writeText(out.resolve("active-case.txt"),id);List<ResearchEngine.Hit> hits=new ArrayList<>();
    for(String source:Files.readAllLines(input.resolve(id+".tsv"))) {
     String[] fields=source.split("\t");for(int i=0;i<fields.length;i++)fields[i]=decode(fields[i]);
     hits.add(new ResearchEngine.Hit(new ResearchEngine.Passage(fields),1));
    }
    ResearchEngine.Result evidence=new ResearchEngine.Result(hits,Collections.emptySet(),"Pinned oracle evidence for host capability measurement");
    NativeRuntime.reset(session);final byte[] system=b(EvidencePrompt.SYSTEM);
    AnswerEngine.Generator generator=new AnswerEngine.Generator(){
     public int run(byte[] prompt,int limit,NativeRuntime.Sink sink){return NativeRuntime.generateChat(session,system,prompt,limit,sink);}
     public int countTokens(byte[] prompt){return NativeRuntime.countChatTokens(session,system,prompt);}
     public int runWithSources(byte[] prompt,int limit,NativeRuntime.Sink sink,int sources,boolean combined){return NativeRuntime.generateClaims(session,system,prompt,limit,sink,sources,combined);}
    };
    long begun=System.nanoTime();
    AnswerEngine.Outcome result=AnswerEngine.answer(question,evidence,generator,x->partial(out,id,x),()->false);
    String prompt=result.prompt,raw=result.rawDraft,error="";int tokens=result.tokens;double first=result.firstTokenMs,total=result.totalMs;boolean diagnostic=!result.invokedModel;
    ResearchEngine.Result selected=EvidencePrompt.select(question,evidence);
    if(diagnostic){
     prompt=EvidencePrompt.build(question,selected);ByteArrayOutputStream buffer=new ByteArrayOutputStream();long[] firstTime={0};begun=System.nanoTime();final long begin=begun;
     try{
      if(generator.countTokens(b(prompt))+EvidencePrompt.OUTPUT_TOKENS>EvidencePrompt.CONTEXT_TOKENS)throw new IllegalStateException("Diagnostic prompt exceeds unchanged budget");
      tokens=generator.runWithSources(b(prompt),EvidencePrompt.OUTPUT_TOKENS,piece->{if(firstTime[0]==0)firstTime[0]=System.nanoTime();buffer.write(piece,0,piece.length);partial(out,id,new String(buffer.toByteArray(),StandardCharsets.UTF_8));},selected.hits.size(),question.toLowerCase(Locale.ROOT).startsWith("compare "));
     }catch(RuntimeException e){error=e.toString();}
     total=(System.nanoTime()-begin)/1e6;first=firstTime[0]==0?0:(firstTime[0]-begin)/1e6;raw=new String(buffer.toByteArray(),StandardCharsets.UTF_8);
    }
    String record="{\"id\":"+q(id)+",\"question\":"+q(question)+",\"route\":"+q(result.kind.name())+",\"text\":"+q(result.text)+",\"reason\":"+q(result.reason)+",\"controller_invoked\":"+result.invokedModel+",\"diagnostic_only\":"+diagnostic+",\"prompt\":"+q(prompt)+",\"system\":"+q(EvidencePrompt.SYSTEM)+",\"raw\":"+q(raw)+",\"resolved_raw\":"+q(EvidencePrompt.resolve(raw,selected))+",\"error\":"+q(error)+",\"tokens\":"+tokens+",\"prompt_tokens\":"+generator.countTokens(b(prompt))+",\"first_token_ms\":"+first+",\"generation_total_ms\":"+total+",\"controller_total_ms\":"+result.totalMs+",\"resources_after\":"+Arrays.toString(NativeRuntime.resourceState())+"}\n";
    writeText(out.resolve(id+".json"),record,StandardOpenOption.CREATE_NEW);
    System.out.println(id+" "+result.kind+" diagnostic="+diagnostic+" tokens="+tokens+" ms="+total);System.out.flush();
   }
  }finally{NativeRuntime.close(session);}
 }
}
