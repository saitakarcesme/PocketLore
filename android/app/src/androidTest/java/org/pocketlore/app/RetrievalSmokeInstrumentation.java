package org.pocketlore.app;

import android.app.Instrumentation;
import android.os.Bundle;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.*;
import org.json.*;

/** Executes the production pack validator and retriever, and checks host/Android parity. */
public final class RetrievalSmokeInstrumentation extends Instrumentation {
    @Override public void onCreate(Bundle args) {super.onCreate(args);start();}
    private static void require(boolean ok,String message) {if(!ok)throw new AssertionError(message);}
    @Override public void onStart() {
        Bundle result=new Bundle();
        try {
            File root=new File(getTargetContext().getFilesDir(),"retrieval-tests");
            JSONObject expected=new JSONObject(new String(Files.readAllBytes(new File(root,"expected.json").toPath()),StandardCharsets.UTF_8));
            long start=System.nanoTime();KnowledgePack pack=KnowledgePack.load(new File(root,"reference.plpack"));
            double loadMs=(System.nanoTime()-start)/1e6;
            JSONArray cases=expected.getJSONArray("cases"),output=new JSONArray();
            for(int i=0;i<cases.length();i++) {
                JSONObject c=cases.getJSONObject(i);String query=c.getString("query");
                start=System.nanoTime();ResearchEngine.Result found=pack.engine.research(query);double firstMs=(System.nanoTime()-start)/1e6;
                JSONArray expectedHits=c.getJSONArray("hits"),actualHits=new JSONArray();
                require(found.hits.size()==expectedHits.length(),"Different hit count: "+query);
                for(int j=0;j<found.hits.size();j++) {
                    ResearchEngine.Hit h=found.hits.get(j);JSONObject e=expectedHits.getJSONObject(j);
                    require(h.passage.id.equals(e.getString("id")),"Different source ranking: "+query);
                    require(Math.abs(h.score-e.getDouble("score"))<1e-8,"Different BM25 score: "+query);
                    actualHits.put(new JSONObject().put("id",h.passage.id).put("score",h.score));
                }
                boolean blocked=found.hits.isEmpty() || !found.missingTerms.isEmpty() || !EvidencePrompt.uncovered(query,found).isEmpty();
                require(blocked==c.getBoolean("lexical_generation_blocked"),"Different lexical gate: "+query);
                require(found.candidatesScored==c.getInt("candidates_scored"),"Different candidate count: "+query);
                output.put(new JSONObject().put("query",query).put("hits",actualHits).put("lexical_generation_blocked",blocked)
                    .put("candidates_scored",found.candidatesScored).put("first_sweep_ms",firstMs).put("warm_ms",new JSONArray()));
            }
            for(int i=0;i<20;i++)for(int j=0;j<cases.length();j++)pack.engine.research(cases.getJSONObject((i+j)%cases.length()).getString("query"));
            for(int i=0;i<30;i++)for(int j=0;j<cases.length();j++) {
                int index=(i+j)%cases.length();String query=cases.getJSONObject(index).getString("query");
                start=System.nanoTime();pack.engine.research(query);double elapsed=(System.nanoTime()-start)/1e6;
                output.getJSONObject(index).getJSONArray("warm_ms").put(elapsed);
            }
            JSONObject report=new JSONObject().put("environment","Existing AOSP x86_64 emulator; not physical Android")
                .put("pack_sha256",pack.sha256).put("validated_archive_and_index_ms",loadMs).put("cases",output).put("passed",true);
            result.putString("report",report.toString());finish(-1,result);
        } catch(Throwable error){result.putString("failure",error.toString());finish(1,result);}
    }
}
