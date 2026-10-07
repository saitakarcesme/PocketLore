package org.pocketlore.app;
import java.io.*;
import java.security.MessageDigest;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.locks.ReentrantLock;
import java.util.function.LongSupplier;
/** One intake budget, including queue time. Cooperative refusal is not preemption. */
final class OcrDeadline {
 static final long BUDGET_NS=30000000000L;
 private final LongSupplier clock;
 private final long start;
 private final AtomicBoolean cancelled=new AtomicBoolean();
 OcrDeadline(){this(System::nanoTime);}
 OcrDeadline(LongSupplier clock){this.clock=clock;start=clock.getAsLong();}
 void cancel(){cancelled.set(true);}
 boolean stopped(){long elapsed=clock.getAsLong()-start;return cancelled.get()||Thread.currentThread().isInterrupted()||elapsed<0||elapsed>=BUDGET_NS;}
 long remaining()throws IOException{long elapsed=clock.getAsLong()-start;if(cancelled.get()||Thread.currentThread().isInterrupted())throw new IOException("OCR cancelled");if(elapsed<0||elapsed>=BUDGET_NS)throw new IOException("OCR publication deadline expired");return BUDGET_NS-elapsed;}
 void check()throws IOException{remaining();}
 void publish(OcrDeadline current)throws IOException{if(this!=current)throw new IOException("Stale OCR job");check();}
 void lock(ReentrantLock lock)throws IOException,InterruptedException{
  while(true){long left=remaining();if(lock.tryLock(Math.min(left,10000000L),TimeUnit.NANOSECONDS)){try{check();return;}catch(IOException e){lock.unlock();throw e;}}}
 }
 String hash(byte[] bytes)throws Exception{check();MessageDigest hash=MessageDigest.getInstance("SHA-256");for(int i=0;i<bytes.length;i+=8192){check();hash.update(bytes,i,Math.min(8192,bytes.length-i));}check();return hex(hash.digest());}
 String hash(InputStream in,long expected)throws Exception{check();MessageDigest hash=MessageDigest.getInstance("SHA-256");byte[] buffer=new byte[8192];long count=0;while(true){check();int n=in.read(buffer);check();if(n<0)break;if(n==0)continue;if(count>expected-n)throw new IOException("OCR asset size changed");count+=n;hash.update(buffer,0,n);}if(count!=expected)throw new IOException("OCR asset size changed");check();return hex(hash.digest());}
 static String hex(byte[] bytes){StringBuilder b=new StringBuilder(64);for(byte v:bytes)b.append(String.format(java.util.Locale.ROOT,"%02x",v&255));return b.toString();}
}
