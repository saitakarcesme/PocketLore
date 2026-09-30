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
            File model=new File(root,"model.gguf");
            java.security.MessageDigest md=java.security.MessageDigest.getInstance("SHA-256");
            try(InputStream in=new FileInputStream(model)){byte[] buf=new byte[65536];int n;while((n=in.read(buf))!=-1)md.update(buf,0,n);}
            StringBuilder hash=new StringBuilder();for(byte b:md.digest())hash.append(String.format(java.util.Locale.ROOT,"%02x",b&255));
            if(!hash.toString().equals(fixture.getString("model_sha256")))throw new AssertionError("Unexpected model");
            session=NativeRuntime.create();long start=System.nanoTime();NativeRuntime.load(session,model.getAbsolutePath().getBytes(StandardCharsets.UTF_8));
            double load=(System.nanoTime()-start)/1e6;final long id=session;
            byte[] system=EvidencePrompt.SYSTEM.getBytes(StandardCharsets.UTF_8);
            byte[] oversized=new String(new char[2200]).replace("\0","water ").getBytes(StandardCharsets.UTF_8);
            if(NativeRuntime.countChatTokens(id,system,oversized)+256<=2048)throw new AssertionError("Overflow fixture too small");
            boolean rejected=false;
            try {NativeRuntime.generateClaims(id,system,oversized,256,piece->{throw new AssertionError("Over-budget tokens emitted");},2,false);}
            catch(IllegalStateException overflow){rejected=overflow.getMessage().contains("context");}
            if(!rejected)throw new AssertionError("Native token budget not enforced");
            NativeRuntime.cancel(id);
            if(NativeRuntime.generateClaims(id,system,"test".getBytes(StandardCharsets.UTF_8),10,piece->{throw new AssertionError("Cancelled tokens emitted");},1,false)!=-1)throw new AssertionError("Native cancellation failed");
            NativeRuntime.reset(id);
            AnswerEngine.Generator generator=new AnswerEngine.Generator(){
                public int run(byte[] p,int limit,NativeRuntime.Sink sink){return NativeRuntime.generateChat(id,EvidencePrompt.SYSTEM.getBytes(StandardCharsets.UTF_8),p,limit,sink);}
                public int runWithSources(byte[] prompt,int limit,NativeRuntime.Sink sink,int sources,boolean combined) {return NativeRuntime.generateClaims(id,EvidencePrompt.SYSTEM.getBytes(StandardCharsets.UTF_8),prompt,limit,sink,sources,combined);}
                    public int countTokens(byte[] p){return NativeRuntime.countChatTokens(id,EvidencePrompt.SYSTEM.getBytes(StandardCharsets.UTF_8),p);}
            };
            JSONArray cases=fixture.getJSONArray("cases"), outputs=new JSONArray();
            cases.put(new JSONObject().put("id","conflict-fixture").put("question","test lamp active"));
            for(int i=0;i<cases.length();i++) {
                JSONObject c=cases.getJSONObject(i);String question=c.getString("question");NativeRuntime.reset(id);
                boolean fictional=c.getString("id").equals("conflict-fixture");
                ResearchEngine.Result evidence=fictional ? new ResearchEngine(new java.io.StringReader(
                    "fixture-a\tFictional sensor A\thttps://example.invalid/a\t2026-01-01\tFictional control test\tThe test lamp is active.\n"+
                    "fixture-b\tFictional sensor B\thttps://example.invalid/b\t2026-01-01\tFictional control test\tThe test lamp is not active.\n")).research(question) : pack.engine.research(question);
                AnswerEngine.Outcome answer=AnswerEngine.answer(question,evidence,generator,t->{},()->false);
                java.util.Set<String> opened=new java.util.LinkedHashSet<>();
                android.text.SpannableString linked=NativePanel.linkClaims(answer,opened::add);
                android.text.style.ClickableSpan[] spans=linked.getSpans(0,linked.length(),android.text.style.ClickableSpan.class);
                runOnMainSync(()->{for(android.text.style.ClickableSpan span:spans)span.onClick(new android.view.View(getTargetContext()));});
                if(!opened.equals(answer.citedIds))throw new AssertionError("Claim link callback did not resolve exact cited IDs");
                JSONArray sources=new JSONArray();for(ResearchEngine.Hit hit:evidence.hits)sources.put(new JSONObject().put("id",hit.passage.id).put("text",hit.passage.text).put("date",hit.passage.sourceDate).put("url",hit.passage.url));
                JSONObject row=new JSONObject().put("id",c.getString("id")).put("fictional_fixture",fictional).put("question",question).put("kind",answer.kind.toString()).put("text",answer.text).put("raw_draft",answer.rawDraft).put("reason",answer.reason).put("prompt",answer.prompt).put("sources",sources).put("claim_links_checked",spans.length).put("tokens",answer.tokens).put("first_token_ms",answer.firstTokenMs).put("total_ms",answer.totalMs)
                    .put("prompt_tokens",answer.prompt.isEmpty()?0:generator.countTokens(answer.prompt.getBytes(StandardCharsets.UTF_8)));
                outputs.put(row);
                try(FileOutputStream out=new FileOutputStream(new File(root,"partial-results.json"))){out.write(outputs.toString(2).getBytes(StandardCharsets.UTF_8));}
            }
            JSONObject report=new JSONObject().put("environment","AOSP x86_64 emulator; not physical Android").put("runtime",NativeRuntime.identity()).put("system_prompt",EvidencePrompt.SYSTEM).put("model_sha256",hash.toString()).put("pack_sha256",pack.sha256).put("load_ms",load).put("native_budget_and_cancel_checks",true).put("cases",outputs);
            try(FileOutputStream out=new FileOutputStream(new File(root,"results.json"))){out.write(report.toString(2).getBytes(StandardCharsets.UTF_8));}
            result.putString("report","Real outputs saved to files/synthesis-tests/results.json");finish(-1,result);
        }catch(Throwable error){result.putString("failure",error.toString());finish(1,result);}finally{if(session!=0)NativeRuntime.close(session);}
    }
}
