package org.pocketlore.app;
import java.nio.file.*;import java.util.*;
public final class LinkHarness {
 static String q(String s){return ScaleHarness.q(s);}static String d(String s){return ScaleHarness.decode(s);}
 public static void main(String[] args)throws Exception{
  Path inputs=Path.of(args[0]),out=Path.of(args[1]);Files.createDirectories(out);Map<String,EvidenceLinker.Score> scores=new HashMap<>();
  if(args.length>2)for(String line:Files.readAllLines(Path.of(args[2]))){String[] f=line.split("\t",-1);if(scores.put(f[0],new EvidenceLinker.Score(Double.parseDouble(f[1]),Double.parseDouble(f[2]),Double.parseDouble(f[3]),Integer.parseInt(f[4]),d(f[5])))!=null)throw new IllegalArgumentException("Duplicate score identity");}
  LinkedHashMap<String,EvidenceLinker.Pair> pairs=new LinkedHashMap<>();StringBuilder results=new StringBuilder("[");boolean first=true;
  for(String line:Files.readAllLines(inputs.resolve("drafts.tsv"))){String[] f=line.split("\t",-1);String id=f[0],question=d(f[1]),raw=d(f[2]);int tokens=Integer.parseInt(f[3]);String failure="",rendered="",claims="[]",links="[]";BoundAnswer.Cancel cancel=new BoundAnswer.Cancel();
   try{BoundAnswer.Catalog catalog=BindingHarness.catalog(inputs,id,cancel);BoundAnswer.Draft draft=BoundAnswer.parse(question,raw,catalog,tokens,cancel);
    for(BoundAnswer.Claim claim:draft.claims)for(EvidenceLinker.Candidate candidate:EvidenceLinker.candidates(claim,catalog,cancel))for(EvidenceLinker.Pair pair:candidate.pairs)pairs.put(pair.key,pair);
    if(args.length>2){BoundAnswer.Draft bound=EvidenceLinker.bind(draft,catalog,scores,cancel);BoundAnswer.Rendered r=EvidenceLinker.render(bound,cancel);rendered=r.text;claims=BindingHarness.spans(bound);StringBuilder ls=new StringBuilder("[");for(int i=0;i<r.links.size();i++){if(i>0)ls.append(',');BoundAnswer.Link l=r.links.get(i);ls.append("{\"start_utf16\":").append(l.start).append(",\"end_utf16\":").append(l.end).append('}');}links=ls.append(']').toString();}
   }catch(IllegalArgumentException e){failure=e.getMessage();}
   if(!first)results.append(',');first=false;results.append("{\"id\":").append(q(id)).append(",\"question\":").append(q(question)).append(",\"failure\":").append(q(failure)).append(",\"rendered\":").append(q(rendered)).append(",\"claims\":").append(claims).append(",\"links\":").append(links).append(",\"route\":").append(q(rendered.isEmpty()?"WITHHELD":"SCREEN_ELIGIBLE")).append('}');
  }
  Files.writeString(out.resolve("linked.json"),results.append("]\n").toString());StringBuilder ps=new StringBuilder("[");first=true;for(EvidenceLinker.Pair pair:pairs.values()){if(!first)ps.append(',');first=false;ps.append("{\"key\":").append(q(pair.key)).append(",\"premise\":").append(q(pair.premise)).append(",\"hypothesis\":").append(q(pair.hypothesis)).append('}');}Files.writeString(out.resolve("pairs.json"),ps.append("]\n").toString());System.out.println("Pairs: "+pairs.size());
 }
}
