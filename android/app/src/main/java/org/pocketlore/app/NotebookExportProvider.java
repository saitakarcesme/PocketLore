package org.pocketlore.app;

import android.content.*;
import android.database.*;
import android.net.Uri;
import android.os.ParcelFileDescriptor;
import android.provider.OpenableColumns;
import java.io.*;

/** Read-only, explicitly granted export files; no source/catalog access. */
public final class NotebookExportProvider extends ContentProvider {
    public boolean onCreate(){return true;}
    private File file(Uri uri)throws FileNotFoundException {
        String name=uri.getLastPathSegment();
        if(uri.getPathSegments().size()!=1||name==null||!name.matches("notebook-[a-f0-9-]+\\.md"))throw new FileNotFoundException("Invalid export");
        File f=new File(new File(getContext().getCacheDir(),"notebook-exports"),name);
        if(!f.isFile())throw new FileNotFoundException("Export no longer available");return f;
    }
    public String getType(Uri uri){return "text/markdown";}
    public ParcelFileDescriptor openFile(Uri uri,String mode)throws FileNotFoundException {if(!"r".equals(mode))throw new FileNotFoundException("Read-only export");return ParcelFileDescriptor.open(file(uri),ParcelFileDescriptor.MODE_READ_ONLY);}
    public Cursor query(Uri uri,String[] projection,String selection,String[] args,String order){try{File f=file(uri);String[] columns=projection==null?new String[]{OpenableColumns.DISPLAY_NAME,OpenableColumns.SIZE}:projection;MatrixCursor c=new MatrixCursor(columns);Object[] row=new Object[columns.length];for(int i=0;i<columns.length;i++)row[i]=OpenableColumns.DISPLAY_NAME.equals(columns[i])?f.getName():OpenableColumns.SIZE.equals(columns[i])?f.length():null;c.addRow(row);return c;}catch(IOException e){throw new IllegalArgumentException(e);}}
    public Uri insert(Uri u,ContentValues v){throw new UnsupportedOperationException();}
    public int update(Uri u,ContentValues v,String s,String[] a){throw new UnsupportedOperationException();}
    public int delete(Uri u,String s,String[] a){throw new UnsupportedOperationException();}
}
