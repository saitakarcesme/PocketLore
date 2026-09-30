package org.pocketlore.app;

import java.nio.file.*;
import java.util.*;
import java.util.concurrent.*;

/** Behavioral contracts over real source text, not a second BM25 implementation. */
public final class RetrievalIndexCheck {
    private static void check(boolean ok,String message){if(!ok)throw new AssertionError(message);}
    public static void main(String[] args) throws Exception {
        ResearchEngine engine=new ResearchEngine(Files.newBufferedReader(Path.of(args[0])));
        ResearchEngine.Result absent=engine.research("quasar entanglement");
        check(absent.hits.isEmpty() && absent.candidatesScored==0,"Absent terms caused passage scanning or hits");
        ResearchEngine.Result exact=engine.research("condensation");
        check(exact.candidatesScored>0 && exact.candidatesScored<engine.size(),"Selective query did not use postings");
        check(exact.answer.equals(engine.research("CONDENSATION condensation").answer),"Case/repetition changed ranking");
        ResearchEngine.Result expanded=engine.research("dark");
        check(!expanded.hits.isEmpty() && expanded.missingTerms.contains("dark"),"Ranking expansion falsely established exact evidence coverage");
        check(expanded.hits.stream().anyMatch(h->h.passage.text.contains("Lighting is important")),"Real illumination source not retrieved");
        String query="Compare aquifer recharge with surface runoff.";String answer=engine.research(query).answer;
        ExecutorService pool=Executors.newFixedThreadPool(4);
        try {
            List<Future<String>> tasks=new ArrayList<>();
            for(int i=0;i<40;i++)tasks.add(pool.submit(()->engine.research(query).answer));
            for(Future<String> task:tasks)check(answer.equals(task.get()),"Concurrent immutable index changed ranking");
        } finally {pool.shutdownNow();}
        try {exact.hits.clear();throw new AssertionError("Mutable hits");}catch(UnsupportedOperationException expected){}
        try {expanded.missingTerms.clear();throw new AssertionError("Mutable coverage");}catch(UnsupportedOperationException expected){}
        System.out.println("PASS: unknown/selective postings, case/repetition, expansion coverage isolation, real source lookup, concurrent determinism and immutable results");
    }
}
