package org.pocketlore.app;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.Reader;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;

/** Immutable inverted BM25 index. Ranking expansion never establishes answer support. */
public final class ResearchEngine {
    interface DiskProvider { Result research(String question); int size(); default Result sourceResearch(String question){return research(question);} }
    private DiskProvider disk;
    ResearchEngine(DiskProvider provider){disk=provider;}
    static ResearchEngine combined(List<ResearchEngine> engines){return new ResearchEngine(new DiskProvider(){
        public int size(){int total=0;for(ResearchEngine e:engines)total+=e.size();return total;}
        public Result sourceResearch(String q){
            List<Hit> hits=new ArrayList<>();int candidates=0;
            for(ResearchEngine e:engines){Result r=e.sourceResearch(q);for(Hit h:r.hits)hits.add(new Hit(h.passage,rankScore(q,h.passage)+h.score*.01));candidates+=r.candidatesScored;}
            Set<String> missing=new TreeSet<>(rankTerms(q)),present=new HashSet<>();
            for(Hit h:hits)present.addAll(rankTerms(h.passage.title+" "+h.passage.text));missing.removeAll(present);
            if(!missing.isEmpty())hits.clear();
            return new Result(diverse(hits),missing,"Eligible reference candidates only; not verified support",candidates);
        }
        public Result research(String q){List<Hit> hits=new ArrayList<>();int candidates=0;for(ResearchEngine e:engines){Result r=e.research(q);for(Hit h:r.hits)hits.add(new Hit(h.passage,rankScore(q,h.passage)+h.score*0.01));candidates+=r.candidatesScored;}
            // Missing query vocabulary is a conservative retrieval veto, never entailment.
            Set<String> missing=new HashSet<>(rankTerms(q)),present=new HashSet<>();
            for(Hit h:hits)present.addAll(rankTerms(h.passage.title+" "+h.passage.text));missing.removeAll(present);
            if(!missing.isEmpty())hits.clear();
            hits=diverse(hits);
            return new Result(hits,missing,hits.isEmpty()?"No supporting passage in active collections.":"Retrieved sources only; inspect their dates, scope and rights. No generated answer inferred.",candidates);}

    });}

    /** Shared bounded ranking; exact titles outrank longer titles containing the same words. */
    static double rankScore(String q,Passage p){
        Set<String> query=new HashSet<>(rankTerms(q)),title=new HashSet<>(rankTerms(p.title)),body=new HashSet<>(rankTerms(p.text));
        double score=0;for(String t:query){if(title.contains(t))score+=5;if(body.contains(t))score+=1;}
        if(!title.isEmpty()&&query.equals(title))score+=100;
        else if(!title.isEmpty()&&query.containsAll(title))score+=15;
        Set<String> overlap=new HashSet<>(title);overlap.retainAll(query);score+=overlap.size()/(double)Math.max(1,title.size());
        Set<String> opening=new HashSet<>(rankTerms(p.text.split("[.!?]",2)[0]));for(String t:query)if(opening.contains(t))score+=2;
        return score;
    }
    /** First select distinct documents, then at most one additional passage per document. */
    static List<Hit> diverse(List<Hit> input){
        input.sort(Comparator.comparingDouble((Hit h)->h.score).reversed().thenComparing(h->h.passage.id));
        List<Hit> out=new ArrayList<>();Set<String> docs=new java.util.LinkedHashSet<>();
        for(Hit h:input)if(docs.add(h.passage.url)){out.add(h);if(out.size()==4)return out;}
        for(String url:docs)for(Hit h:input)if(h.passage.url.equals(url)&&!out.contains(h)){out.add(h);break;}
        return new ArrayList<>(out.subList(0,Math.min(4,out.size())));
    }

