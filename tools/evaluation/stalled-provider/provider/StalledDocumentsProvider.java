package org.pocketlore.app;

import android.database.*;
import android.os.*;
import android.provider.*;
import java.io.*;
import java.util.concurrent.*;

/** Test APK only. Bounded, synthetic transport fixtures; never installed in the product APK. */
public final class StalledDocumentsProvider extends DocumentsProvider {
    private volatile CountDownLatch release=new CountDownLatch(1);
    private volatile String state="idle";
    private volatile int opens;
    @Override public boolean onCreate(){
        for(String kind:new String[]{"model","pack"})for(String mode:new String[]{"stall-empty","stall-prefix","short","retry"})
            getContext().grantUriPermission("org.pocketlore.app",DocumentsContract.buildDocumentUri("org.pocketlore.fixture.documents",kind+"-"+mode),android.content.Intent.FLAG_GRANT_READ_URI_PERMISSION);
        return true;
    }
    @Override public Cursor queryRoots(String[] projection){return new MatrixCursor(new String[]{DocumentsContract.Root.COLUMN_ROOT_ID});}
    @Override public Cursor queryChildDocuments(String id,String[] projection,String sort){return new MatrixCursor(new String[]{DocumentsContract.Document.COLUMN_DOCUMENT_ID});}
    @Override public Cursor queryDocument(String id,String[] projection){
        MatrixCursor c=new MatrixCursor(new String[]{DocumentsContract.Document.COLUMN_DOCUMENT_ID,OpenableColumns.DISPLAY_NAME,OpenableColumns.SIZE,DocumentsContract.Document.COLUMN_MIME_TYPE});
        c.addRow(new Object[]{id,id,id.startsWith("model")?8:new File(getContext().getFilesDir(),"reference.plpack").length(),"application/octet-stream"});return c;
    }
    @Override public Bundle call(String method,String arg,Bundle extras){
        if(method.equals("release"))release.countDown();
        if(method.equals("reset")){release.countDown();release=new CountDownLatch(1);state="idle";opens=0;}
        Bundle b=new Bundle();b.putString("state",state);b.putInt("opens",opens);return b;
    }
    @Override public ParcelFileDescriptor openDocument(String id,String mode,CancellationSignal signal)throws FileNotFoundException {
        opens++;if(signal!=null)signal.throwIfCanceled();
        try {
            ParcelFileDescriptor[] pipe=ParcelFileDescriptor.createPipe();CountDownLatch gate=release;
            new Thread(()->{
                try(OutputStream out=new ParcelFileDescriptor.AutoCloseOutputStream(pipe[1])) {
                    boolean model=id.startsWith("model");
                    byte[] bytes=model?"GGUFtest".getBytes(java.nio.charset.StandardCharsets.UTF_8):java.nio.file.Files.readAllBytes(new File(getContext().getFilesDir(),"reference.plpack").toPath());
                    if(id.contains("stall")) {
                        if(id.endsWith("prefix"))out.write(bytes,0,4);
                        state="stalled";gate.await(15,TimeUnit.SECONDS);
                        // After release a write proves whether the importer closed its endpoint.
                        out.write(bytes);state="released-with-reader";
                    } else if(id.endsWith("short")){out.write(bytes,0,4);state="short-eof";}
                    else {for(int off=0;off<bytes.length;off+=7)out.write(bytes,off,Math.min(7,bytes.length-off));state="complete";}
                }catch(IOException closed){state="reader-closed";}catch(InterruptedException e){state="interrupted";}
            },"fixture-writer").start();return pipe[0];
        }catch(IOException e){throw new FileNotFoundException(e.toString());}
    }
}
