package org.pocketlore.app;
import java.io.*;import java.util.concurrent.atomic.AtomicBoolean;
public final class FormatPolicyProbe {
 interface Work{void run()throws Exception;}static void deny(Work w)throws Exception{try{w.run();throw new AssertionError("Missing refusal");}catch(IOException expected){}}
 public static void main(String[] args)throws Exception{
  String[] types={"docx","pptx","odt","odp","epub","html"};String[] mimes={"application/vnd.openxmlformats-officedocument.wordprocessingml.document","application/vnd.openxmlformats-officedocument.presentationml.presentation","application/vnd.oasis.opendocument.text","application/vnd.oasis.opendocument.presentation","application/epub+zip","text/html"};
  for(int i=0;i<types.length;i++){String ext=types[i];DocumentFormatPolicy.verifyMime(ext,mimes[i]);DocumentFormatPolicy.verifyMime(ext,null);DocumentFormatPolicy.verifyMime(ext,"application/octet-stream");deny(()->DocumentFormatPolicy.verifyMime(ext,"image/png"));}
  deny(()->DocumentBytes.read(new InputStream(){public int read(){throw new AssertionError("Read began after cancellation");}},4,()->true));
  AtomicBoolean cancelled=new AtomicBoolean();deny(()->DocumentBytes.read(new ByteArrayInputStream(new byte[16]){public synchronized int read(byte[] b,int o,int n){int x=super.read(b,o,n);cancelled.set(true);return x;}},16,cancelled::get));
  assert DocumentBytes.read(new ByteArrayInputStream(new byte[16]),16,()->false).length==16;deny(()->DocumentBytes.read(new ByteArrayInputStream(new byte[17]),16,()->false));
  StructuredDocuments.Budget duration=new StructuredDocuments.Budget(()->false);Thread.sleep(20020);assert duration.getAsBoolean();deny(duration::check);
  System.out.println("PASS: six provider MIME matches/generic cases and six mismatches; no-read cancellation, mid-read cancellation, exact/over byte limit; actual20second deadline refusal");
 }
}
