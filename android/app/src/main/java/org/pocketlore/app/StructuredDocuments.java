package org.pocketlore.app;

import java.io.*;
import java.nio.charset.*;
import java.nio.ByteBuffer;
import java.util.*;
import java.util.function.BooleanSupplier;
import java.util.zip.*;
import javax.xml.parsers.SAXParserFactory;
import org.xml.sax.*;
import org.xml.sax.ext.DefaultHandler2;

/** Bounded offline projection, never an XML byte-offset map or a layout renderer. */
final class StructuredDocuments {
 static final String VERSION="PocketLore structured personal extractor v1";
 static final int INPUT=4194304,ENTRIES=256,ENTRY=2097152,EXPANDED=16777216,RATIO=100,DEPTH=64,NODES=100000;
 static final String W="http://schemas.openxmlformats.org/wordprocessingml/2006/main", A="http://schemas.openxmlformats.org/drawingml/2006/main", P="http://schemas.openxmlformats.org/presentationml/2006/main", R="http://schemas.openxmlformats.org/officeDocument/2006/relationships", REL="http://schemas.openxmlformats.org/package/2006/relationships", OFFICE="urn:oasis:names:tc:opendocument:xmlns:office:1.0", TEXT="urn:oasis:names:tc:opendocument:xmlns:text:1.0", DRAW="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0";
 static boolean supports(String f){return Arrays.asList("docx","pptx","odt","odp","epub","html","htm").contains(f);}
 static final class Budget implements BooleanSupplier {
  final BooleanSupplier caller;final long start=System.nanoTime();Budget(BooleanSupplier c){caller=c;}
  public boolean getAsBoolean(){return caller.getAsBoolean()||Thread.currentThread().isInterrupted()||System.nanoTime()-start>=20_000_000_000L;}
  void check()throws IOException{PersonalText.check(this);}
 }
 static final class Result {final String text;final List<PersonalText.Span> spans;Result(String t,List<PersonalText.Span>s){text=t;spans=s;}}
 static final class Output {
  final StringBuilder text=new StringBuilder();final List<PersonalText.Span> spans=new ArrayList<>();final Budget budget;
  Output(Budget b){budget=b;}
  void add(String value,String location)throws IOException{budget.check();value=value.trim();if(value.isEmpty())return;PersonalText.require(value.length()<=20000,"Document paragraph exceeds limit");if(text.length()>0)text.append('\n');int start=text.length();text.append(value);PersonalText.require(text.length()<=PersonalText.MAX_TEXT,"Extracted text exceeds limit");PersonalText.add(spans,start,text.length(),location);}
  Result finish()throws IOException{budget.check();PersonalText.validate(text.toString());PersonalText.require(!spans.isEmpty(),"Empty or image-only document; OCR is not performed");return new Result(text.toString(),spans);}
 }
 static final class Node {
  final String ns,name;final Map<String,String> attrs=new LinkedHashMap<>();final List<Object> children=new ArrayList<>();
  Node(String ns,String name){this.ns=ns;this.name=name;}
  boolean is(String u,String n){return ns.equals(u)&&name.equals(n);}
  String attr(String name){return attrs.getOrDefault(name,"");}
  String attr(String ns,String name){return attrs.getOrDefault("{"+ns+"}"+name,"");}
 }
 static Node xml(byte[] bytes,Budget budget)throws Exception {
  PersonalText.require(bytes.length<=ENTRY,"XML entry exceeds limit");budget.check();
  SAXParserFactory factory=SAXParserFactory.newInstance();factory.setNamespaceAware(true);factory.setValidating(false);
  XMLReader reader=factory.newSAXParser().getXMLReader();reader.setFeature("http://xml.org/sax/features/external-general-entities",false);reader.setFeature("http://xml.org/sax/features/external-parameter-entities",false);
  final Deque<Node> stack=new ArrayDeque<>();final Node[] root={null};final int[] count={0};
  DefaultHandler2 handler=new DefaultHandler2(){
   void guard()throws SAXException{try{budget.check();}catch(IOException e){throw new SAXException(e);}}
   public void startDTD(String n,String p,String s)throws SAXException{throw new SAXException("DTDs and entities are forbidden");}
   public InputSource resolveEntity(String p,String s)throws SAXException{throw new SAXException("External XML resource forbidden");}
   public void skippedEntity(String n)throws SAXException{throw new SAXException("Unresolved entity");}
   public void warning(SAXParseException e)throws SAXException{throw e;}public void error(SAXParseException e)throws SAXException{throw e;}public void fatalError(SAXParseException e)throws SAXException{throw e;}
   public void startElement(String ns,String local,String q,Attributes a)throws SAXException{guard();if(stack.size()>=DEPTH||++count[0]>NODES||a.getLength()>64)throw new SAXException("XML structure exceeds limits");Node n=new Node(ns,local);for(int i=0;i<a.getLength();i++)n.attrs.put(a.getURI(i).isEmpty()?a.getLocalName(i):"{"+a.getURI(i)+"}"+a.getLocalName(i),a.getValue(i));if(stack.isEmpty()){if(root[0]!=null)throw new SAXException("Multiple XML roots");root[0]=n;}else stack.peek().children.add(n);stack.push(n);}
   public void characters(char[] c,int a,int n)throws SAXException{guard();if(!stack.isEmpty())stack.peek().children.add(new String(c,a,n));}
   public void endElement(String u,String l,String q)throws SAXException{guard();stack.pop();}
  };
  reader.setContentHandler(handler);reader.setErrorHandler(handler);reader.setEntityResolver(handler);reader.setProperty("http://xml.org/sax/properties/lexical-handler",handler);
  try(InputStream in=new ByteArrayInputStream(bytes)){reader.parse(new InputSource(new FilterInputStream(in){public int read(byte[] b,int o,int n)throws IOException{budget.check();return super.read(b,o,Math.min(n,8192));}public int read()throws IOException{budget.check();return super.read();}}));}
  budget.check();PersonalText.require(root[0]!=null,"Empty XML");return root[0];
 }
 static List<Node> nodes(Node root,String ns,String name){List<Node> result=new ArrayList<>();collect(root,ns,name,result);return result;}
 static void collect(Node n,String ns,String name,List<Node> result){if(n.is(ns,name))result.add(n);for(Object c:n.children)if(c instanceof Node)collect((Node)c,ns,name,result);}
 static Node one(Node root,String ns,String name)throws IOException{List<Node> a=nodes(root,ns,name);PersonalText.require(a.size()==1,"Missing or ambiguous "+name);return a.get(0);}
 static String path(String value)throws IOException {PersonalText.require(!value.isEmpty()&&value.length()<=512&&!value.startsWith("/")&&!value.contains("\\")&&!value.contains(":")&&!value.contains("%")&&!value.contains("\u0000"),"Unsafe archive path");for(String part:value.split("/",-1))PersonalText.require(!part.equals("..")&&!part.equals(".")&&!part.isEmpty(),"Unsafe archive path");return value;}
 static String target(String base,String relative)throws IOException {
  PersonalText.require(!relative.isEmpty()&&!relative.contains(":")&&!relative.startsWith("/")&&!relative.contains("\\")&&!relative.contains("%")&&!relative.contains("#")&&!relative.contains("?"),"External or unsupported document relationship");
  Deque<String> parts=new ArrayDeque<>();int slash=base.lastIndexOf('/');if(slash>=0)parts.addAll(Arrays.asList(base.substring(0,slash).split("/")));
  for(String part:relative.split("/",-1)){if(part.equals("..")){PersonalText.require(!parts.isEmpty(),"Relationship escapes archive");parts.removeLast();}else if(!part.equals(".")){PersonalText.require(!part.isEmpty(),"Empty relationship segment");parts.add(part);}}
  return path(String.join("/",parts));
 }
 static Map<String,byte[]> unzip(byte[] raw,File cache,Budget budget)throws Exception {
  PersonalText.require(raw.length<=INPUT&&raw.length>=4&&raw[0]=='P'&&raw[1]=='K'&&raw[2]==3&&raw[3]==4,"Expected unencrypted document ZIP");Map<String,byte[]> files=new LinkedHashMap<>();Map<String,Long> crc=new HashMap<>();Map<String,Integer> methods=new HashMap<>();Map<String,Long> sizes=new HashMap<>();int total=0;Map<String,byte[]> streamed=new LinkedHashMap<>();
  try(ZipInputStream zip=new ZipInputStream(new ByteArrayInputStream(raw))){ZipEntry e;Set<String> names=new HashSet<>();while((e=zip.getNextEntry())!=null){budget.check();PersonalText.require(names.size()<ENTRIES,"Too many ZIP entries");String name=e.getName();if(e.isDirectory())name=name.substring(0,name.length()-1);path(name);PersonalText.require(names.add(name),"Duplicate ZIP path");PersonalText.require(e.getMethod()==0||e.getMethod()==8,"Unsupported ZIP compression");byte[] b=DocumentBytes.read(zip,ENTRY,budget);total+=b.length;PersonalText.require(total<=EXPANDED,"ZIP expanded aggregate exceeds limit");zip.closeEntry();long compressed=e.getCompressedSize();PersonalText.require(compressed>=0&&compressed<=raw.length&&(long)b.length<=Math.max(1,compressed)*RATIO,"ZIP compression ratio exceeds limit");CRC32 c=new CRC32();c.update(b);PersonalText.require(e.getCrc()==c.getValue(),"ZIP CRC mismatch");streamed.put(e.getName(),b);if(!e.isDirectory()){files.put(name,b);crc.put(name,c.getValue());methods.put(name,e.getMethod());sizes.put(name,compressed);}else PersonalText.require(b.length==0,"Nonempty directory entry");}}
  // No duplicate staging archive: independent structure and payload verification over original bytes.
  DocumentZip.verify(raw,streamed,budget);
  for(Map.Entry<String,byte[]> entry:files.entrySet()){String name=entry.getKey().toLowerCase(Locale.ROOT);if(name.endsWith(".xml")||name.endsWith(".rels")||name.endsWith(".opf")||name.endsWith(".xhtml"))xml(entry.getValue(),budget);}
  budget.check();return files;
 }
 static byte[] required(Map<String,byte[]> files,String name)throws IOException{byte[] b=files.get(name);PersonalText.require(b!=null,"Missing document part: "+name);return b;}
 static Node part(Map<String,byte[]> files,String name,Budget b)throws Exception{return xml(required(files,name),b);}
 static Map<String,Node> relationships(Node root)throws IOException{PersonalText.require(root.is(REL,"Relationships"),"Invalid relationships root");Map<String,Node> out=new HashMap<>();for(Node n:nodes(root,REL,"Relationship"))PersonalText.require(!n.attr("Id").isEmpty()&&out.put(n.attr("Id"),n)==null,"Duplicate relationship ID");return out;}
 static String resolve(Map<String,Node> rel,String id,String base,String type)throws IOException{Node n=rel.get(id);PersonalText.require(n!=null&&n.attr("Type").equals(R+"/"+type)&&!n.attr("TargetMode").equals("External"),"Missing or external content relationship");return target(base,n.attr("Target"));}
 static String rootPart(Map<String,byte[]> files,Budget b)throws Exception{Map<String,Node> rel=relationships(part(files,"_rels/.rels",b));String id=null;for(Map.Entry<String,Node> e:rel.entrySet())if(e.getValue().attr("Type").equals(R+"/officeDocument")){PersonalText.require(id==null,"Ambiguous office document");id=e.getKey();}return resolve(rel,id,"","officeDocument");}
 static String relPath(String name){int slash=name.lastIndexOf('/');return (slash<0?"":name.substring(0,slash+1))+"_rels/"+name.substring(slash+1)+".rels";}
 static void officeType(Map<String,byte[]> files,String main,String mime,Budget b)throws Exception{Node ct=part(files,"[Content_Types].xml",b);boolean found=false;for(Node n:nodes(ct,"http://schemas.openxmlformats.org/package/2006/content-types","Override")){String type=n.attr("ContentType");PersonalText.require(!type.toLowerCase(Locale.ROOT).contains("macro"),"Macro-enabled documents unsupported");if(n.attr("PartName").equals("/"+main)){PersonalText.require(type.equals(mime),"Document type does not match extension");found=true;}}PersonalText.require(found,"Missing document content type");}
 static Node fallback(Node n)throws IOException {Node found=null;for(Object child:n.children)if(child instanceof Node&&((Node)child).is("http://schemas.openxmlformats.org/markup-compatibility/2006","Fallback")){PersonalText.require(found==null,"Ambiguous Office fallback");found=(Node)child;}PersonalText.require(found!=null,"Office extension has no supported fallback");return found;}
 static void text(Node n,String format,StringBuilder out,Budget b)throws IOException{
  b.check();if(n.is("http://schemas.openxmlformats.org/markup-compatibility/2006","AlternateContent")){text(fallback(n),format,out,b);return;}if(n.attr(TEXT,"display").equals("none"))return;if(n.attr(TEXT,"display").equals("condition"))throw new IOException("Conditional ODF visibility unsupported");if(n.is(W,"del")||n.is(W,"instrText")||n.is(OFFICE,"annotation")||n.is(TEXT,"tracked-changes"))return;
  if(n.is(W,"r")){for(Node hidden:nodes(n,W,"vanish"))if(!Arrays.asList("0","false","off").contains(hidden.attr(W,"val")))return;}
  if(n.is(TEXT,"hidden-text")||n.is(TEXT,"hidden-paragraph"))throw new IOException("Conditional hidden ODF text unsupported");
  if(n.is(W,"tab")||n.is(A,"tab")||n.is(TEXT,"tab")){out.append('\t');return;}if(n.is(W,"br")||n.is(A,"br")||n.is(TEXT,"line-break")){out.append('\n');return;}
  if(n.is(TEXT,"s")){String c=n.attr(TEXT,"c");int count=c.isEmpty()?1:Integer.parseInt(c);PersonalText.require(count>0&&count<=1000,"ODF space repetition exceeds limit");for(int i=0;i<count;i++)out.append(' ');return;}
  boolean literal=format.equals("odt")||format.equals("odp")||n.is(W,"t")||n.is(A,"t");
  for(Object child:n.children){if(child instanceof String){if(literal)out.append((String)child);}else text((Node)child,format,out,b);PersonalText.require(out.length()<=20000,"Paragraph exceeds limit");}
 }
 static void paragraphs(Node n,String format,String location,Output out,int[] ordinal)throws IOException {
  out.budget.check();if(n.is("http://schemas.openxmlformats.org/markup-compatibility/2006","AlternateContent")){paragraphs(fallback(n),format,location,out,ordinal);return;}if(n.attr(TEXT,"display").equals("none"))return;if(n.attr(TEXT,"display").equals("condition"))throw new IOException("Conditional ODF visibility unsupported");if(n.is(OFFICE,"annotation")||n.is(TEXT,"tracked-changes")||n.is(W,"del"))return;
  boolean p=format.equals("docx")?n.is(W,"p"):format.equals("pptx")?n.is(A,"p"):n.is(TEXT,"p")||n.is(TEXT,"h");
  if(p){StringBuilder s=new StringBuilder();text(n,format,s,out.budget);out.add(s.toString(),location+"; paragraph "+(++ordinal[0]));return;}
  for(Object c:n.children)if(c instanceof Node)paragraphs((Node)c,format,location,out,ordinal);
 }
 static Result extract(byte[] raw,String format,File cache,Budget b)throws Exception {
  b.check();PersonalText.require(raw.length<=INPUT,"Document input exceeds limit");Output out=new Output(b);
  if(format.equals("html")||format.equals("htm")){DocumentHtml.extract(raw,"HTML body",out);return out.finish();}
  Map<String,byte[]> files=unzip(raw,cache,b);
  if(format.equals("docx")||format.equals("pptx")){
   String main=rootPart(files,b);officeType(files,main,format.equals("docx")?"application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml":"application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml",b);
   Node document=part(files,main,b);
   if(format.equals("docx")){PersonalText.require(document.is(W,"document"),"Invalid DOCX document root");paragraphs(one(document,W,"body"),format,main,out,new int[]{0});}
   else{PersonalText.require(document.is(P,"presentation"),"Invalid presentation root");Map<String,Node> rel=relationships(part(files,relPath(main),b));List<Node> slides=nodes(one(document,P,"sldIdLst"),P,"sldId");Set<String> seen=new HashSet<>();int i=0;for(Node slide:slides){String name=resolve(rel,slide.attr(R,"id"),main,"slide");PersonalText.require(seen.add(name),"Repeated slide relationship");Node n=part(files,name,b);PersonalText.require(n.is(P,"sld"),"Invalid slide root");PersonalText.require(!Arrays.asList("0","false").contains(n.attr("show")),"Hidden presentation slides unsupported");for(Node shape:nodes(n,P,"cNvPr"))PersonalText.require(!Arrays.asList("1","true").contains(shape.attr("hidden")),"Hidden presentation shapes unsupported");paragraphs(n,format,"Slide "+(++i)+"; "+name,out,new int[]{0});}}
  }else if(format.equals("odt")||format.equals("odp")){
   String mime=new String(required(files,"mimetype"),StandardCharsets.US_ASCII);PersonalText.require(mime.equals("application/vnd.oasis.opendocument."+(format.equals("odt")?"text":"presentation")),"ODF type differs from extension");Node manifest=part(files,"META-INF/manifest.xml",b);PersonalText.require(nodes(manifest,"urn:oasis:names:tc:opendocument:xmlns:manifest:1.0","encryption-data").isEmpty(),"Encrypted ODF unsupported");Node doc=part(files,"content.xml",b);Node body=one(doc,OFFICE,"body");
   if(format.equals("odt"))paragraphs(one(body,OFFICE,"text"),format,"content.xml",out,new int[]{0});else{int i=0;for(Node page:nodes(one(body,OFFICE,"presentation"),DRAW,"page"))paragraphs(page,format,"Slide "+(++i)+"; content.xml",out,new int[]{0});}
  }else if(format.equals("epub")){
   PersonalText.require(new String(required(files,"mimetype"),StandardCharsets.US_ASCII).equals("application/epub+zip"),"Invalid EPUB mimetype");PersonalText.require(!files.containsKey("META-INF/encryption.xml"),"Encrypted EPUB unsupported");Node container=part(files,"META-INF/container.xml",b);Node rootfile=one(container,"urn:oasis:names:tc:opendocument:xmlns:container","rootfile");PersonalText.require(rootfile.attr("media-type").equals("application/oebps-package+xml"),"Unsupported EPUB rootfile");String name=path(rootfile.attr("full-path"));Node opf=part(files,name,b);String ns="http://www.idpf.org/2007/opf";PersonalText.require(opf.is(ns,"package"),"Invalid EPUB package");Map<String,Node> items=new HashMap<>();for(Node item:nodes(one(opf,ns,"manifest"),ns,"item"))PersonalText.require(!item.attr("id").isEmpty()&&items.put(item.attr("id"),item)==null,"Duplicate EPUB item");Set<String> seen=new HashSet<>();int i=0;
   for(Node ref:nodes(one(opf,ns,"spine"),ns,"itemref")){Node item=items.get(ref.attr("idref"));PersonalText.require(item!=null&&item.attr("media-type").equals("application/xhtml+xml"),"Missing or non-text EPUB spine item");String content=target(name,item.attr("href"));PersonalText.require(seen.add(content),"Repeated EPUB spine item");byte[] html=required(files,content);xml(html,b);DocumentHtml.extract(html,"Spine item "+(++i)+"; "+content,out,files,content);}
  }else throw new IOException("Unsupported structured format");
  return out.finish();
 }
 private StructuredDocuments(){}
}
