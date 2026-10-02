package org.pocketlore.app;
import java.util.*;
import java.util.concurrent.CancellationException;
/** Constructed transport fixtures only; this authority makes no semantic qualification claim. */
public final class Behavior {
 static final String draft="A test fixture has two parts. [[S1]]\nGAPS: none";
 static final String[] row={"edition:doc:passage","Transport fixture","https://example.invalid/fixture","2026-10-02","Constructed test only","A test fixture has two parts. 😀"};
 static int tests;
 static GeneralGroundedAnswer.Context context(String[] r,String provenance,String legal){return GeneralGroundedAnswer.supplied("What does the fixture contain?",Arrays.asList(new ResearchEngine.Passage(r,provenance,legal)));}
 static GeneralGroundedAnswer.Context ctx=context(row,"edition revision1","Test fixture rights");
 static ReviewedAnswerVerifier.Region fact(int a,int b,int source,int start,int end){return new ReviewedAnswerVerifier.Region(a,b,true,true,Arrays.asList(new ReviewedAnswerVerifier.SourceSpan(source,start,end)));}
 static List<ReviewedAnswerVerifier.Region> regions(){return Arrays.asList(fact(0,draft.indexOf('\n'),0,0,28),new ReviewedAnswerVerifier.Region(draft.indexOf('\n')+1,draft.length(),false,true,Collections.emptyList()));}
 static ReviewedAnswerVerifier.Review review(String bind,boolean complete,boolean absent,List<ReviewedAnswerVerifier.Region> regions){return new ReviewedAnswerVerifier.Review(bind,"test-only authority",complete,absent,Arrays.asList("What the fixture contains"),regions);}
 static ReviewedAnswerVerifier verifier(ReviewedAnswerVerifier.Review r,boolean trusted){return new ReviewedAnswerVerifier(new ReviewedAnswerVerifier.Authority(){public boolean independentlyQualified(){return trusted;}public ReviewedAnswerVerifier.Review inspect(String h,GeneralGroundedAnswer.Context c,String d,java.util.function.BooleanSupplier stop){return r;}});}
 static void result(boolean ok,String label){if(!ok)throw new AssertionError(label);tests++;System.out.println("PASS "+label);}
 static void rejects(ReviewedAnswerVerifier.Review r,GeneralGroundedAnswer.Context c,String d,String label){result(!verifier(r,true).rejection(c,d,()->false).isEmpty(),label);}
 public static void main(String[] args){
  String hash=ReviewedAnswerVerifier.binding(ctx,draft);ReviewedAnswerVerifier.Review good=review(hash,true,false,regions());
  result(verifier(good,true).rejection(ctx,draft,()->false).isEmpty(),"exact constructed binding, not semantic proof");
  result(!verifier(good,false).rejection(ctx,draft,()->false).isEmpty(),"untrusted authority");
  rejects(good,ctx,draft+" False tail.","changed draft");
  rejects(good,GeneralGroundedAnswer.supplied("Different obligation",ctx.sources),draft,"changed question");
  for(int i=0;i<row.length;i++){String[] changed=row.clone();changed[i]+=" changed";rejects(good,context(changed,"edition revision1","Test fixture rights"),draft,"changed source field "+i);}
  rejects(good,context(row,"edition revision2","Test fixture rights"),draft,"changed collection revision");
  rejects(good,context(row,"edition revision1","Changed rights"),draft,"changed license bytes");
  rejects(review(hash,false,false,regions()),ctx,draft,"incomplete obligation");
  rejects(review(hash,true,true,regions()),ctx,draft,"absent is not useful answer");
  rejects(review(hash,true,false,Arrays.asList(fact(0,10,0,0,28))),ctx,draft,"unreviewed tail");
  rejects(review(hash,true,false,Arrays.asList(fact(1,draft.length(),0,0,28))),ctx,draft,"unreviewed prefix");
  rejects(review(hash,true,false,Arrays.asList(fact(0,20,0,0,28),fact(19,draft.length(),0,0,28))),ctx,draft,"overlap");
  rejects(review(hash,true,false,Arrays.asList(fact(0,draft.length(),1,0,28))),ctx,draft,"missing source");
  rejects(review(hash,true,false,Arrays.asList(fact(0,draft.length(),0,0,999))),ctx,draft,"invalid source offset");
  rejects(review(hash,true,false,Arrays.asList(fact(0,draft.length(),0,30,31))),ctx,draft,"split source surrogate pair");
  rejects(review(hash,true,false,Arrays.asList(new ReviewedAnswerVerifier.Region(0,draft.length(),true,false,Arrays.asList(new ReviewedAnswerVerifier.SourceSpan(0,0,28))))),ctx,draft,"unsupported full draft");
  rejects(review(hash,true,false,Arrays.asList(new ReviewedAnswerVerifier.Region(0,draft.length(),false,true,Collections.emptyList()))),ctx,draft,"nonfactual cannot certify answer");
  rejects(review(hash,true,false,Arrays.asList(fact(0,draft.length(),0,29,30))),ctx,draft,"whitespace-only evidence");
  GeneralGroundedAnswer.Context two=GeneralGroundedAnswer.supplied(ctx.question,Arrays.asList(ctx.sources.get(0),new ResearchEngine.Passage(new String[]{"second","Other",row[2],row[3],row[4],row[5]})));
  String h2=ReviewedAnswerVerifier.binding(two,draft);rejects(review(h2,true,false,Arrays.asList(fact(0,draft.length(),1,0,28))),two,draft,"wrong-neighbor visible citation");
  String splitDraft="A test fixture has two parts. [[S2]]";
  int cut=splitDraft.indexOf("S2");
  rejects(review(ReviewedAnswerVerifier.binding(two,splitDraft),true,false,Arrays.asList(fact(0,cut,0,0,28),fact(cut,splitDraft.length(),0,0,28))),two,splitDraft,"split citation cannot evade source binding");
  List<ResearchEngine.Passage> swapped=new ArrayList<>(two.sources);Collections.reverse(swapped);rejects(review(h2,true,false,regions()),GeneralGroundedAnswer.supplied(ctx.question,swapped),draft,"source order");
  try{verifier(good,true).rejection(ctx,draft,()->true);throw new AssertionError("cancel ignored");}catch(CancellationException expected){result(true,"cancellation");}
  try{ReviewedAnswerVerifier.binding(ctx,"invalid \ud800");throw new AssertionError("invalid UTF16 accepted");}catch(IllegalArgumentException expected){result(true,"invalid UTF16 hash identity");}
  System.out.println("PASS "+tests+" structural review controls; no generated usefulness or trusted production authority inferred");
 }
}
