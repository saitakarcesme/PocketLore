package org.pocketlore.app;
import android.content.*;import android.database.*;import android.net.Uri;import android.os.*;import android.provider.OpenableColumns;import java.io.*;import java.nio.charset.StandardCharsets;import org.json.*;
/** Test-only read provider for frozen public UI fixtures; no private file access. */
public final class PersonalFixtureProvider extends ContentProvider {
 public boolean onCreate(){return true;}
 byte[] bytes(Uri u)throws Exception{String key;if(u.getLastPathSegment().equals("invalid.json"))key="invalid_document";else if(u.getLastPathSegment().equals("accessible.txt"))key="document";else throw new FileNotFoundException();try(InputStream in=getContext().getAssets().open("cases.json")){return new JSONObject(new String(in.readAllBytes(),StandardCharsets.UTF_8)).getString(key).getBytes(StandardCharsets.UTF_8);}}
 public Cursor query(Uri u,String[] p,String s,String[] a,String sort){try{MatrixCursor c=new MatrixCursor(new String[]{OpenableColumns.DISPLAY_NAME,OpenableColumns.SIZE});c.addRow(new Object[]{u.getLastPathSegment(),bytes(u).length});return c;}catch(Exception e){throw new IllegalArgumentException(e);}}
 public String getType(Uri u){return "application/octet-stream";}
 public ParcelFileDescriptor openFile(Uri u,String mode)throws FileNotFoundException{try{if(!mode.equals("r"))throw new IOException("Read-only fixture");byte[] data=bytes(u);ParcelFileDescriptor[] pipe=ParcelFileDescriptor.createPipe();new Thread(()->{try(OutputStream out=new ParcelFileDescriptor.AutoCloseOutputStream(pipe[1])){out.write(data);}catch(IOException ignored){}}).start();return pipe[0];}catch(Exception e){throw new FileNotFoundException(e.toString());}}
 public int delete(Uri u,String s,String[] a){throw new UnsupportedOperationException();}public Uri insert(Uri u,ContentValues v){throw new UnsupportedOperationException();}public int update(Uri u,ContentValues v,String s,String[] a){throw new UnsupportedOperationException();}
}
