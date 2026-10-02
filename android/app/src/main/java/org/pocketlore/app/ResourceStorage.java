package org.pocketlore.app;

import java.io.*;
import java.util.function.BooleanSupplier;

/** Only app-owned import stages are removable; no general cache-directory deletion. */
public final class ResourceStorage {
    public static final long RESERVE_BYTES=256L*1024*1024;
    public static final long TARGET_BYTES=45_000_000_000L,HARD_BYTES=50_000_000_000L;
    /** Snapshot must include the current app data and package; unknown values fail closed. */
    public static final class Snapshot {
        public final long used,available;
        public Snapshot(long used,long available){this.used=used;this.available=available;}
    }
    public interface Meter { Snapshot sample() throws IOException; }
    public static final class Ledger {
        private final Meter meter;
        private long reserved;
        public Ledger(Meter meter){this.meter=java.util.Objects.requireNonNull(meter);}
        public synchronized long reservedBytes(){return reserved;}
        public synchronized Reservation reserve(long peak)throws IOException {
            Snapshot s=meter.sample();
            if(s==null||s.used<0||s.available<0||peak<0)throw new IOException("Storage usage unknown or invalid");
            final long total,held;
            try{held=Math.addExact(reserved,peak);total=Math.addExact(s.used,held);}
            catch(ArithmeticException e){throw new IOException("Storage accounting overflow",e);}
            if(total>HARD_BYTES)throw new IOException("Projected app-owned storage exceeds 50 GB hard cap");
            if(total>TARGET_BYTES)throw new IOException("Projected app-owned storage exceeds 45 GB target; remove or reallocate assets first");
            requireSpace(held,s.available);
            reserved=held;return new Reservation(this,peak,total);
        }
    }
    public static final class Reservation implements AutoCloseable {
        private final Ledger ledger;private final long bytes;private boolean closed;
        public final long projectedBytes;
        private Reservation(Ledger ledger,long bytes,long projected){this.ledger=ledger;this.bytes=bytes;projectedBytes=projected;}
        public void close(){synchronized(ledger){if(!closed){ledger.reserved-=bytes;closed=true;}}}
    }
    private static Ledger appLedger;
    public static synchronized void configure(Meter meter){
        if(appLedger!=null)throw new IllegalStateException("Storage meter already configured");
        appLedger=new Ledger(meter);
    }
    public static Reservation reserve(long peak)throws IOException {
        Ledger ledger;synchronized(ResourceStorage.class){ledger=appLedger;}
        if(ledger==null)throw new IOException("App storage measurement unavailable");
        return ledger.reserve(peak);
    }
    /** Conservative stage allocation: payload plus bounded filesystem/transaction headroom. */
    public static long stagePeak(long bytes)throws IOException {
        if(bytes<0)throw new IOException("Unknown stage size");
        try{return Math.addExact(bytes,1024L*1024);}
        catch(ArithmeticException e){throw new IOException("Stage size overflow",e);}
    }
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
