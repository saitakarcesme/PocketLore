package org.pocketlore.app;
import java.util.*;
public final class GuardedBehavior {
 static int checks;
 static void reject(Runnable f){try{f.run();}catch(IllegalArgumentException|IllegalStateException e){checks++;return;}throw new AssertionError("Unexpected guarded approval");}
 static Map<String,EvidenceLinker.Score> scores(BoundAnswer.Draft d,BoundAnswer.Catalog c){Map<String,EvidenceLinker.Score> m=new HashMap<>();for(BoundAnswer.Claim cl:d.claims)for(EvidenceLinker.Candidate ca:EvidenceLinker.candidates(cl,c,new BoundAnswer.Cancel()))for(EvidenceLinker.Pair p:ca.pairs)m.put(p.key,new EvidenceLinker.Score(0,1,0,50,""));return m;}
 public static void main(String[] args){
  // Constructed controls, not corpus facts or inference. Even perfect mock scores must fail unsafe claims.
  BoundAnswer.Catalog c=FrameBehavior.catalog("Arbordale","Arbordale is the capital and largest city of Newland.");
  BoundAnswer.Draft d=FrameBehavior.draft(c,"Arbordale is the capital and largest city of Newland.");Map<String,EvidenceLinker.Score> m=scores(d,c);
  GuardedEvidenceLinker.Result r=GuardedEvidenceLinker.bind(d,c,m,new BoundAnswer.Cancel());if(!r.proof.draft.claims.get(0).text.equals(d.claims.get(0).text))throw new AssertionError("Rewritten prose");checks++;
  reject(()->GuardedEvidenceLinker.bind(d,c,new HashMap<>(),new BoundAnswer.Cancel()));
  for(String text:Arrays.asList("Newland is the capital and largest city of Arbordale.","Arbordale is the capital and largest city of Newland. All visitors travel free.","Arbordale is not the capital and largest city of Newland.")){
   BoundAnswer.Draft bad=FrameBehavior.draft(c,text);reject(()->GuardedEvidenceLinker.bind(bad,c,scores(bad,c),new BoundAnswer.Cancel()));}
  BoundAnswer.Cancel stop=new BoundAnswer.Cancel();stop.cancel();reject(()->GuardedEvidenceLinker.bind(d,c,m,stop));GuardedEvidenceLinker.bind(d,c,m,new BoundAnswer.Cancel());checks++;
  Map<String,EvidenceLinker.Score> failed=new HashMap<>();for(String key:m.keySet())failed.put(key,new EvidenceLinker.Score(0,1,0,513,""));reject(()->GuardedEvidenceLinker.bind(d,c,failed,new BoundAnswer.Cancel()));
  Map<String,EvidenceLinker.Score> nan=new HashMap<>();for(String key:m.keySet())nan.put(key,new EvidenceLinker.Score(0,Double.NaN,0,50,""));reject(()->GuardedEvidenceLinker.bind(d,c,nan,new BoundAnswer.Cancel()));
  System.out.println("Guarded composition behavioral checks: "+checks);
 }
}
