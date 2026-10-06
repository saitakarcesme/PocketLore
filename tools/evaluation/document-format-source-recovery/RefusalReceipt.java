package org.pocketlore.app;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.*;
/** Lossless nullable Throwable fields, bounded independently of parser acceptance predicates. */
final class RefusalReceipt {
 private static String quoted(String value)throws IOException{
  if(value==null)return "null";
  if(value.length()>4096)throw new IOException("Refusal receipt message exceeds bound");
  StringBuilder out=new StringBuilder();out.append('"');
  final char[] hex="0123456789abcdef".toCharArray();
  for(int i=0;i<value.length();i++){
   char c=value.charAt(i);
   if(c=='"'||c=='\\')out.append('\\').append(c);
   else if(c<32||c>126){out.append("\\u");for(int shift=12;shift>=0;shift-=4)out.append(hex[(c>>shift)&15]);}
   else out.append(c);
  }
  return out.append('"').toString();
 }
 static String encode(Throwable original)throws IOException{
  if(original==null)throw new IOException("Missing actual refusal");
  StringBuilder out=new StringBuilder("{\"schema\":\"actual-exception-v1\",\"causes\":[");
  Set<Throwable> seen=Collections.newSetFromMap(new IdentityHashMap<Throwable,Boolean>());
  Throwable current=original;int count=0;String termination="end";
  while(current!=null){
   if(seen.contains(current)){termination="cycle";break;}
   if(count==8){termination="depth";break;}
   seen.add(current);if(count++>0)out.append(',');
   out.append("{\"class\":").append(quoted(current.getClass().getName())).append(",\"message\":").append(quoted(current.getMessage())).append('}');
   current=current.getCause();
  }
  out.append("],\"termination\":").append(quoted(termination)).append('}');
  return Base64.getEncoder().encodeToString(out.toString().getBytes(StandardCharsets.US_ASCII));
 }
 private RefusalReceipt(){}
}
