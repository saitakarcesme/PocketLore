package org.pocketlore.places;
import java.io.*;import java.security.*;import java.util.*;import java.util.function.*;
/** One intake budget; blocking open/parse phases are checked on return, not preempted. */
public final class PlacesBudget implements AutoCloseable {
 public static final long NANOS=20000000000L;
 private final BooleanSupplier external;private final LongSupplier clock;private final long start;
 private static final java.util.concurrent.Semaphore WATCH_SLOT=new java.util.concurrent.Semaphore(1);
 private final Set<Query> queries=new HashSet<>();private volatile boolean cancelled,retired;private volatile Throwable callbackFailure;private Thread watcher;private volatile Thread owner;
 public PlacesBudget(BooleanSupplier cancel){this(cancel,System::nanoTime);}
 public PlacesBudget(BooleanSupplier cancel,LongSupplier clock){this.external=Objects.requireNonNull(cancel);this.clock=Objects.requireNonNull(clock);start=clock.getAsLong();}
 public long remaining()throws InterruptedIOException{long elapsed=clock.getAsLong()-start;if(cancelled||external.getAsBoolean()||Thread.currentThread().isInterrupted()||(owner!=null&&owner.isInterrupted()))throw new InterruptedIOException("Places operation cancelled");if(callbackFailure!=null)throw new InterruptedIOException("Places query cancellation failed");if(elapsed<0||elapsed>=NANOS)throw new InterruptedIOException("Places overall query deadline exceeded");return NANOS-elapsed;}
 public void check()throws InterruptedIOException{remaining();}
 public void publish(PlacesBudget current)throws InterruptedIOException{if(this!=current)throw new InterruptedIOException("Stale places operation");check();}
 public synchronized void cancel(){cancelled=true;notifyAll();}
 public final class Query implements AutoCloseable {
  private final Runnable cancellation;private volatile boolean active=true;private final java.util.concurrent.atomic.AtomicBoolean signalled=new java.util.concurrent.atomic.AtomicBoolean();
  private Query(Runnable cancellation){this.cancellation=cancellation;}
  private void signal(){if(active&&signalled.compareAndSet(false,true))try{cancellation.run();}catch(Throwable e){callbackFailure=e;}}
  public void close(){synchronized(PlacesBudget.this){active=false;queries.remove(this);PlacesBudget.this.notifyAll();}}
 }
 /** At most one cancellation watchdog globally; a stuck Android callback prevents replacement workers. */
 public synchronized Query query(Runnable cancellation)throws InterruptedIOException{
  Objects.requireNonNull(cancellation);check();if(retired)throw new InterruptedIOException("Places query owner is closed");if(owner!=null&&owner!=Thread.currentThread())throw new InterruptedIOException("Foreign places query owner");
  boolean acquired=watcher==null;
  if(acquired&&!WATCH_SLOT.tryAcquire())throw new InterruptedIOException("Places cancellation worker is still owned by another operation");
  Query q=null;
  try{
   q=new Query(cancellation);queries.add(q);owner=Thread.currentThread();
   if(acquired){watcher=new Thread(this::watch,"places-query-deadline");watcher.setDaemon(true);watcher.start();}
   return q;
  }catch(RuntimeException|Error e){
   if(q!=null){queries.remove(q);q.active=false;}
   if(acquired){retired=true;WATCH_SLOT.release();}
   throw e;
  }
 }
 private void watch(){
  try{List<Query> pending;
   synchronized(this){while(true){boolean stop=retired;try{check();}catch(Throwable e){cancelled=true;stop=true;}
    if(stop){pending=new ArrayList<>(queries);break;}
    try{wait(10);}catch(InterruptedException e){cancelled=true;pending=new ArrayList<>(queries);break;}
   }}
   // Never hold the ownership monitor while invoking Android CancellationSignal.cancel().
   for(Query q:pending)q.signal();
  }finally{WATCH_SLOT.release();}
 }
 public void close(){Thread t;synchronized(this){retired=true;if(!queries.isEmpty())cancelled=true;notifyAll();t=watcher;}
  if(t!=null&&t!=Thread.currentThread()){boolean interrupted=Thread.interrupted();try{t.join(1000);if(t.isAlive())throw new IllegalStateException("Places watchdog did not stop; further queries refused until release");}catch(InterruptedException e){Thread.currentThread().interrupt();throw new IllegalStateException("Places watchdog close interrupted",e);}finally{if(interrupted)Thread.currentThread().interrupt();}}
 }
 public String hash(byte[] raw)throws IOException{check();try{MessageDigest md=MessageDigest.getInstance("SHA-256");for(int i=0;i<raw.length;i+=8192){check();md.update(raw,i,Math.min(8192,raw.length-i));}check();StringBuilder out=new StringBuilder(64);for(byte b:md.digest())out.append(String.format(Locale.ROOT,"%02x",b&255));check();return out.toString();}catch(NoSuchAlgorithmException e){throw new IOException(e);}}
 private static String field(String s){return Objects.requireNonNull(s).length()+":"+s;}
 public static String identity(String id,long ordinal){if(ordinal<0)throw new IllegalArgumentException("Negative source ordinal");return field(id)+":"+ordinal;}
 public static String identity(String edition,String shard,String id,long ordinal){return field(edition)+field(shard)+identity(id,ordinal);}
 public static int compare(double distance,String edition,String shard,String id,long ordinal,double other,String otherEdition,String otherShard,String otherId,long otherOrdinal){int n=Double.compare(distance,other);if(n==0)n=edition.compareTo(otherEdition);if(n==0)n=shard.compareTo(otherShard);if(n==0)n=id.compareTo(otherId);return n==0?Long.compare(ordinal,otherOrdinal):n;}
}