    public static final class Passage {
        public final String id, title, url, sourceDate, license, text;
        public final String collectionProvenance;
        final List<String> terms;
        Passage(String[] row) {this(row, "Bundled starter source");}
        Passage(String[] row,String provenance) {
            collectionProvenance=provenance;
            id = row[0]; title = row[1]; url = row[2]; sourceDate = row[3];
            license = row[4]; text = row[5]; terms = tokenize(title + " " + text);
        }
    }
    public static final class Hit {
        public final Passage passage;
        public final double score;
        Hit(Passage passage, double score) { this.passage = passage; this.score = score; }
    }
    public static final class Result {
        public final List<Hit> hits;
        public final Set<String> missingTerms;
        public final String answer;
        public final int candidatesScored;
        Result(List<Hit> hits, Set<String> missingTerms, String answer) {
            this(hits, missingTerms, answer, 0);
        }
        Result(List<Hit> hits, Set<String> missingTerms, String answer, int candidatesScored) {
            this.candidatesScored = candidatesScored;
            this.hits = Collections.unmodifiableList(hits);
            this.missingTerms = Collections.unmodifiableSet(missingTerms);
            this.answer = answer;
        }
    }
    private static final Set<String> STOP = new HashSet<>(Arrays.asList(
        "a", "an", "and", "are", "as", "at", "be", "by", "can", "do", "does", "for",
        "from", "how", "i", "in", "is", "it", "of", "on", "or", "the", "to", "was",
        "what", "when", "where", "which", "why", "with", "would", "explain", "compare",
        "between", "versus", "than", "about", "me", "please", "both"));
    private final List<Passage> passages = new ArrayList<>();
    // Exact vocabulary remains separate: expansion must not weaken the answer abstention gate.
    private final Set<String> vocabulary = new HashSet<>();
    private static final class Posting {
        final int passage; final double contribution;
        Posting(int passage, double contribution) { this.passage=passage; this.contribution=contribution; }
    }
    private final Map<String, List<Posting>> index = new HashMap<>();
    private static final Set<String> RANK_STOP = new HashSet<>(Arrays.asList(
        "should", "could", "would", "get", "gets", "got", "make", "makes", "made", "me", "my", "we", "our", "your", "you", "their", "they", "them"));
    // Small, explicit ranking hints, not equivalences for evidence coverage or factual claims.
    private static final Map<String, List<String>> EXPANSIONS = expansions();
    private static Map<String, List<String>> expansions() {
        Map<String, List<String>> result=new HashMap<>();
        for(String group : Arrays.asList("dark night illumination", "crack fracture", "underground groundwater", "ultraviolet uv")) {
            List<String> words=new ArrayList<>();for(String word:group.split(" "))words.add(stem(word));
            for(String word:words)result.put(word,Collections.unmodifiableList(words));
        }
        return Collections.unmodifiableMap(result);
    }
    // Deliberately limited English inflection folding; original passage text/IDs are untouched.
    private static String stem(String word) {
        if(word.length()>4 && word.endsWith("ies"))return word.substring(0,word.length()-3)+"y";
        if(word.length()>3 && word.endsWith("s") && !word.endsWith("ss") && !word.endsWith("us") && !word.endsWith("is"))word=word.substring(0,word.length()-1);
        if(word.length()>5 && word.endsWith("ing"))word=word.substring(0,word.length()-3);
        else if(word.length()>4 && word.endsWith("ed"))word=word.substring(0,word.length()-2);
        if(word.length()>3 && word.endsWith("e") && !word.endsWith("ee"))word=word.substring(0,word.length()-1);
        int n=word.length();
        if(n>3 && word.charAt(n-1)==word.charAt(n-2) && "bdfgmnprt".indexOf(word.charAt(n-1))>=0)word=word.substring(0,n-1);
        return word;
    }
    static List<String> rankTerms(String text) {
        List<String> result=new ArrayList<>();
        for(String term:tokenize(text))if(!RANK_STOP.contains(term))result.add(stem(term));
        return result;
    }
    private void buildIndex() {
        Map<String, Map<Integer, Double>> frequencies=new HashMap<>();
        double[] lengths=new double[passages.size()];double total=0;
        for(int i=0;i<passages.size();i++) {
            Passage passage=passages.get(i);
            for(String term:rankTerms(passage.text)) {
                Map<Integer,Double> posting=frequencies.computeIfAbsent(term,k->new HashMap<>());
                posting.put(i,posting.getOrDefault(i,0.0)+1);lengths[i]++;
            }
            // A document-wide title is useful context, but must not swamp the actual passage.
            for(String term:rankTerms(passage.title)) {
                Map<Integer,Double> posting=frequencies.computeIfAbsent(term,k->new HashMap<>());
                posting.put(i,posting.getOrDefault(i,0.0)+0.3);lengths[i]+=0.3;
            }
            total+=lengths[i];
        }
        double average=Math.max(total/passages.size(),1);
        for(Map.Entry<String,Map<Integer,Double>> term:frequencies.entrySet()) {
            double idf=Math.log(1+(passages.size()-term.getValue().size()+0.5)/(term.getValue().size()+0.5));
            List<Posting> postings=new ArrayList<>();
            for(Map.Entry<Integer,Double> item:term.getValue().entrySet()) {
                int doc=item.getKey();double tf=item.getValue();
                postings.add(new Posting(doc,idf*tf*2.2/(tf+1.2*(0.25+0.75*lengths[doc]/average))));
            }
            postings.sort(Comparator.comparingInt(p->p.passage));index.put(term.getKey(),Collections.unmodifiableList(postings));
        }
    }

