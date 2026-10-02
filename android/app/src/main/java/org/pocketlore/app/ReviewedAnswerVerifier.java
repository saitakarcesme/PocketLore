package org.pocketlore.app;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.*;
import java.util.function.BooleanSupplier;

/** Whole-output review binding, NOT an entailment engine. No production authority is provided. */
public final class ReviewedAnswerVerifier implements GroundedGeneration.Verifier {
    public interface Authority {
        /** Deployment qualification is external to the generator and to this structural validator. */
        boolean independentlyQualified();
        Review inspect(String binding, GeneralGroundedAnswer.Context context, String draft, BooleanSupplier stop);
    }
    public static final class SourceSpan {
        public final int source, start, end;
        public SourceSpan(int source,int start,int end){this.source=source;this.start=start;this.end=end;}
    }
    public static final class Region {
        public final int start,end;
        public final boolean factual,supported;
        public final List<SourceSpan> evidence;
        public Region(int start,int end,boolean factual,boolean supported,List<SourceSpan> evidence){
            this.start=start;this.end=end;this.factual=factual;this.supported=supported;
            this.evidence=Collections.unmodifiableList(new ArrayList<>(evidence));
        }
    }
    public static final class Review {
        public final String binding,reviewIdentity;
        public final boolean complete,absent;
        public final List<String> obligations;
        public final List<Region> regions;
        public Review(String binding,String identity,boolean complete,boolean absent,List<String> obligations,List<Region> regions){
            this.binding=binding;reviewIdentity=identity;this.complete=complete;this.absent=absent;
            this.obligations=Collections.unmodifiableList(new ArrayList<>(obligations));
            this.regions=Collections.unmodifiableList(new ArrayList<>(regions));
        }
    }
    private final Authority authority;
    public ReviewedAnswerVerifier(Authority authority){this.authority=authority;}
    public boolean qualified(){return authority!=null&&authority.independentlyQualified();}
    private static void check(BooleanSupplier stop){if(stop.getAsBoolean()||Thread.currentThread().isInterrupted())throw new java.util.concurrent.CancellationException();}
    /** Length-prefixed UTF8 binds exact bytes/order; no delimiter ambiguity or normalization. */
    public static String binding(GeneralGroundedAnswer.Context context,String draft){
        if(draft==null||draft.length()>16000)throw new IllegalArgumentException("Draft exceeds review admission");
        try{
            ByteArrayOutputStream bytes=new ByteArrayOutputStream();DataOutputStream out=new DataOutputStream(bytes);
            write(out,"PocketLore whole-output review v1");write(out,GeneralGroundedAnswer.SYSTEM);write(out,context.question);write(out,draft);
            out.writeInt(context.sources.size());long units=0;
            for(ResearchEngine.Passage p:context.sources){
                units+=p.text.length();if(units>12000)throw new IllegalArgumentException("Evidence exceeds review admission");
                for(String value:new String[]{p.id,p.title,p.url,p.sourceDate,p.license,p.text,p.collectionProvenance,p.offlineLicense})write(out,value);
            }
            byte[] digest=MessageDigest.getInstance("SHA-256").digest(bytes.toByteArray());StringBuilder hex=new StringBuilder();
            for(byte b:digest)hex.append(String.format(Locale.ROOT,"%02x",b&255));return hex.toString();
        }catch(IOException|java.security.NoSuchAlgorithmException e){throw new IllegalStateException(e);}
    }
    private static void write(DataOutputStream out,String value)throws IOException{
        if(value==null||value.length()>65536)throw new IllegalArgumentException("Missing or oversized review identity");
        for(int i=0;i<value.length();i++){
            char ch=value.charAt(i);
            if(Character.isHighSurrogate(ch)){if(i+1>=value.length()||!Character.isLowSurrogate(value.charAt(++i)))throw new IllegalArgumentException("Invalid UTF16 identity");}
            else if(Character.isLowSurrogate(ch))throw new IllegalArgumentException("Invalid UTF16 identity");
        }
        byte[] bytes=value.getBytes(StandardCharsets.UTF_8);out.writeInt(bytes.length);out.write(bytes);
    }
    private static boolean boundary(String text,int n){return n>=0&&n<=text.length()&&!(n>0&&n<text.length()&&Character.isHighSurrogate(text.charAt(n-1))&&Character.isLowSurrogate(text.charAt(n)));}
    private static boolean span(String text,int a,int b){return boundary(text,a)&&boundary(text,b)&&a<b&&!text.substring(a,b).trim().isEmpty();}
    public String rejection(GeneralGroundedAnswer.Context context,String draft,BooleanSupplier stop){
        check(stop);if(!qualified())return "Independent review authority unavailable";
        String hash=binding(context,draft);Review review=authority.inspect(hash,context,draft,stop);check(stop);
        if(review==null||!hash.equals(review.binding)||review.reviewIdentity==null||review.reviewIdentity.trim().isEmpty())return "Missing or stale whole-answer review";
        if(review.absent||!review.complete)return "Evidence absent or question obligations incomplete";
        if(review.obligations.isEmpty()||review.obligations.size()>32||review.regions.isEmpty()||review.regions.size()>64)return "Review coverage missing or exceeds admission";
        for(String obligation:review.obligations)if(obligation==null||obligation.trim().isEmpty()||obligation.length()>2048)return "Invalid reviewed obligation";
        int cursor=0,facts=0;
        for(Region region:review.regions){
            check(stop);
            if(!span(draft,region.start,region.end)||region.start<cursor)return "Invalid or overlapping UTF16 review region";
            if(!draft.substring(cursor,region.start).trim().isEmpty())return "Unreviewed output before region";
            if(!region.supported)return "Review rejects output region";
            if(region.factual){
                facts++;if(region.evidence.isEmpty()||region.evidence.size()>16)return "Factual region lacks bounded source evidence";
                for(SourceSpan link:region.evidence){
                    check(stop);if(link.source<0||link.source>=context.sources.size())return "Missing reviewed source";
                    ResearchEngine.Passage p=context.sources.get(link.source);
                    if(p.collectionProvenance.contains("Generation disabled:")||!span(p.text,link.start,link.end))return "Source scope or UTF16 evidence binding invalid";
                }
            }else if(!region.evidence.isEmpty())return "Nonfactual region cannot masquerade as cited evidence";
            cursor=region.end;
        }
        if(facts==0||!draft.substring(cursor).trim().isEmpty())return "No factual answer or unreviewed output tail";
        java.util.regex.Matcher citations=java.util.regex.Pattern.compile("\\[\\[S(\\d+)\\]\\]").matcher(draft);
        while(citations.find()){
            check(stop);int index;try{index=Integer.parseInt(citations.group(1))-1;}catch(NumberFormatException e){return "Invalid citation";}
            boolean bound=false;
            for(Region region:review.regions)if(region.start<=citations.start()&&region.end>=citations.end()){
                for(SourceSpan link:region.evidence)if(link.source==index)bound=true;
            }
            if(!bound)return "Visible citation differs from inspected source span or crosses review regions";
        }
        check(stop);return "";
    }
}
