package org.pocketlore.app;

import android.content.*;
import android.database.*;
import android.database.sqlite.*;
import java.util.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.function.BooleanSupplier;

/** Private snapshots and annotations; never evidence admission for generation. */
final class NotebookStore extends SQLiteOpenHelper {
    static final int MAX_RECORD_BYTES=2*1024*1024, MAX_RECORDS=10000, PAGE_SIZE=20;
    static final long MAX_CONTENT_BYTES=16L*1024*1024, MAX_DB_BYTES=64L*1024*1024, MAX_EXPORT_BYTES=32L*1024*1024;
    static final String BYTE_SQL="length(CAST(kind AS BLOB))+length(CAST(title AS BLOB))+length(CAST(question AS BLOB))+length(CAST(body AS BLOB))+length(CAST(provenance AS BLOB))+length(CAST(note AS BLOB))";
    static final String HEADER="# PocketLore notebook\n\nOffline snapshots and personal notes. Source rights and answer limitations remain attached; check them before redistribution.\n\n";
    static final String SEPARATOR="\n---\n\n";
    static final class Entry {
        long id,created; String kind,title,question,body,provenance,note; boolean bookmark;
        String portable() {
            return "# "+title+"\n\nKind: "+kind+"\nCaptured: "+new java.text.SimpleDateFormat("yyyy-MM-dd HH:mm:ss 'UTC'",Locale.ROOT){{setTimeZone(TimeZone.getTimeZone("UTC"));}}.format(new Date(created))+
                "\n\nLocal snapshot; capture time is not the source publication date. No new verification or permission is implied.\n\n"+
                (question.isEmpty()?"":"## Question\n\n"+question+"\n\n")+"## Content\n\n"+body+"\n\n## Source and coverage\n\n"+provenance+
                "\n\n## Personal note (not source evidence)\n\n"+note+"\n\n";
        }
    }
    static final class Summary {long id,created;String kind,title;boolean bookmark,hasNote;}
    static final class Page {final List<Summary> entries=new ArrayList<>();int number,total;int pages(){return Math.max(1,(total+PAGE_SIZE-1)/PAGE_SIZE);}}
    NotebookStore(Context c){this(c,"reader-notebook.sqlite");}
    NotebookStore(Context c,String name){super(c,name,null,2);}
    private static ResourceStorage.Reservation reserve(){try{return ResourceStorage.reserve(2*MAX_DB_BYTES+MAX_RECORD_BYTES);}catch(IOException e){throw new IllegalStateException("Notebook storage admission failed; saved records retained: "+e.getMessage(),e);}}
    @Override public void onCreate(SQLiteDatabase db){db.execSQL("CREATE TABLE entries (id INTEGER PRIMARY KEY, created INTEGER NOT NULL, kind TEXT NOT NULL, title TEXT NOT NULL, question TEXT NOT NULL, body TEXT NOT NULL, provenance TEXT NOT NULL, note TEXT NOT NULL DEFAULT '', bookmark INTEGER NOT NULL DEFAULT 0, stored_bytes INTEGER NOT NULL DEFAULT 0)");indexes(db);}
    private void indexes(SQLiteDatabase db){db.execSQL("CREATE INDEX IF NOT EXISTS notebook_order ON entries(created DESC,id DESC)");db.execSQL("CREATE INDEX IF NOT EXISTS notebook_bookmarks ON entries(bookmark,created DESC,id DESC)");db.execSQL("CREATE INDEX IF NOT EXISTS notebook_kind ON entries(kind,created DESC,id DESC)");}
    @Override public void onUpgrade(SQLiteDatabase db,int old,int next){if(old!=1||next!=2)throw new IllegalStateException("Unsupported notebook schema; existing records retained");try(ResourceStorage.Reservation ignored=reserve()){db.execSQL("ALTER TABLE entries ADD COLUMN stored_bytes INTEGER NOT NULL DEFAULT 0");db.execSQL("UPDATE entries SET stored_bytes="+BYTE_SQL);indexes(db);}}
    @Override public void onOpen(SQLiteDatabase db){super.onOpen(db);try(Cursor c=db.rawQuery("PRAGMA page_size",null)){c.moveToFirst();try(Cursor limit=db.rawQuery("PRAGMA max_page_count="+(MAX_DB_BYTES/c.getLong(0)),null)){limit.moveToFirst();}}}
    static long measureBytes(String... fields){long n=0;for(String f:fields){if(f==null)throw new IllegalArgumentException("Notebook text is missing");n=Math.addExact(n,f.getBytes(StandardCharsets.UTF_8).length);}return n;}
    static long bytes(String... fields){long n=measureBytes(fields);if(n>MAX_RECORD_BYTES)throw new IllegalArgumentException("Record exceeds the 2 MiB notebook limit; nothing was truncated or saved.");return n;}
    private void admit(SQLiteDatabase db,long incoming,long replaced,boolean adding){try(Cursor c=db.rawQuery("SELECT count(*),coalesce(sum("+BYTE_SQL+"),0) FROM entries",null)){c.moveToFirst();if(adding&&c.getLong(0)>=MAX_RECORDS)throw new IllegalStateException("Notebook record limit is 10,000. Existing records are retained.");long projected=Math.addExact(c.getLong(1)-replaced,incoming);if(projected>MAX_CONTENT_BYTES&&incoming>replaced)throw new IllegalStateException("Notebook text budget is 16 MiB, including titles, sources and notes. Existing records are retained.");}}
    long add(String kind,String title,String question,String body,String provenance,boolean bookmark){long n=bytes(kind,title,question,body,provenance,"");try(ResourceStorage.Reservation ignored=reserve()){SQLiteDatabase db=getWritableDatabase();db.beginTransaction();try{admit(db,n,0,true);ContentValues v=new ContentValues();v.put("created",System.currentTimeMillis());v.put("kind",kind);v.put("title",title);v.put("question",question);v.put("body",body);v.put("provenance",provenance);v.put("bookmark",bookmark?1:0);v.put("stored_bytes",n);long id=db.insertOrThrow("entries",null,v);db.setTransactionSuccessful();return id;}finally{db.endTransaction();}}}
    private static String escaped(String q){return q.replace("\\","\\\\").replace("%","\\%").replace("_","\\_");}
    Page page(String query,boolean bookmarks,int requested){String where=(bookmarks?"bookmark=1":"1=1")+" AND (title LIKE ? ESCAPE '\\' OR question LIKE ? ESCAPE '\\' OR note LIKE ? ESCAPE '\\')";String q="%"+escaped(query)+"%";String[] args={q,q,q};SQLiteDatabase db=getReadableDatabase();db.beginTransactionNonExclusive();try{Page p=new Page();try(Cursor c=db.rawQuery("SELECT count(*) FROM entries WHERE "+where,args)){c.moveToFirst();p.total=c.getInt(0);}p.number=Math.max(0,Math.min(requested,p.pages()-1));try(Cursor c=db.query("entries",new String[]{"id","created","substr(kind,1,64)","substr(title,1,160)","bookmark","length(note)>0"},where,args,null,null,"created DESC,id DESC",p.number*PAGE_SIZE+","+PAGE_SIZE)){while(c.moveToNext())p.entries.add(summary(c));}db.setTransactionSuccessful();return p;}finally{db.endTransaction();}}
    private Summary summary(Cursor c){Summary s=new Summary();s.id=c.getLong(0);s.created=c.getLong(1);s.kind=c.getString(2);s.title=c.getString(3);s.bookmark=c.getInt(4)!=0;s.hasNote=c.getInt(5)!=0;return s;}
    List<Summary> recentResearch(){List<Summary> result=new ArrayList<>();try(Cursor c=getReadableDatabase().query("entries",new String[]{"id","created","substr(kind,1,64)","substr(title,1,160)","bookmark","length(note)>0"},"kind=?",new String[]{"research"},null,null,"created DESC,id DESC","3")){while(c.moveToNext())result.add(summary(c));}return result;}
    /** Legacy test callers receive one bounded page; product history uses Page totals. */
    @Deprecated List<Entry> list(String q,boolean bookmarks){List<Entry> result=new ArrayList<>();for(Summary s:page(q,bookmarks,0).entries)result.add(get(s.id));return result;}
    private Cursor detail(SQLiteDatabase db,String where,String[] args,String order){Cursor c=db.query("entries",null,where,args,null,null,order,"1");if(c instanceof SQLiteCursor)((SQLiteCursor)c).setWindow(new CursorWindow("Notebook detail",4L*1024*1024));return c;}
    Entry get(long id){try(Cursor c=detail(getReadableDatabase(),"id=?",new String[]{Long.toString(id)},null)){if(!c.moveToFirst())throw new IllegalArgumentException("Saved record is unavailable or was removed.");return read(c);}}
    void update(long id,boolean bookmark,String note){edit(id,bookmark,note);}
    void note(long id,String note){edit(id,null,note);}
    private void edit(long id,Boolean bookmark,String note){if(note==null||note.length()>20000)throw new IllegalArgumentException("Notes are limited to 20,000 characters.");try(ResourceStorage.Reservation ignored=reserve()){SQLiteDatabase db=getWritableDatabase();db.beginTransaction();try{Entry e=get(id);long old=measureBytes(e.kind,e.title,e.question,e.body,e.provenance,e.note),next=measureBytes(e.kind,e.title,e.question,e.body,e.provenance,note);if(next>MAX_RECORD_BYTES&&next>old)throw new IllegalArgumentException("Record exceeds 2 MiB; existing snapshot retained.");admit(db,next,old,false);ContentValues v=new ContentValues();v.put("note",note);v.put("stored_bytes",next);if(bookmark!=null)v.put("bookmark",bookmark?1:0);if(db.update("entries",v,"id=?",new String[]{Long.toString(id)})!=1)throw new IllegalArgumentException("Saved record no longer exists.");db.setTransactionSuccessful();}finally{db.endTransaction();}}}
    void remove(long id){try(ResourceStorage.Reservation ignored=reserve()){getWritableDatabase().delete("entries","id=?",new String[]{Long.toString(id)});}}
    static long writeRecord(Writer out,Entry e,long written,BooleanSupplier cancelled)throws IOException{PersonalText.check(cancelled);String record=e.portable()+SEPARATOR;long next=Math.addExact(written,record.getBytes(StandardCharsets.UTF_8).length);if(next>MAX_EXPORT_BYTES)throw new IOException("Notebook export exceeds 32 MiB; saved data is unchanged.");out.write(record);PersonalText.check(cancelled);return next;}
    long exportAll(Writer out,BooleanSupplier cancelled)throws IOException{SQLiteDatabase db=getReadableDatabase();db.beginTransactionNonExclusive();long written=HEADER.getBytes(StandardCharsets.UTF_8).length;try{out.write(HEADER);long created=Long.MAX_VALUE,id=Long.MAX_VALUE;while(true){PersonalText.check(cancelled);Entry e;try(Cursor c=detail(db,"created<? OR (created=? AND id<?)",new String[]{""+created,""+created,""+id},"created DESC,id DESC")){if(!c.moveToFirst())break;e=read(c);}written=writeRecord(out,e,written,cancelled);created=e.created;id=e.id;}db.setTransactionSuccessful();return written;}finally{db.endTransaction();}}
    private Entry read(Cursor c){Entry e=new Entry();e.id=c.getLong(c.getColumnIndexOrThrow("id"));e.created=c.getLong(c.getColumnIndexOrThrow("created"));e.kind=c.getString(c.getColumnIndexOrThrow("kind"));e.title=c.getString(c.getColumnIndexOrThrow("title"));e.question=c.getString(c.getColumnIndexOrThrow("question"));e.body=c.getString(c.getColumnIndexOrThrow("body"));e.provenance=c.getString(c.getColumnIndexOrThrow("provenance"));e.note=c.getString(c.getColumnIndexOrThrow("note"));e.bookmark=c.getInt(c.getColumnIndexOrThrow("bookmark"))!=0;long n=measureBytes(e.kind,e.title,e.question,e.body,e.provenance,e.note);if(c.getColumnIndex("stored_bytes")>=0&&c.getLong(c.getColumnIndexOrThrow("stored_bytes"))!=n)throw new IllegalStateException("Saved record accounting is corrupt; original retained.");return e;}
}
