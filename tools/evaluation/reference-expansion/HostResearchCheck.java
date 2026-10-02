package org.pocketlore.app;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
/** Public development observations; JSON is encoded by the host collector, not graded here. */
public final class HostResearchCheck {
    static String b64(String s){return Base64.getEncoder().encodeToString(s.getBytes(StandardCharsets.UTF_8));}
    public static void main(String[] args)throws Exception{
        List<ResearchEngine.Passage> passages=new ArrayList<>();String legal=Files.readString(Path.of(args[2]));
        for(String line:Files.readAllLines(Path.of(args[0]))){String[] row=line.split("\t",-1);if(row.length!=7)throw new AssertionError("Malformed host source");passages.add(new ResearchEngine.Passage(Arrays.copyOf(row,6),row[6],legal));}
        long start=System.nanoTime();ResearchEngine engine=new ResearchEngine(passages);System.err.println("index_open_ns="+(System.nanoTime()-start));
        for(String line:Files.readAllLines(Path.of(args[1]))){String[] c=line.split("\t",2);start=System.nanoTime();ResearchWorkspace.Result r=ResearchWorkspace.create(c[1],engine,()->false);long elapsed=System.nanoTime()-start;
            List<String> ids=new ArrayList<>();for(ResearchBrief.Quote q:r.brief.quotes){q.verify(q.source);if(!r.brief.text.substring(q.displayStart,q.displayEnd).equals(q.source.text))throw new AssertionError("Quote changed");ids.add(q.source.id);}
            System.out.println(c[0]+"\t"+elapsed+"\t"+String.join(",",ids)+"\t"+b64(r.brief.text));
        }
        try{ResearchWorkspace.create("Reference",engine,()->true);throw new AssertionError("Cancellation ignored");}catch(java.util.concurrent.CancellationException expected){}
        ResearchEngine.Passage p=passages.get(0);ResearchBrief.Quote q=new ResearchBrief.Quote(p,0,p.text.length());
        try{q.verify(new ResearchEngine.Passage(new String[]{p.id,p.title,p.url,p.sourceDate,p.license,p.text},p.collectionProvenance,legal+"changed"));throw new AssertionError("Changed license binding accepted");}catch(IllegalArgumentException expected){}
        System.err.println("cancel_and_changed_license_rejected=true");
    }
}
