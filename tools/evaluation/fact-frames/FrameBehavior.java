package org.pocketlore.app;
import java.util.*;
public final class FrameBehavior {
 static int checks;static void check(boolean b){if(!b)throw new AssertionError("Frame behavior "+checks);checks++;}
 static void reject(Runnable f){try{f.run();}catch(IllegalArgumentException|IllegalStateException e){checks++;return;}throw new AssertionError("Unexpected approval");}
 static BoundAnswer.Catalog catalog(String title,String text){String a=String.join("",Collections.nCopies(64,"a"));return new BoundAnswer.Catalog(Arrays.asList(new BoundAnswer.Source(a,"test-1",a,BoundAnswer.sha(text),title,"2026-10-01","Constructed control fixture; not corpus facts",text)),new BoundAnswer.Cancel());}
 static BoundAnswer.Draft draft(BoundAnswer.Catalog c,String text){return BoundAnswer.parse("Describe the documented relation.","O1|P1.1|Context|none|"+text,c,30,new BoundAnswer.Cancel());}
 static FactFrames.Proof bind(BoundAnswer.Catalog c,String text){return FactFrames.bind(draft(c,text),c,new BoundAnswer.Cancel());}
 public static void main(String[] args){
  // Name substitution establishes the same relation independent of article/case identity.
  for(String city:Arrays.asList("Arbordale","Stonebay","Athens")){
   BoundAnswer.Catalog c=catalog("Control",city+" is the capital and largest city of Newland.");String text=city+" is the capital and largest city of Newland.";FactFrames.Proof p=bind(c,text);check(p.trace.size()==2);check(p.draft.claims.get(0).text.equals(text));check(p.draft.claims.get(0).references.get(0).text().equals(text));
   reject(()->bind(c,"Newland is the capital and largest city of "+city+"."));reject(()->bind(c,text+" All visitors receive free transport."));reject(()->bind(c,city+" is not the capital and largest city of Newland."));
  }
  BoundAnswer.Catalog temp=catalog("Control","In food processing, flash processing is a process of food preservation in which packaged foods (e.g., milk and fruit juices) are treated with mild heat, usually to less than 100 °C (212 °F), to eliminate pathogens and extend shelf life.");
  check(bind(temp,"The usual temperature qualification for flash processing is less than 100 °C (212 °F).").trace.size()==1);reject(()->bind(temp,"The usual temperature qualification for flash processing is less than 100 °C (100 °F)."));reject(()->bind(temp,"The temperature for flash processing is always exactly 100 °C (212 °F)."));
  BoundAnswer.Catalog formula=catalog("Control","A difference of 1.0 in magnitude corresponds to the brightness ratio of [TeX: {\\displaystyle {\\sqrt[{5}]{100}}}] , or about 2.512.");
  check(bind(formula,"The brightness ratio for a one-magnitude difference is the fifth root of 100, which is approximately 2.512.").trace.size()==1);reject(()->bind(formula,"A magnitude difference of 1 corresponds to the brightness ratio of the square root of 100, or about 2.512."));reject(()->bind(formula,"A magnitude difference of 1 corresponds to the brightness ratio of the square root of 100, or about 10."));
  BoundAnswer.Catalog output=catalog("Control","Castings (also called residue) is the end-product of the breakdown of organic matter by earthworms. These excreta have been shown to contain reduced levels of contaminants and a higher saturation of nutrients than the organic materials before vermicomposting.");
  check(bind(output,"Castings is the material left by earthworms after they break down organic matter.").trace.size()==1);reject(()->bind(output,"Castings is the organic input consumed by earthworms before processing."));
  String temporal="After joining with the Kingdom of Eastland to form the Crown of Eastland, Arbordale, which continued to be the capital of the Principality of Westland, became the most important city in the Crown of Eastland and its main economic and administrative centre, only to be overtaken by Baytown, wrested from old control by the settlers, shortly before the dynastic union between the Crown of Northland and the Crown of Eastland in 1516.";
  BoundAnswer.Catalog time=catalog("Control",temporal);check(bind(time,"Arbordale continued as capital of the Principality of Westland after joining the Kingdom of Eastland.").trace.size()==1);reject(()->bind(time,"Arbordale first became capital of the Principality of Westland after joining the Kingdom of Eastland."));
  BoundAnswer.Cancel cancel=new BoundAnswer.Cancel();cancel.cancel();reject(()->FactFrames.sources(formula,cancel));reject(()->FactFrames.bind(draft(formula,"A difference of 1.0 in magnitude corresponds to the brightness ratio of 2.512."),formula,cancel));
  check(bind(formula,"A difference of 1.0 in magnitude corresponds to the brightness ratio of 2.512.").trace.size()==1);
  String a=String.join("",Collections.nCopies(64,"a"));reject(()->new BoundAnswer.Source(a,"id",a,BoundAnswer.sha("unchanged"),"T","date","rights","changed"));
  BoundAnswer.Source one=formula.sources.get(0);reject(()->new BoundAnswer.Catalog(Arrays.asList(one,one),new BoundAnswer.Cancel()));
  FactFrames.Proof p=bind(formula,"The brightness ratio for a one-magnitude difference is the fifth root of 100, which is approximately 2.512.");BoundAnswer.Rendered r=EvidenceLinker.render(p.draft,new BoundAnswer.Cancel());check(r.links.size()==1);check(r.text.substring(r.links.get(0).start,r.links.get(0).end).equals("[1]"));check(p.draft.claims.get(0).references.get(0).text().contains("[{5}]"));
  System.out.println("Frame behavioral checks: "+checks);
 }
}
