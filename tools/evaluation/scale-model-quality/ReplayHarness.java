package org.pocketlore.app;
import java.nio.file.*;import java.util.*;
/** Replay the frozen controller against actual drafts; no inference or semantic certification. */
public final class ReplayHarness {
 public static void main(String[] args)throws Exception {
  Path input=Path.of(args[0]);int count=0;
  for(String line:Files.readAllLines(input.resolve("replay.tsv"))){
   String[] row=line.split("\t",-1);String question=ScaleHarness.decode(row[1]);List<ResearchEngine.Hit> hits=new ArrayList<>();
   for(String source:Files.readAllLines(input.resolve(row[0]+".tsv"))){String[] f=source.split("\t");for(int i=0;i<f.length;i++)f[i]=ScaleHarness.decode(f[i]);hits.add(new ResearchEngine.Hit(new ResearchEngine.Passage(f),1));}
   String actual=ObligationAnswer.failure(question,ScaleHarness.decode(row[2]),hits,Integer.parseInt(row[3]),Integer.parseInt(row[4]),512);
   if(!actual.equals(ScaleHarness.decode(row[5])))throw new AssertionError(row[0]+" controller drift: "+actual);
   count++;
  }
  if(count<192)throw new AssertionError("Incomplete four-model replay");
  if(ObligationAnswer.plan("First; second; third").size()!=3)throw new AssertionError("Obligation plan");
  for(String q:new String[]{"", "a;b;c;d;e", "x".repeat(1001)}){boolean rejected=false;try{ObligationAnswer.plan(q);}catch(IllegalArgumentException e){rejected=true;}if(!rejected)throw new AssertionError("Unbounded question accepted");}
  List<ResearchEngine.Hit> none=Collections.emptyList();
  if(!ObligationAnswer.failure("Explain", "O1: text",none,1200,512,512).contains("boundary"))throw new AssertionError("Token boundary accepted");
  if(!ObligationAnswer.failure("Explain", "O2: text",none,1200,1,512).contains("Wrong"))throw new AssertionError("Extra obligation accepted");
  if(!ObligationAnswer.failure("Explain", "O1: Insufficient evidence",none,1200,1,512).contains("withheld"))throw new AssertionError("Abstention published");
  System.out.println("PASS actual-draft controller replay and bounded obligation regressions: "+count);
 }
}
