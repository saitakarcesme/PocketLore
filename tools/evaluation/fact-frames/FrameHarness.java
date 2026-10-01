package org.pocketlore.app;
import java.nio.file.*;import java.util.*;
public final class FrameHarness {
 static String q(String s){return ScaleHarness.q(s);}static String d(String s){return ScaleHarness.decode(s);}
 public static void main(String[] args)throws Exception{
  Path inputs=Path.of(args[0]),out=Path.of(args[1]);Files.createDirectories(out);StringBuilder results=new StringBuilder("[");boolean first=true;
  for(String line:Files.readAllLines(inputs.resolve("drafts.tsv"))){String[] f=line.split("\t",-1);String id=f[0],question=d(f[1]),raw=d(f[2]);int tokens=Integer.parseInt(f[3]);String failure="",rendered="",claims="[]",links="[]";BoundAnswer.Cancel cancel=new BoundAnswer.Cancel();List<String>trace=new ArrayList<>();StringBuilder grounds=new StringBuilder("[");StringBuilder requested=new StringBuilder("[");
   BoundAnswer.Catalog catalog=BindingHarness.catalog(inputs,id,cancel);boolean gf=true;
   for(FactFrames.Ground ground:FactFrames.sources(catalog,cancel)){if(!gf)grounds.append(',');gf=false;grounds.append("{\"fact\":").append(q(ground.fact.key())).append(",\"refs\":[");for(int i=0;i<ground.refs.size();i++){if(i>0)grounds.append(',');grounds.append(q(ground.refs.get(i).label));}grounds.append("]}");}grounds.append(']');
   try{
    if(raw.equals("@PROBE")){String passage=d(f[4]),text=d(f[5]);List<String>labels=new ArrayList<>();String subject="";for(BoundAnswer.Span span:catalog.spans.values())if(span.source.id.equals(passage)){labels.add(span.label);subject=span.source.title;}raw="O1|"+String.join(",",labels)+"|"+subject+"|none|"+text;}
    BoundAnswer.Draft draft=BoundAnswer.parse(question,raw,catalog,tokens,cancel);boolean rf=true;
    for(BoundAnswer.Claim claim:draft.claims){if(!rf)requested.append(',');rf=false;requested.append("{\"text\":").append(q(claim.text)).append(",\"frames\":[");try{List<FactFrames.Fact> fs=FactFrames.claim(claim);for(int i=0;i<fs.size();i++){if(i>0)requested.append(',');requested.append(q(fs.get(i).key()));}requested.append("],\"failure\":\"\"}");}catch(IllegalArgumentException e){requested.append("],\"failure\":").append(q(e.getMessage())).append('}');}}
    FactFrames.Proof proof=FactFrames.bind(draft,catalog,cancel);trace=proof.trace;BoundAnswer.Rendered r=EvidenceLinker.render(proof.draft,cancel);rendered=r.text;claims=BindingHarness.spans(proof.draft);StringBuilder ls=new StringBuilder("[");for(int i=0;i<r.links.size();i++){if(i>0)ls.append(',');BoundAnswer.Link l=r.links.get(i);ls.append("{\"start_utf16\":").append(l.start).append(",\"end_utf16\":").append(l.end).append('}');}links=ls.append(']').toString();
   }catch(IllegalArgumentException e){failure=e.getMessage();}
   requested.append(']');if(!first)results.append(',');first=false;results.append("{\"id\":").append(q(id)).append(",\"question\":").append(q(question)).append(",\"failure\":").append(q(failure)).append(",\"rendered\":").append(q(rendered)).append(",\"claims\":").append(claims).append(",\"links\":").append(links).append(",\"source_frames\":").append(grounds).append(",\"requested_frames\":").append(requested).append(",\"proof\":[");for(int i=0;i<trace.size();i++){if(i>0)results.append(',');results.append(q(trace.get(i)));}results.append("],\"route\":").append(q(rendered.isEmpty()?"WITHHELD":"SCREEN_ELIGIBLE")).append('}');
  }Files.writeString(out.resolve("linked.json"),results.append("]\n").toString());
 }
}
