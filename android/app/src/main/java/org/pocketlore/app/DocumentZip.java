package org.pocketlore.app;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.charset.*;
import java.util.*;
import java.util.zip.*;

/** Independent bounded central/local/payload verification over the admitted original bytes. */
final class DocumentZip {
 private static void require(boolean ok,String why)throws IOException{PersonalText.require(ok,"ZIP integrity: "+why);}
 private static void range(byte[] b,long p,long n)throws IOException{require(p>=0&&n>=0&&p<=b.length&&n<=b.length-p,"range");}
 private static int u16(byte[] b,int p)throws IOException{range(b,p,2);return (b[p]&255)|((b[p+1]&255)<<8);}
 private static long u32(byte[] b,int p)throws IOException{range(b,p,4);return (long)u16(b,p)|((long)u16(b,p+2)<<16);}
 private static void extra(byte[] b,int p,int n)throws IOException{
  range(b,p,n);int end=p+n;while(p<end){require(end-p>=4,"extra header");int tag=u16(b,p),len=u16(b,p+2);require(tag!=1&&len<=end-p-4,"ZIP64 or extra length");p+=4+len;}require(p==end,"extra boundary");
 }
 private static String name(byte[] b,int p,int n)throws IOException{
  range(b,p,n);require(n>0&&n<=2048,"name length");
  try{return StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT).onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(b,p,n)).toString();}
  catch(CharacterCodingException e){throw new IOException("ZIP integrity: invalid UTF8 name",e);}
 }
 private static final class Entry {String name;int flags,method,version,offset,data,end;long crc,compressed,size;}
 static void verify(byte[] raw,Map<String,byte[]> streamed,StructuredDocuments.Budget budget)throws IOException{
  budget.check();require(raw.length<=StructuredDocuments.INPUT&&raw.length>=22,"input");
  int end=-1;
  for(int p=raw.length-22;p>=Math.max(0,raw.length-65557);p--){
   if((p&1023)==0)budget.check();
   if(u32(raw,p)==0x06054b50L&&p+22+u16(raw,p+20)==raw.length){require(end==-1,"ambiguous EOCD");end=p;}
  }
  require(end>=0,"EOCD/comment/trailing data");
  int count=u16(raw,end+10);long length=u32(raw,end+12),start=u32(raw,end+16);
  require(u16(raw,end+4)==0&&u16(raw,end+6)==0&&u16(raw,end+8)==count,"multiple disks/count");
  require(count>0&&count<=StructuredDocuments.ENTRIES&&count!=65535&&length!=0xffffffffL&&start!=0xffffffffL,"count/ZIP64");
  require(start+length==end&&start>=0&&start<=end,"central boundary");
  List<Entry> entries=new ArrayList<>();Set<String> names=new HashSet<>();int p=(int)start;long expanded=0;
  for(int i=0;i<count;i++){
   budget.check();require(p+46<=end&&u32(raw,p)==0x02014b50L,"central header");Entry e=new Entry();
   e.version=u16(raw,p+6);e.flags=u16(raw,p+8);e.method=u16(raw,p+10);e.crc=u32(raw,p+16);e.compressed=u32(raw,p+20);e.size=u32(raw,p+24);
   int nn=u16(raw,p+28),en=u16(raw,p+30),cn=u16(raw,p+32);long off=u32(raw,p+42);
   require(e.version<=20&&u16(raw,p+34)==0&&off!=0xffffffffL&&e.size!=0xffffffffL&&e.compressed!=0xffffffffL,"version/disk/ZIP64");
   require((e.method==0||e.method==8)&&(e.flags&~0x080e)==0&&(e.method!=0||(e.flags&14)==0),"method/flags");
   require((long)p+46+nn+en+cn<=end,"central lengths");e.name=name(raw,p+46,nn);String safe=e.name.endsWith("/")?e.name.substring(0,e.name.length()-1):e.name;
   StructuredDocuments.path(safe);require(names.add(safe),"duplicate name");extra(raw,p+46+nn,en);
   require(e.size<=StructuredDocuments.ENTRY&&e.compressed<=raw.length&&e.size<=Math.max(1,e.compressed)*StructuredDocuments.RATIO,"payload limits");
   expanded+=e.size;require(expanded<=StructuredDocuments.EXPANDED,"aggregate");require(off<start,"local offset");e.offset=(int)off;
   byte[] expected=streamed.get(e.name);require(expected!=null&&expected.length==e.size,"stream correspondence");
   if(e.name.endsWith("/"))require(e.size==0,"directory payload");
   entries.add(e);p+=46+nn+en+cn;
  }
  require(p==end&&streamed.size()==entries.size(),"central count/stream set");
  entries.sort(Comparator.comparingInt(e->e.offset));int cursor=0;
  for(int i=0;i<entries.size();i++){
   budget.check();Entry e=entries.get(i);p=e.offset;int next=i+1<entries.size()?entries.get(i+1).offset:(int)start;
   require(p==cursor&&p+30<=next&&u32(raw,p)==0x04034b50L,"local gap/overlap/header");
   require(u16(raw,p+4)==e.version&&u16(raw,p+6)==e.flags&&u16(raw,p+8)==e.method,"local identity");
   int nn=u16(raw,p+26),en=u16(raw,p+28);require((long)p+30+nn+en<=next,"local lengths");
   require(name(raw,p+30,nn).equals(e.name),"local name");extra(raw,p+30+nn,en);e.data=p+30+nn+en;
   long dataEnd=(long)e.data+e.compressed;require(dataEnd<=next,"payload overlap");e.end=(int)dataEnd;
   long lc=u32(raw,p+14),lz=u32(raw,p+18),lu=u32(raw,p+22);
   if((e.flags&8)==0){require(lc==e.crc&&lz==e.compressed&&lu==e.size&&e.end==next,"local sizes/CRC/boundary");}
   else{
    require((lc==0||lc==e.crc)&&(lz==0||lz==e.compressed)&&(lu==0||lu==e.size),"descriptor local authority");
    int d=e.end;require(next-d==12||next-d==16,"descriptor boundary");
    if(next-d==16){require(u32(raw,d)==0x08074b50L,"descriptor signature");d+=4;}
    require(u32(raw,d)==e.crc&&u32(raw,d+4)==e.compressed&&u32(raw,d+8)==e.size,"descriptor authority");
   }
   verifyPayload(raw,e,streamed.get(e.name),budget);cursor=next;
  }
  require(cursor==start,"local coverage");budget.check();
 }
 private static void verifyPayload(byte[] raw,Entry e,byte[] expected,StructuredDocuments.Budget budget)throws IOException{
  CRC32 crc=new CRC32();int at=0;
  if(e.method==0){require(e.compressed==e.size,"stored size");while(at<expected.length){budget.check();int n=Math.min(8192,expected.length-at);for(int i=0;i<n;i++)require(raw[e.data+at+i]==expected[at+i],"stored bytes");crc.update(raw,e.data+at,n);at+=n;}}
  else{
   Inflater inflater=new Inflater(true);byte[] buffer=new byte[8192];
   try{
    inflater.setInput(raw,e.data,(int)e.compressed);
    while(!inflater.finished()){
     budget.check();int n;
     try{n=inflater.inflate(buffer);}catch(DataFormatException x){throw new IOException("ZIP integrity: deflate payload",x);}
     require(n<=expected.length-at,"expanded size");
     for(int i=0;i<n;i++)require(buffer[i]==expected[at+i],"inflated bytes");crc.update(buffer,0,n);at+=n;
     require(n>0||inflater.finished(),"deflate progress/dictionary/truncation");
    }
    require(inflater.getBytesRead()==e.compressed&&inflater.getRemaining()==0,"compressed trailing bytes");
   }finally{inflater.end();}
  }
  require(at==e.size&&crc.getValue()==e.crc,"payload size/CRC");budget.check();
 }
 private DocumentZip(){}
}
