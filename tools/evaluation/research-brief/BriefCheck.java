package org.pocketlore.app;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
public final class BriefCheck {
 static void require(boolean ok){if(!ok)throw new AssertionError();}
 static ResearchEngine.Passage source(String id,String text){return new ResearchEngine.Passage(new String[]{id,"Subject Ω","https://example.org/source","Snapshot 2026-10-01","Fixture rights",text},"Constructed behavioral fixture, not corpus facts");}
 static ResearchEngine.Result evidence(ResearchEngine.Passage... ps){List<ResearchEngine.Hit> h=new ArrayList<>();for(ResearchEngine.Passage p:ps)h.add(new ResearchEngine.Hit(p,1));return new ResearchEngine.Result(h,Collections.emptySet(),"");}
 static void rejects(Runnable r){try{r.run();}catch(IllegalArgumentException|java.util.concurrent.CancellationException e){return;}throw new AssertionError("Expected rejection");}
 static void tests(){
  String text="Subject Ω 😀 has \\sqrt[5]{100} [12] only when the stated condition holds. An unsupported tail remains visible as source text.";
  ResearchEngine.Passage p=source("edition-a:p1",text);ResearchBrief.Brief b=ResearchBrief.create("Subject condition",evidence(p),()->false);
  require(b.quotes.size()==1&&!b.generated&&!b.completenessVerified);ResearchBrief.Quote q=b.quotes.get(0);
  require(b.text.substring(q.displayStart,q.displayEnd).equals(text)&&q.sourceEnd==text.length()&&q.sourceStart==0);q.verify(p);
  rejects(()->q.verify(source(p.id,text.replace("only when","regardless of whether"))));rejects(()->q.verify(null));rejects(()->q.verify(source("other-edition:p1",text)));
  rejects(()->ResearchBrief.create("Subject condition",evidence(p),()->true));
  java.util.concurrent.atomic.AtomicInteger calls=new java.util.concurrent.atomic.AtomicInteger();rejects(()->ResearchBrief.create("Subject condition",evidence(p,p),()->calls.incrementAndGet()>2));
  rejects(()->ResearchBrief.create("Subject condition",evidence(p,p),()->false));
  ResearchBrief.Brief oversized=ResearchBrief.create("Subject condition",evidence(source("long","x".repeat(8193))),()->false);require(oversized.quotes.isEmpty()&&oversized.omitted==1);
  ResearchEngine.Passage noRights=new ResearchEngine.Passage(new String[]{"id","title","url","date","",text},"provenance");require(ResearchBrief.create("Subject condition",evidence(noRights),()->false).quotes.isEmpty());
  ResearchEngine.Passage unreviewed=new ResearchEngine.Passage(new String[]{"id","title","url","date","rights",text},"Generation disabled: rights unresolved");require(ResearchBrief.create("Subject condition",evidence(unreviewed),()->false).quotes.isEmpty());
  require(ResearchBrief.create("Subject condition",evidence(p,source("edition-b:p1",text)),()->false).quotes.size()==2);
  require(ResearchBrief.create("Subject condition",evidence(),()->false).text.contains("No answer inferred"));
  rejects(()->ResearchBrief.create("x".repeat(2049),evidence(p),()->false));
  System.err.println("14 behavioral groups pass: whole-tail/subject, UTF-16, math, source mutations, namespaces, cancellation, metadata and bounds");
 }
 public static void main(String[] args)throws Exception{
  tests();List<ResearchEngine.Passage> passages=new ArrayList<>();
  for(String line:Files.readAllLines(Path.of(args[0]))){String[] r=line.split("\t",-1);passages.add(new ResearchEngine.Passage(Arrays.copyOf(r,6),r[6]));}
  ResearchEngine engine=new ResearchEngine(passages);
  ResearchEngine.Passage original=passages.get(0);ResearchBrief.Quote bound=ResearchBrief.create(original.title,evidence(original),()->false).quotes.get(0);
  for(String line:Files.readAllLines(Path.of(args[2]))){String draft=new String(Base64.getDecoder().decode(line),StandardCharsets.UTF_8);
   ResearchEngine.Passage substituted=new ResearchEngine.Passage(new String[]{original.id,original.title,original.url,original.sourceDate,original.license,draft},original.collectionProvenance);
   rejects(()->bound.verify(substituted));
  }
  System.err.println("Historical unsupported draft substitution rejected without old inference");
  for(String line:Files.readAllLines(Path.of(args[1]))){String[] r=line.split("\t",2);long start=System.nanoTime();ResearchBrief.Brief b=ResearchBrief.create(r[1],engine.research(r[1]),()->false);long elapsed=System.nanoTime()-start;
   List<String> ids=new ArrayList<>();for(ResearchBrief.Quote q:b.quotes){q.verify(q.source);ids.add(q.source.id);}
   System.out.println(r[0]+"\t"+elapsed+"\t"+String.join(",",ids)+"\t"+Base64.getEncoder().encodeToString(b.text.getBytes(StandardCharsets.UTF_8))+"\t"+b.availability.name());
  }
 }
}
