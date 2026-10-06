package org.pocketlore.app;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.function.BooleanSupplier;

/** Expiry only for new, explicitly owned share snapshots; legacy files remain untouched. */
final class NotebookShareLease {
    static final long LIFETIME_MS=24L*60*60*1000;
    static final String SUFFIX=".share-owned-v523";
    static String digest(File file,BooleanSupplier cancelled)throws IOException{
        try(InputStream in=new FileInputStream(file)){
            MessageDigest md=MessageDigest.getInstance("SHA-256");byte[] bytes=new byte[16384];int n;
            while((n=in.read(bytes))!=-1){if(cancelled.getAsBoolean())throw new IOException("Share cleanup cancelled");md.update(bytes,0,n);}
            StringBuilder hex=new StringBuilder();for(byte b:md.digest())hex.append(String.format(java.util.Locale.ROOT,"%02x",b&255));return hex.toString();
        }catch(java.security.NoSuchAlgorithmException e){throw new IOException(e);}
    }
    static void record(File file,long now,BooleanSupplier cancelled)throws IOException{
        if(!file.getName().matches("notebook-[a-f0-9-]+\\.md")||file.length()>32L*1024*1024)throw new IOException("Invalid owned share snapshot");
        File receipt=new File(file.getPath()+SUFFIX);if(!receipt.createNewFile())throw new IOException("Share ownership receipt already exists");
        try(FileOutputStream out=new FileOutputStream(receipt)){
            out.write((now+"\n"+file.length()+"\n"+digest(file,cancelled)+"\n").getBytes(StandardCharsets.US_ASCII));out.getFD().sync();
        }catch(IOException e){receipt.delete();throw e;}
    }
    static int expire(File directory,long now,BooleanSupplier cancelled)throws IOException{
        File[] files=directory.listFiles();if(files==null)throw new IOException("Share storage cannot be inspected");int removed=0;
        // The enclosing notebook cache has an independent 64 MiB byte bound.
        for(File receipt:files){if(cancelled.getAsBoolean())throw new IOException("Share cleanup cancelled");String name=receipt.getName();
            if(!name.endsWith(SUFFIX)||receipt.length()>256)continue;
            String base=name.substring(0,name.length()-SUFFIX.length());if(!base.matches("notebook-[a-f0-9-]+\\.md"))continue;
            File file=new File(directory,base);if(!file.isFile()||!file.getCanonicalFile().getParentFile().equals(directory.getCanonicalFile()))continue;
            String[] parts;try(InputStream in=new FileInputStream(receipt)){parts=new String(in.readNBytes(257),StandardCharsets.US_ASCII).split("\n");}
            try{if(parts.length!=3)continue;long created=Long.parseLong(parts[0]),length=Long.parseLong(parts[1]);
                if(created<0||now<created||now-created<LIFETIME_MS||length<0||length>32L*1024*1024||file.length()!=length||!parts[2].matches("[a-f0-9]{64}"))continue;
                if(!digest(file,cancelled).equals(parts[2]))continue;
                if(file.delete()){receipt.delete();removed++;}
            }catch(NumberFormatException ignored){/* Invalid ownership never authorizes deletion. */}
        }return removed;
    }
}
