package org.pocketlore.app;
import java.io.*;import java.nio.file.*;import java.nio.charset.StandardCharsets;import java.security.MessageDigest;import java.util.*;import java.util.concurrent.atomic.AtomicInteger;
/** Executes exact production classes. No Android stubs and no extractor implementation here. */
public final class BatchProbe {
 static String sha(String s)throws Exception{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(s.getBytes(StandardCharsets.UTF_8)));}
 static String b64(String s){return Base64.getEncoder().encodeToString(s.getBytes(StandardCharsets.UTF_8));}
 static void require(boolean b,String m){if(!b)throw new AssertionError(m);}
 public static void main(String[] args)throws Exception{
  List<String> lines=Files.readAllLines(Path.of(args[0]),StandardCharsets.UTF_8);int count=0;
  for(String line:lines){String[] v=line.split("\t",-1);require(v.length==7,"Case schema");AtomicInteger checks=new AtomicInteger();int stop=Integer.parseInt(v[3]);StructuredDocuments.Budget budget=new StructuredDocuments.Budget(()->stop>=0&&checks.incrementAndGet()>stop);StructuredDocuments.Result result=null;Exception failure=null;
   long start=System.nanoTime();
   try(InputStream in=Files.newInputStream(Path.of(v[1]))){byte[] raw=DocumentBytes.read(in,StructuredDocuments.INPUT,budget);result=StructuredDocuments.extract(raw,v[2],new File(args[1]),budget);}catch(Exception e){failure=e;}
   if(v[4].equals("-")){require(failure!=null,"Unexpected acceptance: "+v[0]);require((failure instanceof IOException || failure instanceof org.xml.sax.SAXException) && !(failure instanceof FileNotFoundException) && !(failure instanceof java.nio.file.NoSuchFileException),"Unrelated failure: "+v[0]);boolean interrupted=false;Throwable cause=failure;for(int depth=0;cause!=null&&depth<16;depth++,cause=cause.getCause())if(cause instanceof InterruptedIOException)interrupted=true;require(interrupted==(stop>=0),"Unexpected cancellation/deadline: "+v[0]);System.out.println("REFUSE\t"+v[0]+"\t"+failure.getClass().getName()+"\t"+RefusalReceipt.encode(failure)+"\t"+checks.get());}
   else{if(failure!=null)throw new AssertionError(v[0],failure);require(sha(result.text).equals(v[4])&&result.text.length()==Integer.parseInt(v[5]),"Text mismatch: "+v[0]);StringBuilder spans=new StringBuilder();int previous=-1;for(PersonalText.Span s:result.spans){require(s.start>=0&&s.start>=previous&&s.end>s.start&&s.end<=result.text.length(),"Invalid range");require(!(s.start>0&&Character.isLowSurrogate(result.text.charAt(s.start)))&&!(s.end<result.text.length()&&Character.isLowSurrogate(result.text.charAt(s.end))),"Surrogate split");previous=s.end;spans.append(s.start).append('\t').append(s.end).append('\t').append(b64(s.location)).append('\n');}
    require(v[6].equals("-")||sha(spans.toString()).equals(v[6]),"Independent span mismatch: "+v[0]);System.out.println("PASS\t"+v[0]+"\t"+sha(result.text)+"\t"+result.text.length()+"\t"+result.spans.size()+"\t"+sha(spans.toString()));if(!v[6].equals("-"))System.out.println("EXACT\t"+v[0]+"\t"+b64(result.text)+"\t"+b64(spans.toString()));
   }
   require(new File(args[1]).list().length==0,"Owned parser staging left behind");System.out.println("TIME\t"+v[0]+"\t"+(System.nanoTime()-start));count++;
  }
  FormatPolicyProbe.main(new String[0]);
  System.out.println("COMPLETE\t"+count);
 }
}
