package org.pocketlore.app;
import java.util.*;

/** Experimental composition: classifier approval never overrides semantic failure.
 * NLI-selected and final proof references are distinct audit artifacts.
 * No verifier/model is deployed by this shared controller.
 */
final class GuardedEvidenceLinker {
 static final class Result {
  final BoundAnswer.Draft scored;
  final FactFrames.Proof proof;
  Result(BoundAnswer.Draft scored,FactFrames.Proof proof){this.scored=scored;this.proof=proof;}
 }
 static Result bind(BoundAnswer.Draft draft,BoundAnswer.Catalog catalog,
                    Map<String,EvidenceLinker.Score> scores,BoundAnswer.Cancel cancel){
  cancel.check();
  BoundAnswer.Draft scored=EvidenceLinker.bind(draft,catalog,scores,cancel);
  // This may replace incorrect classifier-selected neighbors with exact proven spans.
  // It cannot make a classifier rejection eligible or retain an unproved claim tail.
  FactFrames.Proof proof=FactFrames.bind(scored,catalog,cancel);
  cancel.check();return new Result(scored,proof);
 }
 private GuardedEvidenceLinker(){}
}
