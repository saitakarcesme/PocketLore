package org.pocketlore.app;
import java.nio.file.*;import java.util.*;
/** Reject fixture formatting faults before native historical audits, not semantic errors. */
public final class HistoryPreflight {
 public static void main(String[] args)throws Exception{
  Path input=Path.of(args[0]);int count=0;
  for(String row:Files.readAllLines(input.resolve("history.tsv"))){String[] f=row.split("\t");BoundAnswer.Cancel cancel=new BoundAnswer.Cancel();BoundAnswer.Catalog catalog=BindingHarness.catalog(input,f[1],cancel);StringBuilder raw=new StringBuilder();
   for(String line:Files.readAllLines(input.resolve(f[0]+".claims.tsv"))){String[] c=line.split("\t");List<String> refs=new ArrayList<>();for(String n:c[1].split(","))for(String label:catalog.spans.keySet())if(label.startsWith("P"+n+"."))refs.add(label);raw.append('O').append(c[0]).append('|').append(String.join(",",refs)).append('|').append(ScaleHarness.decode(c[2])).append('|').append(ScaleHarness.decode(c[3])).append('|').append(ScaleHarness.decode(c[4])).append('\n');}
   BoundAnswer.parse(ScaleHarness.decode(f[2]),raw.toString(),catalog,1,cancel);count++;
  }System.out.println("PASS structurally valid historical wrappers="+count+"; support not asserted");
 }
}
