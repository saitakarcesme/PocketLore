package org.pocketlore.app;

import android.app.*;
import android.content.Intent;
import android.os.Bundle;
import android.widget.Button;
import java.io.*;
import java.nio.file.Files;
import java.nio.charset.StandardCharsets;
import java.util.*;
import org.json.*;

/** Public frozen filters and actual production Activity controls; no inference. */
public final class RegionalInstrumentation extends Instrumentation {
    private JSONObject report=new JSONObject();private File dir;
    private static void check(boolean ok,String why){if(!ok)throw new AssertionError(why);}
    private void save()throws Exception{Files.write(new File(dir,"results.json").toPath(),report.toString(2).getBytes(StandardCharsets.UTF_8));}
    private static JSONArray ids(List<TravelCatalog.Poi> ps){JSONArray a=new JSONArray();for(TravelCatalog.Poi p:ps)a.put(p.id);return a;}
    private interface Attempt{void run()throws Exception;}
    private static void rejects(Attempt a)throws Exception{try{a.run();}catch(Exception expected){return;}throw new AssertionError("Invalid input accepted");}
    @Override public void onCreate(Bundle args){super.onCreate(args);start();}
    @Override public void onStart(){Bundle bundle=new Bundle();TravelActivity activity=null;
        try{
            dir=new File(getTargetContext().getFilesDir(),"regional-tests");dir.mkdirs();
            JSONObject fixture=new JSONObject(new String(Files.readAllBytes(new File(dir,"cases.json").toPath()),StandardCharsets.UTF_8));
            byte[] raw;try(InputStream in=getTargetContext().getAssets().open("dc-monuments.tsv")){raw=in.readAllBytes();}
            long begin=System.nanoTime();TravelCatalog c=new TravelCatalog(new ByteArrayInputStream(raw));report.put("load_ms",(System.nanoTime()-begin)/1e6);
            check(c.pois.size()==25,"POI count");JSONArray sources=new JSONArray();for(TravelCatalog.Poi p:c.pois)sources.put(new JSONObject().put("id",p.id).put("name",p.name).put("description",p.description).put("lat",p.lat).put("lon",p.lon).put("category",p.category).put("revision",p.revision).put("source_hash",p.sourceHash).put("url",p.url).put("coordinate_claim",p.coordinateClaim).put("evidence",p.evidence()));
            report.put("sources",sources);JSONArray cases=new JSONArray();report.put("filters",cases);save();
            for(int i=0;i<fixture.getJSONArray("cases").length();i++){
                JSONObject f=fixture.getJSONArray("cases").getJSONObject(i);begin=System.nanoTime();JSONArray found=ids(c.filter(f.getString("category"),f.getString("require"),f.getString("avoid")));double ms=(System.nanoTime()-begin)/1e6;
                cases.put(new JSONObject().put("id",f.getString("id")).put("actual",found).put("ms",ms));save();check(found.toString().equals(f.getJSONArray("expected").toString()),"Frozen filter mismatch: "+f.getString("id")+" "+found);
            }
            JSONArray plans=new JSONArray();report.put("plans",plans);
            for(String category:new String[]{"museum","monument","park-garden","civic","restaurant"}){
                String origin="Q178114";List<TravelCatalog.Poi> found=c.nearby(origin,2,3,category,"","");
                plans.put(new JSONObject().put("category",category).put("ids",ids(found)).put("text",c.plan(origin,2,3,category,"","")));
            }
            check(c.nearby("Q178114",0,3,"museum","","").isEmpty(),"Zero radius");
            check(c.nearby("Q178114",2,3,"museum","history","history").isEmpty(),"Relaxed conflicting preferences");
            List<TravelCatalog.Poi> preferred=c.nearby("Q178114",2,3,"museum","art museum","Women");
            report.put("preferred_plan",new JSONObject().put("ids",ids(preferred)).put("text",c.plan("Q178114",2,3,"museum","art museum","Women")));
            rejects(()->c.nearby("Q178114",Double.NaN,3));rejects(()->c.nearby("Q178114",Double.POSITIVE_INFINITY,3));rejects(()->c.nearby("Q178114",-1,3));rejects(()->c.nearby("Q0",2,3));rejects(()->c.nearby("Q178114",2,0));rejects(()->c.nearby("Q178114",2,6));
            byte[] corrupt=raw.clone();corrupt[corrupt.length/2]^=1;rejects(()->new TravelCatalog(new ByteArrayInputStream(corrupt)));
            String textPack=new String(raw,StandardCharsets.UTF_8);
            String[] invalidRow=textPack.split("\n")[0].split("\t",-1);invalidRow[12]="Q0$invalid";
            rejects(()->TravelCatalog.parse(String.join("\t",invalidRow)+"\n"+textPack.substring(textPack.indexOf('\n')+1)));
            report.put("rejected_controls",8);save();
            activity=(TravelActivity)startActivitySync(new Intent(getTargetContext(),TravelActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));final TravelActivity a=activity;
            runOnMainSync(()->{
                check(a.catalog!=null,"Activity catalog");a.category.setSelection(2);a.query.setText("natural history");a.avoid.setText("");a.search.performClick();
                check(a.sources.getChildCount()==1,"Actual category search");((Button)a.sources.getChildAt(0)).performClick();
            });
            getUiAutomation().waitForIdle(100,3000);String visible=text(getUiAutomation().getRootInActiveWindow());TravelCatalog.Poi inspected=c.get("Q148554");
            check(visible.contains(inspected.name)&&visible.contains(inspected.sourceHash)&&visible.contains(inspected.revision)&&visible.contains(inspected.coordinateClaim)&&visible.contains(inspected.url)&&visible.contains("CC0-1.0")&&visible.contains("hours may be stale")&&visible.contains("Routing and walking times are unavailable"),"Actual dialog provenance/disclosures");
            report.put("inspection_text",visible);
            android.graphics.Bitmap image=getUiAutomation().takeScreenshot();try(FileOutputStream f=new FileOutputStream(new File(dir,"inspection.png"))){check(image!=null&&image.compress(android.graphics.Bitmap.CompressFormat.PNG,100,f),"Screenshot");}if(image!=null)image.recycle();
            sendKeyDownUpSync(android.view.KeyEvent.KEYCODE_BACK);
            runOnMainSync(()->{
                a.query.setText("art museum");a.avoid.setText("Women");a.origin.setSelection(0);a.radius.setText("2");a.plan.performClick();
                check(a.sources.getChildCount()==preferred.size()+1,"Plan source count");
                for(int i=0;i<preferred.size();i++)check(((Button)a.sources.getChildAt(i+1)).getText().toString().contains("["+preferred.get(i).id+"]"),"Missing candidate source button");
                check(a.output.getText().toString().equals(c.plan("Q178114",2,3,"museum","art museum","Women")),"Actual filtered plan");
                try{report.put("activity_plan",a.output.getText().toString());}catch(Exception e){throw new RuntimeException(e);}
                a.query.setText("history");a.avoid.setText("history");a.plan.performClick();check(a.output.getText().toString().contains("No matching candidates")&&a.sources.getChildCount()==1,"Conflicting Activity preferences");
                a.category.setSelection(5);a.query.setText("");a.avoid.setText("");a.search.performClick();check(a.sources.getChildCount()==0,"Absent Activity category");
            });
            report.put("activity_controls",true).put("status","PASS");save();
        }catch(Throwable failure){try{report.put("status","FAIL").put("failure",failure.toString());save();}catch(Exception ignored){}bundle.putString("failure",failure.toString());}
        finally{if(activity!=null){final TravelActivity a=activity;runOnMainSync(a::finish);}}
        finish(report.optString("status").equals("PASS")?-1:1,bundle);
    }
    private static String text(android.view.accessibility.AccessibilityNodeInfo n){if(n==null)return "";StringBuilder s=new StringBuilder();if(n.getText()!=null)s.append(n.getText()).append('\n');for(int i=0;i<n.getChildCount();i++)s.append(text(n.getChild(i)));return s.toString();}
}
