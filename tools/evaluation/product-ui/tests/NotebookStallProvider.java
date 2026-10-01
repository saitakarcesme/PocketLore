package org.pocketlore.app;
import android.content.*;import android.database.Cursor;import android.net.Uri;import android.os.*;import android.system.*;import java.io.*;
/** Test-only destination: deliberately retains a pipe without draining it. */
public final class NotebookStallProvider extends ContentProvider {
 private ParcelFileDescriptor reader;
 public boolean onCreate(){return true;}
 public synchronized ParcelFileDescriptor openFile(Uri uri,String mode)throws FileNotFoundException{
  try {if(uri.getLastPathSegment().equals("success"))return ParcelFileDescriptor.open(new File(getContext().getFilesDir(),"notebook-retry.md"),mode.contains("w")?ParcelFileDescriptor.MODE_CREATE|ParcelFileDescriptor.MODE_TRUNCATE|ParcelFileDescriptor.MODE_READ_WRITE:ParcelFileDescriptor.MODE_READ_ONLY);
   if(reader!=null)reader.close();ParcelFileDescriptor[] pipe=ParcelFileDescriptor.createPipe();reader=pipe[0];return pipe[1];
  }catch(IOException e){throw new FileNotFoundException(e.toString());}
 }
 public synchronized Bundle call(String method,String arg,Bundle extras){Bundle b=new Bundle();try{
  b.putBoolean("opened",reader!=null);
  if(reader!=null){StructPollfd p=new StructPollfd();p.fd=reader.getFileDescriptor();p.events=(short)OsConstants.POLLIN;Os.poll(new StructPollfd[]{p},0);b.putBoolean("closed",(p.revents&OsConstants.POLLHUP)!=0);}
  if(method.equals("release")&&reader!=null){reader.close();reader=null;}
 }catch(Exception e){throw new IllegalStateException(e);}return b;}
 public String getType(Uri u){return "text/markdown";}public Cursor query(Uri u,String[]p,String s,String[]a,String o){return null;}public Uri insert(Uri u,ContentValues v){throw new UnsupportedOperationException();}public int update(Uri u,ContentValues v,String s,String[]a){throw new UnsupportedOperationException();}public int delete(Uri u,String s,String[]a){return 0;}
}
