package org.pocketlore.app;
import java.io.*;import java.nio.file.*;import java.nio.charset.StandardCharsets;import java.util.*;import java.util.concurrent.atomic.AtomicInteger;
/** Executes the exact production extractor on host JAXP, not Android or a fixture-only parser. */
public final class ExtractionProbe {
 static String b64(String s){return Base64.getEncoder().encodeToString(s.getBytes(StandardCharsets.UTF_8));}
 public static void main(String[] args)throws Exception {
  AtomicInteger checks=new AtomicInteger();int stop=Integer.parseInt(args[3]);StructuredDocuments.Budget budget=new StructuredDocuments.Budget(()->stop>=0&&checks.incrementAndGet()>stop);
  try{byte[] raw=DocumentBytes.read(new FileInputStream(args[0]),StructuredDocuments.INPUT,budget);StructuredDocuments.Result r=StructuredDocuments.extract(raw,args[1],new File(args[2]),budget);System.out.println("TEXT\t"+b64(r.text));for(PersonalText.Span span:r.spans)System.out.println("SPAN\t"+span.start+"\t"+span.end+"\t"+b64(span.location));}
  catch(Exception e){System.err.println(e.getClass().getName()+": "+e.getMessage());System.exit(2);}
 }
}
