package org.pocketlore.app;
import android.app.*;import android.content.*;import android.os.*;import android.graphics.*;import java.io.*;import java.nio.file.*;import org.json.*;
/** Diagnostic lifecycle comparison only; never substitutes for the six feature phases. */
public final class ModernTeardownProbe extends Instrumentation {
 Bundle args;public void onCreate(Bundle b){args=b;super.onCreate(b);start();}
 public void onStart(){Bundle b=new Bundle();JSONObject r=new JSONObject();Activity a=null;File dir=new File(getTargetContext().getFilesDir(),"modern-probe-"+args.getString("run_id"));dir.mkdirs();try{
  r.put("run_id",args.getString("run_id")).put("automation",Boolean.parseBoolean(args.getString("automation","false")));
  if(Boolean.parseBoolean(args.getString("automation","false"))){a=startActivitySync(new Intent(getTargetContext(),MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));waitForIdleSync();Bitmap image=getUiAutomation().takeScreenshot();if(image==null)throw new IOException("No screenshot");try(OutputStream out=new FileOutputStream(new File(dir,"probe.png"))){image.compress(Bitmap.CompressFormat.PNG,100,out);}image.recycle();Activity current=a;runOnMainSync(current::finish);}
  r.put("status","PASS");Files.write(new File(dir,"report.json").toPath(),r.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8));DeviceEvidence.emit(this,args,dir);b.putString("report",r.toString());finish(-1,b);
 }catch(Throwable t){b.putString("error",android.util.Log.getStackTraceString(t));finish(1,b);}}
}
