package org.pocketlore.app;

import android.app.Instrumentation;
import android.content.Intent;
import android.os.Bundle;
import android.widget.Button;
import java.io.*;
import java.nio.charset.StandardCharsets;

public final class TravelInstrumentation extends Instrumentation {
    @Override public void onCreate(Bundle args){super.onCreate(args);start();}
    @Override public void onStart(){Bundle result=new Bundle();TravelActivity activity=null;
        try{
            byte[] raw;try(InputStream in=getTargetContext().getAssets().open("dc-monuments.tsv")){raw=in.readAllBytes();}
            String report="AOSP x86_64 emulator; not physical Android\n"+TravelChecks.run(raw);
            activity=(TravelActivity)startActivitySync(new Intent(getTargetContext(),TravelActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));final TravelActivity a=activity;
            runOnMainSync(()->{
                TravelChecks.require(a.catalog!=null,"UI catalog load");
                a.query.setText("Lincoln");a.search.performClick();TravelChecks.require(a.sources.getChildCount()==1,"UI search result");
                ((Button)a.sources.getChildAt(0)).performClick();TravelChecks.require(a.inspectedId.equals("Q213559"),"UI source inspection");
            });
            sendKeyDownUpSync(android.view.KeyEvent.KEYCODE_BACK);
            runOnMainSync(()->{
                a.query.setText("");a.origin.setSelection(0);a.radius.setText("2");a.plan.performClick();TravelChecks.require(a.output.getText().toString().contains("National Museum of African American History and Culture [Q3073495]"),"UI plan");
                a.command.setText("convert 1 mi km");a.calculate.performClick();TravelChecks.require(a.output.getText().toString().contains("1.609344 km"),"UI calculator");
                a.command.setText("add-days 2023-02-29 1");a.calculate.performClick();TravelChecks.require(a.output.getText().toString().startsWith("Cannot calculate:"),"UI invalid date");
                a.query.setText("nonexistent restaurant");a.search.performClick();TravelChecks.require(a.sources.getChildCount()==0,"UI absent venue");
                a.query.setText("");a.search.performClick();a.plan.performClick();
            });
            report+="\nPASS: actual Activity search, inspection button, planning, calculator, invalid-date and absent-place UI actions\nTotal assertions including UI: "+TravelChecks.checks+"\n";
            try(FileOutputStream out=new FileOutputStream(new File(getTargetContext().getFilesDir(),"travel-results.txt"))){out.write(report.getBytes(StandardCharsets.UTF_8));}
            result.putString("report",report);finish(-1,result);
        }catch(Throwable failure){result.putString("failure",failure.toString());finish(1,result);}
    }
}
