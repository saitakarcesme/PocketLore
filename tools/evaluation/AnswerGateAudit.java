package org.pocketlore.app;
import java.nio.file.*;
import java.io.StringReader;
/** Current production routing up to model availability; deliberately no mock generation. */
public final class AnswerGateAudit {
    public static void main(String[] args)throws Exception {
        ResearchEngine engine=new ResearchEngine(new StringReader(Files.readString(Path.of(args[0]))));
        for(String line:Files.readAllLines(Path.of(args[1]))){
            String[] row=line.split("\t",2);long start=System.nanoTime();
            AnswerEngine.Outcome answer=AnswerEngine.answer(row[1],engine.research(row[1]),null,t->{},()->false);
            if(answer.invokedModel || !answer.rawDraft.isEmpty())throw new AssertionError("Unexpected generation");
            System.out.println(row[0]+"\t"+answer.kind+"\t"+answer.reason+"\t"+(System.nanoTime()-start)/1e6);
        }
    }
}
