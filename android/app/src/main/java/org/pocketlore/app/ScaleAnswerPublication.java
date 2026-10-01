package org.pocketlore.app;

import java.util.*;
import java.util.function.BooleanSupplier;

/** Exact-output review transport, not an entailment classifier or a model self-audit. */
final class ScaleAnswerPublication {
 static void field(StringBuilder b,String name,String value){b.append(name).append(':').append(value.length()).append(':').append(value).append('\n');}
 static final class Citation {
  final int start,end;final List<ScaleAnswerAdapter.Reference> references;
  Citation(int start,int end,List<ScaleAnswerAdapter.Reference> refs){this.start=start;this.end=end;references=Collections.unmodifiableList(new ArrayList<>(refs));}
 }
 static final class Candidate {
  final String text,fingerprint,reviewPacket;final int claimCount,obligationCount;final List<Citation> citations;
  private Candidate(String text,String packet,int claims,int obligations,List<Citation> citations){this.text=text;reviewPacket=packet;fingerprint=BoundAnswer.sha(packet);claimCount=claims;obligationCount=obligations;this.citations=Collections.unmodifiableList(new ArrayList<>(citations));}
 }
 static Candidate prepare(ScaleAnswerAdapter.Prepared prepared,String raw,int tokens,BooleanSupplier cancel){
  ScaleAnswerAdapter.cancelled(cancel);
  BoundAnswer.Draft draft=BoundAnswer.parse(prepared.question,raw,prepared.catalog,tokens,new BoundAnswer.Cancel());
  StringBuilder rendered=new StringBuilder(),packet=new StringBuilder();List<Citation> links=new ArrayList<>();
  field(packet,"protocol","scale-answer-publication-v1");field(packet,"question",prepared.question);field(packet,"raw",raw);field(packet,"tokens",Integer.toString(tokens));
  List<String> obligations=BoundAnswer.obligations(prepared.question);for(int i=0;i<obligations.size();i++)field(packet,"obligation-"+(i+1),obligations.get(i));
  int ordinal=0;
  for(BoundAnswer.Claim claim:draft.claims){
   ScaleAnswerAdapter.cancelled(cancel);ordinal++;
   // Metadata stays visible; it does not repair unsupported prose and is itself reviewed.
   rendered.append("Subject: ").append(claim.subject).append("\nScope: ").append(claim.qualifier).append('\n').append(claim.text).append(' ');
   int start=rendered.length();rendered.append('[').append(ordinal).append(']');int end=rendered.length();rendered.append('\n');
   field(packet,"claim-"+ordinal,claim.text);field(packet,"subject-"+ordinal,claim.subject);field(packet,"scope-"+ordinal,claim.qualifier);field(packet,"claim-obligation-"+ordinal,Integer.toString(claim.obligation));
   List<ScaleAnswerAdapter.Reference> refs=new ArrayList<>();
   for(BoundAnswer.Span span:claim.references){
    ScaleAnswerAdapter.Reference ref=prepared.link(claim.obligation,span.label,cancel);refs.add(ref);
    field(packet,"source-identity",ref.source.fingerprint());field(packet,"source-key",ref.source.key());
    field(packet,"source-title",ref.source.title);field(packet,"source-date",ref.source.date);field(packet,"source-rights",ref.source.rights);field(packet,"source-history",ref.source.history);field(packet,"source-exceptions",ref.source.exceptions);
    field(packet,"source-label",ref.sentenceLabel);field(packet,"source-start-utf16",Integer.toString(ref.start));field(packet,"source-end-utf16",Integer.toString(ref.end));field(packet,"source-excerpt",ref.source.text.substring(ref.start,ref.end));
   }
   links.add(new Citation(start,end,refs));
  }
  String text=rendered.toString();field(packet,"rendered",text);ScaleAnswerAdapter.cancelled(cancel);
  return new Candidate(text,packet.toString(),draft.claims.size(),draft.count,links);
 }
 static final class Permit {
  final String fingerprint,receiptHash,reviewer;final List<Boolean> claims,obligations;final boolean independent;
  Permit(String fingerprint,String receiptHash,String reviewer,boolean independent,List<Boolean> claims,List<Boolean> obligations){this.fingerprint=fingerprint;this.receiptHash=receiptHash;this.reviewer=reviewer;this.independent=independent;this.claims=Collections.unmodifiableList(new ArrayList<>(claims));this.obligations=Collections.unmodifiableList(new ArrayList<>(obligations));}
 }
 static final class Reviews {
  private final Map<String,Permit> permits;
  Reviews(Map<String,Permit> permits){this.permits=Collections.unmodifiableMap(new HashMap<>(permits));}
 }
 static Candidate publish(Candidate candidate,Reviews reviews,BooleanSupplier cancel){
  ScaleAnswerAdapter.cancelled(cancel);Permit p=reviews.permits.get(candidate.fingerprint);
  ScaleAnswerAdapter.require(p!=null&&p.independent,"Independent exact-output review unavailable");
  ScaleAnswerAdapter.require(p.fingerprint.equals(candidate.fingerprint)&&p.receiptHash.matches("[0-9a-f]{64}")&&p.reviewer!=null&&!p.reviewer.trim().isEmpty(),"Incomplete review identity");
  ScaleAnswerAdapter.require(p.claims.size()==candidate.claimCount&&p.obligations.size()==candidate.obligationCount,"Incomplete whole-answer review");
  for(Boolean supported:p.claims)ScaleAnswerAdapter.require(Boolean.TRUE.equals(supported),"Unsupported or unreviewed claim");
  for(Boolean complete:p.obligations)ScaleAnswerAdapter.require(Boolean.TRUE.equals(complete),"Incomplete or unreviewed obligation");
  ScaleAnswerAdapter.cancelled(cancel);return candidate;
 }
 private ScaleAnswerPublication(){}
}
