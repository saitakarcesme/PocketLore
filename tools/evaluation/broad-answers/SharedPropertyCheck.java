package org.pocketlore.app;
import java.nio.file.*;import java.util.*;
/** Actual failed drafts/excerpts; no generated success credit. */
public final class SharedPropertyCheck {
 static String read(Path p)throws Exception{return new String(Files.readAllBytes(p),java.nio.charset.StandardCharsets.UTF_8);}
 public static void main(String[] args)throws Exception{
  for(String id:new String[]{"compare-heat","multi-methods"}){
   Path p=Paths.get(args[0],id);List<ResearchEngine.Hit> hits=new ArrayList<>();
   for(int i=0;i<2;i++){String[] row={"s"+i,read(p.resolve("title"+i)),"https://example.invalid/"+i,"fixture source date","fixture rights",read(p.resolve("excerpt"+i))};hits.add(new ResearchEngine.Hit(new ResearchEngine.Passage(row),1));}
   ResearchEngine.Result e=new ResearchEngine.Result(hits,Collections.emptySet(),"");
   String error=AnswerEngine.comparisonSupportFailure(read(p.resolve("question")),read(p.resolve("draft")),e,900);
   if(error.isEmpty())throw new AssertionError("Unsupported shared property survived: "+id);
  }
  // A genuinely shared stated property must not be rejected merely for using 'both'.
  List<ResearchEngine.Hit> hits=new ArrayList<>();for(String title:new String[]{"Baking","Boiling"}){String[] row={title,title,"https://example.invalid/"+title,"date","rights",title+" uses heat."};hits.add(new ResearchEngine.Hit(new ResearchEngine.Passage(row),1));}
  if(!AnswerEngine.comparisonSupportFailure("Compare baking and boiling.","Both baking and boiling use heat.",new ResearchEngine.Result(hits,Collections.emptySet(),""),900).isEmpty())throw new AssertionError("Shared supported property rejected");
  System.out.println("PASS: actual shared-property leakage withheld; shared supported control retained");
 }
}
