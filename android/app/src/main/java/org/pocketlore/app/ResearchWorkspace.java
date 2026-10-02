package org.pocketlore.app;

import java.util.*;
import java.util.function.BooleanSupplier;

/** General, extractive research sections; no relation templates or generated factual prose. */
public final class ResearchWorkspace {
    public static final int MAX_PARTS=6, MAX_QUOTES_PER_PART=2, MAX_QUOTE_UNITS=12288;
    public static final class Section {
        public final String question;
        public final EvidenceAvailability.Scope availability;
        public final List<ResearchBrief.Quote> quotes;
        public final Set<String> missingTerms;
        Section(String question,EvidenceAvailability.Scope scope,List<ResearchBrief.Quote> quotes,Set<String> missing){
            this.question=question;availability=scope;this.quotes=Collections.unmodifiableList(quotes);
            missingTerms=Collections.unmodifiableSet(new TreeSet<>(missing));
        }
    }
    public static final class Result {
        public final ResearchBrief.Brief brief;
        public final List<Section> sections;
        Result(ResearchBrief.Brief brief,List<Section> sections){this.brief=brief;this.sections=Collections.unmodifiableList(sections);}
    }
    public static List<String> plan(String question){
        if(question==null||question.trim().isEmpty()||question.length()>2048)throw new IllegalArgumentException("Enter 1–2048 characters of research questions");
        List<String> parts=new ArrayList<>();
        for(String part:question.trim().split("(?:[\\r\\n;]+|(?<=\\?)\\s+)"))if(!part.trim().isEmpty())parts.add(part.trim());
        if(parts.size()>MAX_PARTS)throw new IllegalArgumentException("Use at most six subquestions, separated by new lines or semicolons");
        return parts;
    }
    private static void check(BooleanSupplier stop){if(stop.getAsBoolean()||Thread.currentThread().isInterrupted())throw new java.util.concurrent.CancellationException("Research cancelled; no partial brief saved");}
    public static Result create(String question,ResearchEngine engine,BooleanSupplier stop){
        List<String> parts=plan(question);List<Section> sections=new ArrayList<>();List<ResearchBrief.Quote> all=new ArrayList<>();
        StringBuilder text=new StringBuilder("Source-backed research brief · exact quotations\nNot a generated answer. Sections follow your subquestions, not inferred factual relationships.\nTap a quotation for the exact passage, source revision, attribution and license.\n\n");
        int units=0,omitted=0;
        for(String part:parts){
            check(stop);EvidenceAvailability.Scope scope=EvidenceAvailability.scope(part);
            ResearchEngine.Result evidence=scope==EvidenceAvailability.Scope.REFERENCE?engine.research(part):new ResearchEngine.Result(Collections.emptyList(),Collections.emptySet(),"");
            ResearchBrief.Brief selected=ResearchBrief.create(part,evidence,stop);
            text.append("Subquestion ").append(sections.size()+1).append(" (your input, not a source claim):\n").append(part).append("\n");
            List<ResearchBrief.Quote> quotes=new ArrayList<>();
            if(scope!=EvidenceAvailability.Scope.REFERENCE)text.append("Unknown — ").append(EvidenceAvailability.reason(scope)).append("\n");
            else {
                for(ResearchBrief.Quote candidate:selected.quotes){
                    check(stop);ResearchEngine.Passage p=candidate.source;candidate.verify(p);
                    if(quotes.size()==MAX_QUOTES_PER_PART||p.text.length()>MAX_QUOTE_UNITS-units){omitted++;continue;}
                    // Full paragraph and its qualifiers survive; article footnotes are never parsed as app IDs.
                    text.append("\nSource: ").append(p.title).append("\nSnapshot: ").append(p.sourceDate).append("\nAttribution / rights: ").append(p.license).append("\nExact quotation [").append(p.id).append("]:\n“");
                    int start=text.length();text.append(p.text);int end=text.length();text.append("”\n");
                    ResearchBrief.Quote bound=new ResearchBrief.Quote(p,start,end);quotes.add(bound);all.add(bound);units+=p.text.length();
                }
                if(quotes.isEmpty())text.append("Unknown — no admissible relevant passage selected from active collections. No answer inferred.\n");
                else text.append("\nCoverage not verified: inspect whether these excerpts answer every part, condition and premise of this subquestion.\n");
                if(!evidence.missingTerms.isEmpty())text.append("Unmatched query terms (not a factual judgment): ").append(String.join(", ",new TreeSet<>(evidence.missingTerms))).append("\n");
            }
            sections.add(new Section(part,scope,quotes,evidence.missingTerms));omitted+=selected.omitted;text.append("\n");
        }
        check(stop);
        text.append("Comparison / connection gap: no relationship between sections, causal chain, verdict, live status or personal result has been inferred. Any unanswered part remains Unknown.\n");
        if(omitted>0)text.append("Omitted candidate passages: ").append(omitted).append(" (bounded selection, relevance, size or source review).\n");
        return new Result(new ResearchBrief.Brief(text.toString(),all,omitted),sections);
    }
}
