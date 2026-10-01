package org.pocketlore.app;
import java.nio.file.*;import java.util.*;
public final class Export {
 public static void main(String[] a)throws Exception{
  Path input=Path.of(a[0]);StringBuilder b=new StringBuilder("{");boolean first=true;
  for(String line:Files.readAllLines(Path.of(a[1]))){String id=line.split("\t")[0];BoundAnswer.Cancel cancel=new BoundAnswer.Cancel();SentenceEvidence ev=new SentenceEvidence(BindingHarness.catalog(input,id,cancel),cancel);if(!first)b.append(',');first=false;b.append(BindingHarness.q(id)).append(":[");boolean sf=true;
   for(Map.Entry<String,BoundAnswer.Span> e:ev.sentences.entrySet()){if(!sf)b.append(',');sf=false;BoundAnswer.Span s=e.getValue();b.append("{\"sentence_id\":").append(BindingHarness.q(e.getKey())).append(",\"span\":").append(BindingHarness.spans(new BoundAnswer.Draft("",Arrays.asList(new BoundAnswer.Claim(1,s.source.title,"none",s.text(),Arrays.asList(s))),1))).append('}');}b.append(']');
  }Files.writeString(Path.of(a[2]),b.append('}').toString());
 }
}
