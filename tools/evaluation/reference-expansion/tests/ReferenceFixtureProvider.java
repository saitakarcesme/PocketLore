package org.pocketlore.app;
import android.content.*;import android.database.*;import android.net.Uri;import android.os.*;import android.provider.OpenableColumns;import java.io.*;
/** Test-only provider restricted to invocation-owned public collection bytes. */
public final class ReferenceFixtureProvider extends ContentProvider {
 public boolean onCreate(){return true;}
 File file(Uri uri)throws FileNotFoundException{java.util.List<String> parts=uri.getPathSegments();if(parts.size()!=2||!parts.get(0).matches("[A-Za-z0-9-]+")||!parts.get(1).matches("[a-z-]+\\.plpack"))throw new FileNotFoundException("Invalid fixture path");return new File(new File(getContext().getFilesDir(),"reference-expansion-"+parts.get(0)),parts.get(1));}
 public Cursor query(Uri u,String[] projection,String selection,String[] args,String sort){String[] cols=projection==null?new String[]{OpenableColumns.DISPLAY_NAME,OpenableColumns.SIZE}:projection;MatrixCursor c=new MatrixCursor(cols);try{Object[] row=new Object[cols.length];for(int i=0;i<cols.length;i++)row[i]=cols[i].equals(OpenableColumns.SIZE)?file(u).length():u.getLastPathSegment();c.addRow(row);return c;}catch(Exception e){throw new IllegalArgumentException(e);}}
 public String getType(Uri uri){return "application/zip";}
 public ParcelFileDescriptor openFile(Uri u,String mode)throws FileNotFoundException{if(mode.contains("w")){if(!"export.plpack".equals(u.getLastPathSegment()))throw new FileNotFoundException("Only invocation-owned export is writable");return ParcelFileDescriptor.open(file(u),ParcelFileDescriptor.MODE_CREATE|ParcelFileDescriptor.MODE_TRUNCATE|ParcelFileDescriptor.MODE_READ_WRITE);}return ParcelFileDescriptor.open(file(u),ParcelFileDescriptor.MODE_READ_ONLY);}
 public Uri insert(Uri u,ContentValues v){throw new UnsupportedOperationException();}public int update(Uri u,ContentValues v,String s,String[] a){throw new UnsupportedOperationException();}public int delete(Uri u,String s,String[] a){throw new UnsupportedOperationException();}
}
