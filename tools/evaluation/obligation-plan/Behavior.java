package org.pocketlore.app;
import java.nio.file.*;import java.util.*;
public final class Behavior {
 static int checks;static void reject(Runnable r){try{r.run();}catch(IllegalArgumentException|IllegalStateException e){checks++;return;}throw new AssertionError("Unexpected approval");}
 public static void main(String[] args)throws Exception{
  BoundAnswer.Cancel cancel=new BoundAnswer.Cancel();BoundAnswer.Catalog c=FrameBehavior.catalog("Control","A plant needs water. Growth requires adequate light.");SentenceEvidence e=new SentenceEvidence(c,cancel);String question="Describe the documented relation; explain its condition.";List<String> rows=Files.readAllLines(Path.of(args[0]));
  ObligationLedger.Plan p=ObligationLedger.parse(question,BindingHarness.decode(rows.get(0)),25,e,cancel);checks++;
  for(String row:rows.subList(1,rows.size()))reject(()->ObligationLedger.parse(question,BindingHarness.decode(row),25,e,cancel));
  reject(()->ObligationLedger.parse(question,BindingHarness.decode(rows.get(0)),160,e,cancel));BoundAnswer.Cancel stopped=new BoundAnswer.Cancel();stopped.cancel();reject(()->ObligationLedger.parse(question,BindingHarness.decode(rows.get(0)),25,e,stopped));
  String raw="O1|P1.1|Control|none|A plant needs water. Every visitor gets a free ticket.\nO2|P1.2|Control|none|Growth requires adequate light.";BoundAnswer.Draft d=ObligationLedger.candidate(p,raw,50,cancel);if(!ObligationLedger.preview(d,cancel).text.contains("Every visitor gets a free ticket."))throw new AssertionError("Tail silently deleted");checks++;
  reject(ObligationLedger::requirePublicationAuthorization);reject(()->ObligationLedger.candidate(p,raw,352,cancel));reject(()->ObligationLedger.candidate(p,raw.replace("O1|P1.1","O1|P1.2"),50,cancel));
  BoundAnswer.Source s=c.sources.get(0);reject(()->new BoundAnswer.Source(s.edition,s.id,s.documentHash,s.hash,s.title,s.date,s.rights,s.text+"Changed."));
  String other=String.join("",Collections.nCopies(64,"b"));BoundAnswer.Source second=new BoundAnswer.Source(other,s.id,s.documentHash,s.hash,s.title,s.date,s.rights,s.text);BoundAnswer.Catalog mixed=new BoundAnswer.Catalog(Arrays.asList(s,second),cancel);if(mixed.spans.get("P1.1").source.key().equals(mixed.spans.get("P2.1").source.key()))throw new AssertionError("Lost namespace");checks++;
  System.out.println("Obligation ledger checks: "+checks);
 }
}
