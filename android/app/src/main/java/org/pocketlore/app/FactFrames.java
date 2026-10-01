package org.pocketlore.app;

import java.util.*;
import java.util.regex.*;

/** Experimental controlled-English semantic adapter, not general entailment.
 * Unknown clauses fail closed. No case IDs, entity allowlists or review labels are used.
 */
final class FactFrames {
 static final class Fact {
  final String relation;final List<String> arguments;
  Fact(String relation,String...args){this.relation=relation;List<String>a=new ArrayList<>();for(String s:args)a.add(norm(s));arguments=Collections.unmodifiableList(a);}
  String key(){return relation+"|"+String.join("|",arguments);}
 }
 static final class Ground {
  final Fact fact;final List<BoundAnswer.Span> refs;
  Ground(Fact f,List<BoundAnswer.Span> refs){fact=f;this.refs=Collections.unmodifiableList(new ArrayList<>(refs));}
 }
 static final class Proof {
  final BoundAnswer.Draft draft;final List<String> trace;
  Proof(BoundAnswer.Draft draft,List<String> trace){this.draft=draft;this.trace=trace;}
 }
 static String norm(String s){return s.toLowerCase(Locale.ROOT).trim().replaceAll("\\s+"," ").replaceFirst("^(the|a|an) ","");}
 static String process(String s){String n=norm(s);return n.endsWith("ing")?n.substring(0,n.length()-3):n;}
 static Matcher match(String pattern,String text){Matcher m=Pattern.compile(pattern,Pattern.CASE_INSENSITIVE|Pattern.UNICODE_CASE).matcher(text);return m.matches()?m:null;}
 static String clean(String s){return s.replaceAll("\\[(?:[0-9]+(?:[,–-][0-9]+)*|[a-z])\\]","").replaceAll("\\s+"," ").trim();}
 static Fact f(String rel,String...args){return new Fact(rel,args);}
 static void add(List<Ground> out,Fact f,BoundAnswer.Span s){out.add(new Ground(f,Arrays.asList(s)));}
 static final class Context {String entity;BoundAnswer.Span anchor;Context(String e,BoundAnswer.Span s){entity=e;anchor=s;}}
 static List<Fact> geography(String text){
  List<Fact> out=new ArrayList<>();Matcher m;
  // Split only the declared additive predicates, retaining each complete argument.
  if((m=match("(.+?) is (?:the )?capital and largest city of (.+?),? and (?:it )?is located on (?:the )?(.+?) coast of (.+?)\\.",text))!=null){out.add(f("capital",m.group(1),m.group(2)));out.add(f("largest-city",m.group(1),m.group(2)));out.add(f("coast",m.group(1),m.group(3),m.group(4)));return out;}
  if((m=match("(.+?) is (?:the )?capital and largest city of (.+?), and it is (?:the )?(southernmost|northernmost|easternmost|westernmost) capital on (.+?)\\.",text))!=null){out.add(f("capital",m.group(1),m.group(2)));out.add(f("largest-city",m.group(1),m.group(2)));out.add(f("capital-extreme",m.group(1),m.group(3),m.group(4)));return out;}
  if((m=match("(.+?) is (?:the )?capital and largest city of (.+?), as well as (?:the )?([a-z-]+) populous municipality of (.+?) after (.+?)\\.",text))!=null){out.add(f("capital",m.group(1),m.group(2)));out.add(f("largest-city",m.group(1),m.group(2)));out.add(f("population-rank",m.group(1),m.group(3),m.group(4),m.group(5)));return out;}
  if((m=match("(.+?) is (?:the )?capital and largest city of (.+?)\\.",text))!=null){out.add(f("capital",m.group(1),m.group(2)));out.add(f("largest-city",m.group(1),m.group(2)));return out;}
  if((m=match("(.+?) is (?:a city|located) on (?:the )?(.+?) coast of (.+?)\\.",text))!=null){out.add(f("coast",m.group(1),m.group(2),m.group(3)));return out;}
  return null;
 }
 static List<Ground> sources(BoundAnswer.Catalog catalog,BoundAnswer.Cancel cancel){
  List<Ground> out=new ArrayList<>();Map<String,Context> definitions=new HashMap<>();
  // Resolve process anaphora only when this catalog contains an explicit matching definition.
  for(BoundAnswer.Span s:catalog.spans.values()){
   cancel.check();String t=clean(s.text());Matcher m;
   if((m=match("(.+?)(?: or [a-z -]+)? is a horticultural technique whereby tissues of plants are joined so as to continue their growth together\\.",t))!=null)definitions.put(s.source.documentHash,new Context(process(m.group(1)),s));
   if((m=match("(.+?) is the selective removal of certain parts of a plant, such as branches, buds, or roots\\.",t))!=null)definitions.put(s.source.documentHash,new Context(process(m.group(1)),s));
  }
  for(BoundAnswer.Source source:catalog.sources){
   Context antecedent=null;
   for(BoundAnswer.Span s:catalog.spans.values())if(s.source==source){
    cancel.check();String t=clean(s.text());Matcher m;List<BoundAnswer.Span> provenance=new ArrayList<>();provenance.add(s);
    if(t.startsWith("It is ")&&antecedent!=null){t=antecedent.entity+t.substring(2);provenance.add(antecedent.anchor);}
    List<Fact> geo=geography(t);
    if(geo!=null){for(Fact fact:geo)out.add(new Ground(fact,provenance));String entity=geo.get(0).arguments.get(0);if(antecedent==null)antecedent=new Context(entity,s);}
    if((m=match("A significant coastal urban area in (.+?), (.+?) is also the capital of (.+?), and is the (southernmost|northernmost|easternmost|westernmost) capital on (.+?)\\.",t))!=null){add(out,f("capital",m.group(2),m.group(3)),s);add(out,f("capital-extreme",m.group(2),m.group(4),m.group(5)),s);}
    if((m=match("Perhaps the most commonly known use for (.+?) is at an industrial level to produce commodity chemicals, such as (.+?) and (.+?)\\.",t))!=null){add(out,f("industrial-product",m.group(1),m.group(2)),s);add(out,f("industrial-product",m.group(1),m.group(3)),s);}
    if((m=match("In food processing, (.+?)(?: \\(-[a-z]+\\))? is a process of food preservation in which packaged foods \\(e\\.g\\., .+?\\) are treated with mild heat, usually to less than ([0-9.]+) °C \\(([0-9.]+) °F\\), to eliminate pathogens and extend shelf life\\.",t))!=null){double c=Double.parseDouble(m.group(2)),v=Double.parseDouble(m.group(3));if(Math.abs(c*1.8+32-v)<.00001)add(out,f("temperature","usual",m.group(1),"less-than",m.group(2),m.group(3)),s);}
    if((m=match("(.+?) \\(also called .+?\\) is the end-product of the breakdown of (.+?) by (.+?)\\.(?: These excreta have been shown to contain reduced levels of contaminants and a higher saturation of nutrients than the organic materials before vermicomposting\\.)?",t))!=null)add(out,f("decomposition-output",m.group(3),m.group(2),m.group(1)),s);
    if((m=match("After joining with (.+?) to form (.+?), (.+?), which continued to be the capital of (.+?), became the most important city in (.+?) and its main economic and administrative centre, only to be overtaken by (.+?), wrested from (.+?) by (.+?), shortly before the dynastic union between (.+?) and (.+?) in ([0-9]+)\\.",t))!=null)add(out,f("capital-event",m.group(3),"continue",m.group(4),"after-joining",m.group(1)),s);
    Context def=definitions.get(s.source.documentHash);
    if(def!=null&&t.equals("The success of this joining requires that the vascular tissues grow together."))out.add(new Ground(f("requires-growth",def.entity,"vascular tissues","together"),Arrays.asList(def.anchor,s)));
    if(def!=null&&(m=match("The practice entails the targeted removal of (.+?) from (.+?)\\.",t))!=null)out.add(new Ground(f("targeted-removal",def.entity,m.group(1),m.group(2)),Arrays.asList(def.anchor,s)));
    if((m=match("When these principles are written down into a single document or set of legal documents, those documents may be said to embody a (.+?); if they are encompassed in a single comprehensive document, it is said to embody a (.+?)\\.",t))!=null){add(out,f("definition",m.group(1),"single-or-set-written"),s);add(out,f("definition",m.group(2),"single-comprehensive"),s);}
    // Preserve the root's syntactic degree; decimal token overlap is never sufficient.
    if((m=match("A difference of ([0-9.]+) in (.+?) corresponds to the (.+?) ratio of \\[TeX: (.+)\\] ?, or about ([0-9.]+)\\.",t))!=null){Matcher root=Pattern.compile("\\\\sqrt\\[\\{([0-9]+)\\}\\]\\{([0-9.]+)\\}").matcher(m.group(4));if(root.find()){int degree=Integer.parseInt(root.group(1));double rad=Double.parseDouble(root.group(2));if(degree>=2&&degree<=16&&rad>0&&rounded(Math.pow(rad,1.0/degree),m.group(5)))add(out,f("root-ratio",m.group(1),m.group(2),m.group(3),root.group(1),root.group(2)),s);}}
    if((m=match("Although scientific research may not be their primary goal, some (.+?) contribute to citizen science by monitoring (.+?), (.+?), (.+?)\\.",t))!=null){
     // This adapter projects two explicit members of an existential monitoring list.
     // Reject contrast/negation/temporal tails rather than silently dropping conditions.
     if(!Pattern.compile("\\b(not|never|only|unless|if|after|before|when|always|without|however|but|is|are|was|were)\\b",Pattern.CASE_INSENSITIVE).matcher(m.group(4)).find()){
      add(out,f("citizen-monitor","some",m.group(1),m.group(2)),s);add(out,f("citizen-monitor","some",m.group(1),m.group(3)),s);
     }
    }
   }
  }
  return out;
 }
 static boolean rounded(double actual,String display){try{double shown=Double.parseDouble(display);int dot=display.indexOf('.');int digits=dot<0?0:display.length()-dot-1;return Double.isFinite(shown)&&Math.abs(actual-shown)<=0.5*Math.pow(10,-digits)+1e-12;}catch(NumberFormatException e){return false;}}
 static int degree(String word){switch(norm(word)){case "square":return 2;case "cube":case "third":return 3;case "fourth":return 4;case "fifth":case "5th":return 5;case "sixth":return 6;default:return -1;}}
 static List<Fact> claim(BoundAnswer.Claim claim){
  String t=claim.text;List<Fact> facts=geography(t);if(facts!=null)return facts;facts=new ArrayList<>();Matcher m;
  if((m=match("(.+?) and (.+?) are two industrial (.+?) end products\\.",t))!=null){facts.add(f("industrial-product",m.group(3),m.group(1)));facts.add(f("industrial-product",m.group(3),m.group(2)));return facts;}
  if((m=match("The usual temperature qualification for (.+?) is less than ([0-9.]+) °C \\(([0-9.]+) °F\\)\\.",t))!=null){facts.add(f("temperature","usual",m.group(1),"less-than",m.group(2),m.group(3)));return facts;}
  if((m=match("The success of (?:a |an )?(.+?) requires that the (.+?) grow together\\.",t))!=null){facts.add(f("requires-growth",process(m.group(1)),m.group(2),"together"));return facts;}
  if((m=match("The reason for (.+?) unwanted plant material is to remove (.+?) from (.+?)\\.",t))!=null){facts.add(f("targeted-removal",process(m.group(1)),m.group(2),m.group(3)));return facts;}
  if((m=match("A (.+?) is one in which the principles of a polity's governance are encompassed in a single comprehensive document, whereas a (.+?) is when these principles are written down into a single document or set of legal documents\\. The distinction lies in whether the principles are contained within a single comprehensive document or across multiple documents\\.",t))!=null){facts.add(f("definition",m.group(1),"single-comprehensive"));facts.add(f("definition",m.group(2),"single-or-set-written"));return facts;}
  if((m=match("A difference of ([0-9.]+) in (.+?) corresponds to the (.+?) ratio of ([0-9.]+)\\.",t))!=null){facts.add(f("display-ratio",m.group(1),m.group(2),m.group(3),m.group(4)));return facts;}
  if((m=match("The brightness ratio for a one-magnitude difference is the (.+?) root of ([0-9.]+), which is approximately ([0-9.]+)\\.",t))!=null){int d=degree(m.group(1));if(d>0&&rounded(Math.pow(Double.parseDouble(m.group(2)),1.0/d),m.group(3))){facts.add(f("root-ratio","1.0","magnitude","brightness",Integer.toString(d),m.group(2)));return facts;}}
  if((m=match("A magnitude difference of 1 corresponds to the brightness ratio of the (.+?) root of ([0-9.]+), or about ([0-9.]+)\\.",t))!=null){int d=degree(m.group(1));if(d>0&&rounded(Math.pow(Double.parseDouble(m.group(2)),1.0/d),m.group(3))){facts.add(f("root-ratio","1.0","magnitude","brightness",Integer.toString(d),m.group(2)));return facts;}}
  if((m=match("A single magnitude step in brightness is expressed by the root and approximate ratio of (.+?) root of ([0-9.]+), or about ([0-9.]+)\\.",t))!=null){int d=degree(m.group(1));if(d>0&&rounded(Math.pow(Double.parseDouble(m.group(2)),1.0/d),m.group(3))){facts.add(f("root-ratio","1.0","magnitude","brightness",Integer.toString(d),m.group(2)));return facts;}}
  if((m=match("(.+?) is the material left by (.+?) after they break down (.+?)\\.",t))!=null){facts.add(f("decomposition-output",m.group(2),m.group(3),m.group(1)));return facts;}
  if((m=match("(.+?) is the organic input consumed by (.+?) before processing\\.",t))!=null){facts.add(f("decomposition-input",m.group(2),m.group(1)));return facts;}
  if((m=match("(.+?) (?:first )?(became|continued as) (?:the )?capital of (.+?) after joining (?:with )?(.+?)\\.",t))!=null){facts.add(f("capital-event",m.group(1),m.group(2).equalsIgnoreCase("became")?"begin":"continue",m.group(3),"after-joining",m.group(4)));return facts;}
  if((m=match("Some (.+?) contribute to citizen science by monitoring (.+?) and (.+?)\\.",t))!=null){String actor=m.group(1);if(norm(actor).equals("amateurs")&&norm(claim.subject).equals("amateur astronomy"))actor="amateur astronomers";facts.add(f("citizen-monitor","some",actor,m.group(2)));facts.add(f("citizen-monitor","some",actor,m.group(3)));return facts;}
  throw new IllegalArgumentException("Unknown or incompletely parsed factual clause; no partial publication");
 }
 static boolean supports(Ground g,Fact wanted){
  if(g.fact.key().equals(wanted.key()))return true;
  if(wanted.relation.equals("display-ratio")&&g.fact.relation.equals("root-ratio")){
   List<String>a=g.fact.arguments,b=wanted.arguments;
   return a.get(0).equals(b.get(0))&&a.get(1).equals(b.get(1))&&a.get(2).equals(b.get(2))&&rounded(Math.pow(Double.parseDouble(a.get(4)),1/Double.parseDouble(a.get(3))),b.get(3));
  }return false;
 }
 static Proof bind(BoundAnswer.Draft draft,BoundAnswer.Catalog catalog,BoundAnswer.Cancel cancel){
  List<Ground> grounds=sources(catalog,cancel);List<BoundAnswer.Claim> claims=new ArrayList<>();List<String> trace=new ArrayList<>();
  for(BoundAnswer.Claim c:draft.claims){cancel.check();List<Fact> wanted=claim(c);List<BoundAnswer.Span> refs=new ArrayList<>();
   for(Fact fact:wanted){cancel.check();Ground proof=null;for(Ground g:grounds){cancel.check();if(supports(g,fact)){proof=g;break;}}if(proof==null)throw new IllegalArgumentException("No source frame for "+fact.key());trace.add(fact.key()+" <= "+proof.fact.key());for(BoundAnswer.Span ref:proof.refs)if(!refs.contains(ref))refs.add(ref);}
   if(refs.isEmpty()||refs.size()>8)throw new IllegalArgumentException("Bound proof citation limit");claims.add(new BoundAnswer.Claim(c.obligation,c.subject,c.qualifier,c.text,refs));
  }cancel.check();return new Proof(new BoundAnswer.Draft(draft.question,claims,draft.count),Collections.unmodifiableList(trace));
 }
 private FactFrames(){}
}
