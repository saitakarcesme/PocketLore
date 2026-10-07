package org.pocketlore.app;
import java.io.*;import java.util.concurrent.atomic.*;import java.util.concurrent.locks.*;
/** Authored boundary controls; no recognizer, image, provider, or Android execution. */
public final class DeadlineProbe {
 static int count;
 static void ok(boolean b,String n){if(!b)throw new AssertionError(n);System.out.println("PASS "+n);count++;}
 interface Action{void run()throws Exception;}
 static void refuse(String name,Action a)throws Exception{boolean rejected=false;try{a.run();}catch(IOException e){rejected=true;}ok(rejected,name);}
 static native long nativeRemaining(long budget,long start,long tick,boolean cancel,boolean millis);
 public static void main(String[] args)throws Exception{
  System.load(args[0]);AtomicLong clock=new AtomicLong(100);OcrDeadline d=new OcrDeadline(clock::get);clock.set(30000000099L);ok(d.remaining()==1,"positive-before-boundary");clock.incrementAndGet();refuse("exact-boundary-refusal",d::check);
  clock.set(10);d=new OcrDeadline(clock::get);clock.set(9);refuse("negative-elapsed-refusal",d::check);
  clock.set(Long.MAX_VALUE-10);d=new OcrDeadline(clock::get);clock.set(Long.MIN_VALUE+9);ok(d.remaining()==29999999980L,"wraparound-elapsed");
  d=new OcrDeadline();d.cancel();refuse("cancel-before-start",d::check);d=new OcrDeadline();Thread.currentThread().interrupt();refuse("interrupt-refusal",d::check);Thread.interrupted();d.check();
  clock.set(0);d=new OcrDeadline(clock::get);clock.set(12000000000L);ok(d.remaining()==18000000000L,"queue-consumes-budget");
  for(String phase:new String[]{"late-init","late-recognition","late-conversion","late-hash","late-ui"}){clock.set(0);OcrDeadline p=new OcrDeadline(clock::get);p.check();clock.set(30000000000L);refuse(phase,()->p.publish(p));}
  OcrDeadline old=new OcrDeadline(),next=new OcrDeadline();refuse("uncancelled-stale-owner",()->old.publish(next));old.cancel();refuse("old-owner-new-owner",()->old.publish(next));next.publish(next);
  OcrDeadline hash=new OcrDeadline();ok(hash.hash("abc".getBytes("UTF-8")).equals("ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"),"hash-positive");ok(!hash.hash("abd".getBytes("UTF-8")).equals("ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"),"hash-mismatch");
  OcrDeadline stream=new OcrDeadline();refuse("stream-cancel",()->stream.hash(new ByteArrayInputStream(new byte[]{1}){public synchronized int read(byte[] b,int o,int l){stream.cancel();return super.read(b,o,l);}},1));
  clock.set(0);OcrDeadline timed=new OcrDeadline(clock::get);refuse("stream-expiry",()->timed.hash(new ByteArrayInputStream(new byte[]{1}){public synchronized int read(byte[] b,int o,int l){clock.set(30000000000L);return super.read(b,o,l);}},1));
  for(boolean cancel:new boolean[]{false,true}){ReentrantLock lock=new ReentrantLock();lock.lock();clock.set(0);OcrDeadline waiting=new OcrDeadline(clock::get);AtomicReference<Throwable> failure=new AtomicReference<>();AtomicBoolean refused=new AtomicBoolean();Thread child=new Thread(()->{try{waiting.lock(lock);lock.unlock();failure.set(new AssertionError("lock admitted"));}catch(IOException e){refused.set(true);}catch(Throwable t){failure.set(t);}});child.start();if(cancel)waiting.cancel();else clock.set(30000000000L);child.join(1000);lock.unlock();ok(!child.isAlive()&&failure.get()==null&&refused.get(),cancel?"lock-cancel":"lock-expiry-and-release");OcrDeadline fresh=new OcrDeadline();fresh.lock(lock);lock.unlock();}
  ok(nativeRemaining(30000000000L,100,101,false,false)==29999999999L,"native-relative-nanoseconds");ok(nativeRemaining(1999999,0,0,false,true)==1,"native-floor-milliseconds");ok(nativeRemaining(1,0,1,false,false)==0,"native-expired");ok(nativeRemaining(30,0,0,true,false)==0,"native-cancel");ok(nativeRemaining(30,10,9,false,false)==0,"native-backward-clock");
  for(long b:new long[]{0,-1,30000000001L,Long.MAX_VALUE}){boolean reject=false;try{nativeRemaining(b,0,0,false,false);}catch(IllegalArgumentException e){reject=true;}ok(reject,"native-invalid-budget-"+b);}
  // Existing transport controls use the exact accepted production header and authored bytes.
  Class.forName("Transport").getMethod("main",String[].class).invoke(null,(Object)new String[]{args[0],args[1]});
  System.out.println("DEADLINE_COMPLETE "+count);
 }
}