    public ResearchEngine(Reader reader) throws IOException {
        Set<String> ids = new HashSet<>();
        try (BufferedReader input = new BufferedReader(reader)) {
            String line;
            while ((line = input.readLine()) != null) {
                if (line.startsWith("#") || line.trim().isEmpty()) continue;
                String[] row = line.split("\t", -1);
                if (row.length != 6 || !ids.add(row[0])) throw new IOException("Invalid knowledge pack row");
                for (String field : row) if (field.trim().isEmpty()) throw new IOException("Empty knowledge pack field");
                Passage passage = new Passage(row);
                passages.add(passage);
                vocabulary.addAll(passage.terms);
            }
        }
        if (passages.isEmpty()) throw new IOException("Knowledge pack is empty");
        buildIndex();
    }

    /** A single index over verified active collections; an empty selection is valid. */
    ResearchEngine(List<Passage> verified) throws IOException {
        Set<String> ids=new HashSet<>();
        for(Passage p:verified){if(!ids.add(p.id))throw new IOException("Duplicate library citation");passages.add(p);vocabulary.addAll(p.terms);}
        if(!passages.isEmpty())buildIndex();
    }

    static List<String> tokenize(String text) {
        List<String> words = new ArrayList<>();
        for (String word : text.toLowerCase(Locale.ROOT).split("[^a-z0-9]+")) {
            if (word.length() > 1 && !STOP.contains(word)) words.add(word);
        }
        return words;
    }

    public int size() { return disk==null?passages.size():disk.size(); }
    /** Counts describe logical index payload, not JVM object allocation or serialized storage. */
    public long[] resourceCounts(){if(disk!=null)return new long[]{disk.size(),-1,-1,-1};long postings=0,characters=0;for(List<Posting> list:index.values())postings+=list.size();for(Passage p:passages)characters+=p.text.length();return new long[]{passages.size(),index.size(),postings,characters};}
    /** Brief-only exclusion precedes combined truncation; generation and browse ranking are unchanged. */
    public Result sourceResearch(String question){
        Result result=disk==null?research(question):disk.sourceResearch(question);
        List<Hit> eligible=new ArrayList<>();for(Hit h:result.hits)if(!h.passage.collectionProvenance.contains("Generation disabled:"))eligible.add(h);
        return new Result(eligible,result.missingTerms,result.answer,result.candidatesScored);
    }
    public Result research(String question) {
        if(disk!=null)return disk.research(question);
        Set<String> terms = new HashSet<>(tokenize(question));
        Set<String> missing = new java.util.TreeSet<>(terms);
        missing.removeAll(vocabulary);
        // Sorted query keys make floating point accumulation and ties deterministic.
        Map<String,Double> query=new java.util.TreeMap<>();
        for(String term:rankTerms(question))query.put(term,1.0);
        for(String term:new ArrayList<>(query.keySet()))
            for(String expansion:EXPANSIONS.getOrDefault(term,Collections.emptyList()))query.putIfAbsent(expansion,0.7);
        Map<Integer,Double> scores=new HashMap<>();
        for(Map.Entry<String,Double> term:query.entrySet()) {
            for(Posting posting:index.getOrDefault(term.getKey(),Collections.emptyList()))
                scores.merge(posting.passage,term.getValue()*posting.contribution,Double::sum);
        }
        List<Hit> hits = new ArrayList<>();
        for(Map.Entry<Integer,Double> score:scores.entrySet())hits.add(new Hit(passages.get(score.getKey()),score.getValue()));
        hits.sort(Comparator.comparingDouble((Hit h) -> h.score).reversed().thenComparing(h -> h.passage.id));
        if (hits.size() > 4) hits = new ArrayList<>(hits.subList(0, 4));
        StringBuilder answer = new StringBuilder();
        if (hits.isEmpty()) {
            answer.append("No supporting passage in this installed pack. Try another question or import a broader knowledge pack. No answer has been inferred.");
        } else {
            answer.append("Relevant evidence\nThese are retrieved pack passages, not a generated explanation or a verified answer.\n\n");
            for (Hit hit : hits) answer.append('[').append(hit.passage.id).append("] ").append(hit.passage.text).append("\n\n");
            if (!missing.isEmpty()) answer.append("Query terms absent from the pack: ").append(String.join(", ", missing)).append(". The evidence may not cover the full question.\n");
            answer.append("Comparison and synthesis require checking these passages yourself in this build.");
        }
        return new Result(hits, missing, answer.toString(), scores.size());
    }
}
