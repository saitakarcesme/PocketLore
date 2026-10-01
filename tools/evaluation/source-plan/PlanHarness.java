package org.pocketlore.app;
import java.nio.file.*;import java.util.*;
public final class PlanHarness {
 static String q(String s){return BindingHarness.q(s);}
 static String frames(SourcePlan.Catalog c){StringBuilder b=new StringBuilder("[");boolean first=true;for(Map.Entry<String,FactFrames.Ground> e:c.facts.entrySet()){if(!first)b.append(',');first=false;b.append("{\"id\":").append(q(e.getKey())).append(",\"fact\":").append(q(e.getValue().fact.key())).append(",\"spans\":[");for(int i=0;i<e.getValue().refs.size();i++){if(i>0)b.append(',');BoundAnswer.Span s=e.getValue().refs.get(i);b.append(q(s.label));}b.append("]}");}return b.append(']').toString();}
 public static void main(String[] args)throws Exception{
  Path input=Path.of(args[0]),out=Path.of(args[2]);Files.createDirectories(out);long session=NativeRuntime.create(),start=System.nanoTime();
  try{NativeRuntime.load(session,BindingHarness.b(args[1]));Files.writeString(out.resolve("load.json"),"{\"identity\":"+q(NativeRuntime.identity())+",\"load_ms\":"+(System.nanoTime()-start)/1e6+"}",StandardOpenOption.CREATE_NEW);
   for(String row:Files.readAllLines(input.resolve("cases.tsv"))){String[] f=row.split("\t");String id=f[0],question=BindingHarness.decode(f[1]);BoundAnswer.Cancel cancel=new BoundAnswer.Cancel();SourcePlan.Catalog catalog=new SourcePlan.Catalog(BindingHarness.catalog(input,id,cancel),cancel);BindingHarness.Stage plan=new BindingHarness.Stage(),draft=new BindingHarness.Stage();String failure="",claims="[]",rendered="",links="[]";
    Files.writeString(out.resolve(id+".frames.json"),frames(catalog),StandardOpenOption.CREATE_NEW);
    try{if(catalog.facts.isEmpty())throw new IllegalArgumentException("No source frames; planner and prose not run");plan=BindingHarness.generate(session,SourcePlan.SYSTEM,SourcePlan.prompt(question,catalog,cancel),128,out.resolve(id+".plan"));if(!plan.failure.isEmpty())throw new IllegalArgumentException(plan.failure);SourcePlan.Plan selected=SourcePlan.parse(question,plan.raw,plan.tokens,catalog,cancel);
     draft=BindingHarness.generate(session,BoundAnswer.DRAFT_SYSTEM,SourcePlan.prosePrompt(selected,cancel),320,out.resolve(id+".draft"));if(!draft.failure.isEmpty())throw new IllegalArgumentException(draft.failure);BoundAnswer.Draft bound=SourcePlan.bind(selected,BoundAnswer.parse(question,draft.raw,catalog.sources,draft.tokens,cancel),cancel);claims=BindingHarness.spans(bound);BoundAnswer.Rendered r=EvidenceLinker.render(bound,cancel);rendered=r.text;StringBuilder ls=new StringBuilder("[");for(int i=0;i<r.links.size();i++){if(i>0)ls.append(',');BoundAnswer.Link l=r.links.get(i);ls.append("{\"start_utf16\":").append(l.start).append(",\"end_utf16\":").append(l.end).append('}');}links=ls.append(']').toString();
    }catch(IllegalArgumentException e){failure=e.getMessage();}
    String result="{\"id\":"+q(id)+",\"question\":"+q(question)+",\"plan\":"+BindingHarness.json(plan)+",\"draft\":"+BindingHarness.json(draft)+",\"claims\":"+claims+",\"rendered\":"+q(rendered)+",\"links\":"+links+",\"failure\":"+q(failure)+",\"route\":"+q(rendered.isEmpty()?"WITHHELD":"SCREEN_ELIGIBLE")+",\"native_after\":"+Arrays.toString(NativeRuntime.resourceState())+"}\n";
    Files.writeString(out.resolve(id+".json"),result,StandardOpenOption.CREATE_NEW);System.out.println(id+" "+(plan.tokens+draft.tokens)+" "+failure);System.out.flush();
   }
  }finally{NativeRuntime.close(session);Files.writeString(out.resolve("closed.json"),Arrays.toString(NativeRuntime.resourceState()));}
 }
}
