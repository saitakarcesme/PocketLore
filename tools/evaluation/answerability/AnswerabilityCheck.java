package org.pocketlore.app;
import java.nio.file.*;
/** Tests production coverage on real pack excerpts, without generated answer fixtures. */
public final class AnswerabilityCheck {
    public static void main(String[] args)throws Exception {
        ResearchEngine engine=new ResearchEngine(Files.newBufferedReader(Path.of(args[0])));
        int count=0;
        for(String line:Files.readAllLines(Path.of(args[1]))){
            String[] row=line.split("\t",2);boolean eligible=row[0].equals("eligible");
            AnswerEngine.Outcome a=AnswerEngine.answer(row[1],engine.research(row[1]),null,t->{},()->false);
            if(eligible!=a.reason.equals("No local model is loaded."))throw new AssertionError(row[1]+": "+a.reason);
            if(a.invokedModel||!a.rawDraft.isEmpty())throw new AssertionError("Unexpected model output");count++;
        }
        System.out.println("PASS: "+count+" current coverage controls; no model output substituted");
    }
}
