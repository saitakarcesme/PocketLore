package org.pocketlore.app;
import android.content.*;import android.database.*;import android.net.Uri;import android.os.*;import android.provider.OpenableColumns;import java.io.*;
/** Test APK only: bounded public fixtures, never app user files. */
public final class PersonalFixtureProvider extends ContentProvider {
 private ParcelFileDescriptor held;public boolean onCreate(){return true;}
 File file(Uri uri)throws FileNotFoundException{String n=uri.getLastPathSegment();if(n==null||!n.matches("[a-z-]+\\.(txt|md|csv|json|pdf|plpack)"))throw new FileNotFoundException();return new File(getContext().getFilesDir(),n);}
 public Cursor query(Uri u,String[] p,String s,String[] a,String sort){MatrixCursor c=new MatrixCursor(new String[]{OpenableColumns.DISPLAY_NAME,OpenableColumns.SIZE});try{c.addRow(new Object[]{u.getLastPathSegment(),file(u).length()});}catch(Exception e){throw new IllegalArgumentException(e);}return c;}
 public String getType(Uri u){return "application/octet-stream";}
 public ParcelFileDescriptor openFile(Uri u,String mode)throws FileNotFoundException{if(u.getLastPathSegment().equals("stall.txt")||u.getLastPathSegment().equals("stall-export.plpack")){try{ParcelFileDescriptor[] pipe=ParcelFileDescriptor.createPipe();boolean writing=mode.contains("w");held=pipe[writing?0:1];return pipe[writing?1:0];}catch(IOException e){throw new FileNotFoundException(e.toString());}}return ParcelFileDescriptor.open(file(u),mode.contains("w")?ParcelFileDescriptor.MODE_CREATE|ParcelFileDescriptor.MODE_TRUNCATE|ParcelFileDescriptor.MODE_READ_WRITE:ParcelFileDescriptor.MODE_READ_ONLY);}
 public Bundle call(String method,String arg,Bundle extras){Bundle b=new Bundle();b.putBoolean("held",held!=null);if(method.equals("release")&&held!=null){try{held.close();}catch(Exception ignored){}held=null;}return b;}
 public int delete(Uri u,String s,String[] a){try{return file(u).delete()?1:0;}catch(Exception e){return 0;}}
 public Uri insert(Uri u,ContentValues v){throw new UnsupportedOperationException();}public int update(Uri u,ContentValues v,String s,String[] a){throw new UnsupportedOperationException();}
}
