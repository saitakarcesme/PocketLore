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

/** Small transparent BM25 retriever. Scores rank passages; they are not confidence. */
public final class ResearchEngine {
    public static final class Passage {
        public final String id, title, url, sourceDate, license, text;
        final List<String> terms;
        Passage(String[] row) {
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
        Result(List<Hit> hits, Set<String> missingTerms, String answer) {
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
    private final Map<String, Integer> documentFrequency = new HashMap<>();
    private final double averageLength;

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
                for (String term : new HashSet<>(passage.terms))
                    documentFrequency.put(term, documentFrequency.getOrDefault(term, 0) + 1);
            }
        }
        if (passages.isEmpty()) throw new IOException("Knowledge pack is empty");
        averageLength = passages.stream().mapToInt(p -> p.terms.size()).average().orElse(1);
    }

    static List<String> tokenize(String text) {
        List<String> words = new ArrayList<>();
        for (String word : text.toLowerCase(Locale.ROOT).split("[^a-z0-9]+")) {
            if (word.length() > 1 && !STOP.contains(word)) words.add(word);
        }
        return words;
    }

    public int size() { return passages.size(); }
    public Result research(String question) {
        Set<String> terms = new HashSet<>(tokenize(question));
        Set<String> missing = new java.util.TreeSet<>(terms);
        missing.removeAll(documentFrequency.keySet());
        List<Hit> hits = new ArrayList<>();
        for (Passage passage : passages) {
            double score = 0;
            for (String term : terms) {
                int frequency = Collections.frequency(passage.terms, term);
                if (frequency == 0) continue;
                int df = documentFrequency.get(term);
                double idf = Math.log(1 + (passages.size() - df + 0.5) / (df + 0.5));
                score += idf * frequency * 2.2 / (frequency + 1.2 * (0.25 + 0.75 * passage.terms.size() / averageLength));
            }
            if (score > 0) hits.add(new Hit(passage, score));
        }
        hits.sort(Comparator.comparingDouble((Hit h) -> h.score).reversed().thenComparing(h -> h.passage.id));
        if (hits.size() > 4) hits = new ArrayList<>(hits.subList(0, 4));
        StringBuilder answer = new StringBuilder();
        if (hits.isEmpty()) {
            answer.append("No supporting passage in this installed pack. Try a water-cycle question or install a broader pack in a future version. No answer has been inferred.");
        } else {
            answer.append("Relevant evidence\nThese are retrieved pack passages, not a generated explanation or a verified answer.\n\n");
            for (Hit hit : hits) answer.append('[').append(hit.passage.id).append("] ").append(hit.passage.text).append("\n\n");
            if (!missing.isEmpty()) answer.append("Query terms absent from the pack: ").append(String.join(", ", missing)).append(". The evidence may not cover the full question.\n");
            answer.append("Comparison and synthesis require checking these passages yourself in this build.");
        }
        return new Result(hits, missing, answer.toString());
    }
}
