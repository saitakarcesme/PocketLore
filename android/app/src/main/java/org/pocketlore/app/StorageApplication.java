package org.pocketlore.app;

import android.app.Application;
import android.system.Os;
import android.system.OsConstants;
import android.system.StructStat;
import java.io.*;
import java.util.*;

/** Same-process admission for app-private files and APKs, not provider/whole-device accounting. */
public final class StorageApplication extends Application {
    @Override public void onCreate(){
        super.onCreate();
        ResourceStorage.configure(()->{
            Set<String> seen=new HashSet<>();int[] count={0};
            try {
                File nativeDir=new File(getApplicationInfo().nativeLibraryDir).getCanonicalFile();
                long used=measure(new File(getApplicationInfo().dataDir),seen,count,nativeDir);
                used=Math.addExact(used,measure(new File(getApplicationInfo().sourceDir),seen,count,nativeDir));
                // Uncompressed libraries can remain inside APKs; extracted libraries are counted when present.
                if(nativeDir.exists())used=Math.addExact(used,measure(nativeDir,seen,count,nativeDir));
                String[] splits=getApplicationInfo().splitSourceDirs;
                if(splits!=null)for(String path:splits)used=Math.addExact(used,measure(new File(path),seen,count,nativeDir));
                return new ResourceStorage.Snapshot(used,new File(getApplicationInfo().dataDir).getUsableSpace());
            } catch(Exception e){throw new IOException("Cannot measure app/package storage; import denied",e);}
        });
    }
    private static long measure(File file,Set<String> seen,int[] count,File nativeDir)throws Exception {
        if(++count[0]>200000)throw new IOException("Storage inventory exceeds bounded traversal");
        StructStat s=Os.lstat(file.getPath());
        if(!seen.add(s.st_dev+":"+s.st_ino))return 0;
        if(OsConstants.S_ISLNK(s.st_mode)){
            File target=file.getCanonicalFile();
            if(!target.equals(nativeDir))throw new IOException("Unaccounted symbolic link in app storage");
            return Math.addExact(Math.max(s.st_size,Math.multiplyExact(s.st_blocks,512L)),measure(target,seen,count,nativeDir));
        }
        long bytes=Math.max(s.st_size,Math.multiplyExact(s.st_blocks,512L));
        if(OsConstants.S_ISDIR(s.st_mode)){
            File[] children=file.listFiles();if(children==null)throw new IOException("Unreadable storage directory");
            for(File child:children)bytes=Math.addExact(bytes,measure(child,seen,count,nativeDir));
        } else if(!OsConstants.S_ISREG(s.st_mode))throw new IOException("Unaccounted special file in app storage");
        return bytes;
    }
}
