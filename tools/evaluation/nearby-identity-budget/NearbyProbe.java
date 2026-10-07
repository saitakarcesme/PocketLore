package org.pocketlore.places;
import java.io.*;import java.util.*;import java.util.concurrent.*;import java.util.concurrent.atomic.*;
/** Authored pure production-helper controls, never a mock SQLite or Android query. */
public final class NearbyProbe {
 static int count;
 static void ok(boolean b,String name){if(!b)throw new AssertionError(name);System.out.println("PASS "+name);count++;}
 interface Action{void run()throws Exception;}
 static void refused(String name,Action action)throws Exception{try(PlacesBudget positive=new PlacesBudget(()->false)){positive.check();}boolean rejected=false;try{action.run();}catch(InterruptedIOException|IllegalArgumentException e){rejected=true;}ok(rejected,name);}
 static boolean covers(List<double[]> spans,double lon){for(double[] s:spans)if(s[0]<=lon&&lon<=s[1])return true;return false;}
 public static void main(String[] args)throws Exception{
  String first=PlacesBudget.identity("e","s","a",7);ok(first.equals("1:e1:s1:a:7"),"authored-identity");
  ok(!first.equals(PlacesBudget.identity("e","s","b",7)),"distinct-source-ids");ok(!first.equals(PlacesBudget.identity("e","s","a",8)),"distinct-ordinals");
  ok(!first.equals(PlacesBudget.identity("other","s","a",7))&&!first.equals(PlacesBudget.identity("e","other","a",7)),"distinct-editions-shards");
  ok(!PlacesBudget.identity("a:b","c","d",0).equals(PlacesBudget.identity("a","b:c","d",0)),"delimiter-collision");
  ok(PlacesBudget.compare(1,"e","s","a",2,1,"e","s","a",10)<0,"numeric-tie");refused("negative-ordinal",()->PlacesBudget.identity("x",-1));
  ok(PlacesGeometry.primary(null,null)==null&&PlacesGeometry.category(null,null,null,List.of(),List.of())&&!PlacesGeometry.category("null",null,null,List.of(),List.of()),"null-category");
  ok(PlacesGeometry.category("museum","museum",null,List.of(),List.of())&&!PlacesGeometry.category("Museum","museum",null,List.of(),List.of())&&PlacesGeometry.category("culture",null,null,List.of("culture"),List.of()),"exact-category-case");
  List<double[]> spans=PlacesGeometry.spans(0,180,1);ok(covers(spans,179.995)&&covers(spans,-179.995)&&!covers(spans,0)&&PlacesGeometry.distance(0,180,0,-179.995)>.55&&PlacesGeometry.distance(0,180,0,-179.995)<.56,"antimeridian");
  ok(covers(PlacesGeometry.spans(90,45,1),-170)&&covers(PlacesGeometry.spans(90,45,1),170)&&Double.isFinite(PlacesGeometry.distance(90,45,89.9999,-60)),"polar");
  double d=PlacesGeometry.distance(0,0,0,.001);ok(PlacesGeometry.within(d,d)&&!PlacesGeometry.within(d,Math.nextDown(d))&&PlacesGeometry.within(d,Math.nextUp(d)),"radius-boundary");
  refused("invalid-coordinates",()->PlacesGeometry.validate(Double.NaN,0,1,30));refused("oversized-radius",()->PlacesGeometry.validate(0,0,100.0001,30));
  AtomicLong clock=new AtomicLong();PlacesBudget b=new PlacesBudget(()->false,clock::get);clock.set(19999999999L);ok(b.remaining()==1,"positive-expiry-edge");clock.incrementAndGet();refused("expired-edge",b::check);b.close();
  clock.set(10);b=new PlacesBudget(()->false,clock::get);clock.set(9);refused("negative-clock",b::check);b.close();
  clock.set(Long.MAX_VALUE-10);b=new PlacesBudget(()->false,clock::get);clock.set(Long.MIN_VALUE+9);ok(b.remaining()==19999999980L,"wrap-clock");b.close();
  clock.set(0);b=new PlacesBudget(()->false,clock::get);clock.set(12000000000L);ok(b.remaining()==8000000000L,"queue-consumes-budget");b.close();
  for(String phase:new String[]{"between-shards-expiry","late-hash","late-merge","late-publication"}){clock.set(0);PlacesBudget late=new PlacesBudget(()->false,clock::get);late.check();clock.set(20000000000L);refused(phase,()->late.publish(late));late.close();}
  b=new PlacesBudget(()->false);b.cancel();refused("cancel-before-start",b::check);b.close();
  b=new PlacesBudget(()->false);Thread.currentThread().interrupt();boolean stopped=false;try{b.check();}catch(InterruptedIOException e){stopped=true;}finally{Thread.interrupted();b.close();}ok(stopped,"interrupt");
  try(PlacesBudget old=new PlacesBudget(()->false);PlacesBudget fresh=new PlacesBudget(()->false)){refused("uncancelled-stale-owner",()->old.publish(fresh));old.cancel();fresh.publish(fresh);ok(fresh.remaining()>0,"old-cancel-new-owner");ok(fresh.hash(new byte[]{97,98,99}).equals("ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"),"hash-positive");}
  for(boolean expiry:new boolean[]{false,true}){clock.set(0);PlacesBudget query=new PlacesBudget(()->false,clock::get);CountDownLatch signalled=new CountDownLatch(1);AtomicInteger calls=new AtomicInteger();try(PlacesBudget.Query lease=query.query(()->{calls.incrementAndGet();signalled.countDown();})){if(expiry)clock.set(20000000000L);else query.cancel();ok(signalled.await(1,TimeUnit.SECONDS)&&calls.get()==1,expiry?"query-expiry-watchdog":"query-cancel");}finally{query.close();}}
  PlacesBudget closed=new PlacesBudget(()->false);AtomicInteger calls=new AtomicInteger();PlacesBudget.Query lease=closed.query(calls::incrementAndGet);lease.close();closed.cancel();closed.close();ok(calls.get()==0,"closed-registration");refused("retired-owner",()->closed.query(()->{}));
  PlacesBudget error=new PlacesBudget(()->false);CountDownLatch called=new CountDownLatch(1);PlacesBudget.Query bad=error.query(()->{called.countDown();throw new IllegalStateException("authored callback refusal");});error.cancel();if(!called.await(1,TimeUnit.SECONDS))throw new AssertionError("callback absent");refused("callback-error-refusal",error::check);bad.close();error.close();
  PlacesBudget foreign=new PlacesBudget(()->false);PlacesBudget.Query own=foreign.query(()->{});AtomicBoolean rejected=new AtomicBoolean();Thread t=new Thread(()->{try{foreign.query(()->{});}catch(InterruptedIOException e){rejected.set(true);}});t.start();t.join(1000);ok(!t.isAlive()&&rejected.get(),"foreign-owner");own.close();foreign.close();
  PlacesBudget stuck=new PlacesBudget(()->false);CountDownLatch entered=new CountDownLatch(1),release=new CountDownLatch(1);PlacesBudget.Query delayed=stuck.query(()->{entered.countDown();try{release.await(3,TimeUnit.SECONDS);}catch(InterruptedException e){Thread.currentThread().interrupt();}});stuck.cancel();if(!entered.await(1,TimeUnit.SECONDS))throw new AssertionError("callback absent");boolean bounded=false;try{stuck.close();}catch(IllegalStateException e){bounded=true;}
  try{ok(bounded,"bounded-close-refusal");try(PlacesBudget replacement=new PlacesBudget(()->false)){refused("no-replacement-watchdog",()->replacement.query(()->{}));}}finally{release.countDown();delayed.close();stuck.close();}
  try(PlacesBudget retry=new PlacesBudget(()->false);PlacesBudget.Query q=retry.query(()->{})){retry.check();}
  ok(Thread.getAllStackTraces().keySet().stream().noneMatch(x->x.isAlive()&&x.getName().equals("places-query-deadline")),"close-release");
  System.out.println("NEARBY_COMPLETE "+count);
 }
}
