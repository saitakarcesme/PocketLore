package org.pocketlore.app;
import android.app.Instrumentation;import android.os.Bundle;import android.database.sqlite.SQLiteDatabase;import android.database.Cursor;
public final class ScaleProbeInstrumentation extends Instrumentation {
 @Override public void onCreate(Bundle b){super.onCreate(b);start();}
 @Override public void onStart(){Bundle b=new Bundle();try(SQLiteDatabase db=SQLiteDatabase.create(null)){try(Cursor c=db.rawQuery("select sqlite_version()",null)){c.moveToFirst();b.putString("sqlite",c.getString(0));}try{db.execSQL("create virtual table probe using fts5(title,body,content='')");db.execSQL("insert into probe(rowid,title,body) values(1,'Acid','chemistry')");try(Cursor c=db.rawQuery("select rowid from probe where probe match 'Acid' order by bm25(probe)",null)){if(!c.moveToFirst()||c.getInt(0)!=1)throw new AssertionError("FTS5 behavior");}b.putString("fts5","PASS");}catch(Exception e){b.putString("fts5",e.toString());}finish(-1,b);}catch(Exception e){b.putString("failure",e.toString());finish(1,b);}}
}
