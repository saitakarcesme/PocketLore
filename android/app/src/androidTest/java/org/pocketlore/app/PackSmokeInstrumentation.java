package org.pocketlore.app;

import android.app.Instrumentation;
import android.os.Bundle;
import java.io.*;
import java.nio.file.Files;
import org.json.*;

/** Real production import, retrieval, persisted reload and rollback checks on Android. */
public final class PackSmokeInstrumentation extends Instrumentation {
    @Override public void onCreate(Bundle args) {super.onCreate(args);start();}
    private static void check(boolean value,String why) {if(!value)throw new AssertionError(why);}
    @Override public void onStart() {
        Bundle result=new Bundle();JSONObject report=new JSONObject();JSONArray checks=new JSONArray();
        try {
            File root=new File(getTargetContext().getFilesDir(),"pack-tests");
            File install=new File(root,"installed");install.mkdirs();
            long start=System.nanoTime();KnowledgePack pack;
            try(InputStream in=new FileInputStream(new File(root,"valid.plpack"))){pack=KnowledgePack.install(in,install);}
            report.put("import_ms",(System.nanoTime()-start)/1e6).put("pack_sha256",pack.sha256).put("passages",pack.engine.size());
            check(pack.engine.size()>=100,"Larger real corpus not loaded");checks.put("valid_import");
            for(String query:new String[]{"evaporation","Declaration","NAVIGATION","Yosemite"}) {
                ResearchEngine.Result hits=pack.engine.research(query);check(!hits.hits.isEmpty(),"No retrieval: "+query);
                check(hits.hits.get(0).passage.url.startsWith("https://"),"Missing provenance");checks.put("retrieve_"+query);
            }
            File active=new File(install,"knowledge.plpack");String before=KnowledgePack.hash(Files.readAllBytes(active.toPath()));
            KnowledgePack reload=KnowledgePack.load(active);check(reload.sha256.equals(before) && reload.engine.size()==pack.engine.size(),"Restart reload mismatch");checks.put("persisted_reload");
            JSONObject cases=new JSONObject(new String(Files.readAllBytes(new File(root,"cases.json").toPath()),java.nio.charset.StandardCharsets.UTF_8));
            JSONArray rejects=cases.getJSONArray("rejects");JSONArray rejected=new JSONArray();
            for(int i=0;i<rejects.length();i++) {
                String name=rejects.getString(i);boolean failed=false;String message="";
                try(InputStream in=new FileInputStream(new File(root,name))){KnowledgePack.install(in,install);}
                catch(Exception expected){failed=true;message=expected.toString();}
                check(failed,"Corrupt pack accepted: "+name);
                check(before.equals(KnowledgePack.hash(Files.readAllBytes(active.toPath()))),"Corrupt import replaced old pack: "+name);
                check(KnowledgePack.load(active).engine.size()==pack.engine.size(),"Old pack no longer readable");
                rejected.put(new JSONObject().put("case",name).put("error",message));
            }
            checks.put("all_corrupt_imports_rejected_and_previous_pack_preserved");
            for(File f:install.listFiles())check(!f.getName().endsWith(".partial"),"Staging file leaked");checks.put("staging_cleanup");
            report.put("environment","AOSP x86_64 emulator; no physical-device result").put("checks",checks).put("rejected",rejected).put("passed",true);
            result.putString("report",report.toString(2));finish(-1,result);
        } catch(Throwable error) {result.putString("failure",error.toString());finish(1,result);}
    }
}
