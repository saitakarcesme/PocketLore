package org.pocketlore.app;
import java.util.*;
public final class PlanBehavior {
 static int checks;static void reject(Runnable r){try{r.run();}catch(IllegalArgumentException|IllegalStateException e){checks++;return;}throw new AssertionError("Unexpected plan approval");}
 public static void main(String[] args){
  BoundAnswer.Cancel cancel=new BoundAnswer.Cancel();BoundAnswer.Catalog base=FrameBehavior.catalog("Arbordale","Arbordale is the capital and largest city of Newland.");SourcePlan.Catalog catalog=new SourcePlan.Catalog(base,cancel);String question="Describe the documented relation.";
  SourcePlan.Plan plan=SourcePlan.parse(question,"O1|F1,F2",10,catalog,cancel);BoundAnswer.Draft draft=FrameBehavior.draft(base,"Arbordale is the capital and largest city of Newland.");BoundAnswer.Draft bound=SourcePlan.bind(plan,draft,cancel);if(!bound.claims.get(0).text.equals(draft.claims.get(0).text))throw new AssertionError("Rewritten prose");checks++;
  for(String raw:Arrays.asList("O1|F99","O1|F1,F1","O2|F1","O1|F1\nO1|F2","W|O1|No evidence","O1|F1|invented"))reject(()->SourcePlan.parse(question,raw,10,catalog,cancel));
  reject(()->SourcePlan.parse(question,"O1|F1",128,catalog,cancel));
  SourcePlan.Plan incomplete=SourcePlan.parse(question,"O1|F1",10,catalog,cancel);reject(()->SourcePlan.bind(incomplete,draft,cancel));
  reject(()->SourcePlan.bind(plan,FrameBehavior.draft(base,"Arbordale is the capital and largest city of Newland. All visits are free."),cancel));
  reject(()->SourcePlan.bind(plan,FrameBehavior.draft(base,"Newland is the capital and largest city of Arbordale."),cancel));
  SourcePlan.Plan other=SourcePlan.parse("Which city is documented?","O1|F1,F2",10,catalog,cancel);reject(()->SourcePlan.bind(other,draft,cancel));
  BoundAnswer.Cancel stopped=new BoundAnswer.Cancel();stopped.cancel();reject(()->new SourcePlan.Catalog(base,stopped));reject(()->SourcePlan.parse(question,"O1|F1",10,catalog,stopped));reject(()->SourcePlan.bind(plan,draft,stopped));SourcePlan.bind(plan,draft,new BoundAnswer.Cancel());checks++;
  BoundAnswer.Rendered rendered=EvidenceLinker.render(bound,cancel);if(!rendered.text.substring(rendered.links.get(0).start,rendered.links.get(0).end).equals("[1]"))throw new AssertionError("Broken typed link");checks++;
  System.out.println("Source plan behavioral checks: "+checks);
 }
}
