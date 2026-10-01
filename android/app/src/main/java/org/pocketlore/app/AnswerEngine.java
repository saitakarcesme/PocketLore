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
    public interface Generator { int run(byte[] prompt, int limit, NativeRuntime.Sink sink); default int countTokens(byte[] prompt) { return -1; } default int runWithSources(byte[] prompt,int limit,NativeRuntime.Sink sink,int sources,boolean combined){return run(prompt,limit,sink);} }
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
    static Outcome discardAfterCancel(Outcome outcome) {
        return new Outcome(Kind.CANCELLED,"Cancelled. Partial draft discarded.",outcome.rawDraft,"Cancelled",outcome.prompt,
            Collections.emptySet(),outcome.invokedModel,outcome.tokens,outcome.firstTokenMs,outcome.totalMs);
    }
    private static final Pattern BRACKET = Pattern.compile("\\[([^\\[\\]]+)\\]");
    public static Outcome answer(String question, ResearchEngine.Result evidence, Generator generator,
                                 Consumer<String> progress, BooleanSupplier cancelled) {
        long start=System.nanoTime();
        evidence=EvidencePrompt.select(question,evidence);
        if (cancelled.getAsBoolean()) return result(Kind.CANCELLED,"Cancelled. No answer was completed.","","Cancelled","",false,0,0,start);
        if (evidence.hits.isEmpty()) {
            String why = evidence.hits.isEmpty() ? "No supporting passage in this installed pack." :
                "The installed pack does not cover these question terms: " + String.join(", ", evidence.missingTerms) + ".";
            return result(Kind.ABSTAINED,"Insufficient evidence. " + why + " No model answer was inferred.","",why,"",false,0,0,start);
        }
        if (question.length() > 350) return fallback(evidence,"Question exceeds the 350-character generation limit.","","",false,0,0,start);
        Set<String> uncovered=EvidencePrompt.uncovered(question,evidence);
        if (!uncovered.isEmpty()) return result(Kind.ABSTAINED,"Insufficient evidence in the selected excerpts for: " + String.join(", ",uncovered) + ". Inspect the full passages.","","Selected excerpts do not cover the question","",false,0,0,start);
        if (generator == null) return fallback(evidence,"No local model is loaded.","","",false,0,0,start);
        int excerptLimit=900;
        String prompt=EvidencePrompt.build(question,evidence,excerptLimit);
        try {
            int tokens=generator.countTokens(prompt.getBytes(StandardCharsets.UTF_8));
            while(tokens>0 && tokens+EvidencePrompt.OUTPUT_TOKENS>EvidencePrompt.CONTEXT_TOKENS && excerptLimit>200) {
                excerptLimit-=100;prompt=EvidencePrompt.build(question,evidence,excerptLimit);
                tokens=generator.countTokens(prompt.getBytes(StandardCharsets.UTF_8));
            }
            if(tokens>0 && tokens+EvidencePrompt.OUTPUT_TOKENS>EvidencePrompt.CONTEXT_TOKENS)
                return fallback(evidence,"Evidence and output do not fit the model context.","",prompt,false,0,0,start);
            if(!EvidencePrompt.uncovered(question,evidence,excerptLimit).isEmpty())
                return fallback(evidence,"Context reduction removed question coverage; inspect full sources.","",prompt,false,0,0,start);
        } catch(RuntimeException error) { return fallback(evidence,"Context budgeting failed: "+error.getMessage(),"",prompt,false,0,0,start); }
        ByteArrayOutputStream raw=new ByteArrayOutputStream();
        long[] first={0}; int[] callbacks={0};
        int count;
        try {
            count=generator.runWithSources(prompt.getBytes(StandardCharsets.UTF_8),EvidencePrompt.OUTPUT_TOKENS,piece -> {
                if (first[0]==0) first[0]=System.nanoTime();
                callbacks[0]++; raw.write(piece,0,piece.length);
                if (!cancelled.getAsBoolean()) progress.accept(new String(raw.toByteArray(),StandardCharsets.UTF_8));
            },evidence.hits.size(),question.trim().toLowerCase(Locale.ROOT).startsWith("compare "));
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
        String linked=EvidencePrompt.resolve(draft,evidence);
        String error=citationFailure(linked,allowed);
        if(error.isEmpty())error=completeClaimFailure(linked,evidence,excerptLimit);
        if (count>=EvidencePrompt.OUTPUT_TOKENS) error="The model reached the output limit before finishing.";
        Set<String> conflicts=EvidencePrompt.conflicts(evidence);
        if(error.isEmpty() && !conflicts.isEmpty() && (!citations(linked).containsAll(conflicts) ||
            !linked.toLowerCase(Locale.ROOT).matches("(?s).*(disagree|conflict|uncertain|unresolved|contradict).*")))
            error="Potential unresolved source disagreement: ["+String.join("] [",conflicts)+"]. The model did not disclose both sides; its draft was withheld. Inspect these sources.";
        if (error.isEmpty()) error=comparisonSupportFailure(question,linked,evidence,excerptLimit);
        if (error.isEmpty()) error=temporalScopeFailure(linked,evidence,excerptLimit);
        if (error.isEmpty()) error=claimSupportFailure(linked,evidence,excerptLimit);
        if (!error.isEmpty()) return fallback(evidence,error,draft,prompt,true,count,firstMs,start);
        return new Outcome(Kind.GENERATED,linked,draft,"Claim links and lexical support checked; factual entailment still requires source inspection. Sources may differ by conditions or date.",prompt,
            citations(linked),true,count,firstMs,(System.nanoTime()-start)/1e6);
    }
    /** Conservative surface-completeness screen, not a parser or entailment proof.
     * Source-anchored final words catch cut stems without a domain dictionary.
     * Legitimate paraphrases can be withheld; preserve the draft for inspection.
     */
    static String completeClaimFailure(String draft,ResearchEngine.Result evidence,int limit) {
        String[] claims=draft.trim().split("\\n+");
        if(claims.length>4)return "More than four claims; draft withheld.";
        Set<String> dangling=new HashSet<>(Arrays.asList("a","an","the","of","in","to","by","at","and","or","but","while","whereas","because","if","when","which","that","with","without","from","for","as","than","until","before","after","its","their","our","your","this","these","those","is","are","was","were","be","being","been","can","could","may","might","should","must","will","would","not","only","such","same","other","more","most","least","minimum","maximum","each","every","between","within"));
        for(String claim:claims) {
            String prose=BRACKET.matcher(claim).replaceAll("").trim();
            if(!prose.endsWith(".") || prose.matches(".*[,;:]\\s*\\.$"))return "Incomplete sentence ending; draft withheld.";
            if(prose.matches("(?is).*https?://.*|.*www\\..*"))return "Use source labels instead of generated URLs; draft withheld.";
            for(int cp:prose.codePoints().toArray())if(Character.isLetter(cp) && Character.UnicodeScript.of(cp)!=Character.UnicodeScript.LATIN)
                return "Non-English-script claim; draft withheld.";
            Matcher words=Pattern.compile("[A-Za-z]+(?:'[A-Za-z]+)?").matcher(prose);
            List<String> tokens=new ArrayList<>();while(words.find())tokens.add(words.group().toLowerCase(Locale.ROOT));
            if(tokens.size()<2)return "Empty or numbered claim; draft withheld.";
            // A deliberately conservative predicate vocabulary; unknown constructions
            // are withheld rather than treating a noun phrase as a complete clause.
            if(!prose.toLowerCase(Locale.ROOT).matches("(?s).*\\b(is|are|was|were|has|have|had|can|could|may|might|must|will|would|should|does|do|did|contains?|contain|comprises?|includes?|requires?|provides?|protects?|helps?|keeps?|makes?|occurs?|causes?|releases?|released|moves?|rises?|falls?|travels?|flows?|forms?|results?|allows?|enables?|passes?|ensures?|sustains?|generates?|converts?|uses?|refers?|means?|consists?|depends?|varies|differ|differs|preserves?|prevents?|explains?|states?|gives?|leads?|becomes?|builds?|grows?|remains?|reflects?|holds?|happens?|supports?|evaporates?|condenses?|distributes?|retains?|represents?|brings?|bring|carry|pack|check|prepare|avoid|use|stay|remember|know)\\b.*"))
                return "No complete clause predicate recognized; draft withheld.";
            String last=tokens.get(tokens.size()-1);
            if(dangling.contains(last))return "Dangling clause ending; draft withheld.";
            StringBuilder source=new StringBuilder();
            for(ResearchEngine.Hit hit:evidence.hits)if(citations(claim).contains(hit.passage.id))source.append(EvidencePrompt.excerpt(hit,limit)).append(' ');
            Set<String> ending=supportTerms(Collections.singleton(last));
            if(Collections.disjoint(ending,supportTerms(ResearchEngine.tokenize(source.toString()))))
                return "Claim ending lacks a complete source-supported word; draft withheld.";
        }
        return "";
    }
    static String citationFailure(String draft, Set<String> allowed) {
        if (draft.trim().isEmpty()) return "The model returned an empty answer.";
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
    /** Narrow temporal-speed screen, not general entailment: require one cited sentence. */
    static String temporalScopeFailure(String draft,ResearchEngine.Result evidence,int limit) {
        Pattern speed=Pattern.compile("(?i)\\b(slow(?:ly)?|rapid(?:ly)?|fast|quick(?:ly)?)\\b");
        Pattern boundary=Pattern.compile("(?i)\\b(until|before)\\b");
        for(String claim:draft.split("(?<=[.!?])\\s+|\\n+")) {
            String prose=BRACKET.matcher(claim).replaceAll("");
            Matcher movement=speed.matcher(prose),time=boundary.matcher(prose);
            if(!movement.find() || !time.find())continue;
            String modifier=movement.group().toLowerCase(Locale.ROOT).replaceAll("ly$","");
            String relation=time.group().toLowerCase(Locale.ROOT);
            Set<String> event=supportTerms(ResearchEngine.tokenize(prose.substring(time.end())));
            boolean supported=false;
            for(ResearchEngine.Hit hit:evidence.hits)if(citations(claim).contains(hit.passage.id)) {
                for(String sentence:EvidencePrompt.excerpt(hit,limit).split("(?<=[.!?])\\s+|\\n+")) {
                    Matcher sourceSpeed=speed.matcher(sentence),sourceTime=boundary.matcher(sentence);
                    if(!sourceSpeed.find() || !sourceTime.find())continue;
                    if(!sourceSpeed.group().toLowerCase(Locale.ROOT).replaceAll("ly$","").equals(modifier)
                        || !sourceTime.group().equalsIgnoreCase(relation))continue;
                    Set<String> sourceEvent=supportTerms(ResearchEngine.tokenize(sentence.substring(sourceTime.end())));
                    if(!event.isEmpty() && sourceEvent.containsAll(event))supported=true;
                }
            }
            if(!supported)return "A speed claim crosses a temporal boundary not established by a cited sentence; draft withheld.";
        }
        return "";
    }
    /** Conservative lexical/number screen, explicitly not semantic entailment. */
    static String claimSupportFailure(String draft,ResearchEngine.Result evidence,int limit) {
        Set<String> glue=new HashSet<>(Arrays.asList("this","that","these","those","while","whereas","because","also","can","may","into","each","their","them","its","being","both","source","sources","one","other","disagreement","unresolved","conflict","uncertain","reported","reports"));
        for(String claim:draft.split("(?<=[.!?])\\s+|\\n+")) {
            Set<String> ids=citations(claim);if(ids.isEmpty())continue;
            StringBuilder source=new StringBuilder();
            for(ResearchEngine.Hit hit:evidence.hits)if(ids.contains(hit.passage.id))source.append(EvidencePrompt.excerpt(hit,limit)).append(' ');
            Set<String> words=new HashSet<>(ResearchEngine.tokenize(BRACKET.matcher(claim).replaceAll("")));words.removeAll(glue);
            Set<String> original=supportTerms(words);words=new HashSet<>(original);words.retainAll(supportTerms(ResearchEngine.tokenize(source.toString())));
            if(original.size()>0 && words.size()/(double)original.size()<0.65)return "A claim has weak lexical support in its cited excerpts; draft withheld.";
            Matcher numbers=Pattern.compile("\\b[0-9]+(?:[.,][0-9]+)*\\b").matcher(BRACKET.matcher(claim).replaceAll(""));
            Set<String> supportedNumbers=new HashSet<>();Matcher sourceNumbers=Pattern.compile("\\b[0-9]+(?:[.,][0-9]+)*\\b").matcher(source);
            while(sourceNumbers.find())supportedNumbers.add(sourceNumbers.group().replace(",",""));
            while(numbers.find())if(!supportedNumbers.contains(numbers.group().replace(",","")))return "A claim contains a number absent from its cited excerpts; draft withheld.";
        }
        return "";
    }
    private static Set<String> supportTerms(Collection<String> words) {
        Set<String> result=new HashSet<>();
        for(String original:words) {
            String word=original;
            if(word.length()>6 && word.endsWith("ation"))word=word.substring(0,word.length()-5)+"ate";
            else if(word.length()>6 && word.endsWith("ment"))word=word.substring(0,word.length()-4);
            if(word.length()>4 && word.endsWith("ies"))word=word.substring(0,word.length()-3)+"y";
            else if(word.length()>3 && word.endsWith("s") && !word.endsWith("ss") && !word.endsWith("is") && !word.endsWith("us"))word=word.substring(0,word.length()-1);
            if(word.length()>5 && word.endsWith("ing"))word=word.substring(0,word.length()-3);
            else if(word.length()>4 && word.endsWith("ed"))word=word.substring(0,word.length()-2);
            if(word.length()>3 && word.endsWith("e") && !word.endsWith("ee"))word=word.substring(0,word.length()-1);
            result.add(word);
        }
        return result;
    }
    /** Narrow cross-subject leakage screen; conservative, not semantic entailment. */
    static String comparisonSupportFailure(String question,String draft,ResearchEngine.Result evidence,int limit) {
        Matcher comparison=Pattern.compile("(?i)^compare\\s+(.+?)\\s+(?:and|with|versus)\\s+(.+?)[.?!]?$").matcher(question.trim());
        if(!comparison.matches() || evidence.hits.size()!=2)return "";
        List<Set<String>> subjects=Arrays.asList(new HashSet<>(ResearchEngine.tokenize(comparison.group(1))),new HashSet<>(ResearchEngine.tokenize(comparison.group(2))));
        List<Set<String>> sources=Arrays.asList(new HashSet<>(ResearchEngine.tokenize(EvidencePrompt.excerpt(evidence.hits.get(0),limit))),new HashSet<>(ResearchEngine.tokenize(EvidencePrompt.excerpt(evidence.hits.get(1),limit))));
        Set<String> common=new HashSet<>(subjects.get(0));common.retainAll(subjects.get(1));
        for(Set<String> subject:subjects)subject.removeAll(common);
        for(String clause:BRACKET.matcher(draft).replaceAll("").split("(?i)\\b(?:while|whereas)\\b|\\n+")) {
            Set<String> words=new HashSet<>(ResearchEngine.tokenize(clause));
            boolean first=!Collections.disjoint(words,subjects.get(0)),second=!Collections.disjoint(words,subjects.get(1));
            if(first==second)continue;
            int own=first?0:1;
            Set<String> borrowed=new HashSet<>(words);borrowed.retainAll(sources.get(1-own));borrowed.removeAll(sources.get(own));
            borrowed.removeAll(subjects.get(0));borrowed.removeAll(subjects.get(1));
            if(!borrowed.isEmpty())return "A comparison clause borrows terms only supported for the other subject; draft withheld.";
        }
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
