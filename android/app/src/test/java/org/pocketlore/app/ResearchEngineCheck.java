package org.pocketlore.app;
import java.io.StringReader;
import java.nio.file.Files;
import java.nio.file.Path;

/** Executable contract checks, using the actual generated starter pack. */
public final class ResearchEngineCheck {
    public static void main(String[] args) throws Exception {
        ResearchEngine engine = new ResearchEngine(Files.newBufferedReader(Path.of(args[0])));
        require(engine.size() == 8, "pack count");
        require(engine.research("What is condensation?").hits.get(0).passage.id.equals("water-02"), "condensation retrieval");
        require(engine.research("Compare evaporation and condensation").hits.stream().anyMatch(h -> h.passage.id.equals("water-01")), "comparison evidence");
        require(engine.research("quasar supernova").hits.isEmpty(), "unsupported query abstains");
        require(engine.research("   ").hits.isEmpty(), "empty query abstains");
        require(engine.research("groundwater bitcoin").missingTerms.contains("bitcoin"), "partial coverage warning");
        try {
            new ResearchEngine(new StringReader("broken\trow\n"));
            throw new AssertionError("corrupt pack accepted");
        } catch (java.io.IOException expected) { }
        String first = engine.research("infiltration groundwater").answer;
        require(first.equals(engine.research("infiltration groundwater").answer), "deterministic evidence");
        require(first.contains("[water-"), "source references");
        System.out.println("PASS: 8 retrieval, abstention, corruption and citation contract checks");
    }
    private static void require(boolean condition, String name) {
        if (!condition) throw new AssertionError(name);
    }
}
