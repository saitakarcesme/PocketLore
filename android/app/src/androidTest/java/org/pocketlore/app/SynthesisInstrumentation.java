package org.pocketlore.app;

import android.app.Instrumentation;
import android.os.Bundle;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import org.json.*;

/** Real production answer flow and JNI generation; no substituted model responses. */
public final class SynthesisInstrumentation extends Instrumentation {
    @Override public void onCreate(Bundle args){super.onCreate(args);start();}
    @Override public void onStart() {
        Bundle result=new Bundle();long session=0;
        try {
            File root=new File(getTargetContext().getFilesDir(),"synthesis-tests");
            JSONObject fixture=new JSONObject(new String(Files.readAllBytes(new File(root,"cases.json").toPath()),StandardCharsets.UTF_8));
            KnowledgePack pack=KnowledgePack.load(new File(root,"reference.plpack"));
            File model=new File(getTargetContext().getFilesDir(),"model.gguf");
            java.security.MessageDigest md=java.security.MessageDigest.getInstance("SHA-256");
            try(InputStream in=new FileInputStream(model)){byte[] buf=new byte[65536];int n;while((n=in.read(buf))!=-1)md.update(buf,0,n);}
            StringBuilder hash=new StringBuilder();for(byte b:md.digest())hash.append(String.format(java.util.Locale.ROOT,"%02x",b&255));
            if(!hash.toString().equals(fixture.getString("model_sha256")))throw new AssertionError("Unexpected model");
            session=NativeRuntime.create();long start=System.nanoTime();NativeRuntime.load(session,model.getAbsolutePath().getBytes(StandardCharsets.UTF_8));
            double load=(System.nanoTime()-start)/1e6;final long id=session;
            AnswerEngine.Generator generator=new AnswerEngine.Generator(){
                public int run(byte[] p,int limit,NativeRuntime.Sink sink){return NativeRuntime.generateChat(id,EvidencePrompt.SYSTEM.getBytes(StandardCharsets.UTF_8),p,limit,sink);}
                public int countTokens(byte[] p){return NativeRuntime.countChatTokens(id,EvidencePrompt.SYSTEM.getBytes(StandardCharsets.UTF_8),p);}
            };
            JSONArray cases=fixture.getJSONArray("cases"), outputs=new JSONArray();
            for(int i=0;i<cases.length();i++) {
                JSONObject c=cases.getJSONObject(i);String question=c.getString("question");NativeRuntime.reset(id);
                ResearchEngine.Result evidence=pack.engine.research(question);
                AnswerEngine.Outcome answer=AnswerEngine.answer(question,evidence,generator,t->{},()->false);
                JSONArray sources=new JSONArray();for(ResearchEngine.Hit hit:evidence.hits)sources.put(new JSONObject().put("id",hit.passage.id).put("text",hit.passage.text).put("date",hit.passage.sourceDate).put("url",hit.passage.url));
                JSONObject row=new JSONObject().put("id",c.getString("id")).put("question",question).put("kind",answer.kind.toString()).put("text",answer.text).put("raw_draft",answer.rawDraft).put("reason",answer.reason).put("prompt",answer.prompt).put("sources",sources).put("tokens",answer.tokens).put("first_token_ms",answer.firstTokenMs).put("total_ms",answer.totalMs)
                    .put("prompt_tokens",answer.prompt.isEmpty()?0:generator.countTokens(answer.prompt.getBytes(StandardCharsets.UTF_8)));
                outputs.put(row);
            }
            JSONObject report=new JSONObject().put("environment","AOSP x86_64 emulator; not physical Android").put("runtime",NativeRuntime.identity()).put("system_prompt",EvidencePrompt.SYSTEM).put("model_sha256",hash.toString()).put("pack_sha256",pack.sha256).put("load_ms",load).put("cases",outputs);
            try(FileOutputStream out=new FileOutputStream(new File(root,"results.json"))){out.write(report.toString(2).getBytes(StandardCharsets.UTF_8));}
            result.putString("report","Real outputs saved to files/synthesis-tests/results.json");finish(-1,result);
        }catch(Throwable error){result.putString("failure",error.toString());finish(1,result);}finally{if(session!=0)NativeRuntime.close(session);}
    }
}
