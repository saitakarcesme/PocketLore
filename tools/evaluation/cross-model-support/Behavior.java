package org.pocketlore.app;
/** Parser failures are not semantic proof; these controls only enforce declared transport admission. */
public final class Behavior {
 static void eq(CrossModelSupport.Decision actual,CrossModelSupport.Decision expected){if(actual!=expected)throw new AssertionError(actual+" != "+expected);}
 public static void main(String[] args){
  eq(CrossModelSupport.decision("VERDICT: SUPPORTED_COMPLETE\nReasons: test",20,512),CrossModelSupport.Decision.SUPPORTED_COMPLETE);
  eq(CrossModelSupport.decision("VERDICT: REJECT\nReasons: tail unsupported",20,512),CrossModelSupport.Decision.REJECT);
  eq(CrossModelSupport.decision("VERDICT: ABSENT",20,512),CrossModelSupport.Decision.ABSENT);
  eq(CrossModelSupport.decision("VERDICT: SUPPORTED_COMPLETE",512,512),CrossModelSupport.Decision.INVALID);
  eq(CrossModelSupport.decision("VERDICT: SUPPORTED_COMPLETE",-1,512),CrossModelSupport.Decision.INVALID);
  eq(CrossModelSupport.decision("I think it is supported",20,512),CrossModelSupport.Decision.INVALID);
  eq(CrossModelSupport.decision("VERDICT: SUPPORTED_COMPLETE or REJECT",20,512),CrossModelSupport.Decision.INVALID);
  eq(CrossModelSupport.decision("VERDICT: SUPPORTED_COMPLETE",0,512),CrossModelSupport.Decision.INVALID);
  eq(CrossModelSupport.decision(null,20,512),CrossModelSupport.Decision.INVALID);
  eq(CrossModelSupport.decision("VERDICT: SUPPORTED_COMPLETE",20,512,"native error"),CrossModelSupport.Decision.INVALID);
  eq(CrossModelSupport.decision("VERDICT: SUPPORTED_COMPLETE",20,512,null),CrossModelSupport.Decision.INVALID);
  if(args.length==1)try {
   for(String line:java.nio.file.Files.readAllLines(java.nio.file.Path.of(args[0]))){
    String[] f=line.split("\\t",-1);
    eq(CrossModelSupport.decision(new String(java.util.Base64.getDecoder().decode(f[0]),java.nio.charset.StandardCharsets.UTF_8),Integer.parseInt(f[1]),512,f[2]),CrossModelSupport.Decision.valueOf(f[3]));
   }
  }catch(java.io.IOException e){throw new AssertionError(e);}
  System.out.println("PASS: 11 verdict/transport controls; no entailment or completeness qualification");
 }
}
