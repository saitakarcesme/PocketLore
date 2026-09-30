package org.pocketlore.app;

import java.io.ByteArrayOutputStream;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.function.BooleanSupplier;
import java.util.function.Consumer;
import java.util.regex.*;

/** Deterministic routing and citation integrity checks, not factual entailment verification. */
public final class AnswerEngine {
    public enum Kind { GENERATED, FALLBACK, ABSTAINED, CANCELLED }
    public interface Generator { int run(byte[] prompt, int limit, NativeRuntime.Sink sink); }
    public static final class Outcome {
        public final Kind kind;
        public final String text, rawDraft, reason, prompt;
        public final Set<String> citedIds;
        public final boolean invokedModel;
        public final int tokens;
        public final double firstTokenMs, totalMs;
        Outcome(Kind kind, String text, String raw, String reason, String prompt, Set<String> ids,
                boolean invoked, int tokens, double first, double total) {
            this.kind=kind; this.text=text; rawDraft=raw; this.reason=reason; this.prompt=prompt;
            citedIds=Collections.unmodifiableSet(new LinkedHashSet<>(ids)); invokedModel=invoked;
            this.tokens=tokens; firstTokenMs=first; totalMs=total;
        }
    }
    private static final Pattern BRACKET = Pattern.compile("\\[([^\\[\\]]+)\\]");
    public static Outcome answer(String question, ResearchEngine.Result evidence, Generator generator,
                                 Consumer<String> progress, BooleanSupplier cancelled) {
        long start=System.nanoTime();
        if (cancelled.getAsBoolean()) return result(Kind.CANCELLED,"Cancelled. No answer was completed.","","Cancelled","",false,0,0,start);
        if (evidence.hits.isEmpty() || !evidence.missingTerms.isEmpty()) {
            String why = evidence.hits.isEmpty() ? "No supporting passage in this installed pack." :
                "The installed pack does not cover these question terms: " + String.join(", ", evidence.missingTerms) + ".";
            return result(Kind.ABSTAINED,"Insufficient evidence. " + why + " No model answer was inferred.","",why,"",false,0,0,start);
        }
        if (question.length() > 350) return fallback(evidence,"Question exceeds the 350-character generation limit.","","",false,0,0,start);
        Set<String> uncovered=EvidencePrompt.uncovered(question,evidence);
        if (!uncovered.isEmpty()) return result(Kind.ABSTAINED,"Insufficient evidence in the selected excerpts for: " + String.join(", ",uncovered) + ". Inspect the full passages.","","Selected excerpts do not cover the question","",false,0,0,start);
        if (generator == null) return fallback(evidence,"No local model is loaded.","","",false,0,0,start);
        String prompt=EvidencePrompt.build(question,evidence);
        ByteArrayOutputStream raw=new ByteArrayOutputStream();
        long[] first={0}; int[] callbacks={0};
        int count;
        try {
            count=generator.run(prompt.getBytes(StandardCharsets.UTF_8),128,piece -> {
                if (first[0]==0) first[0]=System.nanoTime();
                callbacks[0]++; raw.write(piece,0,piece.length);
                if (!cancelled.getAsBoolean()) progress.accept(new String(raw.toByteArray(),StandardCharsets.UTF_8));
            });
        } catch (RuntimeException error) {
            String draft=new String(raw.toByteArray(),StandardCharsets.UTF_8);
            if (cancelled.getAsBoolean()) return result(Kind.CANCELLED,"Cancelled. Partial draft discarded.",draft,"Cancelled",prompt,true,callbacks[0],elapsedFirst(first[0],start),start);
            return fallback(evidence,"Local generation failed: " + error.getMessage(),draft,prompt,true,callbacks[0],elapsedFirst(first[0],start),start);
        }
        String draft=new String(raw.toByteArray(),StandardCharsets.UTF_8).trim();
        double firstMs=elapsedFirst(first[0],start);
        if (count<0 || cancelled.getAsBoolean()) return result(Kind.CANCELLED,"Cancelled. Partial draft discarded.",draft,"Cancelled",prompt,true,callbacks[0],firstMs,start);
        if (draft.toLowerCase(Locale.ROOT).startsWith("insufficient evidence"))
            return result(Kind.ABSTAINED,"Insufficient evidence. The local model declined to answer; inspect the passages.",draft,"Model abstention",prompt,true,count,firstMs,start);
        Set<String> allowed=EvidencePrompt.ids(evidence);
        String error=citationFailure(draft,allowed);
        if (count>=128) error="The model reached the output limit before finishing.";
        if (!error.isEmpty()) return fallback(evidence,error,draft,prompt,true,count,firstMs,start);
        return new Outcome(Kind.GENERATED,draft,draft,"Citation IDs checked; factual support still requires source inspection.",prompt,
            citations(draft),true,count,firstMs,(System.nanoTime()-start)/1e6);
    }
    static String citationFailure(String draft, Set<String> allowed) {
        if (draft.isBlank()) return "The model returned an empty answer.";
        Set<String> citations=citations(draft);
        if (citations.isEmpty()) return "The model omitted source citations.";
        if (!allowed.containsAll(citations)) return "The model cited a source outside the supplied evidence.";
        for (String sentence:draft.split("(?<=[.!?])\\s+|\\n+")) {
            String prose=BRACKET.matcher(sentence).replaceAll("").trim();
            if (prose.isEmpty()) continue;
            if (citations(sentence).isEmpty()) return "A generated sentence is missing a source citation.";
            if (ResearchEngine.tokenize(prose).size()<2) return "The generated answer contains too little explanatory text.";
        }
        if (ResearchEngine.tokenize(BRACKET.matcher(draft).replaceAll("")).size()<2)
            return "The model returned citations without an answer.";
        return "";
    }
    static Set<String> citations(String text) {
        Set<String> ids=new LinkedHashSet<>(); Matcher matcher=BRACKET.matcher(text);
        while (matcher.find()) ids.add(matcher.group(1));
        return ids;
    }
    private static double elapsedFirst(long first,long start) { return first==0?0:(first-start)/1e6; }
    private static Outcome fallback(ResearchEngine.Result evidence,String reason,String raw,String prompt,boolean invoked,int tokens,double first,long start) {
        return result(Kind.FALLBACK,"Extractive fallback — not a generated answer.\n" + reason + "\n\n" + evidence.answer,raw,reason,prompt,invoked,tokens,first,start);
    }
    private static Outcome result(Kind kind,String text,String raw,String reason,String prompt,boolean invoked,int tokens,double first,long start) {
        return new Outcome(kind,text,raw,reason,prompt,Collections.emptySet(),invoked,tokens,first,(System.nanoTime()-start)/1e6);
    }
    private AnswerEngine() {}
}
