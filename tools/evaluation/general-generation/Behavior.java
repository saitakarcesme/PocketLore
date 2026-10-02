package org.pocketlore.app;
import java.nio.file.*;import java.util.*;import java.io.*;import java.util.concurrent.CancellationException;
public final class Behavior {
 public static void main(String[] args)throws Exception{
  List<ResearchEngine.Passage> rows=new ArrayList<>();for(String line:Files.readAllLines(Path.of(args[0]))){String[] f=line.split("\t");for(int i=0;i<f.length;i++)f[i]=new String(Base64.getDecoder().decode(f[i]),java.nio.charset.StandardCharsets.UTF_8);rows.add(new ResearchEngine.Passage(f));}
  ResearchEngine engine=new ResearchEngine(rows);String query="Compare the conservation of soil moisture when mulch covers the surface with the reduction in pest and weed pressure across a sequence of different crops; distinguish nutrients from moisture without assuming identical benefits.";
  GeneralGroundedAnswer.Context c=GeneralGroundedAnswer.retrieve(query,engine,()->false);
  if(c.retrievalQueries.size()<3||c.sources.isEmpty()||c.sources.size()>8)throw new AssertionError("bounded long-query retrieval");
  for(ResearchEngine.Passage p:c.sources)if(!c.prompt().contains(p.text))throw new AssertionError("paragraph cut");
  boolean cancelled=false;try{GeneralGroundedAnswer.retrieve(query,engine,()->true);}catch(CancellationException e){cancelled=true;}if(!cancelled)throw new AssertionError("cancellation");
  if(GeneralGroundedAnswer.retrieve(query,engine,()->false).sources.size()!=c.sources.size())throw new AssertionError("retry changed");
  boolean duplicate=false;try{GeneralGroundedAnswer.supplied(query,Arrays.asList(rows.get(0),rows.get(0)));}catch(IllegalArgumentException e){duplicate=true;}if(!duplicate)throw new AssertionError("duplicate");
  if(GeneralGroundedAnswer.structuralFailure("Invented [[S999]]. GAPS: none",c).isEmpty())throw new AssertionError("unknown citation");
  if(!GeneralGroundedAnswer.publicationRoute("Invented [[S1]]. GAPS: none",c).startsWith("WITHHELD"))throw new AssertionError("format promoted as support");
  System.out.println("PASS: long query windows, bounded full paragraphs, cancellation/retry, duplicate identity, missing citation, no structural promotion");
  System.out.println("Queries: "+c.retrievalQueries);for(ResearchEngine.Passage p:c.sources)System.out.println(p.id+"\t"+p.title);
 }
}
