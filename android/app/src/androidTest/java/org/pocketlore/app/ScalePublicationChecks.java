package org.pocketlore.app;
import java.util.*;
/** Constructed mechanics only; no factual/model/independent-review success is asserted. */
public final class ScalePublicationChecks {
 static void ok(boolean value){if(!value)throw new AssertionError("Publication invariant");}
 static void denied(Runnable r){try{r.run();}catch(IllegalArgumentException|IllegalStateException expected){return;}throw new AssertionError("Unreviewed publication accepted");}
 static ScaleAnswerPublication.Reviews review(ScaleAnswerPublication.Candidate c,List<Boolean> claims,List<Boolean> obligations){return new ScaleAnswerPublication.Reviews(Collections.singletonMap(c.fingerprint,new ScaleAnswerPublication.Permit(c.fingerprint,"f".repeat(64),"Constructed reviewer fixture, not a real approval",true,claims,obligations)));}
 public static void run(){
  String text="Fixture subject Ω keeps \\sqrt[5]{100} [12] only under the stated condition.";
  String[] f={"a".repeat(64),"fixture-shard","test","1","b".repeat(64),BoundAnswer.sha(text),"Fixture subject Ω","https://example.invalid/source","https://example.invalid/history","2026-01-01","Constructed fixture rights","No real source clearance","c".repeat(64),"constructed"};
  ScaleAnswerAdapter.Snapshot s=new ScaleAnswerAdapter.Snapshot(f,text);
  ScaleAnswerAdapter.Review r=new ScaleAnswerAdapter.Review(s.fingerprint(),0,text.length(),BoundAnswer.sha(text),"d".repeat(64),"e".repeat(64),true);
  ScaleAnswerAdapter.Evidence e=ScaleAnswerAdapter.admit(s,0,text.length(),new ScaleAnswerAdapter.Ledger(Collections.singletonMap(s.key(),r)),()->false);
  ScaleAnswerAdapter.Prepared p=new ScaleAnswerAdapter.Prepared("Explain the fixture relation",Collections.singletonList(e),()->false);
  String raw="O1|P1.1|Fixture subject Ω|only under the stated condition|"+text;
  ScaleAnswerPublication.Candidate c=p.candidate(raw,30,()->false);
  ScaleAnswerPublication.Reviews approval=review(c,Collections.singletonList(true),Collections.singletonList(true));
  ok(p.publish(c,approval,()->false)==c);ok(c.text.contains(text));ok(c.text.startsWith("Subject: Fixture subject Ω\nScope: only under the stated condition\n"));
  ok(c.citations.size()==1&&c.text.substring(c.citations.get(0).start,c.citations.get(0).end).equals("[1]"));ok(c.citations.get(0).references.get(0).source==s);ok(c.reviewPacket.contains("\\sqrt[5]{100} [12]"));
  denied(()->p.publish(c,new ScaleAnswerPublication.Reviews(Collections.emptyMap()),()->false));
  denied(()->p.publish(c,review(c,Collections.singletonList(false),Collections.singletonList(true)),()->false));
  denied(()->p.publish(c,review(c,Collections.emptyList(),Collections.singletonList(true)),()->false));
  denied(()->p.publish(c,review(c,Collections.singletonList(true),Collections.singletonList(false)),()->false));
  denied(()->p.publish(c,review(c,Collections.singletonList(true),Collections.emptyList()),()->false));
  denied(()->p.publish(c,approval,()->true));ok(p.publish(c,approval,()->false)==c);
  for(String changed:new String[]{raw+" An invented tail is also true.",raw.replace("Fixture subject Ω|","Another subject|"),raw.replace("only under the stated condition|","always|"),raw.replace("keeps","rejects")}){
   ScaleAnswerPublication.Candidate altered=p.candidate(changed,30,()->false);denied(()->p.publish(altered,approval,()->false));
  }
  ScaleAnswerAdapter.Prepared differentQuestion=new ScaleAnswerAdapter.Prepared("Define the fixture relation",Collections.singletonList(e),()->false);
  denied(()->differentQuestion.publish(differentQuestion.candidate(raw,30,()->false),approval,()->false));
  denied(()->p.candidate(raw.replace("P1.1","12"),30,()->false));denied(()->p.candidate(raw,30,()->true));
  // A different source namespace cannot inherit the original answer's review.
  String[] other=f.clone();other[1]="other-fixture-shard";ScaleAnswerAdapter.Snapshot t=new ScaleAnswerAdapter.Snapshot(other,text);
  ScaleAnswerAdapter.Review tr=new ScaleAnswerAdapter.Review(t.fingerprint(),0,text.length(),BoundAnswer.sha(text),"d".repeat(64),"e".repeat(64),true);
  ScaleAnswerAdapter.Prepared tp=new ScaleAnswerAdapter.Prepared(p.question,Collections.singletonList(ScaleAnswerAdapter.admit(t,0,text.length(),new ScaleAnswerAdapter.Ledger(Collections.singletonMap(t.key(),tr)),()->false)),()->false);
  denied(()->tp.publish(tp.candidate(raw,30,()->false),approval,()->false));
  System.out.println("Constructed exact-output publication checks pass; no real independent approval or generated success");
  System.out.println("Constructed rendered fixture:\n"+c.text);
 }
}
