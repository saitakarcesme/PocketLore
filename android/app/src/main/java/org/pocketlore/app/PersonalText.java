package org.pocketlore.app;
import java.io.*;import java.nio.*;import java.nio.charset.*;import java.util.*;import java.util.function.BooleanSupplier;
/** Strict local text parsing. Offsets always address the unchanged decoded UTF-16 text. */
final class PersonalText {
 static final int MAX_TEXT=500000,MAX_SEGMENTS=1000;
 static final class Span {final int start,end;final String location;Span(int a,int b,String l){start=a;end=b;location=l;}}
 static void check(BooleanSupplier cancel)throws IOException {if(cancel.getAsBoolean()||Thread.currentThread().isInterrupted())throw new InterruptedIOException("Document operation cancelled");}
 static void require(boolean b,String s)throws IOException{if(!b)throw new IOException(s);}
 static String decode(byte[] raw)throws IOException {String s=StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT).onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(raw)).toString();validate(s);return s;}
 static void validate(String s)throws IOException{require(!s.trim().isEmpty(),"Document has no searchable text");require(s.length()<=MAX_TEXT,"Extracted text exceeds500000 UTF-16 units");for(int i=0;i<s.length();i++){char c=s.charAt(i);require(c>=32||c=='\n'||c=='\r'||c=='\t',"Unsupported control character in text");if(Character.isHighSurrogate(c)){require(i+1<s.length()&&Character.isLowSurrogate(s.charAt(++i)),"Invalid Unicode surrogate");}else require(!Character.isLowSurrogate(c),"Invalid Unicode surrogate");}}
 static void add(List<Span> out,int a,int b,String location)throws IOException {require(out.size()<MAX_SEGMENTS,"Too many document passages");require(b>a&&b-a<=20000,"Document record exceeds20000 UTF-16 units");out.add(new Span(a,b,location));}
 static List<Span> plain(String s,BooleanSupplier cancel)throws IOException {List<Span> out=new ArrayList<>();for(int a=0;a<s.length();){check(cancel);int b=Math.min(s.length(),a+2000);if(b<s.length()){int newline=s.lastIndexOf('\n',b-1);if(newline>a)b=newline+1;if(Character.isLowSurrogate(s.charAt(b)))b--;}
 if(!s.substring(a,b).trim().isEmpty())add(out,a,b,"Text UTF-16 "+a+"–"+b);a=b;}return out;}
 static List<Span> csv(String s,BooleanSupplier cancel)throws IOException {
  List<Span> out=new ArrayList<>();int i=0,rowStart=0,fields=0,width=-1,row=1;List<String> headers=new ArrayList<>();
  while(i<s.length()) {check(cancel);StringBuilder value=new StringBuilder();
   if(s.charAt(i)=='"'){i++;boolean closed=false;while(i<s.length()){check(cancel);char c=s.charAt(i++);if(c=='"'){if(i<s.length()&&s.charAt(i)=='"'){value.append('"');i++;}else{closed=true;break;}}else value.append(c);}require(closed,"Unclosed quoted CSV field");require(i==s.length()||s.charAt(i)==','||s.charAt(i)=='\r'||s.charAt(i)=='\n',"Unexpected text after CSV quote");}
   else {while(i<s.length()&&s.charAt(i)!=','&&s.charAt(i)!='\r'&&s.charAt(i)!='\n'){require(s.charAt(i)!='"',"Quote inside unquoted CSV field");value.append(s.charAt(i++));}}
   fields++;if(row==1)headers.add(value.toString().replaceAll("[\\r\\n\\t]"," "));
   if(i<s.length()&&s.charAt(i)==','){i++;if(i<s.length())continue;fields++;if(row==1)headers.add("");}
   int end=i;if(i<s.length()&&s.charAt(i)=='\r'){i++;if(i<s.length()&&s.charAt(i)=='\n')i++;}else if(i<s.length()&&s.charAt(i)=='\n')i++;
   if(width<0)width=fields;require(fields==width,"CSV rows have inconsistent field counts");String label="CSV record "+row+"; "+fields+" fields; headers: "+String.join(" | ",headers);require(label.length()<=2000,"CSV headers too large");add(out,rowStart,end,label);rowStart=i;fields=0;row++;
  }return out;
 }
 static List<Span> json(String s,BooleanSupplier cancel)throws IOException {return new Json(s,cancel).parse();}
 static final class Json {
  final String s;final BooleanSupplier cancel;int i;final List<Span> out=new ArrayList<>();Json(String s,BooleanSupplier c){this.s=s;cancel=c;}
  void ws(){while(i<s.length()&&" \t\r\n".indexOf(s.charAt(i))>=0)i++;}
  void take(char c)throws IOException{ws();require(i<s.length()&&s.charAt(i++)==c,"Invalid JSON punctuation");}
  String string()throws IOException {take('"');StringBuilder b=new StringBuilder();while(i<s.length()){char c=s.charAt(i++);if(c=='"'){for(int j=0;j<b.length();j++){char u=b.charAt(j);if(Character.isHighSurrogate(u))require(j+1<b.length()&&Character.isLowSurrogate(b.charAt(++j)),"Invalid JSON Unicode surrogate");else require(!Character.isLowSurrogate(u),"Invalid JSON Unicode surrogate");}return b.toString();}require(c>=32,"Control character inside JSON string");if(c=='\\'){require(i<s.length(),"Incomplete JSON escape");char e=s.charAt(i++);if(e=='u'){require(i+4<=s.length(),"Incomplete JSON Unicode escape");require(s.substring(i,i+4).matches("[0-9a-fA-F]{4}"),"Invalid JSON Unicode escape");try{b.append((char)Integer.parseInt(s.substring(i,i+4),16));}catch(NumberFormatException x){throw new IOException("Invalid JSON Unicode escape");}i+=4;}else{int k="\"\\/bfnrt".indexOf(e);require(k>=0,"Invalid JSON escape");b.append(new char[]{'"','\\','/','\b','\f','\n','\r','\t'}[k]);}}else b.append(c);}throw new IOException("Unclosed JSON string");}
  void value(String path,int depth)throws IOException {check(cancel);require(depth<=32,"JSON nesting exceeds32");ws();require(i<s.length(),"Missing JSON value");int a=i;char c=s.charAt(i);
   if(c=='{'){i++;ws();Set<String> keys=new HashSet<>();if(i<s.length()&&s.charAt(i)=='}'){i++;return;}while(true){String key=string();require(keys.add(key),"Duplicate JSON key");take(':');value(path+"/"+key.replace("~","~0").replace("/","~1"),depth+1);ws();require(i<s.length(),"Unclosed JSON object");char e=s.charAt(i++);if(e=='}')return;require(e==',',"Invalid JSON object");}}
   else if(c=='['){i++;ws();if(i<s.length()&&s.charAt(i)==']'){i++;return;}int n=0;while(true){value(path+"/"+n++,depth+1);ws();require(i<s.length(),"Unclosed JSON array");char e=s.charAt(i++);if(e==']')return;require(e==',',"Invalid JSON array");}}
   else if(c=='"')string();else{while(i<s.length()&&",]} \r\n\t".indexOf(s.charAt(i))<0)i++;String token=s.substring(a,i);require(token.matches("true|false|null|-?(?:0|[1-9][0-9]*)(?:\\.[0-9]+)?(?:[eE][+-]?[0-9]+)?"),"Invalid JSON value");}
   require(path.length()<=1500,"JSON pointer too long");add(out,a,i,"JSON pointer "+(path.isEmpty()?"/":path.replace("\n","\\n").replace("\r","\\r").replace("\t","\\t").replace("\b","\\b").replace("\f","\\f")));
  }
  List<Span> parse()throws IOException{value("",0);ws();require(i==s.length(),"Trailing JSON content");require(!out.isEmpty(),"JSON contains no scalar text or values");return out;}
 }
}
