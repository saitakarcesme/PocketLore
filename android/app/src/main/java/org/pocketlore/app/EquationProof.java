package org.pocketlore.app;
import java.util.*;import java.util.regex.*;
/** Compositional finite mathematical language. No whole-answer patterns or text rewriting. */
final class EquationProof {
 static final class Term {final int degree;final double radicand;final String decimal;Term(int d,double r,String n){degree=d;radicand=r;decimal=n;}double value(){return degree==0?Double.parseDouble(decimal):Math.pow(radicand,1.0/degree);}}
 static final class Compiler {
  final List<String> words=new ArrayList<>();final FactFrames.Ground ground;final List<String> args;final BoundAnswer.Cancel cancel;int pos;
  Compiler(String text,FactFrames.Ground g,BoundAnswer.Cancel cancel){ground=g;args=g.fact.arguments;this.cancel=cancel;Matcher m=Pattern.compile("[A-Za-z]+|[0-9]+(?:\\.[0-9]+)?(?:st|nd|rd|th)?|[.,-]").matcher(text.toLowerCase(Locale.ROOT));int end=0;while(m.find()){if(!text.substring(end,m.start()).trim().isEmpty())fail();words.add(m.group());end=m.end();}if(!text.substring(end).trim().isEmpty())fail();if(words.size()>240)fail();}
  void fail(){throw new IllegalArgumentException("Unproved mathematical clause");}boolean eat(String s){cancel.check();if(pos<words.size()&&words.get(pos).equals(s)){pos++;return true;}return false;}void need(String s){if(!eat(s))fail();}String take(){cancel.check();if(pos==words.size())fail();return words.get(pos++);}void article(){if(!eat("the")&&!eat("a"))eat("an");}
  boolean phrase(String s){int save=pos;for(String w:s.split(" "))if(!eat(w)){pos=save;return false;}return true;}
  double number(){String s=take();List<String> names=Arrays.asList("zero","one","two","three","four","five","six","seven","eight","nine","ten","eleven","twelve","thirteen","fourteen","fifteen","sixteen");int n=names.indexOf(s);if(n>=0)return n;try{double x=Double.parseDouble(s);if(!Double.isFinite(x)||x<0||x>1e12)fail();return x;}catch(NumberFormatException e){fail();return 0;}}
  void dimension(){String name=args.get(1);if(phrase(name))return;for(BoundAnswer.Span s:ground.refs)if(s.source.title.toLowerCase(Locale.ROOT).endsWith(name)&&phrase(s.source.title.toLowerCase(Locale.ROOT)))return;fail();}
  int ordinal(String s){List<String> names=Arrays.asList("","","square","cube","fourth","fifth","sixth","seventh","eighth","ninth","tenth","eleventh","twelfth","thirteenth","fourteenth","fifteenth","sixteenth");if(s.equals("third"))return 3;int i=names.indexOf(s);if(i>=2)return i;try{return Integer.parseInt(s.replaceFirst("(st|nd|rd|th)$",""));}catch(NumberFormatException e){return -1;}}
  Term term(){article();int save=pos;String word=take();int degree=ordinal(word);if(degree>=2&&degree<=16&&eat("root")){need("of");double r=number();if(r<=0)fail();Term t=new Term(degree,r,null);if(degree!=Integer.parseInt(args.get(3))||r!=Double.parseDouble(args.get(4)))fail();return t;}pos=save;String display=take();try{double n=Double.parseDouble(display);if(!Double.isFinite(n)||n<0||n>1e12)fail();}catch(NumberFormatException e){fail();}return new Term(0,0,display);}
  void step(){double value=number();if(value!=Double.parseDouble(args.get(0)))fail();}
  void ratio(boolean requireStep){article();if(!phrase(args.get(2)))fail();need("ratio");if(requireStep){need("for");article();step();need("-");dimension();need("difference");need("in");dimension();}}
  void equal(Term a,Term b,boolean approximate){if(a.degree==0&&b.degree==0)fail();Term exact=a.degree!=0?a:b;Term shown=a.degree==0?a:b;if(shown.degree!=0){if(exact.degree!=shown.degree||exact.radicand!=shown.radicand)fail();}else if(approximate){if(!FactFrames.rounded(exact.value(),shown.decimal))fail();}else if(Math.abs(exact.value()-shown.value())>1e-12)fail();}
  void valueOfRatio(Term term){if(term.degree!=0)return;if(!FactFrames.rounded(Math.pow(Double.parseDouble(args.get(4)),1.0/Double.parseDouble(args.get(3))),term.decimal))fail();}
  void predicate(Term subject){
   if(eat("represents")){valueOfRatio(subject);ratio(true);return;}
   need("is");if(eat("used")){if(subject.degree==0)fail();need("to");need("calculate");ratio(true);return;}
   boolean approx=eat("approximately");Term object=term();equal(subject,object,approx);relative(object.degree==0?subject:object);
  }
  void relative(Term antecedent){if(eat(",")){need("which");predicate(antecedent);}}
  void sentence(){int save=pos;article();if(eat("difference")){need("of");step();need("in");dimension();need("corresponds");need("to");ratio(false);need("of");Term t=term();valueOfRatio(t);relative(t);}else{pos=save;predicate(term());}need(".");}
  void compile(){if(words.isEmpty())fail();while(pos<words.size())sentence();}
 }
 static List<BoundAnswer.Span> prove(String text,List<FactFrames.Ground> grounds,BoundAnswer.Cancel cancel){
  for(FactFrames.Ground g:grounds){cancel.check();if(!g.fact.relation.equals("root-ratio"))continue;try{new Compiler(text,g,cancel).compile();return g.refs;}catch(IllegalArgumentException e){/* Another independently grounded equation may match. */}}
  throw new IllegalArgumentException("Complete mathematical semantics not proved by selected source plan");
 }
 private EquationProof(){}
}
