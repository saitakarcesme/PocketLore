package org.pocketlore.app;
import java.nio.file.*;import java.util.*;
/** Replay real saved stage bytes without model access. */
public final class ReplayLedger {
 public static void main(String[] args)throws Exception{
  Path input=Path.of(args[0]);StringBuilder all=new StringBuilder("[");boolean first=true;
  for(String row:Files.readAllLines(Path.of(args[1]))){String[] f=row.split("\t",-1);String id=f[0],question=BindingHarness.decode(f[1]),failure="",rendered="",claims="[]";BoundAnswer.Cancel cancel=new BoundAnswer.Cancel();SentenceEvidence catalog=new SentenceEvidence(BindingHarness.catalog(input,id,cancel),cancel);
   try{if(!BindingHarness.decode(f[6]).isEmpty())throw new IllegalArgumentException(BindingHarness.decode(f[6]));ObligationLedger.Plan p=ObligationLedger.parse(question,BindingHarness.decode(f[2]),Integer.parseInt(f[3]),catalog,cancel);if(!BindingHarness.decode(f[7]).isEmpty())throw new IllegalArgumentException(BindingHarness.decode(f[7]));BoundAnswer.Draft d=ObligationLedger.candidate(p,BindingHarness.decode(f[4]),Integer.parseInt(f[5]),cancel);rendered=ObligationLedger.preview(d,cancel).text;claims=BindingHarness.spans(d);}catch(IllegalArgumentException e){failure=e.getMessage();}
   if(!first)all.append(',');first=false;all.append("{\"id\":").append(BindingHarness.q(id)).append(",\"rendered\":").append(BindingHarness.q(rendered)).append(",\"claims\":").append(claims).append(",\"failure\":").append(BindingHarness.q(failure)).append('}');
  }Files.writeString(Path.of(args[2]),all.append(']').toString());
 }
}
