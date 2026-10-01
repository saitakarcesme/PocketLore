package org.pocketlore.app;
import java.nio.file.*;import java.util.*;
public final class Behavior {
 public static void main(String[] a)throws Exception{
  BoundAnswer.Catalog c=FrameBehavior.catalog("level","A difference of 1.0 in level corresponds to the intensity ratio of [TeX: {\\displaystyle {\\sqrt[{3}]{8}}}] , or about 2.0.");List<FactFrames.Ground> grounds=FactFrames.sources(c,new BoundAnswer.Cancel());if(grounds.isEmpty())throw new AssertionError("Source formula not parsed");int n=0;
  for(String row:Files.readAllLines(Path.of(a[0]))){String[] f=row.split("\t");String text=BindingHarness.decode(f[0]);boolean expected=Boolean.parseBoolean(f[1]),actual=true;try{EquationProof.prove(text,grounds,new BoundAnswer.Cancel());}catch(IllegalArgumentException e){actual=false;}if(actual!=expected)throw new AssertionError("Mathematical control "+n+": "+text);n++;}
  BoundAnswer.Cancel stop=new BoundAnswer.Cancel();stop.cancel();try{EquationProof.prove("The cube root of 8 is approximately 2.0.",grounds,stop);throw new AssertionError("Cancellation bypass");}catch(IllegalStateException expected){n++;}
  System.out.println("Compositional mathematical checks: "+n);
 }
}
