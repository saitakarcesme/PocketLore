package org.pocketlore.app;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import java.util.function.BooleanSupplier;
import java.util.zip.*;
import org.json.*;

/** Bounded, read-only SQLite FTS4 edition. No corpus objects or long-lived SQLite handles. */
final class BroadPack {
 static final long MAX_ARCHIVE=128L*1024*1024,MAX_DATABASE=256L*1024*1024;
 final File archive,database;final JSONObject manifest;final String hash,id;
 static String hash(File f)throws Exception{MessageDigest md=MessageDigest.getInstance("SHA-256");try(InputStream in=new FileInputStream(f)){byte[] b=new byte[65536];int n;while((n=in.read(b))!=-1)md.update(b,0,n);}StringBuilder out=new StringBuilder();for(byte b:md.digest())out.append(String.format(Locale.ROOT,"%02x",b&255));return out.toString();}
 static JSONObject metadata(File f)throws Exception{try(ZipFile z=new ZipFile(f)){ZipEntry e=z.getEntry("manifest.json");if(e==null||e.getSize()>2*1024*1024||e.getSize()<2)throw new IOException("Manifest size invalid");try(InputStream in=z.getInputStream(e)){ByteArrayOutputStream out=new ByteArrayOutputStream();byte[] b=new byte[4096];int n;while((n=in.read(b))!=-1){if(out.size()+n>2*1024*1024)throw new IOException("Manifest limit");out.write(b,0,n);}return new JSONObject(out.toString("UTF-8"));}}}
 static byte[] licenseBytes(File archive)throws Exception{try(ZipFile z=new ZipFile(archive)){ZipEntry e=z.getEntry("CC-BY-SA-4.0.html");require(e!=null&&e.getSize()>5000&&e.getSize()<131072,"Offline license missing/oversized");try(InputStream in=z.getInputStream(e)){ByteArrayOutputStream out=new ByteArrayOutputStream();byte[] b=new byte[4096];int n;while((n=in.read(b))!=-1){require(out.size()+n<131072,"License limit");out.write(b,0,n);}byte[] result=out.toByteArray();require(KnowledgePack.hash(result).equals("170b3685f24d098f590c92867787e7be3a86260aed1b96bf4a7594f72a9116be"),"Offline license hash mismatch");return result;}}}
 static String licenseText(File files,String citation)throws Exception{require(citation.matches("p[0-9a-f]{64}_wiki-.*"),"Not a broad citation");File archive=new File(new File(files,"pack-library"),citation.substring(1,65)+".plpack");String html=new String(licenseBytes(archive),StandardCharsets.UTF_8);return android.text.Html.fromHtml(html,android.text.Html.FROM_HTML_MODE_LEGACY).toString();}
 static boolean isBroad(File f)throws Exception{return metadata(f).optString("format").equals("pocketlore-sqlite-v1");}
 BroadPack(File archive,File db,String hash)throws Exception{
  this.archive=archive;database=db;this.hash=hash;manifest=metadata(archive);id=manifest.getString("id");
  require(id.matches("[a-z0-9-]{1,80}")&&manifest.getString("format").equals("pocketlore-sqlite-v1"),"Broad edition identity");
  require(manifest.getString("license").equals("CC-BY-SA-4.0")&&!manifest.getBoolean("distribution_ready"),"Broad license/review status invalid");
  require(manifest.getInt("documents")>0&&manifest.getInt("documents")<=5000&&manifest.getInt("passages")>0&&manifest.getInt("passages")<=100000,"Broad count admission");
  require(archive.length()<=MAX_ARCHIVE&&manifest.getLong("db_bytes")<=MAX_DATABASE,"Broad storage admission");
 }
 static void require(boolean b,String why)throws IOException{if(!b)throw new IOException(why);}
 static void cancelled(BooleanSupplier c)throws IOException{if(c.getAsBoolean()||Thread.currentThread().isInterrupted())throw new InterruptedIOException("Broad import cancelled");}
 SQLiteDatabase open(){SQLiteDatabase db=SQLiteDatabase.openDatabase(database.getPath(),null,SQLiteDatabase.OPEN_READONLY|SQLiteDatabase.NO_LOCALIZED_COLLATORS);try(Cursor c=db.rawQuery("PRAGMA cache_size=-2048",null)){c.moveToFirst();}try(Cursor c=db.rawQuery("PRAGMA mmap_size=0",null)){c.moveToFirst();}return db;}
 static BroadPack prepare(File archive,File directory,String hash,BooleanSupplier cancel)throws Exception{
  File db=new File(directory,hash+".sqlite"),stage=new File(directory,hash+".sqlite.partial");BroadPack pack=new BroadPack(archive,db,hash);
  licenseBytes(archive);
  ResourceStorage.requireSpace(pack.manifest.getLong("db_bytes"),directory.getUsableSpace());
  try{try(ZipFile z=new ZipFile(archive)){
    require(z.size()==3&&z.getEntry("CC-BY-SA-4.0.html")!=null,"Missing offline license or extra members");ZipEntry entry=z.getEntry("index.sqlite");require(entry!=null&&entry.getSize()==pack.manifest.getLong("db_bytes"),"Index size invalid");
    try(InputStream in=z.getInputStream(entry)){ResourceStorage.copy(in,stage,MAX_DATABASE,cancel);}
   }
   require(stage.length()==pack.manifest.getLong("db_bytes")&&hash(stage).equals(pack.manifest.getString("db_sha256")),"Index SHA-256 mismatch");
   new BroadPack(archive,stage,hash).validate(cancel);require(hash(stage).equals(pack.manifest.getString("db_sha256")),"Validation changed index bytes");cancelled(cancel);Files.move(stage.toPath(),db.toPath(),StandardCopyOption.ATOMIC_MOVE,StandardCopyOption.REPLACE_EXISTING);return pack;
  }finally{stage.delete();}
 }
 void validate(BooleanSupplier cancel)throws Exception{
  // SQLite FTS4 integrity validation issues a virtual-table write command even
  // when checking only. Use the private import stage, then verify unchanged bytes.
  try(SQLiteDatabase db=SQLiteDatabase.openDatabase(database.getPath(),null,SQLiteDatabase.OPEN_READWRITE|SQLiteDatabase.NO_LOCALIZED_COLLATORS)){
   try(Cursor c=db.rawQuery("SELECT sql FROM sqlite_master WHERE name='search'",null)){require(c.moveToFirst()&&c.getString(0).equals("CREATE VIRTUAL TABLE search USING fts4(title,body,tokenize=porter)"),"Unsupported search schema");}
   try(Cursor c=db.rawQuery("PRAGMA integrity_check",null)){require(c.moveToFirst(),"No SQLite integrity result");require(c.getString(0).equals("ok"),"SQLite integrity failure: "+c.getString(0));}
   require(db.getVersion()==210,"Unexpected index version");JSONArray expected=manifest.getJSONArray("schema");int i=0;
   try(Cursor c=db.rawQuery("SELECT name,sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY name",null)){while(c.moveToNext()){require(i<expected.length()&&c.getString(0).equals(expected.getJSONArray(i).getString(0))&&c.getString(1).equals(expected.getJSONArray(i).getString(1)),"Index schema mismatch");i++;}}require(i==expected.length(),"Missing index schema");
   try(Cursor c=db.rawQuery("SELECT max(length(body)) FROM documents",null)){require(c.moveToFirst()&&c.getLong(0)<=1000000,"Document row memory admission");}
   try(Cursor c=db.rawQuery("SELECT max(length(body)) FROM passages",null)){require(c.moveToFirst()&&c.getLong(0)<=32000,"Passage row memory admission");}
   try(Cursor c=db.rawQuery("SELECT count(*) FROM sqlite_master WHERE type NOT IN ('table','index')",null)){require(c.moveToFirst()&&c.getInt(0)==0,"Views/triggers are not permitted");}
   int docs=0,passages=0;
   try(Cursor c=db.rawQuery("SELECT id,title,url,date,rights,provenance,body,sha FROM documents",null)){while(c.moveToNext()){cancelled(cancel);for(int n=0;n<8;n++)require(c.getString(n)!=null&&!c.getString(n).isEmpty(),"Missing source metadata");require(c.getString(4).contains("CC BY-SA 4.0")&&c.getString(5).contains("Contributor history:")&&c.getString(5).contains("Generation disabled:"),"Missing license/attribution or extraction review warning");require(KnowledgePack.hash(c.getString(6).getBytes(StandardCharsets.UTF_8)).equals(c.getString(7)),"Source content hash mismatch");docs++;}}
   try(Cursor c=db.rawQuery("SELECT p.body,p.sha,p.start,p.end,d.body,p.citation FROM passages p JOIN documents d ON p.document=d.id ORDER BY p.pid",null)){while(c.moveToNext()){cancelled(cancel);String body=c.getString(0),source=c.getString(4);int start=c.getInt(2),end=c.getInt(3);require(start>=0&&end>start&&end<=source.length()&&source.substring(start,end).equals(body),"Passage source offsets mismatch");require(KnowledgePack.hash(body.getBytes(StandardCharsets.UTF_8)).equals(c.getString(1))&&c.getString(5).matches("wiki-[0-9]+-[0-9a-f]{16}"),"Passage content hash/ID invalid");passages++;}}
   require(docs==manifest.getInt("documents")&&passages==manifest.getInt("passages"),"Index counts mismatch");
   try(Cursor c=db.rawQuery("SELECT count(*) FROM search",null)){require(c.moveToFirst()&&c.getInt(0)==passages,"Search row mismatch");}
  }
 }
 ResearchEngine engine(){return new ResearchEngine(new ResearchEngine.DiskProvider(){
  public int size(){return manifest.optInt("passages");}
  public ResearchEngine.Result research(String question){
   List<String> terms=new ArrayList<>(new LinkedHashSet<>(ResearchEngine.tokenize(question)));if(terms.size()>24)terms=terms.subList(0,24);List<ResearchEngine.Hit> hits=new ArrayList<>();int candidates=0;
   if(!terms.isEmpty())try(SQLiteDatabase db=open()){
    StringBuilder match=new StringBuilder();for(String t:terms){if(match.length()>0)match.append(" AND ");match.append('"').append(t).append('"');}
    try(Cursor c=db.rawQuery("SELECT p.citation,p.body,p.sha,d.title,d.url,d.date,d.rights,d.provenance FROM search JOIN passages p ON p.pid=search.docid JOIN documents d ON d.id=p.document WHERE search MATCH ? ORDER BY search.docid LIMIT 64",new String[]{match.toString()})){
     while(c.moveToNext()){candidates++;String title=c.getString(3),text=c.getString(1);double score=0;Set<String> titleTerms=new HashSet<>(ResearchEngine.tokenize(title)),bodyTerms=new HashSet<>(ResearchEngine.tokenize(text));for(String t:terms){if(titleTerms.contains(t))score+=5;if(bodyTerms.contains(t))score+=1;}
      String provenance="Collection: "+id+"\nEdition SHA-256: "+hash+"\n"+c.getString(7)+"\nPassage SHA-256: "+c.getString(2)+"\n"+manifest.optString("warning");
      String[] row={"p"+hash+"_"+c.getString(0),title,c.getString(4),c.getString(5),c.getString(6),text};hits.add(new ResearchEngine.Hit(new ResearchEngine.Passage(row,provenance),score));
     }
    }
   }catch(Exception e){throw new IllegalStateException("Cannot query saved broad index",e);}
   hits.sort(Comparator.comparingDouble((ResearchEngine.Hit h)->h.score).reversed().thenComparing(h->h.passage.id));if(hits.size()>4)hits=new ArrayList<>(hits.subList(0,4));
   return new ResearchEngine.Result(hits,Collections.emptySet(),hits.isEmpty()?"No matching evidence in the historical edition.":"Historical extracted source passages; inspect omissions and attribution. No generated answer inferred.",candidates);
  }
 });}
}
