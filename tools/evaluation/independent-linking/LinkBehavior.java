package org.pocketlore.app;
import java.util.*;
public final class LinkBehavior {
 static int checks;static void check(boolean b){checks++;if(!b)throw new AssertionError("Behavior "+checks);}
 static void rejects(Runnable r){try{r.run();}catch(IllegalArgumentException|IllegalStateException e){checks++;return;}throw new AssertionError("Expected rejection");}
 public static void main(String[] args){
  String e=String.join("",Collections.nCopies(64,"a")),h=String.join("",Collections.nCopies(64,"b"));String text="Athens was a centre of philosophy. Formula [5] is ordinary text.";
  BoundAnswer.Source s=new BoundAnswer.Source(e,"article-1",h,BoundAnswer.sha(text),"Athens","2026-10-01","Test fixture; not factual corpus",text);BoundAnswer.Cancel cancel=new BoundAnswer.Cancel();BoundAnswer.Catalog catalog=new BoundAnswer.Catalog(Arrays.asList(s),cancel);
  BoundAnswer.Draft d=BoundAnswer.parse("Describe Athens.","O1|P1.1|Athens|none|It was a centre of philosophy. Formula [5] is ordinary text.",12,catalog,cancel);
  Map<String,EvidenceLinker.Score> scores=new HashMap<>();List<EvidenceLinker.Candidate> candidates=EvidenceLinker.candidates(d.claims.get(0),catalog,cancel);check(candidates.size()==2);check(candidates.get(0).pairs.size()==3);
  rejects(()->EvidenceLinker.bind(d,catalog,scores,cancel));
  for(EvidenceLinker.Candidate c:candidates)for(EvidenceLinker.Pair p:c.pairs)scores.put(p.key,new EvidenceLinker.Score(0,1,0,12,""));
  BoundAnswer.Draft bound=EvidenceLinker.bind(d,catalog,scores,cancel);BoundAnswer.Rendered rendered=EvidenceLinker.render(bound,cancel);check(rendered.text.contains("Subject: Athens\nIt was"));check(rendered.text.contains("Formula [5]"));check(rendered.links.size()==1);BoundAnswer.Link link=rendered.links.get(0);check(rendered.text.substring(link.start,link.end).equals("[1]"));check(link.references.get(0).source==s);check(link.references.get(0).text().equals("Athens was a centre of philosophy."));
  // Reject a bad tail even when full-claim and first sentence scores pass.
  for(EvidenceLinker.Candidate c:candidates)scores.put(c.pairs.get(2).key,new EvidenceLinker.Score(.7,.1,.2,12,""));rejects(()->EvidenceLinker.bind(d,catalog,scores,cancel));
  check(!new EvidenceLinker.Score(0,1,0,513,"").admits());check(!new EvidenceLinker.Score(0,1,0,12,"cancelled").admits());check(!new EvidenceLinker.Score(0,Double.NaN,0,12,"").admits());check(!new EvidenceLinker.Score(0,1,1,12,"").admits());check(!new EvidenceLinker.Score(.03,.96,.01,12,"").admits());check(!new EvidenceLinker.Score(.01,.94,.05,12,"").admits());check(new EvidenceLinker.Score(.02,.95,.03,512,"").admits());
  // Namespace and source corruption remain separate from classification.
  rejects(()->new BoundAnswer.Source(e,"article-1",h,BoundAnswer.sha(text),"Athens","date","rights",text+"x"));rejects(()->new BoundAnswer.Catalog(Arrays.asList(s,s),cancel));
  BoundAnswer.Source other=new BoundAnswer.Source(h,"article-1",h,BoundAnswer.sha(text),"Athens","date","rights",text);check(new BoundAnswer.Catalog(Arrays.asList(s,other),cancel).sources.size()==2);
  check(!new EvidenceLinker.Pair("a","bc").key.equals(new EvidenceLinker.Pair("ab","c").key));
  cancel.cancel();rejects(()->EvidenceLinker.bind(d,catalog,scores,cancel));rejects(()->EvidenceLinker.render(bound,cancel));rejects(()->EvidenceLinker.candidates(d.claims.get(0),catalog,cancel));
  // Retry is a separate transaction; no shared cancelled state or asset mutation.
  check(EvidenceLinker.render(bound,new BoundAnswer.Cancel()).text.equals(rendered.text));
  System.out.println("Independent binding behavioral checks: "+checks);
 }
}
