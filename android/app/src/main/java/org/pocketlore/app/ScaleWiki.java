package org.pocketlore.app;
import java.io.*;import java.nio.charset.StandardCharsets;import java.security.*;import java.util.*;import java.util.function.BooleanSupplier;import java.util.zip.*;import org.json.*;import android.util.JsonReader;
/** Read-only FTS5 and streaming source slices. Unknown rights always deny generation. */
final class ScaleWiki {
 static final long MAX_RAW=128L*1024*1024,MAX_PACKED=64L*1024*1024,MAX_RECORD=32L*1024*1024;
 static final class Hit {final ScaleLibrary.Entry edition;final String shard,id,title,tier,rights,url,date,revision,sourceRow,sourceHash;final long block,offset,length;final String recordHash;Hit(ScaleLibrary.Entry e,String shard,JSONArray r)throws Exception{edition=e;this.shard=shard;id=r.getString(0);title=r.getString(1);tier=r.getString(2);rights=r.getString(3);url=r.getString(4);date=r.getString(5);revision=r.getString(6);sourceRow=r.getString(7);sourceHash=r.getString(8);block=Long.parseLong(r.getString(9));offset=Long.parseLong(r.getString(10));length=Long.parseLong(r.getString(11));recordHash=r.getString(12).toLowerCase(Locale.ROOT);}String identity(){return edition.id+":"+shard+":"+id+":"+revision+":"+sourceHash;}boolean mayGenerate(){return false;}}
 static final String COLS="id,title,tier,rights,url,modified,revision,source_row,hex(text_sha256),block_id,offset,length,hex(sha256)";
 static File database(ScaleLibrary.Entry e,String shard)throws Exception{return ScaleLibrary.resolve(e.directory,shard+"/catalog.sqlite");}
 static List<Hit> search(ScaleLibrary.Entry e,String question,BooleanSupplier cancel)throws Exception{
  ScaleLibrary.check(question.length()<=1000&&!question.trim().isEmpty(),"Query length");List<Hit> hits=new ArrayList<>();Set<String> seen=new HashSet<>();String[] tokens=question.toLowerCase(Locale.ROOT).split("[^\\p{L}\\p{N}]+");Set<String> stop=new HashSet<>(Arrays.asList("a an the is are of to in and or for from with what how why which when does do by on at as into explain compare between".split(" ")));List<String> terms=new ArrayList<>();for(String t:tokens)if(!t.isEmpty()&&!stop.contains(t)&&!terms.contains(t)){terms.add(t);if(terms.size()==16)break;}String expr="";for(String t:terms)expr+=(expr.isEmpty()?"":" OR ")+"\""+t+"\"";
  JSONArray shards=e.manifest.getJSONArray("shards");for(int i=0;i<shards.length();i++){ScaleLibrary.cancelled(cancel);String shard=shards.getString(i),path=database(e,shard).getPath();JSONArray exact=NativeIndex.rows(path,"SELECT "+COLS+" FROM articles WHERE title=? LIMIT 4",new String[]{question.trim()},4,cancel);for(int n=0;n<exact.length();n++){Hit h=new Hit(e,shard,exact.getJSONArray(n));if(seen.add(h.identity()))hits.add(h);}}
  // Redirects are resolved only against shards actually in this active collection.
  if(e.manifest.has("aliases")) {
   String aliasPath=ScaleLibrary.resolve(e.directory,e.manifest.getString("aliases")).getPath();
   JSONArray redirects=NativeIndex.rows(aliasPath,"SELECT s.name,a.target FROM aliases a JOIN shard_names s ON s.id=a.shard WHERE a.alias=? ORDER BY a.target LIMIT 12",new String[]{question.trim().replace('_',' ').toLowerCase(Locale.ROOT)},12,cancel);
   Set<String> installed=new HashSet<>();for(int i=0;i<shards.length();i++)installed.add(shards.getString(i));
   for(int i=0;i<redirects.length();i++){JSONArray row=redirects.getJSONArray(i);String targetShard=aliasShardName(row.getString(0));if(installed.contains(targetShard)){Hit h=byId(e,targetShard,row.getString(1),cancel);if(seen.add(h.identity()))hits.add(h);}}
  }
  List<List<Hit>> rankedShards=new ArrayList<>();
  if(!expr.isEmpty())for(int i=0;i<shards.length();i++){ScaleLibrary.cancelled(cancel);String shard=shards.getString(i),path=database(e,shard).getPath();JSONArray ranked=NativeIndex.rows(path,"SELECT rowid FROM search WHERE search MATCH ? ORDER BY bm25(search,5.0,1.0) LIMIT 12",new String[]{expr},12,cancel);List<Hit> local=new ArrayList<>();for(int n=0;n<ranked.length();n++)local.add(byId(e,shard,ranked.getJSONArray(n).getString(0),cancel));rankedShards.add(local);}
  // Round-robin shard ranks: do not let the first shard fill every non-exact slot.
  for(int rank=0;rank<12;rank++)for(List<Hit> local:rankedShards)if(rank<local.size()){Hit h=local.get(rank);if(seen.add(h.identity()))hits.add(h);}
  // Exact titles first; distinct article identities. This is not the host global-IDF ranking.
  return hits.subList(0,Math.min(12,hits.size()));
 }
 // Sealed aliases retain acquisition filenames; installed shard directories omit that extension.
 static String aliasShardName(String name){return name.replaceFirst("\\.(?:sqlite|parquet)$", "");}
 static Hit byId(ScaleLibrary.Entry e,String shard,String id,BooleanSupplier cancel)throws Exception{JSONArray a=NativeIndex.rows(database(e,shard).getPath(),"SELECT "+COLS+" FROM articles WHERE id=?",new String[]{id},1,cancel);ScaleLibrary.check(a.length()==1,"Unknown article");return new Hit(e,shard,a.getJSONArray(0));}
 static final class Read {String text,wikitextScope;long rawBlockBytes,recordBytes,temporaryBytes;boolean previewTruncated;}
 static Read read(Hit h,File cache,BooleanSupplier cancel)throws Exception{
  ScaleLibrary.cancelled(cancel);ScaleLibrary.check(h.length>0&&h.length<=MAX_RECORD,"Article record exceeds measured 32 MiB admission");JSONArray a=NativeIndex.rows(database(h.edition,h.shard).getPath(),"SELECT offset,length,raw_length,hex(sha256) FROM blocks WHERE id=?",new String[]{Long.toString(h.block)},1,cancel);ScaleLibrary.check(a.length()==1,"Missing block");JSONArray b=a.getJSONArray(0);long offset=Long.parseLong(b.getString(0)),packed=Long.parseLong(b.getString(1)),raw=Long.parseLong(b.getString(2));String hash=b.getString(3).toLowerCase(Locale.ROOT);ScaleLibrary.check(packed>0&&packed<=MAX_PACKED&&raw>0&&raw<=MAX_RAW&&h.offset>=0&&h.length<=raw-h.offset,"Block/slice admission");File file=ScaleLibrary.resolve(h.edition.directory,h.shard+"/articles.blocks");ScaleLibrary.check(offset>=0&&packed<=file.length()-offset,"Block file bounds");ResourceStorage.requireSpace(h.length,cache.getUsableSpace());File record=File.createTempFile("scale-record-",".json",cache);Read result=new Read();result.rawBlockBytes=raw;result.recordBytes=h.length;MessageDigest blockDigest=MessageDigest.getInstance("SHA-256"),recordDigest=MessageDigest.getInstance("SHA-256");Inflater inflater=new Inflater();
  try(RandomAccessFile raf=new RandomAccessFile(file,"r")){raf.seek(offset);final long[] left={packed};InputStream limited=new InputStream(){public int read()throws IOException{byte[] one=new byte[1];return read(one,0,1)==-1?-1:one[0]&255;}public int read(byte[] bytes,int start,int len)throws IOException{if(left[0]==0)return -1;int n=raf.read(bytes,start,(int)Math.min(len,left[0]));if(n<0)throw new EOFException("Truncated compressed block");left[0]-=n;return n;}};
   long position=0,selected=0;try(InflaterInputStream in=new InflaterInputStream(limited,inflater,65536);FileOutputStream out=new FileOutputStream(record)){byte[] buffer=new byte[65536];int n;while((n=in.read(buffer))!=-1){ScaleLibrary.cancelled(cancel);ScaleLibrary.check(position+n<=raw,"Inflation exceeds declared bound");blockDigest.update(buffer,0,n);long from=Math.max(position,h.offset),to=Math.min(position+n,h.offset+h.length);if(to>from){int start=(int)(from-position),count=(int)(to-from);out.write(buffer,start,count);recordDigest.update(buffer,start,count);selected+=count;}position+=n;}ScaleLibrary.check(inflater.finished()&&inflater.getRemaining()==0&&left[0]==0&&position==raw&&selected==h.length,"Truncated/trailing zlib or wrong slice");out.getFD().sync();}
   ScaleLibrary.check(ScaleLibrary.hex(blockDigest.digest()).equals(hash)&&ScaleLibrary.hex(recordDigest.digest()).equals(h.recordHash),"Block/article checksum mismatch");result.temporaryBytes=record.length();
   SourceTextSlice.read(record,result,h.sourceHash,cancel);return result;
  }finally{inflater.end();java.nio.file.Files.deleteIfExists(record.toPath());}
 }
 static ScaleAnswerAdapter.Snapshot answerSnapshot(Hit h,Read r)throws Exception {
  ScaleLibrary.check(!r.previewTruncated,"A preview cannot supply full-document answer offsets");
  String rights="Wikipedia contributors; CC BY-SA 4.0 dataset terms; source status: "+h.rights;
  String history="https://en.wikipedia.org/w/index.php?curid="+h.id+"&action=history";
  // The verified JSON record hash binds the exact retained formula/unit supplement and range map.
  return new ScaleAnswerAdapter.Snapshot(new String[]{h.edition.manifest.getString("source_inventory_sha256"),h.shard,h.id,h.revision,h.recordHash,h.sourceHash.toLowerCase(Locale.ROOT),h.title,h.url,history,h.date,rights,"Unresolved source-specific exceptions; see retained source ranges",h.recordHash,r.wikitextScope},r.text);
 }
 static String answerReview(Hit h,Read r,ScaleAnswerAdapter.Ledger ledger)throws Exception {
  ScaleAnswerAdapter.Snapshot snapshot=answerSnapshot(h,r);ScaleAnswerAdapter.Review review=ledger.get(snapshot);
  if(review==null||!review.independentlyCleared)return "Answer evidence unavailable: independent source-specific rights and fidelity review is pending. No generated answer or research-brief approval is inferred.";
  ScaleAnswerAdapter.admit(snapshot,review.start,review.end,ledger,()->false);
  return "Exact reviewed span is available to the typed obligation controller; independent claim support and completeness are still required before publication.";
 }
 static String detail(Hit h,Read r){return h.title+" ("+h.tier+")\n"+r.text+(r.previewTruncated?"\n[Preview limited to 64,000 characters; full retained source remains in the collection.]":"")+"\n\nArticle revision: "+h.revision+"\nSource date: "+h.date+"\n"+h.url+"\nHistory: https://en.wikipedia.org/w/index.php?title="+android.net.Uri.encode(h.title)+"&action=history\nWikipedia contributors; CC BY-SA 4.0 dataset terms. Source-specific rights: "+h.rights+"\nRetained wikitext scope: "+r.wikitextScope+"\nCitation identity: "+h.identity()+"\nSource row: "+h.sourceRow+"\nText SHA-256: "+h.sourceHash+"\nThis source is not cleared for generated answers. Leads are not full articles.";}
}
