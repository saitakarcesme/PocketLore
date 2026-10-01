"""Conservative whole dependency structure identity, not general entailment."""
import json
class Unsupported(ValueError):pass
def canonical(sent):
 tokens=list(sent)
 if len(tokens)>512:raise Unsupported('sentence token limit')
 if any(t.pos_=='PRON' for t in tokens):raise Unsupported('unresolved pronoun')
 roots=[t for t in tokens if t.head==t]
 if len(roots)!=1:raise Unsupported('not one rooted sentence')
 def node(t,edge=None):
  children=list(t.children);passive=any(c.dep_=='nsubjpass' for c in children)
  agent=None
  if passive:
   agents=[c for c in children if c.dep_=='agent' and c.lemma_.lower()=='by']
   if len(agents)!=1 or len(list(agents[0].children))!=1:raise Unsupported('passive agent unresolved')
   agent=list(agents[0].children)[0]
   if agent.dep_!='pobj':raise Unsupported('passive agent shape')
  tense=set(t.morph.get('Tense')) if t.pos_ in ['VERB','AUX'] else set()
  for c in children:
   if c.dep_ in ['aux','auxpass']:tense.update(c.morph.get('Tense'))
  result=[]
  for c in children:
   if c.text in ['.',',']:continue
   if passive and c.dep_=='agent':result.append(node(agent,'nsubj'));continue
   if passive and c.dep_=='auxpass' and c.lemma_=='be':continue
   if c.dep_=='aux' and c.lemma_=='do':continue
   result.append(node(c,'dobj' if passive and c.dep_=='nsubjpass' else None))
  return [edge or t.dep_,t.lemma_.lower(),t.pos_,sorted(tense),t.morph.get('Number'),sorted(result,key=lambda x:json.dumps(x,sort_keys=True))]
 return node(roots[0],'ROOT')
def parse(nlp,text):
 doc=nlp(text);trees=[];errors=[]
 for s in doc.sents:
  try:trees.append(canonical(s))
  except Unsupported as e:errors.append(str(e))
 return {'trees':trees,'errors':errors,'tokens':[{'text':t.text,'lemma':t.lemma_,'pos':t.pos_,'dep':t.dep_,'head':t.head.i,'start':t.idx,'end':t.idx+len(t),'morph':str(t.morph)} for t in doc]}
def match(parsed,sources):
 if parsed['errors'] or not parsed['trees']:return None
 matches=[]
 for tree in parsed['trees']:
  found=next((i for i,s in enumerate(sources) if not s['errors'] and s['trees']==[tree]),None)
  if found is None:return None
  matches.append(found)
 return matches
