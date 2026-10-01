package org.pocketlore.app;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.nio.file.attribute.BasicFileAttributes;
import java.security.MessageDigest;
import java.util.*;
import java.util.function.BooleanSupplier;
import java.util.zip.*;
import org.json.*;

/** Version 2 delta transaction. Unchanged content is referenced in a shared immutable object directory. */
final class SharedShardUpdate {
    static void collect(ScaleLibrary lib)throws Exception {
        Set<String> live=new HashSet<>();
        for(ScaleLibrary.Entry e:lib.entries())if(e.manifest.getInt("version")==2){JSONArray fs=e.manifest.getJSONArray("files");for(int i=0;i<fs.length();i++)live.add(fs.getJSONObject(i).getString("sha256"));}
        File objects=new File(lib.root,"objects");
        if(objects.isDirectory())for(File f:Objects.requireNonNull(objects.listFiles()))if(f.getName().matches("[a-f0-9]{64}")&&!live.contains(f.getName()))ScaleLibrary.removeTree(f);
    }
    static long uniqueBytes(File root) throws IOException {
        Set<Object> inodes = new HashSet<>();
        final long[] sum = {0};
        try (java.util.stream.Stream<Path> paths = Files.walk(root.toPath())) {
            for (Iterator<Path> it = paths.iterator(); it.hasNext();) {
                Path p = it.next();
                if (Files.isSymbolicLink(p)) throw new IOException("Unexpected managed symlink");
                BasicFileAttributes a = Files.readAttributes(p, BasicFileAttributes.class);
                if (!a.isRegularFile()) continue;
                // A filesystem without inode identities is conservatively over-counted.
                Object key = a.fileKey();
                if (key == null || inodes.add(key)) sum[0] = Math.addExact(sum[0], a.size());
            }
        }
        return sum[0];
    }
    static long admit(long retained, long newBytes, long metadata, long usable) throws Exception {
        long incoming = Math.addExact(newBytes, metadata);
        long peak = Math.addExact(retained, Math.addExact(Math.addExact(incoming,newBytes), 128L*1024*1024));
        ScaleLibrary.check(peak <= ScaleLibrary.HARD, "Joint hard storage limit");
        ResourceStorage.requireSpace(incoming, usable);
        return peak;
    }
    static ScaleLibrary.Entry install(ScaleLibrary library, ZipInputStream zip, byte[] raw,
            JSONObject manifest, List<ScaleLibrary.Entry> old, BooleanSupplier cancel) throws Exception {
        String collection = manifest.getString("collection_key");
        ScaleLibrary.check(collection.matches("[a-z0-9][a-z0-9-]{0,79}"), "Invalid collection key");
        String replaces = manifest.getString("replaces");
        ScaleLibrary.Entry previous = null;
        Map<String,File> available = new HashMap<>();
        for (ScaleLibrary.Entry e : old) {
            if (e.id.equals(replaces)) previous = e;
            JSONArray fs = e.manifest.getJSONArray("files");
            for (int i=0;i<fs.length();i++) {
                JSONObject f=fs.getJSONObject(i);
                if(e.manifest.getInt("version")==2)available.put(f.getString("sha256"),ScaleLibrary.resolve(e.directory,f.getString("path")));
            }
            if (collection.equals(e.manifest.optString("collection_key")))
                ScaleLibrary.check(e.id.equals(replaces), "Stale collection update");
        }
        ScaleLibrary.check(replaces.isEmpty() || previous != null, "Missing delta base");
        if (previous != null) {
            ScaleLibrary.check(previous.kind().equals(manifest.getString("kind")), "Collection kind changed");
            String priorKey=previous.manifest.optString("collection_key");
            ScaleLibrary.check(priorKey.isEmpty() || priorKey.equals(collection), "Collection key changed");
        }
        ScaleLibrary.check(previous != null || old.size()<64, "Collection count limit");
        JSONArray files=manifest.getJSONArray("files");
        long incoming=0;
        for(int i=0;i<files.length();i++) {
            JSONObject f=files.getJSONObject(i);
            if(f.getBoolean("payload")) incoming=Math.addExact(incoming,f.getLong("bytes"));
            else ScaleLibrary.check(available.containsKey(f.getString("sha256")),"Missing shared content");
        }
        library.lastAdmissionPeak=admit(uniqueBytes(library.root.getParentFile()),incoming,raw.length+1048576L,library.root.getUsableSpace());
        File objects=new File(library.root,"objects");ScaleLibrary.check(objects.isDirectory()||objects.mkdirs(),"Create object directory");
        File stage=Files.createTempDirectory(library.root.toPath(),"pending-").toFile();
        String id=ScaleLibrary.hex(MessageDigest.getInstance("SHA-256").digest(raw));
        File dest=new File(library.root,id);boolean moved=false,committed=false;
        library.lastTemporaryPeak=raw.length;library.lastPhysicalPeak=uniqueBytes(library.root.getParentFile());
        try {
            ScaleLibrary.write(new File(stage,"manifest.json"),raw);
            long copied=raw.length;byte[] buffer=new byte[65536];
            for(int i=0;i<files.length();i++) {
                ScaleLibrary.cancelled(cancel);JSONObject f=files.getJSONObject(i);
                File target=ScaleLibrary.safe(stage,f.getString("path"));
                ScaleLibrary.check(target.getParentFile().isDirectory()||target.getParentFile().mkdirs(),"Create shared path");
                if(!f.getBoolean("payload")) {
                    File source=available.get(f.getString("sha256"));
                    ScaleLibrary.check(source.length()==f.getLong("bytes")&&ScaleLibrary.hash(source,cancel).equals(f.getString("sha256")),"Changed shared content");
                    // Manifest references this verified existing object; no copy or link.
                } else {
                    ZipEntry entry=zip.getNextEntry();
                    ScaleLibrary.check(entry!=null&&!entry.isDirectory()&&entry.getName().equals(f.getString("path")),"Delta archive order mismatch");
                    MessageDigest digest=MessageDigest.getInstance("SHA-256");long size=0;
                    try(FileOutputStream out=new FileOutputStream(target)) {
                        int n;while((n=zip.read(buffer))!=-1) {
                            ScaleLibrary.cancelled(cancel);size+=n;
                            ScaleLibrary.check(size<=f.getLong("bytes"),"Overlong delta content");
                            out.write(buffer,0,n);digest.update(buffer,0,n);copied+=n;
                            library.lastTemporaryPeak=Math.max(library.lastTemporaryPeak,copied);
                        }
                        out.getFD().sync();
                    }
                    ScaleLibrary.check(size==f.getLong("bytes")&&ScaleLibrary.hex(digest.digest()).equals(f.getString("sha256")),"Delta content integrity");
                    File object=new File(objects,f.getString("sha256"));
                    if(object.exists()){ScaleLibrary.check(ScaleLibrary.hash(object,cancel).equals(f.getString("sha256")),"Changed existing object");Files.delete(target.toPath());}
                    else Files.move(target.toPath(),object.toPath(),StandardCopyOption.ATOMIC_MOVE);
                }
            }
            library.lastPhysicalPeak=Math.max(library.lastPhysicalPeak,uniqueBytes(library.root.getParentFile()));
            ScaleLibrary.check(zip.getNextEntry()==null,"Unlisted delta content");
            ScaleLibrary.verifySchema(stage,manifest,cancel);ScaleLibrary.cancelled(cancel);
            ScaleLibrary.check(!dest.exists(),"Uncatalogued delta destination");
            Files.move(stage.toPath(),dest.toPath(),StandardCopyOption.ATOMIC_MOVE);moved=true;
            ScaleLibrary.Entry result=new ScaleLibrary.Entry(id,previous==null||previous.active,dest,manifest);
            List<ScaleLibrary.Entry> next=new ArrayList<>();
            for(ScaleLibrary.Entry e:old)if(e!=previous)next.add(e);
            next.add(result);library.commit(next);committed=true;
            // A cleanup failure after commit is recoverable; never remove the new live edition.
            if(previous!=null)try{ScaleLibrary.removeTree(previous.directory);}catch(IOException ignored){}
            return result;
        } finally {
            if(stage.exists())ScaleLibrary.removeTree(stage);
            if(moved&&!committed&&dest.exists())ScaleLibrary.removeTree(dest);
            collect(library);
        }
    }
}
