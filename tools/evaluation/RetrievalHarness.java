package org.pocketlore.app;

import java.nio.file.*;
import java.io.StringReader;
import java.util.*;

/** Host execution of the production Java retriever; no reimplementation of ranking. */
public final class RetrievalHarness {
    private static String quote(String value) {
        StringBuilder b=new StringBuilder("\"");
        for(char c:value.toCharArray()) {
            if(c=='"'||c=='\\')b.append('\\').append(c);
            else if(c<' ')b.append(String.format(Locale.ROOT,"\\u%04x",(int)c));
            else b.append(c);
        }
        return b.append('"').toString();
    }
    private static String strings(Collection<String> values) {
        List<String> out=new ArrayList<>();for(String s:values)out.add(quote(s));return "["+String.join(",",out)+"]";
    }
    public static void main(String[] args) throws Exception {
        String corpus=Files.readString(Path.of(args[0]));
        List<String> queries=Files.readAllLines(Path.of(args[1]));
        long start=System.nanoTime();ResearchEngine engine=new ResearchEngine(new StringReader(corpus));
        double indexMs=(System.nanoTime()-start)/1e6;
        List<ResearchEngine.Result> first=new ArrayList<>();List<Double> firstMs=new ArrayList<>();
        for(String query:queries){start=System.nanoTime();first.add(engine.research(query));firstMs.add((System.nanoTime()-start)/1e6);}
        // Fixed warmup and rotating sweep order prevent one case monopolizing hot-start position.
        for(int i=0;i<30;i++) for(int j=0;j<queries.size();j++) engine.research(queries.get((i+j)%queries.size()));
        List<List<Double>> samples=new ArrayList<>();for(String q:queries)samples.add(new ArrayList<>());
        for(int i=0;i<50;i++) for(int j=0;j<queries.size();j++) {
            int q=(i+j)%queries.size();start=System.nanoTime();ResearchEngine.Result r=engine.research(queries.get(q));
            samples.get(q).add((System.nanoTime()-start)/1e6);
            if(!r.answer.equals(first.get(q).answer))throw new AssertionError("Nondeterministic result: "+queries.get(q));
        }
        List<String> output=new ArrayList<>();
        for(int i=0;i<queries.size();i++) {
            ResearchEngine.Result r=first.get(i);List<String> hits=new ArrayList<>();
            for(ResearchEngine.Hit h:r.hits)hits.add("{\"id\":"+quote(h.passage.id)+",\"score\":"+h.score+"}");
            int candidatesScored=engine.size();
            try { candidatesScored=ResearchEngine.Result.class.getField("candidatesScored").getInt(r); }
            catch(NoSuchFieldException baseline) { /* Frozen baseline scans every passage. */ }
            Set<String> uncovered=EvidencePrompt.uncovered(queries.get(i),r);
            boolean blocked=r.hits.isEmpty() || !r.missingTerms.isEmpty() || !uncovered.isEmpty();
            output.add("{\"query\":"+quote(queries.get(i))+",\"hits\":["+String.join(",",hits)+"],\"missing_terms\":"+strings(r.missingTerms)+
                ",\"excerpt_uncovered\":"+strings(uncovered)+",\"lexical_generation_blocked\":"+blocked+",\"candidates_scored\":"+candidatesScored+",\"first_sweep_ms\":"+firstMs.get(i)+",\"warm_ms\":"+samples.get(i)+"}");
        }
        System.out.println("{\"environment\":\"LLMRig host JVM; not Android or physical device\",\"java\":"+quote(System.getProperty("java.version"))+
            ",\"passages\":"+engine.size()+",\"index_ms\":"+indexMs+",\"cases\":["+String.join(",",output)+"]}");
    }
}
