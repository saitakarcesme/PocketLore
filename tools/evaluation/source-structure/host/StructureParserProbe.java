package org.pocketlore.app;
import java.nio.file.*;import java.nio.charset.StandardCharsets;import java.util.*;
public class StructureParserProbe {
 static String b(String s){return Base64.getEncoder().encodeToString(s.getBytes(StandardCharsets.UTF_8));}
 static String decode(String s){
  java.util.regex.Matcher m=SourceStructureParser.ENTITY.matcher(s);StringBuffer out=new StringBuffer();
  while(m.find()){
   String token=m.group(),value=token;
   switch(token){case "&amp;":value="&";break;case "&apos;":value="'";break;case "&lt;":value="<";break;case "&gt;":value=">";break;case "&quot;":value="\"";break;case "&nbsp;":value="\u00a0";break;default:
    if(token.startsWith("&#")){boolean hex=token.startsWith("&#x")||token.startsWith("&#X");int code=Integer.parseInt(token.substring(hex?3:2,token.length()-1),hex?16:10);value=new String(Character.toChars(code));}
   }
   m.appendReplacement(out,java.util.regex.Matcher.quoteReplacement(value));
  }m.appendTail(out);return out.toString();
 }

 public static void main(String[] args)throws Exception{String s=Files.readString(Path.of(args[0]));List<SourceStructureParser.Node> nodes=SourceStructureParser.parse(s,StructureParserProbe::decode,()->false);int id=0;for(SourceStructureParser.Node n:nodes){StringBuilder a=new StringBuilder();for(Map.Entry<String,String> e:n.attrs.entrySet())a.append(e.getKey()).append('=').append(e.getValue()==null?"<null>":e.getValue()).append('\n');System.out.println(++id+"\t"+n.parent+"\t"+b(n.tag)+"\t"+b(a.toString())+"\t"+n.start+"\t"+n.end+"\t"+b(n.text)+"\t"+n.kind);}try{SourceStructureParser.parse(s,StructureParserProbe::decode,()->true);throw new AssertionError("Cancellation accepted");}catch(java.io.InterruptedIOException expected){} }
}
