package org.pocketlore.app;

import android.app.Instrumentation;
import android.os.Bundle;
import java.io.*;
import java.nio.file.Files;

/** Queued device contract: caller supplies one existing valid small .plpack; no bulk build. */
public final class ScaleLibraryInstrumentation extends Instrumentation {
    @Override public void onCreate(Bundle args){super.onCreate(args);start();}
    static void check(boolean ok,String why){if(!ok)throw new AssertionError(why);}
    @Override public void onStart(){
        Bundle report=new Bundle();
        try{
            File input=new File(getTargetContext().getFilesDir(),"scale-valid.plpack");
            check(input.isFile(),"Supply scale-valid.plpack before running");
            File root=Files.createTempDirectory(getTargetContext().getCacheDir().toPath(),"scale-library-").toFile();
            PackLibrary library=new PackLibrary(root);PackLibrary.Snapshot installed;
            try(InputStream in=new FileInputStream(input)){installed=library.install(in,()->false,input.length());}
            check(installed.entries.size()==1,"Expected one edition");String hash=installed.entries.get(0).hash;
            boolean rejected=false;
            try(InputStream in=new FileInputStream(input)){library.install(in,()->false,input.length()+1);}catch(IOException expected){rejected=true;}
            check(rejected&&library.load().entries.size()==1,"Length mismatch changed catalog");
            library.select(java.util.Collections.emptySet());check(library.load().engine.size()==0,"Disabled edition searched");
            library.select(java.util.Collections.singleton(hash));check(library.load().engine.size()>0,"Enabled edition missing");
            ImportRecovery.begin(root,"pack");check(ImportRecovery.pending(root,"pack"),"No durable marker");
            check(new PackLibrary(root).load().entries.size()==1,"Recovery lost installed edition");
            library.remove(hash);check(new PackLibrary(root).loadMigrating(input).entries.isEmpty(),"Removed edition resurrected");
            check(!new File(root,"pack-library/"+hash+".plpack").exists(),"Removed archive retained");
            rejected=false;try{library.remove(hash);}catch(IOException expected){rejected=true;}
            check(rejected,"Unknown removal accepted");
            report.putString("result","PASS: declared size rollback, toggle persistence, pending recovery, removal and no legacy resurrection; UI confirmation requires separate interaction test");finish(-1,report);
        }catch(Throwable error){report.putString("failure",error.toString());finish(1,report);}
    }
}
