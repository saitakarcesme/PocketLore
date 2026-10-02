package org.pocketlore.app;
import android.content.*;import android.database.*;import android.net.Uri;import android.os.*;import android.provider.OpenableColumns;import java.io.*;
public final class ModelFixtureProvider extends ContentProvider {
 public boolean onCreate(){return true;}
 File file(){return new File(getContext().getFilesDir(),"baseline.gguf");}
 public ParcelFileDescriptor openFile(Uri u,String mode)throws FileNotFoundException{return ParcelFileDescriptor.open(file(),ParcelFileDescriptor.MODE_READ_ONLY);}
 public Cursor query(Uri u,String[]p,String s,String[]a,String o){MatrixCursor c=new MatrixCursor(new String[]{OpenableColumns.SIZE});c.addRow(new Object[]{file().length()});return c;}
 public String getType(Uri u){return "application/octet-stream";}public Uri insert(Uri u,ContentValues v){throw new UnsupportedOperationException();}public int update(Uri u,ContentValues v,String s,String[]a){return 0;}public int delete(Uri u,String s,String[]a){return 0;}
}
