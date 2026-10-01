package org.pocketlore.app;
import java.util.*;import java.nio.file.*;import java.nio.charset.StandardCharsets;
/** Constructed mechanics tests are not corpus facts, source approvals or inference. */
public final class AdapterCheck {
 static void check(boolean ok){if(!ok)throw new AssertionError();}
 static void rejects(Runnable r){try{r.run();}catch(IllegalArgumentException|IllegalStateException e){return;}throw new AssertionError("Invalid adapter input accepted");}
 static ScaleAnswerAdapter.Review approval(ScaleAnswerAdapter.Snapshot s,int start,int end){return new ScaleAnswerAdapter.Review(s.fingerprint(),start,end,BoundAnswer.sha(s.text.substring(start,end)),"a".repeat(64),"b".repeat(64),true);}
 public static void main(String[] args)throws Exception {
  ScalePublicationChecks.run();
  String text="Subject Ω 😀 retains \\sqrt[5]{100} [12] only when the stated condition holds.";
  String[] fields={"a".repeat(64),"shard-a","fixture","1","b".repeat(64),BoundAnswer.sha(text),"Constructed subject","https://example.invalid/1","https://example.invalid/history","2026-01-01","Constructed test rights","No factual corpus clearance","c".repeat(64),"constructed formula context"};
  ScaleAnswerAdapter.Snapshot s=new ScaleAnswerAdapter.Snapshot(fields,text);
  rejects(()->ScaleAnswerAdapter.admit(s,0,text.length(),new ScaleAnswerAdapter.Ledger(Collections.emptyMap()),()->false));
  ScaleAnswerAdapter.Review approval=approval(s,0,text.length());ScaleAnswerAdapter.Ledger ledger=new ScaleAnswerAdapter.Ledger(Collections.singletonMap(s.key(),approval));
  ScaleAnswerAdapter.Evidence e=ScaleAnswerAdapter.admit(s,0,text.length(),ledger,()->false);
  ScaleAnswerAdapter.Prepared p=new ScaleAnswerAdapter.Prepared("Explain the subject",Collections.singletonList(e),()->false);
  ScaleAnswerAdapter.Reference link=p.link(1,"P1.1",()->false);check(link.start==0&&link.end==text.length()&&link.source.text.substring(link.start,link.end).equals(text));check(p.prompt(()->false).contains("\\sqrt[5]{100} [12]"));
  rejects(()->p.link(1,"12",()->false));rejects(()->p.link(2,"P1.1",()->false));rejects(()->p.publish("Invented factual tail.","C1|SUPPORTED\nO1|COMPLETE\nVERDICT|PASS"));
  rejects(()->ScaleAnswerAdapter.admit(s,0,text.length()-1,ledger,()->false));rejects(()->ScaleAnswerAdapter.admit(s,0,text.length(),ledger,()->true));
  String[] changed=fields.clone();changed[9]="2027-01-01";ScaleAnswerAdapter.Snapshot other=new ScaleAnswerAdapter.Snapshot(changed,text);rejects(()->ScaleAnswerAdapter.admit(other,0,text.length(),ledger,()->false));
  changed=fields.clone();changed[1]="shard-b";ScaleAnswerAdapter.Snapshot wrongShard=new ScaleAnswerAdapter.Snapshot(changed,text);rejects(()->ScaleAnswerAdapter.admit(wrongShard,0,text.length(),ledger,()->false));
  rejects(()->new ScaleAnswerAdapter.Snapshot(fields,text+"changed"));rejects(()->new ScaleAnswerAdapter.Prepared("What is my result?",Collections.singletonList(e),()->false));
  rejects(()->new ScaleAnswerAdapter.Prepared("Explain",Arrays.asList(e,e),()->false));
  ScaleAnswerAdapter.Ledger missingReceipt=new ScaleAnswerAdapter.Ledger(Collections.singletonMap(s.key(),new ScaleAnswerAdapter.Review(s.fingerprint(),0,text.length(),BoundAnswer.sha(text),"","",true)));rejects(()->ScaleAnswerAdapter.admit(s,0,text.length(),missingReceipt,()->false));
  int split=text.indexOf("😀")+1;ScaleAnswerAdapter.Ledger cut=new ScaleAnswerAdapter.Ledger(Collections.singletonMap(s.key(),approval(s,split,text.length())));rejects(()->ScaleAnswerAdapter.admit(s,split,text.length(),cut,()->false));
  for(int field:new int[]{4,7,8,10,11,12,13}){String[] f=fields.clone();f[field]=field==4||field==12?"d".repeat(64):f[field]+" changed";ScaleAnswerAdapter.Snapshot altered=new ScaleAnswerAdapter.Snapshot(f,text);rejects(()->ScaleAnswerAdapter.admit(altered,0,text.length(),ledger,()->false));}
  String longText="A".repeat(1201)+".";String[] large=fields.clone();large[5]=BoundAnswer.sha(longText);ScaleAnswerAdapter.Snapshot largeSource=new ScaleAnswerAdapter.Snapshot(large,longText);ScaleAnswerAdapter.Ledger largeReview=new ScaleAnswerAdapter.Ledger(Collections.singletonMap(largeSource.key(),approval(largeSource,0,longText.length())));rejects(()->ScaleAnswerAdapter.admit(largeSource,0,longText.length(),largeReview,()->false));
  check(!p.prompt(()->false).contains("Invented factual tail"));System.out.println("Constructed typed-controller tests pass; no real clearance or generated success");
  Map<String,ScaleAnswerAdapter.Snapshot> real=new HashMap<>();int count=0;for(String line:Files.readAllLines(Path.of(args[0]))){String[] columns=line.split("\t",-1);String[] f=new String[14];for(int i=0;i<14;i++)f[i]=new String(Base64.getDecoder().decode(columns[i]),StandardCharsets.UTF_8);String body=new String(Base64.getDecoder().decode(columns[14]),StandardCharsets.UTF_8);ScaleAnswerAdapter.Snapshot source=new ScaleAnswerAdapter.Snapshot(f,body);real.put(source.id,source);int end=Integer.parseInt(columns[15]);rejects(()->ScaleAnswerAdapter.admit(source,0,end,new ScaleAnswerAdapter.Ledger(Collections.emptyMap()),()->false));count++;}
  check(count==8);System.out.println("8 real sealed bulk snapshots denied without independent review");
  for(String line:Files.readAllLines(Path.of(args[1]))){String[] f=line.split("\t");String question=new String(Base64.getDecoder().decode(f[1]),StandardCharsets.UTF_8);String route;
   if(EvidenceAvailability.scope(question)!=EvidenceAvailability.Scope.REFERENCE)route="withheld_unavailable";
   else{for(String id:f[2].split(",")){ScaleAnswerAdapter.Snapshot source=real.get(id);check(source!=null);rejects(()->ScaleAnswerAdapter.admit(source,0,Math.min(100,source.text.length()),new ScaleAnswerAdapter.Ledger(Collections.emptyMap()),()->false));}route="withheld_pending_source_review";}
   check(route.equals(f[3]));System.out.println(f[0]+"\t"+route+"\tpublished_claims=0");
  }
 }
}
