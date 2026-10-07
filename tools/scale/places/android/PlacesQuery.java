package org.pocketlore.places;
import android.database.Cursor;import android.database.sqlite.SQLiteDatabase;import android.os.CancellationSignal;import java.io.IOException;
/** The signal is registered before rawQuery and retained through lazy cursor iteration. */
public final class PlacesQuery implements AutoCloseable {
 public final Cursor cursor;private final PlacesBudget.Query lease;private final PlacesBudget budget;
 public PlacesQuery(SQLiteDatabase db,String sql,String[] args,PlacesBudget budget)throws IOException{
  this.budget=budget;CancellationSignal signal=new CancellationSignal();lease=budget.query(signal::cancel);Cursor c=null;
  try{budget.check();c=db.rawQuery(sql,args,signal);budget.check();cursor=c;}catch(IOException|RuntimeException|Error e){try{if(c!=null)c.close();}catch(Throwable close){e.addSuppressed(close);}finally{lease.close();}throw e;}
 }
 public boolean next()throws IOException{budget.check();boolean next=cursor.moveToNext();budget.check();return next;}
 public void close(){try{cursor.close();}finally{lease.close();}}
}
