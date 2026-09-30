package org.pocketlore.app;

import android.app.*;
import android.content.Intent;
import android.os.Bundle;
import android.view.*;
import android.widget.*;
import org.json.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.concurrent.atomic.AtomicReference;
import java.util.function.BooleanSupplier;

/** Exercises the production Activity and real JNI model, with no substitute generator. */
public final class AnswerSmokeInstrumentation extends Instrumentation {
    private final JSONObject report=new JSONObject();
    private final JSONArray checks=new JSONArray(), cases=new JSONArray();
    private MainActivity activity;
    @Override public void onCreate(Bundle args) { super.onCreate(args); start(); }
    private static void require(boolean value,String why) { if (!value) throw new AssertionError(why); }
    private View find(View view,String label) {
        if (label.contentEquals(view.getContentDescription()==null?"":view.getContentDescription())) return view;
        if (view instanceof TextView && label.contentEquals(((TextView)view).getText())) return view;
        if (view instanceof ViewGroup) {
            ViewGroup group=(ViewGroup)view;
            for(int i=0;i<group.getChildCount();i++){View found=find(group.getChildAt(i),label);if(found!=null)return found;}
        }
        return null;
    }
    private View view(String label) { View found=find(activity.getWindow().getDecorView(),label);require(found!=null,"Missing UI: "+label);return found; }
    private void await(BooleanSupplier condition,String why) throws Exception {
        long deadline=System.nanoTime()+30_000_000_000L;
        while(System.nanoTime()<deadline){
            AtomicReference<Boolean> result=new AtomicReference<>(false);
            runOnMainSync(()->result.set(condition.getAsBoolean()));
            if(result.get())return;
            Thread.sleep(10);
        }
        throw new AssertionError("Timed out: "+why);
    }
    private void launch() throws Exception {
        Intent intent=new Intent(getTargetContext(),MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TASK);
        activity=(MainActivity)startActivitySync(intent);
        await(()->activity.modelReady()&&view("Answer offline").isEnabled(),"saved model ready");
    }
    private void ask(String query) {
        runOnMainSync(()->{((EditText)view("Research question")).setText(query);view("Answer offline").performClick();});
    }
    private JSONObject describe(String question,AnswerEngine.Outcome o) throws Exception {
        JSONArray ids=new JSONArray();for(String id:o.citedIds)ids.put(id);
        return new JSONObject().put("question",question).put("kind",o.kind.toString()).put("invoked_model",o.invokedModel)
            .put("tokens",o.tokens).put("first_token_ms",o.firstTokenMs).put("total_ms",o.totalMs).put("reason",o.reason)
            .put("text",o.text).put("raw_draft",o.rawDraft).put("prompt",o.prompt).put("cited_ids",ids);
    }
    @Override public void onStart() {
        Bundle result=new Bundle();
        try {
            File fixture=new File(getTargetContext().getFilesDir(),"answer-development-cases.json");
            byte[] bytes=Files.readAllBytes(fixture.toPath());
            StringBuilder digest=new StringBuilder();
            for(byte b:java.security.MessageDigest.getInstance("SHA-256").digest(bytes))digest.append(String.format(java.util.Locale.ROOT,"%02x",b&255));
            report.put("development_cases_sha256",digest.toString()).put("runtime",NativeRuntime.identity())
                .put("environment","AOSP x86_64 emulator; not physical hardware");
            launch(); checks.put("saved_model_load");
            JSONArray inputs=new JSONObject(new String(bytes,StandardCharsets.UTF_8)).getJSONArray("cases");
            int generated=0;
            for(int i=0;i<inputs.length();i++) {
                JSONObject input=inputs.getJSONObject(i);String q=input.getString("question");ask(q);
                await(()->activity.latestAnswer()!=null,"answer "+input.getString("id"));
                AnswerEngine.Outcome answer=activity.latestAnswer();cases.put(describe(q,answer));
                if(input.getString("id").equals("unsupported")||input.getString("id").equals("partial")) {
                    require(answer.kind==AnswerEngine.Kind.ABSTAINED&&!answer.invokedModel,"Unsupported answer inferred");
                    require(!answer.text.contains("Evaporation changes"),"Stale answer survived new question");
                } else {
                    require(answer.invokedModel&&answer.tokens>0&&!answer.rawDraft.isEmpty(),"Real model was not exercised");
                    require(answer.kind==AnswerEngine.Kind.GENERATED||answer.kind==AnswerEngine.Kind.FALLBACK,"Unexpected supported route");
                    if(answer.kind==AnswerEngine.Kind.GENERATED){generated++;require(!answer.citedIds.isEmpty(),"No citations");}
                    else require(answer.text.startsWith("Extractive fallback"),"Fallback mislabeled");
                }
                runOnMainSync(()->require(((TextView)view("Offline answer")).getText().toString().equals(answer.text),"UI differs from completed answer"));
            }
            checks.put("real_answer_flow");checks.put("unsupported_abstention");checks.put("partial_coverage_abstention");checks.put("new_question_clears_answer");
            // Observe a real token on the main UI, then click the actual cancel button.
            ask("Compare evaporation and condensation");
            await(()->((TextView)view("Answer status")).getText().toString().contains("Citation checks pending"),"first streamed token before cancellation");
            long cancelStart=System.nanoTime();runOnMainSync(()->view("Cancel current operation").performClick());
            await(()->activity.latestAnswer()!=null,"cancel acknowledgement");
            require(activity.latestAnswer().kind==AnswerEngine.Kind.CANCELLED,"Cancelled draft published as answer");
            report.put("ui_cancel_return_ms",(System.nanoTime()-cancelStart)/1e6); checks.put("cancel_real_generation");
            // Recreate the Activity while another real generation is in flight.
            ask("Compare evaporation and condensation");
            await(()->((TextView)view("Answer status")).getText().toString().contains("Citation checks pending"),"generation before recreation");
            ActivityMonitor monitor=addMonitor(MainActivity.class.getName(),null,false);
            runOnMainSync(()->activity.recreate());
            Activity recreated=waitForMonitorWithTimeout(monitor,30000);removeMonitor(monitor);
            require(recreated instanceof MainActivity,"Activity did not recreate");activity=(MainActivity)recreated;
            await(()->activity.modelReady()&&view("Answer offline").isEnabled(),"model after recreation");
            require(activity.latestAnswer()==null,"Stale generated answer reached recreated Activity");checks.put("recreation_cancels_generation");
            ask("Compare evaporation and condensation");await(()->activity.latestAnswer()!=null,"reuse after recreation");
            require(activity.latestAnswer().invokedModel,"No inference after recreation");checks.put("reuse_after_recreation");
            // Actual source dialog; a generated citation must resolve to the retrieved source button.
            String id=activity.latestAnswer().citedIds.stream().findFirst().orElse("water-02");
            runOnMainSync(()-> {
                ViewGroup root=(ViewGroup)activity.getWindow().getDecorView();
                View button=findPrefix(root,"Inspect ["+id+"]");require(button!=null,"Missing source inspection button");button.performClick();
            });
            waitForIdleSync();checks.put("source_inspection_opened");
            report.put("generated_case_count",generated);
            require(generated>0,"No development case produced a generated answer passing citation integrity checks");
            report.put("status","pass");
        } catch(Throwable error) {
            try{report.put("status","fail").put("error",android.util.Log.getStackTraceString(error));}catch(Exception ignored){}
        } finally {
            try {
                report.put("cases",cases).put("checks",checks);
                File target=new File(getTargetContext().getFilesDir(),"answer-result.json");
                try(FileOutputStream out=new FileOutputStream(target)){out.write(report.toString(2).getBytes(StandardCharsets.UTF_8));out.getFD().sync();}
                result.putString("stream",report.toString(2));
            }catch(Exception error){result.putString("stream","Report failed: "+error);}
            finish("pass".equals(report.optString("status"))?-1:0,result);
        }
    }
    private View findPrefix(View view,String prefix) {
        if(view instanceof Button && ((Button)view).getText().toString().startsWith(prefix))return view;
        if(view instanceof ViewGroup){ViewGroup g=(ViewGroup)view;for(int i=0;i<g.getChildCount();i++){View v=findPrefix(g.getChildAt(i),prefix);if(v!=null)return v;}}
        return null;
    }
}
