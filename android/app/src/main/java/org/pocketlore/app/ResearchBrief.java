package org.pocketlore.app;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.function.BooleanSupplier;

/** Exact-source research material, deliberately separate from generated answer outcomes. */
public final class ResearchBrief {
    public static final int MAX_QUOTES=4, MAX_TEXT_UNITS=8192;
    public static final class Quote {
        public final ResearchEngine.Passage source;
        public final int sourceStart=0, sourceEnd, displayStart, displayEnd;
        public final String sha256, metadataHash;
        Quote(ResearchEngine.Passage p,int start,int end){source=p;sourceEnd=p.text.length();displayStart=start;displayEnd=end;sha256=hash(p.text);metadataHash=identity(p);}
        public void verify(ResearchEngine.Passage available){
            if(available==null || !metadataHash.equals(identity(available)) || !source.id.equals(available.id))throw new IllegalArgumentException("Source changed or missing");
        }
    }
    public static final class Brief {
        public final String text;
        public final List<Quote> quotes;
        public final int omitted;
        public final boolean generated=false, completenessVerified=false;
        Brief(String text,List<Quote> quotes,int omitted){this.text=text;this.quotes=Collections.unmodifiableList(quotes);this.omitted=omitted;}
    }
    static String hash(String text){try{
        byte[] digest=MessageDigest.getInstance("SHA-256").digest(text.getBytes(StandardCharsets.UTF_8));StringBuilder out=new StringBuilder();for(byte b:digest)out.append(String.format(java.util.Locale.ROOT,"%02x",b&255));return out.toString();
    }catch(Exception e){throw new IllegalStateException(e);}}
    private static String identity(ResearchEngine.Passage p){
        StringBuilder b=new StringBuilder();for(String field:new String[]{p.id,p.title,p.url,p.sourceDate,p.license,p.collectionProvenance,p.text})b.append(field.length()).append(':').append(field);return hash(b.toString());
    }
    private static void cancelled(BooleanSupplier stop){if(stop.getAsBoolean()||Thread.currentThread().isInterrupted())throw new java.util.concurrent.CancellationException("Brief cancelled; no partial result");}
    private static boolean metadata(ResearchEngine.Passage p){
        return !p.id.trim().isEmpty()&&!p.title.trim().isEmpty()&&!p.url.trim().isEmpty()&&!p.sourceDate.trim().isEmpty()&&!p.license.trim().isEmpty()&&!p.collectionProvenance.trim().isEmpty();
    }
    public static Brief create(String question,ResearchEngine.Result evidence,BooleanSupplier stop){
        cancelled(stop);
        if(question==null||question.trim().isEmpty()||question.length()>2048)throw new IllegalArgumentException("Question must contain 1–2048 UTF-16 units");
        StringBuilder out=new StringBuilder("Source-backed research brief · exact quotations\nNot a generated answer. Relevance and complete coverage are unverified.\n\nYour question (not a source assertion):\n").append(question).append("\n\n");
        List<Quote> quotes=new ArrayList<>();Set<String> ids=new HashSet<>();int units=0,omitted=0;
        for(ResearchEngine.Hit hit:evidence.hits){
            cancelled(stop);ResearchEngine.Passage p=hit.passage;
            if(!ids.add(p.id))throw new IllegalArgumentException("Duplicate citation namespace");
            if(!metadata(p)||p.text.trim().isEmpty()||p.collectionProvenance.contains("Generation disabled:")||quotes.size()==MAX_QUOTES||p.text.length()>MAX_TEXT_UNITS-units){omitted++;continue;}
            // Entire passage only: never trim a qualifying tail or splice subject-free sentences.
            out.append("Source article: ").append(p.title).append("\nDate / snapshot: ").append(p.sourceDate).append("\nRights: ").append(p.license).append("\n").append(p.collectionProvenance).append("\nSource URL: ").append(p.url).append("\nQuote [").append(p.id).append("]:\n“");
            int start=out.length();out.append(p.text);int end=out.length();out.append("”\nPassage SHA-256: ").append(hash(p.text)).append("\n\n");quotes.add(new Quote(p,start,end));units+=p.text.length();
        }
        cancelled(stop);
        out.append("Coverage unresolved: these passages may address only part of your question. No comparison, causal connection, false premise, prediction or current status has been inferred. Inspect the full quoted conditions and dates.\n");
        if(quotes.isEmpty())out.append("No admissible source passage selected. No answer inferred.\n");
        if(omitted>0)out.append("Omitted passages: ").append(omitted).append(" (size, missing metadata or unresolved source review). No shortened replacement was inserted.\n");
        return new Brief(out.toString(),quotes,omitted);
    }
}
