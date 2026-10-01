package org.pocketlore.app;

import java.io.StringReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;

/** Deliberately fictional contradiction fixtures test controls, not factual corpus quality. */
public final class SynthesisCheck {
    static void require(boolean value,String message){if(!value)throw new AssertionError(message);}
    static String row(String id,String text){return id+"\tTest sensor\thttps://example.invalid/test\t2026-01-01\tFictional test fixture\t"+text+"\n";}
    public static void main(String[] args)throws Exception {
        ResearchEngine engine=new ResearchEngine(new StringReader(row("test-a","The test lamp is active.")+row("test-b","The test lamp is not active.")));
        ResearchEngine.Result evidence=engine.research("test lamp active");
        require(EvidencePrompt.select("Compare test lamp and active",evidence).hits.size()==2,"Context selection discarded an opposing statement");
        require(EvidencePrompt.conflicts(evidence).size()==2,"Opposite statements not disclosed");
        require(EvidencePrompt.build("test lamp active",evidence).contains("unresolved disagreement"),"Conflict absent from prompt");
        AnswerEngine.Generator silent=(p,n,s)->{s.onToken("The test lamp is active [S1].".getBytes(StandardCharsets.UTF_8));return 12;};
        require(AnswerEngine.answer("test lamp active",evidence,silent,t->{},()->false).kind==AnswerEngine.Kind.FALLBACK,"Undisclosed contradiction published");
        String conflict="The test lamp is active in one source but not active in the other; this disagreement is unresolved [S1] [S2].";
        AnswerEngine.Generator disclosed=(p,n,s)->{s.onToken(conflict.getBytes(StandardCharsets.UTF_8));return 30;};
        AnswerEngine.Outcome qualified=AnswerEngine.answer("test lamp active",evidence,disclosed,t->{},()->false);
        require(qualified.kind==AnswerEngine.Kind.GENERATED && qualified.citedIds.size()==2,"Linked conflict disclosure rejected");
        require(qualified.rawDraft.equals(conflict) && !qualified.text.contains("[S1]"),"Raw draft or alias mapping lost");
        require(!AnswerEngine.claimSupportFailure("The test lamp is active for 731 hours [test-a].",evidence,900).isEmpty(),"Unsupported number accepted");
        AnswerEngine.Generator overBudget=new AnswerEngine.Generator(){public int countTokens(byte[] p){return 3000;}public int run(byte[] p,int n,NativeRuntime.Sink s){throw new AssertionError("Over-budget generation invoked");}};
        require(AnswerEngine.answer("test lamp active",evidence,overBudget,t->{},()->false).kind==AnswerEngine.Kind.FALLBACK,"Budget overflow not withheld");
        AnswerEngine.Generator forbidden=(p,n,s)->{throw new AssertionError("Cancelled generation invoked");};
        require(AnswerEngine.answer("test lamp active",evidence,forbidden,t->{},()->true).kind==AnswerEngine.Kind.CANCELLED,"Cancellation failed");
        ResearchEngine.Result colors=new ResearchEngine(new StringReader(row("color-a","Alpha lamp emits red light.")+row("color-b","Beta lamp emits blue light."))).research("Compare alpha lamp and beta lamp");
        colors=EvidencePrompt.select("Compare alpha lamp and beta lamp",colors);
        require(!AnswerEngine.comparisonSupportFailure("Compare alpha lamp and beta lamp","Alpha lamp emits blue light [color-a] [color-b].",colors,900).isEmpty(),"Cross-subject property transfer accepted");
        require(AnswerEngine.comparisonSupportFailure("Compare alpha lamp and beta lamp","Alpha lamp emits red light [color-a].\nBeta lamp emits blue light [color-b].",colors,900).isEmpty(),"Supported comparison withheld");
        System.out.println("PASS: fictional conflict controls, both-source links, raw preservation, unsupported numbers, token overflow and cancellation");
    }
}
