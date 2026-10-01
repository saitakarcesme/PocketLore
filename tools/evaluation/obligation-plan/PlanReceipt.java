package org.pocketlore.app;
import java.nio.file.*;import java.util.*;
/** Derive exact source plan trace from immutable stages, without model access. */
public final class PlanReceipt {
 public static void main(String[] args)throws Exception{
  Path input=Path.of(args[0]);StringBuilder all=new StringBuilder("[");boolean first=true;
  for(String row:Files.readAllLines(Path.of(args[1]))){String[] f=row.split("\t",-1);String id=f[0],question=BindingHarness.decode(f[1]);BoundAnswer.Cancel cancel=new BoundAnswer.Cancel();SentenceEvidence e=new SentenceEvidence(BindingHarness.catalog(input,id,cancel),cancel);String failure="";List<BoundAnswer.Claim> trace=new ArrayList<>();
   try{if(!BindingHarness.decode(f[6]).isEmpty())throw new IllegalArgumentException(BindingHarness.decode(f[6]));ObligationLedger.Plan p=ObligationLedger.parse(question,BindingHarness.decode(f[2]),Integer.parseInt(f[3]),e,cancel);for(Map.Entry<Integer,ObligationLedger.Part> entry:p.parts.entrySet())trace.add(new BoundAnswer.Claim(entry.getKey(),"UNTRUSTED PLANNER ACCOUNT","not source evidence",entry.getValue().account,entry.getValue().refs));}catch(IllegalArgumentException err){failure=err.getMessage();}
   if(!first)all.append(',');first=false;all.append("{\"id\":").append(BindingHarness.q(id)).append(",\"plan_trace\":").append(BindingHarness.spans(new BoundAnswer.Draft(question,trace,BoundAnswer.obligations(question).size()))).append(",\"failure\":").append(BindingHarness.q(failure)).append('}');
  }Files.writeString(Path.of(args[2]),all.append(']').toString());
 }
}
