package org.pocketlore.app;
import java.util.*;

/** Experimental source-plan selection before prose; never semantic self-approval. */
final class SourcePlan {
 static final String SYSTEM="Select evidence for every numbered question obligation using ONLY the supplied source-grounded fact IDs. Preserve subject, input/output direction and time/conditions; do not invent an unstated link. Output exactly one line per obligation in this format: O1|F1,F2. Select at most eight fact IDs per obligation. If the available facts cannot answer an obligation, output W|O1|reason. No prose answer, heading or explanation outside this format. A selected fact is evidence, not permission to assert a false premise.";
 static final class Catalog {
  final BoundAnswer.Catalog sources;final Map<String,FactFrames.Ground> facts;
  Catalog(BoundAnswer.Catalog sources,BoundAnswer.Cancel cancel){this.sources=sources;Map<String,FactFrames.Ground> m=new LinkedHashMap<>();for(FactFrames.Ground g:FactFrames.sources(sources,cancel)){cancel.check();if(m.size()==32)break;m.put("F"+(m.size()+1),g);}facts=Collections.unmodifiableMap(m);}
 }
 static final class Plan {
  final String question;final Catalog catalog;final Map<Integer,List<FactFrames.Ground>> obligations;
  Plan(String question,Catalog catalog,Map<Integer,List<FactFrames.Ground>> obligations){this.question=question;this.catalog=catalog;this.obligations=Collections.unmodifiableMap(obligations);}
 }
 static String prompt(String question,Catalog c,BoundAnswer.Cancel cancel){
  StringBuilder b=new StringBuilder("Available source-grounded facts (relation and ordered arguments):\n");
  for(Map.Entry<String,FactFrames.Ground> e:c.facts.entrySet()){cancel.check();b.append(e.getKey()).append(" | ").append(e.getValue().fact.key()).append('\n');for(BoundAnswer.Span s:e.getValue().refs)b.append(s.label).append(" | ").append(s.source.title).append(" | ").append(s.source.date).append(" | ").append(s.text()).append('\n');}
  List<String> os=BoundAnswer.obligations(question);b.append("\nQuestion obligations:\n");for(int i=0;i<os.size();i++)b.append("O").append(i+1).append(": ").append(os.get(i)).append('\n');return b.toString();
 }
 static Plan parse(String question,String raw,int tokens,Catalog c,BoundAnswer.Cancel cancel){
  cancel.check();if(tokens<=0||tokens>=128||raw.length()>4000||c.facts.isEmpty())throw new IllegalArgumentException("Empty/truncated plan or unavailable source frames");
  int count=BoundAnswer.obligations(question).size();Map<Integer,List<FactFrames.Ground>> chosen=new LinkedHashMap<>();
  for(String row:raw.trim().split("\\n+")){cancel.check();String[] fields=row.trim().split("\\|",-1);if(fields.length==3&&fields[0].equals("W"))throw new IllegalArgumentException("Planner withheld an obligation");if(fields.length!=2||!fields[0].matches("O[1-4]"))throw new IllegalArgumentException("Malformed plan");int o=Integer.parseInt(fields[0].substring(1));if(o>count||chosen.containsKey(o))throw new IllegalArgumentException("Unknown/duplicate plan obligation");List<FactFrames.Ground> selected=new ArrayList<>();Set<String> seen=new HashSet<>();for(String id:fields[1].split(",")){id=id.trim();FactFrames.Ground g=c.facts.get(id);if(g==null||!seen.add(id))throw new IllegalArgumentException("Unknown/duplicate plan fact");selected.add(g);}if(selected.isEmpty()||selected.size()>8)throw new IllegalArgumentException("Plan fact limit");chosen.put(o,Collections.unmodifiableList(selected));}
  if(chosen.size()!=count)throw new IllegalArgumentException("Unplanned obligation");return new Plan(question,c,chosen);
 }
 static String prosePrompt(Plan p,BoundAnswer.Cancel cancel){
  StringBuilder b=new StringBuilder("Use only the selected evidence for each obligation. Write complete English claims, preserving conditions; do not copy fact tuples as prose.\n");List<String> os=BoundAnswer.obligations(p.question);
  for(Map.Entry<Integer,List<FactFrames.Ground>> e:p.obligations.entrySet()){cancel.check();b.append("\nO").append(e.getKey()).append(": ").append(os.get(e.getKey()-1)).append('\n');Set<BoundAnswer.Span> refs=new LinkedHashSet<>();for(FactFrames.Ground g:e.getValue()){b.append("Ground: ").append(g.fact.key()).append('\n');refs.addAll(g.refs);}for(BoundAnswer.Span s:refs)b.append(s.label).append(" | Subject: ").append(s.source.title).append(" | Date: ").append(s.source.date).append('\n').append(s.text()).append('\n');}return b.toString();
 }
 static BoundAnswer.Draft bind(Plan p,BoundAnswer.Draft draft,BoundAnswer.Cancel cancel){
  cancel.check();if(!p.question.equals(draft.question))throw new IllegalArgumentException("Plan/question mismatch");List<BoundAnswer.Claim> result=new ArrayList<>();
  for(BoundAnswer.Claim c:draft.claims){cancel.check();List<FactFrames.Ground> selected=p.obligations.get(c.obligation);if(selected==null)throw new IllegalArgumentException("No selected obligation");List<BoundAnswer.Span> refs=new ArrayList<>();for(FactFrames.Fact wanted:FactFrames.claim(c)){cancel.check();FactFrames.Ground proof=null;for(FactFrames.Ground g:selected)if(FactFrames.supports(g,wanted)){proof=g;break;}if(proof==null)throw new IllegalArgumentException("Claim not proved by selected plan: "+wanted.key());for(BoundAnswer.Span s:proof.refs)if(!refs.contains(s))refs.add(s);}if(refs.isEmpty()||refs.size()>8)throw new IllegalArgumentException("Plan proof span limit");result.add(new BoundAnswer.Claim(c.obligation,c.subject,c.qualifier,c.text,refs));}
  cancel.check();return new BoundAnswer.Draft(draft.question,result,draft.count);
 }
 private SourcePlan(){}
}
