package org.pocketlore.app;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
public final class CompleteClaimCheck {
 static String d(String v){return new String(Base64.getDecoder().decode(v),StandardCharsets.UTF_8);}
 static ResearchEngine.Result evidence(Path path)throws Exception {
  List<ResearchEngine.Hit> hits=new ArrayList<>();
  for(String line:Files.readAllLines(path)){String[] row=line.split("\t");for(int i=0;i<row.length;i++)row[i]=d(row[i]);hits.add(new ResearchEngine.Hit(new ResearchEngine.Passage(row),1));}
  return new ResearchEngine.Result(hits,Collections.emptySet(),"Frozen source evidence");
 }
 public static void main(String[] args)throws Exception {
  Path root=Path.of(args[0]);int count=0;
  for(String line:Files.readAllLines(root.resolve("regressions.tsv"))) {
   String[] row=line.split("\t");ResearchEngine.Result evidence=evidence(root.resolve(row[0]+".tsv"));String raw=d(row[1]);
   boolean rejected=!AnswerEngine.citationFailure(raw,EvidencePrompt.ids(evidence)).isEmpty() || !AnswerEngine.completeClaimFailure(raw,evidence,900).isEmpty() || !AnswerEngine.claimSupportFailure(raw,evidence,900).isEmpty();
   if(!rejected)throw new AssertionError("Malformed historical output published: "+row[0]);count++;
  }
  for(String line:Files.readAllLines(root.resolve("absent.tsv"))) {
   String[] row=line.split("\t");ResearchEngine.Result ev=evidence(root.resolve(row[0]+".tsv"));
   AnswerEngine.Outcome r=AnswerEngine.answer(d(row[1]),ev,(p,l,s)->{throw new AssertionError("Absent evidence invoked generator");},x->{},()->false);
   if(r.kind!=AnswerEngine.Kind.ABSTAINED)throw new AssertionError("Absent not withheld");count++;
  }
  int unsupported=0;
  for(String line:Files.readAllLines(root.resolve("unsupported.tsv"))) {
   String[] row=line.split("\\t");byte[] raw=d(row[2]).getBytes(StandardCharsets.UTF_8);
   AnswerEngine.Outcome r=AnswerEngine.answer(d(row[1]),evidence(root.resolve(row[0]+".tsv")),(p,l,sink)->{sink.onToken(raw);return 50;},x->{},()->false);
   if(r.kind==AnswerEngine.Kind.GENERATED)throw new AssertionError("Unsupported historical draft published: "+row[0]);unsupported++;
  }
  System.out.println("PASS "+unsupported+" unsupported historical drafts withheld by current controller");
  ResearchEngine.Result dna=evidence(root.resolve("positive.tsv"));String id=dna.hits.get(0).passage.id;
  String good="["+id+"] DNA's instructions are used to make proteins in a two-step process.";
  if(!AnswerEngine.completeClaimFailure(good,dna,900).isEmpty())throw new AssertionError("Complete supported clause rejected");
  if(AnswerEngine.completeClaimFailure("["+id+"] The DNA molecule.",dna,900).isEmpty())throw new AssertionError("Noun fragment accepted");
  if(AnswerEngine.completeClaimFailure(String.join("\n",Collections.nCopies(5,good)),dna,900).isEmpty())throw new AssertionError("Five claims accepted");
  System.out.println("PASS "+count+" historical/absent regressions; complete-clause, noun-fragment and claim-count boundaries");
 }
}
