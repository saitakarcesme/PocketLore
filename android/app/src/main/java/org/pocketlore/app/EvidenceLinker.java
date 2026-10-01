package org.pocketlore.app;

import java.text.BreakIterator;
import java.util.*;

/** Experimental independent-scoring controller. Scores are fallible, not entailment proof.
 * A host adapter supplies scores; no verifier is deployed in the Android answer flow.
 */
final class EvidenceLinker {
 static final double MIN_ENTAILMENT=0.95, MAX_CONTRADICTION=0.02;
 static final class Pair {
  final String premise,hypothesis,key;
  Pair(String premise,String hypothesis){this.premise=premise;this.hypothesis=hypothesis;key=BoundAnswer.sha(premise+"\u0000"+hypothesis);}
 }
 static final class Score {
  final double contradiction,entailment,neutral;final int tokens;final String failure;
  Score(double c,double e,double n,int tokens,String failure){contradiction=c;entailment=e;neutral=n;this.tokens=tokens;this.failure=failure;}
  boolean admits(){return failure.isEmpty()&&tokens>0&&tokens<=512&&Double.isFinite(contradiction)&&Double.isFinite(entailment)&&Double.isFinite(neutral)&&contradiction>=0&&entailment>=0&&neutral>=0&&contradiction<=1&&entailment<=1&&neutral<=1&&Math.abs(contradiction+entailment+neutral-1)<0.00001&&entailment>=MIN_ENTAILMENT&&contradiction<=MAX_CONTRADICTION;}
 }
 static final class Candidate {
  final List<BoundAnswer.Span> refs;final List<Pair> pairs;
  Candidate(BoundAnswer.Claim claim,List<BoundAnswer.Span> refs,BoundAnswer.Cancel cancel){
   this.refs=Collections.unmodifiableList(new ArrayList<>(refs));StringBuilder premise=new StringBuilder();
   for(BoundAnswer.Span s:refs){cancel.check();premise.append(s.source.title).append(": ").append(s.text()).append('\n');}
   LinkedHashSet<String> hypotheses=new LinkedHashSet<>();hypotheses.add(claim.subject+": "+claim.text);
   BreakIterator it=BreakIterator.getSentenceInstance(Locale.US);it.setText(claim.text);int a=it.first();
   for(int z=it.next();z!=BreakIterator.DONE;a=z,z=it.next()){String sentence=claim.text.substring(a,z).trim();if(!sentence.isEmpty())hypotheses.add(claim.subject+": "+sentence);}
   List<Pair> ps=new ArrayList<>();for(String h:hypotheses)ps.add(new Pair(premise.toString(),h));pairs=Collections.unmodifiableList(ps);
  }
  boolean admits(Map<String,Score> scores,BoundAnswer.Cancel cancel){for(Pair p:pairs){cancel.check();Score s=scores.get(p.key);if(s==null||!s.admits())return false;}return true;}
 }
 static List<Candidate> candidates(BoundAnswer.Claim claim,BoundAnswer.Catalog catalog,BoundAnswer.Cancel cancel){
  List<Candidate> result=new ArrayList<>();result.add(new Candidate(claim,claim.references,cancel));
  for(BoundAnswer.Source source:catalog.sources){cancel.check();List<BoundAnswer.Span> refs=new ArrayList<>();for(BoundAnswer.Span span:catalog.spans.values())if(span.source==source)refs.add(span);
   if(!refs.isEmpty()&&!refs.equals(claim.references))result.add(new Candidate(claim,refs,cancel));}
  return Collections.unmodifiableList(result);
 }
 static BoundAnswer.Draft bind(BoundAnswer.Draft draft,BoundAnswer.Catalog catalog,Map<String,Score> scores,BoundAnswer.Cancel cancel){
  List<BoundAnswer.Claim> claims=new ArrayList<>();for(BoundAnswer.Claim c:draft.claims){cancel.check();Candidate chosen=null;for(Candidate candidate:candidates(c,catalog,cancel))if(candidate.admits(scores,cancel)){chosen=candidate;break;}
   if(chosen==null)throw new IllegalArgumentException("Independent evidence score withheld a complete claim");
   claims.add(new BoundAnswer.Claim(c.obligation,c.subject,c.qualifier,c.text,chosen.refs));}
  return new BoundAnswer.Draft(draft.question,claims,draft.count);
 }
 static BoundAnswer.Rendered render(BoundAnswer.Draft draft,BoundAnswer.Cancel cancel){
  StringBuilder b=new StringBuilder();List<BoundAnswer.Link> links=new ArrayList<>();List<String> obligations=BoundAnswer.obligations(draft.question);
  for(int i=0;i<draft.claims.size();i++){cancel.check();BoundAnswer.Claim c=draft.claims.get(i);
   // Visible context, not a silent substitution of metadata for generated prose.
   b.append("Question: ").append(obligations.get(c.obligation-1)).append('\n').append("Subject: ").append(c.subject).append('\n').append(c.text).append(' ');
   int start=b.length();b.append('[').append(i+1).append(']');links.add(new BoundAnswer.Link(start,b.length(),c.references));b.append("\n\n");}
  cancel.check();return new BoundAnswer.Rendered(b.toString().trim(),links);
 }
 private EvidenceLinker(){}
}
