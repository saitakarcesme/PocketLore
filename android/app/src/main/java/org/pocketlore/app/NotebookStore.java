package org.pocketlore.app;

import android.content.*;
import android.database.Cursor;
import android.database.sqlite.*;
import java.util.*;

/** Private presentation snapshots; never used as evidence by the answer engine. */
final class NotebookStore extends SQLiteOpenHelper {
    static final int MAX_RECORD_BYTES=2*1024*1024, MAX_RECORDS=200;
    static final class Entry {
        long id,created; String kind,title,question,body,provenance,note; boolean bookmark;
        String portable() {
            return "# "+title+"\n\nKind: "+kind+"\nCaptured: "+new java.text.SimpleDateFormat("yyyy-MM-dd HH:mm:ss 'UTC'",Locale.ROOT){{setTimeZone(TimeZone.getTimeZone("UTC"));}}.format(new Date(created))+
                "\n\nLocal snapshot; capture time is not the source publication date. No new verification or permission is implied.\n\n"+
                (question.isEmpty()?"":"## Question\n\n"+question+"\n\n")+"## Content\n\n"+body+"\n\n## Source and coverage\n\n"+provenance+
                "\n\n## Personal note (not source evidence)\n\n"+note+"\n\n";
        }
    }
    NotebookStore(Context c){super(c,"reader-notebook.sqlite",null,1);}
    @Override public void onCreate(SQLiteDatabase db){db.execSQL("CREATE TABLE entries (id INTEGER PRIMARY KEY, created INTEGER NOT NULL, kind TEXT NOT NULL, title TEXT NOT NULL, question TEXT NOT NULL, body TEXT NOT NULL, provenance TEXT NOT NULL, note TEXT NOT NULL DEFAULT '', bookmark INTEGER NOT NULL DEFAULT 0)");}
    @Override public void onUpgrade(SQLiteDatabase db,int old,int next){throw new IllegalStateException("Unsupported notebook schema; existing records retained");}
    long add(String kind,String title,String question,String body,String provenance,boolean bookmark){
        if((title+question+body+provenance).getBytes(java.nio.charset.StandardCharsets.UTF_8).length>MAX_RECORD_BYTES)throw new IllegalArgumentException("Source exceeds the 2 MiB notebook limit; it has not been truncated or saved.");
        SQLiteDatabase db=getWritableDatabase();db.beginTransaction();try{
            try(Cursor c=db.rawQuery("SELECT count(*) FROM entries",null)){c.moveToFirst();if(c.getInt(0)>=MAX_RECORDS)throw new IllegalStateException("Notebook is full (200 records). Export or remove records before saving more.");}
            try(Cursor size=db.rawQuery("SELECT coalesce(sum(length(CAST(body AS BLOB))+length(CAST(provenance AS BLOB))),0) FROM entries",null)){size.moveToFirst();if(size.getLong(0)+(body+provenance).getBytes(java.nio.charset.StandardCharsets.UTF_8).length>16L*1024*1024)throw new IllegalStateException("Notebook content limit is 16 MiB. Export or remove records first.");}
            ContentValues v=new ContentValues();v.put("created",System.currentTimeMillis());v.put("kind",kind);v.put("title",title);v.put("question",question);v.put("body",body);v.put("provenance",provenance);v.put("bookmark",bookmark?1:0);
            long id=db.insertOrThrow("entries",null,v);db.setTransactionSuccessful();return id;
        }finally{db.endTransaction();}
    }
    List<Entry> list(String query,boolean bookmarks){
        List<Entry> entries=new ArrayList<>();String where=bookmarks?"bookmark=1":"1=1";
        String escaped=query.replace("\\","\\\\").replace("%","\\%").replace("_","\\_");
        try(Cursor c=getReadableDatabase().query("entries",null,where+" AND (title LIKE ? ESCAPE '\\' OR question LIKE ? ESCAPE '\\' OR note LIKE ? ESCAPE '\\')",new String[]{"%"+escaped+"%","%"+escaped+"%","%"+escaped+"%"},null,null,"created DESC, id DESC")){while(c.moveToNext())entries.add(read(c));}return entries;
    }
    Entry get(long id){try(Cursor c=getReadableDatabase().query("entries",null,"id=?",new String[]{Long.toString(id)},null,null,null)){if(!c.moveToFirst())throw new IllegalArgumentException("Saved record is unavailable or was removed.");return read(c);}}
    void update(long id,boolean bookmark,String note){if(note.length()>20000)throw new IllegalArgumentException("Notes are limited to 20,000 characters.");ContentValues v=new ContentValues();v.put("bookmark",bookmark?1:0);v.put("note",note);if(getWritableDatabase().update("entries",v,"id=?",new String[]{Long.toString(id)})!=1)throw new IllegalArgumentException("Saved record no longer exists.");}
    void note(long id,String note){if(note.length()>20000)throw new IllegalArgumentException("Notes are limited to 20,000 characters.");ContentValues v=new ContentValues();v.put("note",note);if(getWritableDatabase().update("entries",v,"id=?",new String[]{Long.toString(id)})!=1)throw new IllegalArgumentException("Saved record no longer exists.");}
    void remove(long id){getWritableDatabase().delete("entries","id=?",new String[]{Long.toString(id)});}
    private Entry read(Cursor c){Entry e=new Entry();e.id=c.getLong(c.getColumnIndexOrThrow("id"));e.created=c.getLong(c.getColumnIndexOrThrow("created"));e.kind=c.getString(c.getColumnIndexOrThrow("kind"));e.title=c.getString(c.getColumnIndexOrThrow("title"));e.question=c.getString(c.getColumnIndexOrThrow("question"));e.body=c.getString(c.getColumnIndexOrThrow("body"));e.provenance=c.getString(c.getColumnIndexOrThrow("provenance"));e.note=c.getString(c.getColumnIndexOrThrow("note"));e.bookmark=c.getInt(c.getColumnIndexOrThrow("bookmark"))!=0;return e;}
}
