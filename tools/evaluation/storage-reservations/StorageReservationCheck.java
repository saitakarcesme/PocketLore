package org.pocketlore.app;
import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public final class StorageReservationCheck {
    interface Action{void run()throws Exception;}
    static void require(boolean b){if(!b)throw new AssertionError();}
    static void rejects(Action a,String message)throws Exception{try{a.run();}catch(IOException e){require(e.getMessage().contains(message));return;}throw new AssertionError("Expected refusal: "+message);}
    static ResourceStorage.Ledger ledger(long used,long free){return new ResourceStorage.Ledger(()->new ResourceStorage.Snapshot(used,free));}
    static void receipt(String name,String extra){System.out.println("{\"fixture\":\""+name+"\",\"status\":\"PASS\","+extra+"}");}
    static long bytes(Path root)throws IOException{try(java.util.stream.Stream<Path> s=Files.walk(root)){return s.filter(Files::isRegularFile).mapToLong(p->{try{return Files.size(p);}catch(IOException e){throw new UncheckedIOException(e);}}).sum();}}
    public static void main(String[] args)throws Exception {
        Path root=Path.of(args[0]);Files.createDirectories(root);
        long reserve=ResourceStorage.RESERVE_BYTES;
        ResourceStorage.Ledger a=ledger(0,reserve+4096);
        try(ResourceStorage.Reservation r=a.reserve(4096)){require(a.reservedBytes()==4096);}
        rejects(()->ledger(0,reserve+4095).reserve(4096),"Insufficient");
        receipt("available-boundary","\"available_exact\":268439552");
        try(ResourceStorage.Reservation r=ledger(44_999_995_904L,Long.MAX_VALUE).reserve(4096)){require(r.projectedBytes==45_000_000_000L);}
        rejects(()->ledger(44_999_995_905L,Long.MAX_VALUE).reserve(4096),"45 GB");
        receipt("target-boundary","\"projected_exact\":45000000000");
        rejects(()->ledger(49_999_995_905L,Long.MAX_VALUE).reserve(4096),"50 GB");
        rejects(()->ledger(-1,Long.MAX_VALUE).reserve(1),"unknown");
        rejects(()->ledger(1,-1).reserve(1),"unknown");
        rejects(()->ledger(Long.MAX_VALUE,Long.MAX_VALUE).reserve(1),"overflow");
        rejects(()->ResourceStorage.stagePeak(Long.MAX_VALUE),"overflow");
        receipt("hard-boundary","\"unknown_and_overflow_rejected\":true");
        ResourceStorage.Ledger concurrent=ledger(0,reserve+8192);
        CountDownLatch start=new CountDownLatch(1),attempted=new CountDownLatch(2),release=new CountDownLatch(1);
        AtomicInteger admitted=new AtomicInteger(),denied=new AtomicInteger();AtomicReference<Throwable> failure=new AtomicReference<>();
        Runnable job=()->{ResourceStorage.Reservation token=null;try{start.await();try{token=concurrent.reserve(8192);admitted.incrementAndGet();}catch(IOException e){denied.incrementAndGet();}finally{attempted.countDown();}release.await();}catch(Throwable e){failure.set(e);}finally{if(token!=null)token.close();}};
        Thread one=new Thread(job),two=new Thread(job);one.start();two.start();start.countDown();
        try{require(attempted.await(5,TimeUnit.SECONDS));require(admitted.get()==1&&denied.get()==1&&concurrent.reservedBytes()==8192);}finally{release.countDown();one.join(5000);two.join(5000);}
        require(failure.get()==null&&concurrent.reservedBytes()==0);
        ResourceStorage.Reservation token=concurrent.reserve(8192);token.close();token.close();require(concurrent.reservedBytes()==0);
        receipt("concurrent","\"admitted\":1,\"denied\":1,\"remaining_reserved\":0");
        // Dynamic measured host fixture baseline; retained stages are counted on the next request.
        ResourceStorage.configure(()->new ResourceStorage.Snapshot(bytes(root),root.toFile().getUsableSpace()));
        File stage=root.resolve("model.partial").toFile();Path selected=root.resolve("selected.gguf");byte[] old="GGUFretained-user-fixture".getBytes(java.nio.charset.StandardCharsets.UTF_8);Files.write(selected,old);
        rejects(()->ModelImport.copy(new ByteArrayInputStream(new byte[8192]),stage,8192,Long.MAX_VALUE,()->true),"Cancelled");require(!stage.exists());
        InputStream failing=new InputStream(){int reads;public int read()throws IOException{if(++reads>32)throw new IOException("injected provider read failure");return 65;}};
        rejects(()->ModelImport.copy(failing,stage,8192,Long.MAX_VALUE,()->false),"injected");require(!stage.exists());
        AtomicBoolean cancelled=new AtomicBoolean();InputStream during=new ByteArrayInputStream(new byte[8192]){public synchronized int read(byte[] b,int o,int n){int result=super.read(b,o,Math.min(n,1024));cancelled.set(true);return result;}};
        rejects(()->ModelImport.copy(during,stage,8192,Long.MAX_VALUE,cancelled::get),"Cancelled");require(!stage.exists());
        receipt("release","\"before_during_cancel_and_failure_deleted_stage\":true");
        rejects(()->ModelImport.copy(new ByteArrayInputStream("BAD!".getBytes()),stage,4,Long.MAX_VALUE,()->false),"Not a GGUF");require(!stage.exists());require(Arrays.equals(old,Files.readAllBytes(selected)));
        byte[] valid="GGUFnew-bounded-fixture".getBytes(java.nio.charset.StandardCharsets.UTF_8);
        ModelImport.copy(new ByteArrayInputStream(valid),stage,valid.length,Long.MAX_VALUE,()->false);
        long peak=bytes(root);require(Arrays.equals(old,Files.readAllBytes(selected)));
        Files.move(stage.toPath(),selected,StandardCopyOption.ATOMIC_MOVE,StandardCopyOption.REPLACE_EXISTING);
        require(Arrays.equals(valid,Files.readAllBytes(selected))&&!stage.exists());
        // A reservation consuming all current available allowance proves no global tokens leaked.
        try(ResourceStorage.Reservation r=ResourceStorage.reserve(0)){require(r.projectedBytes==bytes(root));}
        receipt("rollback-retry","\"retry_coexistence_logical_bytes\":"+peak+",\"final_fixture_logical_bytes\":"+bytes(root)+",\"real_native_model\":false");
    }
}
