package org.pocketlore.app;

import android.content.ContentResolver;
import android.content.res.AssetFileDescriptor;
import android.net.Uri;
import android.system.ErrnoException;
import android.system.Os;
import android.system.OsConstants;
import android.system.StructPollfd;
import java.io.*;
import java.util.function.BooleanSupplier;

/** Owns a document descriptor. Pipe reads wait in bounded polls, not uninterruptible stream reads. */
public final class DocumentInput extends InputStream {
    private final AssetFileDescriptor asset;
    private final BooleanSupplier cancelled;
    private long remaining;
    private boolean closed;
    private DocumentInput(AssetFileDescriptor asset,BooleanSupplier cancelled)throws IOException {
        this.asset=asset;this.cancelled=cancelled;remaining=asset.getDeclaredLength();
        try {
            int mode=Os.fstat(asset.getFileDescriptor()).st_mode;
            if(OsConstants.S_ISFIFO(mode)) {
                if(asset.getStartOffset()!=0)throw new IOException("Pipe document cannot have a byte offset");
                int flags=Os.fcntlInt(asset.getFileDescriptor(),OsConstants.F_GETFL,0);
                Os.fcntlInt(asset.getFileDescriptor(),OsConstants.F_SETFL,flags|OsConstants.O_NONBLOCK);
            } else if(OsConstants.S_ISREG(mode)) {
                Os.lseek(asset.getFileDescriptor(),asset.getStartOffset(),OsConstants.SEEK_SET);
            } else throw new IOException("Unsupported document descriptor; choose a local file or pipe-backed document");
        }catch(ErrnoException e){throw new IOException("Cannot prepare document descriptor",e);}
    }
    public static InputStream open(ContentResolver resolver,Uri uri,BooleanSupplier cancelled)throws IOException {
        check(cancelled);
        // Provider acquisition/open itself is a platform IPC and may require provider cooperation.
        AssetFileDescriptor asset=resolver.openAssetFileDescriptor(uri,"r");
        if(asset==null)throw new IOException("Cannot open document");
        try{check(cancelled);return new DocumentInput(asset,cancelled);}
        catch(IOException|RuntimeException|Error e){asset.close();throw e;}
    }
    private static void check(BooleanSupplier cancelled)throws InterruptedIOException {
        if(cancelled.getAsBoolean()||Thread.currentThread().isInterrupted())throw new InterruptedIOException("Import cancelled");
    }
    @Override public int read()throws IOException{byte[] b=new byte[1];return read(b,0,1)<0?-1:b[0]&255;}
    @Override public int read(byte[] b,int off,int len)throws IOException {
        if(off<0||len<0||off>b.length-len)throw new IndexOutOfBoundsException();
        if(closed)throw new IOException("Document is closed");
        check(cancelled);if(len==0)return 0;if(remaining==0)return -1;
        StructPollfd poll=new StructPollfd();poll.fd=asset.getFileDescriptor();poll.events=(short)OsConstants.POLLIN;
        while(true) {
            check(cancelled);
            try {
                if(Os.poll(new StructPollfd[]{poll},50)==0)continue;
                check(cancelled);
                int n=Os.read(poll.fd,b,off,(int)(remaining<0?len:Math.min(len,remaining)));
                check(cancelled);
                if(n==0){asset.getParcelFileDescriptor().checkError();if(remaining>0)throw new EOFException("Incomplete document");return -1;}
                if(remaining>0)remaining-=n;return n;
            }catch(ErrnoException e){
                check(cancelled);
                if(e.errno==OsConstants.EAGAIN||e.errno==OsConstants.EINTR)continue;
                throw new IOException("Document read failed",e);
            }
        }
    }
    @Override public void close()throws IOException{if(!closed){closed=true;asset.close();}}
}
