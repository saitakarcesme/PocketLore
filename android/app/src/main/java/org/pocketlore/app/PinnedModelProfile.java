package org.pocketlore.app;

import java.io.*;
import java.security.MessageDigest;
import java.util.function.BooleanSupplier;

/** Exact retained experimental weights only. Identity is not answer-quality qualification. */
final class PinnedModelProfile {
    static final String SHA256="7485fe6f11af29433bc51cab58009521f205840f5b4ae3a32fa7f92e8534fdf5";
    static final long BYTES=2497280256L;
    static boolean identity(String hash,long bytes){return BYTES==bytes&&SHA256.equals(hash);}
    static boolean verify(File file,BooleanSupplier cancel)throws Exception {
        if(!file.isFile()||file.length()!=BYTES)return false;
        long modified=file.lastModified(),count=0;
        MessageDigest digest=MessageDigest.getInstance("SHA-256");
        try(InputStream in=new FileInputStream(file)){
            byte[] buffer=new byte[65536];int n;
            while((n=in.read(buffer))!=-1){
                if(cancel.getAsBoolean()||Thread.currentThread().isInterrupted())throw new InterruptedIOException("Cancelled");
                if(count==0&&(n<4||buffer[0]!='G'||buffer[1]!='G'||buffer[2]!='U'||buffer[3]!='F'))return false;
                count+=n;if(count>BYTES)return false;digest.update(buffer,0,n);
            }
        }
        StringBuilder hash=new StringBuilder();for(byte b:digest.digest())hash.append(String.format(java.util.Locale.ROOT,"%02x",b&255));
        return count==BYTES&&file.length()==BYTES&&file.lastModified()==modified&&identity(hash.toString(),count);
    }
    private PinnedModelProfile(){}
}
