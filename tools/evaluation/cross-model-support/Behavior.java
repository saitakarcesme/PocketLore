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
  eq(CrossModelSupport.decision(null,20,512),CrossModelSupport.Decision.INVALID);
  System.out.println("PASS: 8 verdict/transport controls; no entailment or completeness qualification");
 }
}
