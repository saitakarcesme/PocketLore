package org.pocketlore.app;

import java.util.*;
import java.util.function.BooleanSupplier;

/** Bulk identity/rights admission into the existing typed controller, never semantic approval. */
final class ScaleAnswerAdapter {
 static final int MAX_SPAN=1200,MAX_CONTEXT=7200;
 static void require(boolean ok,String message){if(!ok)throw new IllegalArgumentException(message);}
 static void cancelled(BooleanSupplier c){if(c.getAsBoolean()||Thread.currentThread().isInterrupted())throw new java.util.concurrent.CancellationException("Bulk answer context cancelled");}
 static final class Snapshot {
  final String edition,shard,id,revision,recordHash,textHash,title,url,history,date,rights,exceptions,rawHash,rawScope,text;
  Snapshot(String[] f,String text){
   require(f.length==14,"Snapshot field count");for(String v:f)require(v!=null&&!v.isEmpty(),"Missing source provenance");
   edition=f[0];shard=f[1];id=f[2];revision=f[3];recordHash=f[4];textHash=f[5];title=f[6];url=f[7];history=f[8];date=f[9];rights=f[10];exceptions=f[11];rawHash=f[12];rawScope=f[13];this.text=text;
   for(String h:new String[]{edition,recordHash,textHash,rawHash})require(h.matches("[0-9a-f]{64}"),"Invalid source hash");
   require(BoundAnswer.sha(text).equals(textHash),"Incomplete preview or changed source text");
  }
  String key(){return edition+":"+shard+":"+id+":"+revision+":"+textHash;}
  String fingerprint(){StringBuilder b=new StringBuilder();for(String f:new String[]{edition,shard,id,revision,recordHash,textHash,title,url,history,date,rights,exceptions,rawHash,rawScope})b.append(f.length()).append(':').append(f);return BoundAnswer.sha(b.toString());}
 }
 static final class Review {
  final String snapshot,spanHash,rightsReceipt,fidelityReceipt;final int start,end;final boolean independentlyCleared;
  Review(String snapshot,int start,int end,String spanHash,String rightsReceipt,String fidelityReceipt,boolean approved){this.snapshot=snapshot;this.start=start;this.end=end;this.spanHash=spanHash;this.rightsReceipt=rightsReceipt;this.fidelityReceipt=fidelityReceipt;independentlyCleared=approved;}
 }
 static final class Ledger {
  // Loaded by trusted application packaging, never from source text, model output or imported data labels.
  private final Map<String,Review> reviews;
  Ledger(Map<String,Review> reviews){this.reviews=Collections.unmodifiableMap(new HashMap<>(reviews));}
  Review get(Snapshot s){return reviews.get(s.key());}
 }
 static final class Evidence {
  final Snapshot original;final int start,end;final BoundAnswer.Source source;
  private Evidence(Snapshot s,int start,int end){original=s;this.start=start;this.end=end;String text=s.text.substring(start,end);source=new BoundAnswer.Source(s.edition,s.shard+":"+s.id+":"+s.revision+":"+start+":"+end,s.textHash,BoundAnswer.sha(text),s.title,s.date,s.rights+"\n"+s.history+"\nExceptions: "+s.exceptions,text);}
 }
 static Evidence admit(Snapshot s,int start,int end,Ledger ledger,BooleanSupplier cancel){
  cancelled(cancel);Review r=ledger.get(s);
  require(r!=null&&r.independentlyCleared,"Source-specific independent rights/fidelity review unavailable");
  require(r.snapshot.equals(s.fingerprint()),"Review snapshot mismatch");
  require(r.rightsReceipt.matches("[0-9a-f]{64}")&&r.fidelityReceipt.matches("[0-9a-f]{64}"),"Missing independent review receipt");
  require(start==r.start&&end==r.end&&start>=0&&end>start&&end<=s.text.length()&&end-start<=MAX_SPAN,"Unreviewed or oversized span");
  require(!(start>0&&Character.isLowSurrogate(s.text.charAt(start)))&&!(end<s.text.length()&&Character.isLowSurrogate(s.text.charAt(end))),"Split UTF-16 surrogate");
  require(BoundAnswer.sha(s.text.substring(start,end)).equals(r.spanHash),"Reviewed span changed");
  cancelled(cancel);return new Evidence(s,start,end);
 }
 static final class Reference {
  final int obligation,start,end;final Snapshot source;final String sentenceLabel;
  Reference(int obligation,Evidence e,BoundAnswer.Span span){this.obligation=obligation;source=e.original;start=e.start+span.start;end=e.start+span.end;sentenceLabel=span.label;require(source.text.substring(start,end).equals(span.text()),"Original offset mismatch");}
 }
 static final class Prepared {
  final BoundAnswer.Catalog catalog;final String question;final List<Evidence> evidence;
  Prepared(String question,List<Evidence> evidence,BooleanSupplier cancel){
   cancelled(cancel);require(EvidenceAvailability.scope(question)==EvidenceAvailability.Scope.REFERENCE,"Requested evidence unavailable");
   BoundAnswer.obligations(question);require(!evidence.isEmpty()&&evidence.size()<=6,"No cleared bounded evidence");int chars=0;List<BoundAnswer.Source> sources=new ArrayList<>();for(Evidence e:evidence){cancelled(cancel);chars+=e.source.text.length();sources.add(e.source);}require(chars<=MAX_CONTEXT,"Context character budget");
   this.question=question;this.evidence=Collections.unmodifiableList(new ArrayList<>(evidence));catalog=new BoundAnswer.Catalog(sources,new BoundAnswer.Cancel());
  }
  Reference link(int obligation,String label,BooleanSupplier cancel){cancelled(cancel);require(obligation>=1&&obligation<=BoundAnswer.obligations(question).size(),"Unknown obligation");BoundAnswer.Span s=catalog.spans.get(label);require(s!=null,"Unknown typed source label (formula brackets are text)");for(Evidence e:evidence)if(e.source==s.source)return new Reference(obligation,e,s);throw new IllegalArgumentException("Source not admitted");}
  String prompt(BooleanSupplier cancel){cancelled(cancel);String p=BoundAnswer.prompt(question,catalog,new BoundAnswer.Cancel());cancelled(cancel);return p;}
  String publish(String draft,String modelAudit){throw new IllegalStateException("Independent whole-claim support and obligation coverage required; rights, quotes and self-audit cannot publish");}
 }
 private ScaleAnswerAdapter(){}
}
