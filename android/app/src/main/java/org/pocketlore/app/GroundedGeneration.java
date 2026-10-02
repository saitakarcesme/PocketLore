package org.pocketlore.app;

import java.io.ByteArrayOutputStream;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.function.BooleanSupplier;

/** Native generation orchestration. Support is a separate whole-answer decision, never a citation heuristic. */
public final class GroundedGeneration {
    private GroundedGeneration() {}
    public interface Verifier {
        boolean qualified();
        /** Must assess every factual clause, citation target, condition and question obligation.
         * Called with the exact complete draft/context. A rejection cannot authorize a trimmed answer. */
        String rejection(GeneralGroundedAnswer.Context context,String completeDraft,BooleanSupplier cancelled);
    }
    public static final Verifier UNAVAILABLE=new Verifier(){
        public boolean qualified(){return false;}
        public String rejection(GeneralGroundedAnswer.Context context,String draft,BooleanSupplier stop){return "No qualified independent support verifier is installed.";}
    };
    private static AnswerEngine.Outcome outcome(AnswerEngine.Kind kind,String text,String raw,String reason,String prompt,boolean invoked,int tokens,long start){
        return new AnswerEngine.Outcome(kind,text,raw,reason,prompt,Collections.emptySet(),invoked,tokens,0,(System.nanoTime()-start)/1e6);
    }
    private static void check(BooleanSupplier stop){if(stop.getAsBoolean()||Thread.currentThread().isInterrupted())throw new java.util.concurrent.CancellationException();}
    public static AnswerEngine.Outcome answer(String question,ResearchEngine.Result evidence,AnswerEngine.Generator generator,Verifier verifier,BooleanSupplier stop){
        long start=System.nanoTime();String prompt="",draft="";boolean invoked=false;int tokens=0;
        try{
            check(stop);
            if(verifier==null||!verifier.qualified())return outcome(AnswerEngine.Kind.ABSTAINED,"General generated answers are unavailable: independent whole-answer support verification is not qualified. Use the separately labeled source-backed research brief to inspect evidence.","","Independent support verification unavailable","",false,0,start);
            if(EvidenceAvailability.scope(question)!=EvidenceAvailability.Scope.REFERENCE)return outcome(AnswerEngine.Kind.ABSTAINED,"Unknown — "+EvidenceAvailability.reason(EvidenceAvailability.scope(question)),"","Requested evidence is unavailable","",false,0,start);
            List<ResearchEngine.Passage> sources=new ArrayList<>();Map<String,ResearchEngine.Passage> ids=new HashMap<>();int units=0;
            for(ResearchEngine.Hit hit:evidence.hits){
                check(stop);ResearchEngine.Passage p=hit.passage;
                if(p.collectionProvenance.contains("Generation disabled:"))return outcome(AnswerEngine.Kind.ABSTAINED,"This source collection is not admitted for generated answers. Inspect its source-review limitations.","","Source review required","",false,0,start);
                ResearchEngine.Passage previous=ids.putIfAbsent(p.id,p);
                if(previous!=null&&(!previous.text.equals(p.text)||!previous.url.equals(p.url)||!previous.sourceDate.equals(p.sourceDate)||!previous.license.equals(p.license)||!previous.collectionProvenance.equals(p.collectionProvenance)))throw new IllegalArgumentException("Conflicting source identity");
                if(previous==null&&sources.size()<8&&p.text.length()<=12000-units){sources.add(p);units+=p.text.length();}
            }
            if(sources.isEmpty()||generator==null)return outcome(AnswerEngine.Kind.ABSTAINED,"No admitted evidence or local model is available. No generated answer was inferred.","","Missing evidence or model","",false,0,start);
            GeneralGroundedAnswer.Context context=GeneralGroundedAnswer.supplied(question,sources);
            while(true){check(stop);prompt=context.prompt();int count=generator.countTokens(prompt.getBytes(StandardCharsets.UTF_8));
                if(count<0)throw new IllegalStateException("Exact native token count unavailable");
                if(count<=EvidencePrompt.CONTEXT_TOKENS-EvidencePrompt.OUTPUT_TOKENS)break;
                context=context.withoutLast();if(context.sources.isEmpty())throw new IllegalStateException("No complete source paragraph fits the context");
            }
            ByteArrayOutputStream raw=new ByteArrayOutputStream();invoked=true;
            try{tokens=generator.run(prompt.getBytes(StandardCharsets.UTF_8),EvidencePrompt.OUTPUT_TOKENS,chunk->{check(stop);raw.write(chunk,0,chunk.length);});}
            finally{draft=new String(raw.toByteArray(),StandardCharsets.UTF_8).trim();}
            check(stop);if(tokens<0)throw new java.util.concurrent.CancellationException();
            if(tokens>=EvidencePrompt.OUTPUT_TOKENS)throw new IllegalStateException("Generation exhausted its output budget");
            String failure=GeneralGroundedAnswer.structuralFailure(draft,context);
            if(failure.isEmpty())failure=verifier.rejection(context,draft,stop);
            check(stop);
            if(failure==null||!failure.isEmpty())return outcome(AnswerEngine.Kind.ABSTAINED,"Draft withheld: "+(failure==null?"Verifier returned no decision":failure)+" Inspect the source-backed brief; no unsupported tail was removed.",draft,"Whole-answer support or completeness unverified",prompt,true,tokens,start);
            // Only labels generated by this protocol resolve; source footnotes/formulas remain untouched.
            java.util.regex.Matcher labels=java.util.regex.Pattern.compile("\\[\\[S(\\d+)\\]\\]").matcher(draft);StringBuffer linked=new StringBuffer();Set<String> cited=new LinkedHashSet<>();
            while(labels.find()){String id=context.sources.get(Integer.parseInt(labels.group(1))-1).id;cited.add(id);labels.appendReplacement(linked,java.util.regex.Matcher.quoteReplacement("["+id+"]"));}labels.appendTail(linked);
            check(stop);return new AnswerEngine.Outcome(AnswerEngine.Kind.GENERATED,linked.toString(),draft,"Independent whole-answer verifier approved support and coverage",prompt,cited,true,tokens,0,(System.nanoTime()-start)/1e6);
        }catch(java.util.concurrent.CancellationException cancelled){return outcome(AnswerEngine.Kind.CANCELLED,"Cancelled. Partial draft discarded.",draft,"Cancelled",prompt,invoked,tokens,start);}
        catch(RuntimeException failure){return outcome(AnswerEngine.Kind.ABSTAINED,"Local generation unavailable: "+failure.getMessage(),draft,"Generation or verification failed",prompt,invoked,tokens,start);}
    }
}
