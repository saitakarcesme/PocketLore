package org.pocketlore.app;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;

public final class AnswerEngineCheck {
    static void check(boolean ok,String message) { if (!ok) throw new AssertionError(message); }
    public static void main(String[] args) throws Exception {
        ResearchEngine engine=new ResearchEngine(new InputStreamReader(new FileInputStream(args[0]),StandardCharsets.UTF_8));
        ResearchEngine.Result evidence=engine.research("Compare evaporation and condensation");
        AnswerEngine.Generator forbidden=(p,n,s)->{throw new AssertionError("Model must not run");};
        for (String q:List.of("quasar supernova","Does evaporation cure diabetes?")) {
            var outcome=AnswerEngine.answer(q,engine.research(q),forbidden,t->{},()->false);
            check(outcome.kind==AnswerEngine.Kind.ABSTAINED && !outcome.invokedModel,"Unsupported query inferred");
        }
        var noModel=AnswerEngine.answer("Compare evaporation and condensation",evidence,null,t->{},()->false);
        check(noModel.kind==AnswerEngine.Kind.FALLBACK && !noModel.invokedModel,"No-model route incorrect");
        check(noModel.text.contains("not a generated answer"),"Fallback not labeled");
        for (String draft:List.of("Water evaporates.","Water evaporates [invented].","Water evaporates [water-01]. Ice is hot.","[water-01]")) {
            var bad=AnswerEngine.answer("Compare evaporation and condensation",evidence,(p,n,s)->{s.onToken(draft.getBytes(StandardCharsets.UTF_8));return 12;},t->{},()->false);
            check(bad.kind==AnswerEngine.Kind.FALLBACK && bad.invokedModel,"Invalid citations published: "+draft);
            check(bad.rawDraft.equals(draft),"Rejected raw draft lost");
        }
        ResearchEngine clipped=new ResearchEngine(new StringReader("clip-01\tTitle\thttps://example.invalid\t2026-10-01\tTest fixture\t"+"water ".repeat(80)+"groundwater.\n"));
        var uncovered=AnswerEngine.answer("What is groundwater?",clipped.research("What is groundwater?"),forbidden,t->{},()->false);
        check(uncovered.kind==AnswerEngine.Kind.ABSTAINED && !uncovered.invokedModel,"Evidence outside supplied excerpt used");
        String cited="Evaporation changes liquid water to vapor [water-01]. Condensation changes water vapor to liquid [water-02].";
        var good=AnswerEngine.answer("Compare evaporation and condensation",evidence,(p,n,s)->{s.onToken(cited.getBytes(StandardCharsets.UTF_8));return 24;},t->{},()->false);
        check(good.kind==AnswerEngine.Kind.GENERATED && good.citedIds.equals(Set.of("water-01","water-02")),"Valid citation route failed");
        var lateCancel=AnswerEngine.discardAfterCancel(good);
        check(lateCancel.kind==AnswerEngine.Kind.CANCELLED && lateCancel.citedIds.isEmpty() && !lateCancel.text.contains(cited),"Late UI cancel published completed draft");
        var empty=AnswerEngine.answer("Compare evaporation and condensation",evidence,(p,n,s)->0,t->{},()->false);
        check(empty.kind==AnswerEngine.Kind.FALLBACK && empty.tokens==0 && empty.rawDraft.isEmpty(),"Empty native response published as answer");
        var error=AnswerEngine.answer("Compare evaporation and condensation",evidence,(p,n,s)->{throw new IllegalStateException("decode failure");},t->{},()->false);
        check(error.kind==AnswerEngine.Kind.FALLBACK && error.reason.contains("decode failure"),"Runtime failure route failed");
        var cancelled=AnswerEngine.answer("Compare evaporation and condensation",evidence,forbidden,t->{},()->true);
        check(cancelled.kind==AnswerEngine.Kind.CANCELLED && !cancelled.invokedModel,"Precancel route failed");
        var stopped=AnswerEngine.answer("Compare evaporation and condensation",evidence,(p,n,s)->{s.onToken(cited.getBytes(StandardCharsets.UTF_8));return -1;},t->{},()->false);
        check(stopped.kind==AnswerEngine.Kind.CANCELLED && !stopped.text.contains(cited),"Partial cancelled answer published");
        System.out.println("PASS: 14 answer routing, citation integrity, fallback and cancellation checks (synthetic generator; not model quality)");
    }
}
