package org.pocketlore.app;

import java.io.*;
import java.util.function.BooleanSupplier;

/** Only app-owned import stages are removable; no general cache-directory deletion. */
public final class ResourceStorage {
    public static final long RESERVE_BYTES=256L*1024*1024;
    public static void requireSpace(long incoming,long available)throws IOException {
        if(incoming<0 || available<RESERVE_BYTES || incoming>available-RESERVE_BYTES)throw new IOException("Insufficient storage: import requires its full size plus a 256 MiB reserve");
    }
    public static void copy(InputStream in,File stage,long limit,BooleanSupplier cancelled)throws IOException {
        try(FileOutputStream out=new FileOutputStream(stage)){
            byte[] buffer=new byte[65536];long total=0;int n;
            while(true){if(cancelled.getAsBoolean() || Thread.currentThread().isInterrupted())throw new InterruptedIOException("Import cancelled");n=in.read(buffer);if(n<0)break;total+=n;if(total>limit)throw new IOException("Import exceeds size limit");out.write(buffer,0,n);}
            if(cancelled.getAsBoolean())throw new InterruptedIOException("Import cancelled");out.getFD().sync();
        }catch(IOException|RuntimeException|OutOfMemoryError e){stage.delete();throw e;}
    }
    public static int cleanupPackStages(File dir){return cleanup(dir,false);}
    public static int cleanupModelStage(File dir){return cleanup(dir,true);}
    private static int cleanup(File dir,boolean model){int count=0;File[] files=dir.listFiles();if(files==null)return 0;for(File f:files){String n=f.getName();if((model?n.equals("model.partial"):n.matches("pack-[0-9]+\\.partial"))&&f.isFile()&&f.delete())count++;}return count;}
    private ResourceStorage(){}
}
