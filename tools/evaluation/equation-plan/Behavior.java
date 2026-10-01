package org.pocketlore.app;
import java.nio.file.*;import java.util.*;
public final class Behavior {
 public static void main(String[] a)throws Exception{
  BoundAnswer.Catalog c=FrameBehavior.catalog("level","A difference of 1.0 in level corresponds to the intensity ratio of [TeX: {\\displaystyle {\\sqrt[{3}]{8}}}] , or about 2.0.");List<FactFrames.Ground> grounds=FactFrames.sources(c,new BoundAnswer.Cancel());if(grounds.isEmpty())throw new AssertionError("Source formula not parsed");int n=0;
  for(String row:Files.readAllLines(Path.of(a[0]))){String[] f=row.split("\t");String text=BindingHarness.decode(f[0]);boolean expected=Boolean.parseBoolean(f[1]),actual=true;try{EquationProof.prove(text,grounds,new BoundAnswer.Cancel());}catch(IllegalArgumentException e){actual=false;}if(actual!=expected)throw new AssertionError("Mathematical control "+n+": "+text);n++;}
  BoundAnswer.Cancel stop=new BoundAnswer.Cancel();stop.cancel();try{EquationProof.prove("The cube root of 8 is approximately 2.0.",grounds,stop);throw new AssertionError("Cancellation bypass");}catch(IllegalStateException expected){n++;}
  SourcePlan.Catalog catalog=new SourcePlan.Catalog(c,new BoundAnswer.Cancel());SourcePlan.Plan plan=SourcePlan.parse("Describe the documented relation.","O1|F1",10,catalog,new BoundAnswer.Cancel());
  BoundAnswer.Draft draft=FrameBehavior.draft(c,"The cube root of 8 is used to calculate the intensity ratio for a one-level difference in level.");
  BoundAnswer.Draft bound=SemanticPlan.bind(plan,draft,new BoundAnswer.Cancel());if(!bound.claims.get(0).text.equals(draft.claims.get(0).text))throw new AssertionError("Rewritten prose");n++;
  BoundAnswer.Claim original=draft.claims.get(0);BoundAnswer.Draft wrong=new BoundAnswer.Draft(draft.question,Arrays.asList(new BoundAnswer.Claim(original.obligation,"Other subject",original.qualifier,original.text,original.references)),draft.count);
  try{SemanticPlan.bind(plan,wrong,new BoundAnswer.Cancel());throw new AssertionError("Hidden wrong subject");}catch(IllegalArgumentException expected){n++;}
  BoundAnswer.Rendered rendered=EvidenceLinker.render(bound,new BoundAnswer.Cancel());if(!rendered.text.substring(rendered.links.get(0).start,rendered.links.get(0).end).equals("[1]"))throw new AssertionError("Broken typed citation");n++;
  System.out.println("Compositional mathematical checks: "+n);
 }
}
