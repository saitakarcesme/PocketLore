package org.pocketlore.app;
import java.io.*;import java.nio.file.*;import java.util.*;
/** Actual production ZIP verification; independently authored byte fixtures, no parser mirror. */
public final class CentralProbe {
 public static void main(String[] args)throws Exception{
  BatchProbe.main(new String[]{args[0],args[1]});int count=0;
  for(String line:Files.readAllLines(Path.of(args[2]))){
   String[] v=line.split("\t",-1);BatchProbe.require(v.length==5,"Central case schema");boolean accept=Boolean.parseBoolean(v[2]),cancel=Boolean.parseBoolean(v[3]);
   byte[] raw=Files.readAllBytes(Path.of(v[1]));BatchProbe.require(raw.length<=StructuredDocuments.INPUT,"Central input cap");
   Exception failure=null;Map<String,byte[]> result=null;long start=System.nanoTime();
   try{result=StructuredDocuments.unzip(raw,new File(args[1]),new StructuredDocuments.Budget(()->cancel));}catch(Exception e){failure=e;}
   if(accept){if(failure!=null)throw new AssertionError(v[0],failure);String text=result.isEmpty()?"":new String(result.values().iterator().next(),java.nio.charset.StandardCharsets.UTF_8);BatchProbe.require(BatchProbe.sha(text).equals(v[4]),"Central original byte oracle");}
   else{BatchProbe.require(failure instanceof IOException,"Central refusal: "+v[0]);BatchProbe.require((failure instanceof InterruptedIOException)==cancel,"Central cancellation kind");}
   BatchProbe.require(new File(args[1]).list().length==0,"Central staging clean");
   System.out.println("CENTRAL\t"+v[0]+"\t"+(accept?"PASS":"REFUSE")+"\t"+(accept?v[4]:RefusalReceipt.encode(failure))+"\t"+(System.nanoTime()-start));count++;
  }
  System.out.println("CENTRAL_COMPLETE\t"+count);
 }
}
