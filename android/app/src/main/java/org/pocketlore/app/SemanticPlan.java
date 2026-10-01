package org.pocketlore.app;
import java.util.*;
/** Alternative proof compiler; generation, plans and prose remain immutable. */
final class SemanticPlan {
 static BoundAnswer.Draft bind(SourcePlan.Plan plan,BoundAnswer.Draft draft,BoundAnswer.Cancel cancel){
  cancel.check();if(!plan.question.equals(draft.question))throw new IllegalArgumentException("Plan question mismatch");List<BoundAnswer.Claim> claims=new ArrayList<>();
  for(BoundAnswer.Claim c:draft.claims){cancel.check();List<FactFrames.Ground> grounds=plan.obligations.get(c.obligation);if(grounds==null)throw new IllegalArgumentException("Missing planned obligation");List<BoundAnswer.Span> refs;
   try{BoundAnswer.Draft one=new BoundAnswer.Draft(draft.question,Arrays.asList(c),draft.count);refs=SourcePlan.bind(plan,one,cancel).claims.get(0).references;}catch(IllegalArgumentException e){refs=EquationProof.prove(c.text,grounds,cancel);boolean subject=false;for(BoundAnswer.Span ref:refs)if(FactFrames.norm(c.subject).equals(FactFrames.norm(ref.source.title)))subject=true;if(!subject)throw new IllegalArgumentException("Mathematical subject context mismatch");}
   if(refs.size()>8)throw new IllegalArgumentException("Proof reference bound");claims.add(new BoundAnswer.Claim(c.obligation,c.subject,c.qualifier,c.text,refs));
  }return new BoundAnswer.Draft(draft.question,claims,draft.count);
 }
 private SemanticPlan(){}
}
