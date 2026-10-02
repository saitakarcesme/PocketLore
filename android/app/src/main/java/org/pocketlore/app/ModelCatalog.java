package org.pocketlore.app;

import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.function.BooleanSupplier;

/** Pinned, app-private GGUF objects. The existing model.gguf alias remains the active contract. */
final class ModelCatalog {
    static final long TARGET=45_000_000_000L,HARD=50_000_000_000L;
    static final class Spec {
        final String name,repo,revision,filename,hash;final long bytes;
        Spec(String n,String r,String v,String f,String h,long b){name=n;repo=r;revision=v;filename=f;hash=h;bytes=b;}
        String url(){return "https://huggingface.co/"+repo+"/resolve/"+revision+"/"+filename;}
        String description(){return name+"\n"+bytes+" bytes · Apache-2.0\nSHA-256 "+hash+"\nRevision "+revision+"\nExperimental generation; no phone or independent quality qualification. Native admission still applies.";}
    }
    static final Spec[] SPECS={
        new Spec("Qwen2.5 0.5B Q4_K_M · demo baseline","Qwen/Qwen2.5-0.5B-Instruct-GGUF","9217f5db79a29953eb74d5343926648285ec7e67","qwen2.5-0.5b-instruct-q4_k_m.gguf","74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db",491400032L),
        new Spec("Qwen2.5 1.5B Q4_K_M · optional experiment","Qwen/Qwen2.5-1.5B-Instruct-GGUF","91cad51170dc346986eccefdc2dd33a9da36ead9","qwen2.5-1.5b-instruct-q4_k_m.gguf","6a1a2eb6d15622bf3c96857206351ba97e1af16c30d7a74ee38970e434e9407e",1117320736L),
        new Spec("Qwen3 1.7B Q8_0 · optional experiment","Qwen/Qwen3-1.7B-GGUF","90862c4b9d2787eaed51d12237eafdfe7c5f6077","Qwen3-1.7B-Q8_0.gguf","061b54daade076b5d3362dac252678d17da8c68f07560be70818cace6590cb1a",1834426016L)
    };
    final File files,root,active;
    ModelCatalog(File files)throws IOException {this.files=files;root=new File(files,"model-library");active=new File(files,"model.gguf");if(!root.isDirectory()&&!root.mkdirs())throw new IOException("Cannot create model catalog");}
    File object(Spec spec){return new File(root,spec.hash+".gguf");}
    static Spec identify(String hash,long size)throws IOException {for(Spec s:SPECS)if(s.hash.equals(hash)&&s.bytes==size)return s;throw new IOException("Model is not in the pinned compatible catalog; saved model unchanged");}
    static long admit(long retained,long incoming,long available)throws IOException {
        if(incoming<0||incoming>ModelImport.MAX_BYTES||retained<0||retained>HARD-2*incoming-ResourceStorage.RESERVE_BYTES)throw new IOException("Model transaction exceeds the 50 GB hard limit including reserve");
        ResourceStorage.requireSpace(incoming,available);return retained+2*incoming+ResourceStorage.RESERVE_BYTES;
    }
    Spec verify(File file,BooleanSupplier cancel)throws Exception {
        java.security.MessageDigest digest=java.security.MessageDigest.getInstance("SHA-256");
        try(InputStream in=new FileInputStream(file)){byte[] b=new byte[65536];int n;while((n=in.read(b))!=-1){PersonalText.check(cancel);digest.update(b,0,n);}}
        PersonalText.check(cancel);StringBuilder h=new StringBuilder();for(byte b:digest.digest())h.append(String.format(java.util.Locale.ROOT,"%02x",b&255));return identify(h.toString(),file.length());
    }
    Spec retainActive(BooleanSupplier cancel)throws Exception {
        Spec spec=verify(active,cancel);File dst=object(spec);
        if(!dst.exists())Files.createLink(dst.toPath(),active.toPath());else if(!Files.isSameFile(dst.toPath(),active.toPath()))verify(dst,cancel);
        return spec;
    }
    void retainStage(File stage,Spec spec,BooleanSupplier cancel)throws Exception {
        if(verify(stage,cancel)!=spec)throw new IOException("Selected catalog model does not match imported bytes");
        File dst=object(spec);if(dst.exists()){if(verify(dst,cancel)!=spec)throw new IOException("Stored model corrupt");stage.delete();}
        else Files.move(stage.toPath(),dst.toPath(),StandardCopyOption.ATOMIC_MOVE);
    }
    void activate(Spec spec,BooleanSupplier cancel)throws Exception {
        File candidate=object(spec);if(verify(candidate,cancel)!=spec)throw new IOException("Stored model corrupt");
        File link=new File(files,"model-select.partial");Files.deleteIfExists(link.toPath());
        try{Files.createLink(link.toPath(),candidate.toPath());PersonalText.check(cancel);Files.move(link.toPath(),active.toPath(),StandardCopyOption.ATOMIC_MOVE,StandardCopyOption.REPLACE_EXISTING);}
        finally{Files.deleteIfExists(link.toPath());}
    }
    void remove(Spec spec)throws Exception {File file=object(spec);if(active.exists()&&file.exists()&&Files.isSameFile(active.toPath(),file.toPath()))throw new IOException("Unload and remove the active model first");Files.deleteIfExists(file.toPath());}
}
