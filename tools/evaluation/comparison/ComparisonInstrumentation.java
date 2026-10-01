package org.pocketlore.app;

import android.app.Instrumentation;
import android.os.Bundle;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import org.json.*;

/** Same-device, same-corpus public development comparison. No canned model outputs. */
public final class ComparisonInstrumentation extends Instrumentation {
    @Override public void onCreate(Bundle args) {super.onCreate(args);start();}
    static byte[] bytes(String s){return s.getBytes(StandardCharsets.UTF_8);}
    static double ms(long start){return (System.nanoTime()-start)/1e6;}
    @Override public void onStart(){
        Bundle result=new Bundle();long session=0;
        try {
            File root=new File(getTargetContext().getFilesDir(),"comparison-tests");
            JSONObject protocol=new JSONObject(new String(Files.readAllBytes(new File(root,"protocol.json").toPath()),StandardCharsets.UTF_8));
            long start=System.nanoTime();KnowledgePack pack=KnowledgePack.load(new File(root,"reference.plpack"));double packMs=ms(start);
            if(!pack.sha256.equals(protocol.getString("pack_sha256")))throw new AssertionError("Pack hash mismatch");
            session=NativeRuntime.create();start=System.nanoTime();
            NativeRuntime.load(session,bytes(new File(getTargetContext().getFilesDir(),"model.gguf").getAbsolutePath()));double loadMs=ms(start);final long id=session;
            AnswerEngine.Generator generator=new AnswerEngine.Generator(){
                public int run(byte[] p,int limit,NativeRuntime.Sink sink){return NativeRuntime.generateChat(id,bytes(EvidencePrompt.SYSTEM),p,limit,sink);}
                public int runWithSources(byte[] p,int limit,NativeRuntime.Sink sink,int sources,boolean combined){return NativeRuntime.generateClaims(id,bytes(EvidencePrompt.SYSTEM),p,limit,sink,sources,combined);}
                public int countTokens(byte[] p){return NativeRuntime.countChatTokens(id,bytes(EvidencePrompt.SYSTEM),p);}
            };
            JSONArray outputs=new JSONArray(),cases=protocol.getJSONArray("cases");
            for(int i=0;i<cases.length();i++)for(int j=0;j<2;j++){
                JSONObject c=cases.getJSONObject(i);String q=c.getString("question");boolean generated=(i+j)%2==0;
                NativeRuntime.reset(id);start=System.nanoTime();ResearchEngine.Result evidence=pack.engine.research(q);double retrieval=ms(start);
                String text,raw="",prompt="",kind;int tokens=0;double first=0;
                if(generated){AnswerEngine.Outcome a=AnswerEngine.answer(q,evidence,generator,t->{},()->false);text=a.text;raw=a.rawDraft;prompt=a.prompt;kind=a.kind.toString();tokens=a.tokens;first=a.firstTokenMs;}
                else {text=evidence.answer;kind="EXTRACTIVE";}
                double elapsed=ms(start);JSONArray sources=new JSONArray();
                for(ResearchEngine.Hit h:evidence.hits)sources.put(new JSONObject().put("id",h.passage.id).put("title",h.passage.title).put("text",h.passage.text).put("url",h.passage.url).put("date",h.passage.sourceDate).put("license",h.passage.license));
                outputs.put(new JSONObject().put("id",c.getString("id")).put("question",q).put("system",generated?"pocketlore":"extractive").put("kind",kind).put("text",text).put("raw_draft",raw).put("prompt",prompt).put("sources",sources).put("tokens",tokens).put("first_token_ms",first).put("retrieval_ms",retrieval).put("end_to_end_ms",elapsed));
                Files.write(new File(root,"partial.json").toPath(),bytes(outputs.toString(2)));
            }
            JSONObject report=new JSONObject().put("version",1).put("runtime",NativeRuntime.identity()).put("system_prompt",EvidencePrompt.SYSTEM).put("pack_load_ms",packMs).put("model_load_ms",loadMs).put("rows",outputs);
            Files.write(new File(root,"results.json").toPath(),bytes(report.toString(2)));finish(-1,result);
        }catch(Throwable e){result.putString("failure",e.toString());finish(1,result);}finally{if(session!=0)NativeRuntime.close(session);}
    }
}
