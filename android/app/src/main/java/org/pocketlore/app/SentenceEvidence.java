package org.pocketlore.app;
import java.util.*;
/** Lossless within the existing bounded catalog; sentence presence is not entailment. */
final class SentenceEvidence {
 final BoundAnswer.Catalog catalog;final Map<String,BoundAnswer.Span> sentences;
 SentenceEvidence(BoundAnswer.Catalog catalog,BoundAnswer.Cancel cancel){this.catalog=catalog;Map<String,BoundAnswer.Span> all=new LinkedHashMap<>();for(BoundAnswer.Span span:catalog.spans.values()){cancel.check();if(all.size()>=64)throw new IllegalArgumentException("Sentence evidence limit; no silent omission");all.put("S"+(all.size()+1),span);}sentences=Collections.unmodifiableMap(all);}
 List<BoundAnswer.Span> select(String ids,BoundAnswer.Cancel cancel){List<BoundAnswer.Span> refs=new ArrayList<>();Set<String> seen=new HashSet<>();for(String id:ids.split(",",-1)){cancel.check();id=id.trim();if(!id.matches("S[1-9][0-9]*")||!seen.add(id)||!sentences.containsKey(id))throw new IllegalArgumentException("Unknown/duplicate sentence plan ID");refs.add(sentences.get(id));}if(refs.isEmpty()||refs.size()>8)throw new IllegalArgumentException("Selected sentence limit");return Collections.unmodifiableList(refs);}
}
