package org.pocketlore.app;
import java.util.*;import java.nio.file.*;
/** Behavior tests, not semantic source review or selected-model Android execution. */
public final class BehaviorHarness {
 static int tests=0;
 static void ok(boolean value,String message){tests++;if(!value)throw new AssertionError(message);}
 static void reject(Runnable action){tests++;try{action.run();}catch(IllegalArgumentException|IllegalStateException expected){return;}throw new AssertionError("Expected rejection");}
 static BoundAnswer.Source source(String edition,String id,String text){return new BoundAnswer.Source(edition,id,"c".repeat(64),BoundAnswer.sha(text),"Example","2026-10-01","Test-only non-corpus fixture",text);}
 static void tests(){
  BoundAnswer.Cancel cancel=new BoundAnswer.Cancel();String text="The fifth root of 100 is approximately 2.512. Formula [TeX: sqrt[5]{100}] and article footnote [1] remain text.";
  BoundAnswer.Source a=source("a".repeat(64),"same-id",text),b=source("b".repeat(64),"same-id",text);BoundAnswer.Catalog catalog=new BoundAnswer.Catalog(Arrays.asList(a,b),cancel);
  ok(!catalog.spans.get("P1.1").source.key().equals(catalog.spans.get("P2.1").source.key()),"Edition namespaces collapsed");
  reject(()->new BoundAnswer.Catalog(Arrays.asList(a,a),cancel));
  reject(()->new BoundAnswer.Source(a.edition,a.id,a.documentHash,a.hash,a.title,a.date,a.rights,text+" corrupted"));
  reject(()->new BoundAnswer.Source(a.edition,a.id,a.documentHash,a.hash,a.title,a.date,"",text));
  for(BoundAnswer.Span s:catalog.spans.values())ok(s.text().equals(s.source.text.substring(s.start,s.end)),"Span mismatch");
  String raw="O1|P1.1,P2.1|Root|none|The fifth root of 100 is approximately 2.512, not a [5] source citation.";
  BoundAnswer.Draft draft=BoundAnswer.parse("Explain the root.",raw,catalog,30,cancel);String audit="C1|SUPPORTED\nO1|COMPLETE\nVERDICT|PASS";
  BoundAnswer.Rendered result=BoundAnswer.render(draft,audit,14,cancel);ok(result.links.size()==1,"Formula became link");BoundAnswer.Link link=result.links.get(0);ok(result.text.substring(link.start,link.end).equals("[1]"),"Citation span mismatch");ok(link.references.size()==2,"Lost cross-edition reference");
  // A quotation/reference is never sufficient to render without a separately complete audit.
  reject(()->BoundAnswer.render(draft,"",0,cancel));reject(()->BoundAnswer.render(draft,"C1|UNSUPPORTED\nO1|COMPLETE\nVERDICT|FAIL",15,cancel));
  reject(()->BoundAnswer.parse("Explain",raw.replace("P1.1","P9.1"),catalog,30,cancel));
  reject(()->BoundAnswer.parse("Explain",raw.replace("O1|","O2|"),catalog,30,cancel));
  reject(()->BoundAnswer.parse("Explain",raw,catalog,320,cancel));
  reject(()->BoundAnswer.parse("Explain",raw.replace("P1.1,P2.1","P1.1,P1.1"),catalog,30,cancel));
  reject(()->BoundAnswer.parse("Explain","O1|P1.1|Root|none|The fifth root of.",catalog,30,cancel));
  reject(()->BoundAnswer.parse("Explain; compare",raw,catalog,30,cancel));
  reject(()->BoundAnswer.render(draft,audit,192,cancel));
  BoundAnswer.Cancel early=new BoundAnswer.Cancel();early.cancel();reject(()->new BoundAnswer.Catalog(List.of(a),early));
  BoundAnswer.Cancel during=new BoundAnswer.Cancel();BoundAnswer.Draft pending=BoundAnswer.parse("Explain",raw,catalog,30,during);during.cancel();reject(()->BoundAnswer.auditPrompt(pending,during));reject(()->BoundAnswer.render(pending,audit,14,during));
  BoundAnswer.Cancel retry=new BoundAnswer.Cancel();ok(!BoundAnswer.render(BoundAnswer.parse("Explain",raw,catalog,30,retry),audit,14,retry).text.isEmpty(),"Retry remains cancelled");
 }
 public static void main(String[] args)throws Exception{
  tests();int replay=0;Path dir=Path.of(args[0]);
  for(String row:Files.readAllLines(dir.resolve("replay.tsv"))){String[] f=row.split("\t",-1);String id=f[0],question=ScaleHarness.decode(f[1]),raw=ScaleHarness.decode(f[2]),audit=ScaleHarness.decode(f[4]),expected=ScaleHarness.decode(f[6]);BoundAnswer.Cancel cancel=new BoundAnswer.Cancel();BoundAnswer.Catalog c=BindingHarness.catalog(dir,id,cancel);String failure="",rendered="";
   try{BoundAnswer.Draft d=BoundAnswer.parse(question,raw,c,Integer.parseInt(f[3]),cancel);failure=BoundAnswer.auditFailure(d,audit,Integer.parseInt(f[5]),cancel);if(failure.isEmpty())rendered=BoundAnswer.render(d,audit,Integer.parseInt(f[5]),cancel).text;}catch(IllegalArgumentException e){failure=e.getMessage();}
   ok(failure.equals(expected),id+" route drift: "+failure+" != "+expected);ok(rendered.equals(ScaleHarness.decode(f[7])),id+" renderer drift");replay++;
  }
  System.out.println("PASS typed-reference behavior checks="+tests+", actual draft replays="+replay+"; no semantic or Android execution claim");
 }
}
