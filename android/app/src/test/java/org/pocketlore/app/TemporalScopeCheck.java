package org.pocketlore.app;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;

/** Replays the rejected real-model draft; separate from new JNI generation evidence. */
public final class TemporalScopeCheck {
    static void require(boolean value,String message){if(!value)throw new AssertionError(message);}
    public static void main(String[] args)throws Exception {
        Path root=Paths.get(args[0]);
        ResearchEngine engine=new ResearchEngine(Files.newBufferedReader(root.resolve("sources.tsv")));
        String question=Files.readString(root.resolve("question.txt"));
        String draft=Files.readString(root.resolve("draft.txt"));
        ResearchEngine.Result evidence=engine.research(question);
        AnswerEngine.Generator replay=(p,n,s)->{s.onToken(draft.getBytes(StandardCharsets.UTF_8));return 79;};
        AnswerEngine.Outcome rejected=AnswerEngine.answer(question,evidence,replay,t->{},()->false);
        require(rejected.kind==AnswerEngine.Kind.FALLBACK,"Rejected checkpoint's pre-saturation speed claim was published");
        require(rejected.rawDraft.equals(draft),"Rejected draft was not preserved verbatim");
        require(!rejected.text.contains("moves slowly until"),"Unsupported claim leaked into visible fallback");
        require(rejected.citedIds.isEmpty(),"Withheld draft retained generated claim links");
        String corrected=draft.replace("and moves slowly until","and moves until");
        AnswerEngine.Generator supported=(p,n,s)->{s.onToken(corrected.getBytes(StandardCharsets.UTF_8));return 78;};
        require(AnswerEngine.answer(question,evidence,supported,t->{},()->false).kind==AnswerEngine.Kind.GENERATED,"Removing unsupported speed did not restore the supported path");
        ResearchEngine.Result scoped=new ResearchEngine(new StringReader("scope-test\tFictional scope control\thttps://example.invalid/control\t2026-10-01\tFictional test fixture\tThe test fluid moves slowly until it reaches the sensor.\n")).research("test fluid sensor");
        require(AnswerEngine.temporalScopeFailure("The test fluid moves slowly until it reaches the sensor [scope-test].",scoped,900).isEmpty(),"Explicit temporal support rejected");
        require(!AnswerEngine.temporalScopeFailure("The test fluid moves rapidly until it reaches the sensor [scope-test].",scoped,900).isEmpty(),"Different speed accepted");
        require(!AnswerEngine.temporalScopeFailure("The test fluid moves slowly before it reaches the sensor [scope-test].",scoped,900).isEmpty(),"Different boundary accepted");
        require(!AnswerEngine.temporalScopeFailure("The test fluid moves slowly until it reaches the ocean [scope-test].",scoped,900).isEmpty(),"Different endpoint accepted");
        require(AnswerEngine.temporalScopeFailure("Water in the groundwater system moves slowly [groundwater-abbc88d938b327f2].",evidence,900).isEmpty(),"Unqualified source speed rejected");
        System.out.println("PASS: exact rejected draft withheld and preserved; corrected comparison remains generatable");
    }
}
