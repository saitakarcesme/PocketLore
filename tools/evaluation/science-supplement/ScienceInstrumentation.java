package org.pocketlore.app;

import android.app.*;
import android.os.Bundle;
import android.content.Intent;
import java.io.*;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import org.json.*;

public final class ScienceInstrumentation extends Instrumentation {
    private MainActivity activity;private File dir;private JSONObject report=new JSONObject();
    private static void check(boolean b,String s){if(!b)throw new AssertionError(s);}
    private static byte[] bytes(String s){return s.getBytes(StandardCharsets.UTF_8);}
    private static Object field(Object owner,String name)throws Exception{java.lang.reflect.Field f=owner.getClass().getDeclaredField(name);f.setAccessible(true);return f.get(owner);}
    private void save()throws Exception{Files.write(new File(dir,"results.json").toPath(),bytes(report.toString(2)));}
    private static void await(java.util.function.BooleanSupplier f,String why)throws Exception{long end=System.nanoTime()+20_000_000_000L;while(!f.getAsBoolean()&&System.nanoTime()<end)Thread.sleep(10);check(f.getAsBoolean(),why);}
    private boolean importing(){try{return (Boolean)field(activity,"importing");}catch(Exception e){throw new RuntimeException(e);}}
    private String status(){try{return ((android.widget.TextView)field(activity,"packStatus")).getText().toString();}catch(Exception e){throw new RuntimeException(e);}}
    @Override public void onCreate(Bundle args){super.onCreate(args);start();}
    @Override public void onStart(){Bundle result=new Bundle();File active=new File(getTargetContext().getFilesDir(),"knowledge.plpack");byte[] original=null;
        try {
            dir=new File(getTargetContext().getFilesDir(),"science-tests");original=Files.readAllBytes(active.toPath());
            JSONObject cases=new JSONObject(new String(Files.readAllBytes(new File(dir,"cases.json").toPath()),StandardCharsets.UTF_8));
            File isolated=new File(dir,"installed");isolated.mkdirs();long start=System.nanoTime();KnowledgePack pack;
            try(InputStream in=new FileInputStream(new File(dir,"valid.plpack"))){pack=KnowledgePack.install(in,isolated);}
            report.put("import_ms",(System.nanoTime()-start)/1e6).put("pack_sha256",pack.sha256).put("pack_id",pack.id).put("passages",pack.engine.size());
            JSONArray rows=new JSONArray();report.put("retrieval",rows);save();
            for(int i=0;i<cases.getJSONArray("cases").length();i++){
                JSONObject c=cases.getJSONArray("cases").getJSONObject(i);String q=c.getString("question");start=System.nanoTime();ResearchEngine.Result r=pack.engine.research(q);double ms=(System.nanoTime()-start)/1e6;
                JSONArray hits=new JSONArray();boolean found=false;for(ResearchEngine.Hit h:r.hits){hits.put(new JSONObject().put("id",h.passage.id).put("score",h.score).put("text",h.passage.text));for(int j=0;j<c.getJSONArray("required_ids").length();j++)if(h.passage.id.equals(c.getJSONArray("required_ids").getString(j)))found=true;}
                AnswerEngine.Outcome a=AnswerEngine.answer(q,r,null,t->{},()->false);
                rows.put(new JSONObject().put("id",c.getString("id")).put("question",q).put("expected",c.getString("expected")).put("found_required",found).put("hits",hits).put("retrieval_ms",ms).put("without_model_route",a.kind.toString()).put("reason",a.reason));save();
                if(c.getString("expected").equals("absent"))check(a.kind==AnswerEngine.Kind.ABSTAINED,"Absent query not blocked: "+q);
                else check(found,"Missing required source: "+q);
            }
            JSONArray rejects=new JSONArray();report.put("corruption",rejects);
            for(String name:new String[]{"bitflip.plpack","rights.plpack","source-hash.plpack"}){
                boolean rejected=false;String error="";try(InputStream in=new FileInputStream(new File(dir,name))){KnowledgePack.install(in,isolated);}catch(Exception expected){rejected=true;error=expected.toString();}
                check(rejected&&KnowledgePack.load(new File(isolated,"knowledge.plpack")).sha256.equals(pack.sha256),"Corruption replaced saved pack");rejects.put(new JSONObject().put("case",name).put("error",error));save();
            }
            check(isolated.listFiles((d,n)->n.endsWith(".partial")).length==0,"Staging remains");
            // Exercise production Activity import and its actual citation dialog; the picker result is injected.
            activity=(MainActivity)startActivitySync(new Intent(getTargetContext(),MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));await(activity::modelReady,"Saved model not ready");
            runOnMainSync(()->activity.onActivityResult(411,Activity.RESULT_OK,new Intent().setData(android.net.Uri.fromFile(new File(dir,"valid.plpack")))));await(()->!importing(),"Import stalled");check(status().contains(pack.sha256),"Activity did not import edition");
            String count=((android.widget.TextView)field(activity,"status")).getText().toString();
            check(count.startsWith("24 passages installed"),"Stale installed passage count");report.put("installed_status",count);
            ResearchEngine engine=(ResearchEngine)field(activity,"engine");ResearchEngine.Hit hit=engine.research("What is the difference between magma and lava?").hits.get(0);check(hit.passage.id.startsWith("science-"),"Old pack used");
            runOnMainSync(()->{try{java.lang.reflect.Method m=MainActivity.class.getDeclaredMethod("inspect",ResearchEngine.Hit.class);m.setAccessible(true);m.invoke(activity,hit);}catch(Exception e){throw new RuntimeException(e);}});
            // Inspect real displayed views in the dialog via its decor, not a synthetic expected-answer view.
            getUiAutomation().waitForIdle(100,3000);
            android.view.accessibility.AccessibilityNodeInfo root=getUiAutomation().getRootInActiveWindow();String visible=visibleText(root);
            check(visible.contains(hit.passage.id)&&visible.contains(hit.passage.text)&&visible.contains(hit.passage.url)&&visible.contains(hit.passage.sourceDate)&&visible.contains(hit.passage.license),"Citation dialog missing actual source/provenance");
            report.put("inspection",new JSONObject().put("citation",hit.passage.id).put("visible_text",visible));
            android.graphics.Bitmap image=getUiAutomation().takeScreenshot();try(FileOutputStream screenshot=new FileOutputStream(new File(dir,"source-dialog.png"))){check(image!=null&&image.compress(android.graphics.Bitmap.CompressFormat.PNG,100,screenshot),"Screenshot failed");}if(image!=null)image.recycle();
            sendKeyDownUpSync(android.view.KeyEvent.KEYCODE_BACK);
            runOnMainSync(()->activity.onActivityResult(411,Activity.RESULT_OK,new Intent().setData(android.net.Uri.fromFile(new File(dir,"bitflip.plpack")))));await(()->!importing(),"Corrupt import stalled");check(status().startsWith("Pack rejected; previous library retained.")&&KnowledgePack.load(active).sha256.equals(pack.sha256),"Activity corruption rollback failed");
            report.put("activity_import",true).put("activity_corrupt_rejected",true).put("staging_cleanup",true).put("status","PASS");save();
        }catch(Throwable error){try{report.put("status","FAIL").put("failure",error.toString());save();}catch(Exception ignored){}result.putString("failure",error.toString());}
        finally{
            try{
                if(activity!=null){await(()->!importing(),"Restore waits for import worker");runOnMainSync(activity::finish);}
                if(original!=null){File stage=new File(dir,"restore.plpack");Files.write(stage.toPath(),original);Files.move(stage.toPath(),active.toPath(),StandardCopyOption.ATOMIC_MOVE,StandardCopyOption.REPLACE_EXISTING);check(java.util.Arrays.equals(original,Files.readAllBytes(active.toPath())),"Original library not restored");report.put("original_library_restored",true);save();}
            }catch(Throwable restore){try{report.put("status","FAIL").put("restore_failure",restore.toString());save();}catch(Exception ignored){}}
        }
        finish(report.optString("status").equals("PASS")?-1:1,result);
    }
    private static String visibleText(android.view.accessibility.AccessibilityNodeInfo node){
        if(node==null)return "";StringBuilder text=new StringBuilder();if(node.getText()!=null)text.append(node.getText()).append('\n');
        for(int i=0;i<node.getChildCount();i++)text.append(visibleText(node.getChild(i)));return text.toString();
    }
}
