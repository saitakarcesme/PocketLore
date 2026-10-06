package org.pocketlore.app;
import java.util.*;import java.util.function.*;import java.util.regex.*;import java.io.*;
/** Strict inert HTML tokenizer for validating the imported tree, not executing HTML. */
final class SourceStructureParser {
 static final class Node {int parent,start,end;String tag,text,kind;Map<String,String> attrs=new TreeMap<>();}
 static final Set<String> VOID=new HashSet<>(Arrays.asList("area","base","br","col","embed","hr","img","input","link","meta","param","source","track","wbr"));
 static final Set<String> UNSAFE=new HashSet<>(Arrays.asList("script","style","noscript","iframe","object","embed","svg","audio","video","head"));
 static final Pattern ENTITY=Pattern.compile("&(?:#[xX][0-9a-fA-F]+|#[0-9]+|[a-zA-Z][a-zA-Z0-9]+);");
 static void require(boolean b)throws IOException{if(!b)throw new IOException("Unsupported or inconsistent original HTML structure");}
 static List<Node> parse(String source,UnaryOperator<String> decode,BooleanSupplier cancelled)throws IOException{
  require(source.length()<=4000000);List<Node> nodes=new ArrayList<>();Deque<Integer> stack=new ArrayDeque<>();int pos=0;
  while(pos<source.length()){
   if(cancelled.getAsBoolean())throw new InterruptedIOException("Structure validation cancelled");require(nodes.size()<100000);
   boolean raw=!stack.isEmpty()&&(nodes.get(stack.peek()-1).tag.equals("script")||nodes.get(stack.peek()-1).tag.equals("style"));
   if(raw&&!source.regionMatches(true,pos,"</"+nodes.get(stack.peek()-1).tag,0,nodes.get(stack.peek()-1).tag.length()+2)){
    int end=source.toLowerCase(Locale.ROOT).indexOf("</"+nodes.get(stack.peek()-1).tag,pos);require(end>=0);text(nodes,stack,source,pos,end,decode,true,false);pos=end;continue;
   }
   if(source.startsWith("<!--",pos)){int end=source.indexOf("-->",pos+4);require(end>=0);pos=end+3;continue;}
   if(source.charAt(pos)=='<'){
    int end=pos+1;char quote=0;for(;end<source.length();end++){char c=source.charAt(end);if(quote!=0){if(c==quote)quote=0;}else if(c=='\''||c=='"')quote=c;else if(c=='>')break;}require(end<source.length());String token=source.substring(pos+1,end);
    if(token.startsWith("!")||token.startsWith("?")){pos=end+1;continue;}
    boolean closing=token.startsWith("/"),self=token.endsWith("/");String body=closing?token.substring(1):token;Matcher name=Pattern.compile("^([A-Za-z][A-Za-z0-9:-]*)").matcher(body);require(name.find());String tag=name.group(1).toLowerCase(Locale.ROOT);
    if(closing){require(body.substring(name.end()).trim().isEmpty()&&!stack.isEmpty()&&nodes.get(stack.peek()-1).tag.equals(tag));nodes.get(stack.pop()-1).end=end+1;}
    else {Node n=new Node();n.parent=stack.isEmpty()?0:stack.peek();n.start=pos;n.end=end+1;n.tag=tag;n.text="";n.kind="element";String rest=body.substring(name.end());if(self)rest=rest.substring(0,rest.length()-1);int a=0;
     while(a<rest.length()){while(a<rest.length()&&Character.isWhitespace(rest.charAt(a)))a++;if(a==rest.length())break;int start=a;while(a<rest.length()&&!Character.isWhitespace(rest.charAt(a))&&rest.charAt(a)!='=')a++;require(a>start);String key=rest.substring(start,a).toLowerCase(Locale.ROOT);while(a<rest.length()&&Character.isWhitespace(rest.charAt(a)))a++;String value=null;
      if(a<rest.length()&&rest.charAt(a)=='='){a++;while(a<rest.length()&&Character.isWhitespace(rest.charAt(a)))a++;require(a<rest.length());char q=rest.charAt(a);if(q=='\''||q=='"'){start=++a;while(a<rest.length()&&rest.charAt(a)!=q)a++;require(a<rest.length());value=rest.substring(start,a++);}else{start=a;while(a<rest.length()&&!Character.isWhitespace(rest.charAt(a)))a++;value=rest.substring(start,a);}value=decode.apply(value);}n.attrs.put(key,value);
     }nodes.add(n);if(!self&&!VOID.contains(tag)){require(stack.size()<64);stack.push(nodes.size());}}
    pos=end+1;
   }else {int end=source.indexOf('<',pos);if(end<0)end=source.length();boolean blocked=false;for(int id:stack)if(UNSAFE.contains(nodes.get(id-1).tag))blocked=true;text(nodes,stack,source,pos,end,decode,blocked,true);pos=end;}
  }require(stack.isEmpty());return nodes;
 }
 static void text(List<Node> nodes,Deque<Integer> stack,String s,int start,int end,UnaryOperator<String> decode,boolean blocked,boolean entities)throws IOException{
  Matcher m=ENTITY.matcher(s);m.region(start,end);int pos=start;while(entities&&m.find()){literal(nodes,stack,s,pos,m.start(),blocked);add(nodes,stack,m.start(),m.end(),blocked?"":decode.apply(m.group()),blocked?"omitted-unsafe":"entity");pos=m.end();}literal(nodes,stack,s,pos,end,blocked);
 }
 static void literal(List<Node> nodes,Deque<Integer> stack,String s,int start,int end,boolean blocked)throws IOException{while(start<end){int stop=Math.min(end,start+4096);if(stop<end&&Character.isLowSurrogate(s.charAt(stop)))stop--;add(nodes,stack,start,stop,blocked?"":s.substring(start,stop),blocked?"omitted-unsafe":"literal");start=stop;}}
 static void add(List<Node> nodes,Deque<Integer> stack,int start,int end,String text,String kind)throws IOException{require(nodes.size()<100000);Node n=new Node();n.parent=stack.isEmpty()?0:stack.peek();n.start=start;n.end=end;n.tag="#text";n.text=text;n.kind=kind;nodes.add(n);}
}
