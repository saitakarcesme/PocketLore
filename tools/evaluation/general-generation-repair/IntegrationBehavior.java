package org.pocketlore.app;
import java.util.*;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.atomic.AtomicBoolean;

/** Synthetic lifecycle controls, explicitly not source-entailment evaluation. */
public final class IntegrationBehavior {
 static void require(boolean ok,String message){if(!ok)throw new AssertionError(message);}
 static ResearchEngine.Passage source(String id,String body,String provenance){return new ResearchEngine.Passage(new String[]{id,"Public fixture subject","https://example.invalid/fixture","2026-10-02","Constructed test, not corpus authority",body},provenance);}
 static ResearchEngine.Result evidence(ResearchEngine.Passage... p){List<ResearchEngine.Hit> hits=new ArrayList<>();for(ResearchEngine.Passage s:p)hits.add(new ResearchEngine.Hit(s,1));return new ResearchEngine.Result(hits,Collections.emptySet(),"");}
 static class Gen implements AnswerEngine.Generator {
  int calls,count=20;boolean fail;String draft="The fixture has a recorded condition [[S1]]. GAPS: none";
  public int countTokens(byte[] prompt){return count;}
  public int run(byte[] prompt,int limit,NativeRuntime.Sink sink){calls++;if(fail)throw new IllegalStateException("Injected native failure");sink.onToken(draft.getBytes(StandardCharsets.UTF_8));return 20;}
 }
 static GroundedGeneration.Verifier verifier(String rejection){return new GroundedGeneration.Verifier(){public boolean qualified(){return true;}public String rejection(GeneralGroundedAnswer.Context context,String draft,java.util.function.BooleanSupplier stop){return rejection;}};}
 public static void main(String[] args){
  ResearchEngine.Result e=evidence(source("edition-a_doc", "The fixture has a recorded condition.","Reviewed fixture"));Gen g=new Gen();
  AnswerEngine.Outcome o=GroundedGeneration.answer("Explain the fixture condition",e,g,GroundedGeneration.UNAVAILABLE,()->false);require(g.calls==0&&o.kind==AnswerEngine.Kind.ABSTAINED,"unavailable verifier invoked native");
  o=GroundedGeneration.answer("Explain the fixture condition",e,g,verifier(""),()->true);require(g.calls==0&&o.kind==AnswerEngine.Kind.CANCELLED,"pre-cancel");
  o=GroundedGeneration.answer("Explain the fixture condition",e,g,verifier(""),()->false);require(o.kind==AnswerEngine.Kind.GENERATED&&o.citedIds.contains("edition-a_doc")&&o.text.contains("[edition-a_doc]"),"typed rendering");
  g.draft="The fixture has a recorded condition [[S1]]. An unsupported tail follows [[S1]]. GAPS: none";
  o=GroundedGeneration.answer("Explain the fixture condition",e,g,verifier("Unsupported tail"),()->false);require(o.kind==AnswerEngine.Kind.ABSTAINED&&o.rawDraft.equals(g.draft)&&!o.text.contains("An unsupported tail follows"),"whole draft rejection");
  AtomicBoolean stop=new AtomicBoolean();GroundedGeneration.Verifier delayed=new GroundedGeneration.Verifier(){public boolean qualified(){return true;}public String rejection(GeneralGroundedAnswer.Context c,String d,java.util.function.BooleanSupplier ignored){stop.set(true);return "";}};
  o=GroundedGeneration.answer("Explain the fixture condition",e,g,delayed,stop::get);require(o.kind==AnswerEngine.Kind.CANCELLED,"post-verifier cancel");
  stop.set(false);Gen during=new Gen(){public int run(byte[] p,int l,NativeRuntime.Sink sink){sink.onToken("partial".getBytes(StandardCharsets.UTF_8));stop.set(true);sink.onToken(" discarded".getBytes(StandardCharsets.UTF_8));return 2;}};
  o=GroundedGeneration.answer("Explain the fixture condition",e,during,verifier(""),stop::get);require(o.kind==AnswerEngine.Kind.CANCELLED&&o.rawDraft.equals("partial"),"mid-generation cancel");
  g=new Gen();g.count=-1;o=GroundedGeneration.answer("Explain the fixture condition",e,g,verifier(""),()->false);require(g.calls==0&&o.kind==AnswerEngine.Kind.ABSTAINED,"unknown count");
  Gen tight=new Gen(){public int countTokens(byte[] p){return new String(p,StandardCharsets.UTF_8).contains("second full paragraph")?3000:30;}};
  o=GroundedGeneration.answer("Explain the fixture condition",evidence(e.hits.get(0).passage,source("edition-b_doc","second full paragraph","Reviewed fixture")),tight,verifier(""),()->false);require(o.kind==AnswerEngine.Kind.GENERATED&&!o.prompt.contains("second full paragraph")&&o.prompt.contains(e.hits.get(0).passage.text),"complete paragraph allocation");
  g=new Gen();g.draft="Unavailable source [[S9]]. GAPS: none";o=GroundedGeneration.answer("Explain the fixture condition",e,g,verifier(""),()->false);require(o.kind==AnswerEngine.Kind.ABSTAINED,"bad citation");
  g=new Gen();o=GroundedGeneration.answer("Explain the fixture condition",evidence(source("bulk","Unreviewed", "Generation disabled: rights unreviewed")),g,verifier(""),()->false);require(g.calls==0&&o.kind==AnswerEngine.Kind.ABSTAINED,"rights bypass");
  g.fail=true;o=GroundedGeneration.answer("Explain the fixture condition",e,g,verifier(""),()->false);require(o.kind==AnswerEngine.Kind.ABSTAINED,"exception");g.fail=false;o=GroundedGeneration.answer("Explain the fixture condition",e,g,verifier(""),()->false);require(o.kind==AnswerEngine.Kind.GENERATED,"retry");
  System.out.println("PASS: 12 integration/lifecycle controls; test verifier is synthetic and establishes no entailment or Android execution");
 }
}
