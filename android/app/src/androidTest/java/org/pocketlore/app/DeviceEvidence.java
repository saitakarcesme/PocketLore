package org.pocketlore.app;
import android.app.Instrumentation;import android.os.*;import android.provider.Settings;import android.util.Base64;import java.io.*;import java.nio.file.*;import java.security.*;import java.util.*;import org.json.*;
/** Optional modern test transaction; no production dependency or background service. */
public final class DeviceEvidence {
 public static String begin(Instrumentation test,Bundle args)throws Exception{
  if(!Boolean.parseBoolean(args.getString("device_evidence","false")))return null;
  String before=Settings.System.getString(test.getTargetContext().getContentResolver(),"font_scale");
  String scale=args.getString("font_target");if(scale!=null){if(!scale.equals("1.0")&&!scale.equals("2.0"))throw new IOException("Unsupported test scale");shell(test,"settings put system font_scale "+scale);long end=SystemClock.elapsedRealtime()+3000;while(test.getTargetContext().getResources().getConfiguration().fontScale!=Float.parseFloat(scale)&&SystemClock.elapsedRealtime()<end)Thread.sleep(50);}
  return before==null?"null":before;
 }
 static void shell(Instrumentation test,String command)throws Exception{try(ParcelFileDescriptor fd=test.getUiAutomation().executeShellCommand(command);InputStream in=new ParcelFileDescriptor.AutoCloseInputStream(fd)){while(in.read()!=-1){}}}
 public static void restore(Instrumentation test,String before,JSONObject report)throws Exception{
  if(before==null)return;shell(test,before.equals("null")?"settings delete system font_scale":"settings put system font_scale "+before);
  String actual=Settings.System.getString(test.getTargetContext().getContentResolver(),"font_scale");actual=actual==null?"null":actual;
  report.put("font_original",before).put("font_restored",actual);if(!before.equals(actual))throw new IOException("Device font restoration failed");
 }
 static String hash(byte[] b)throws Exception{StringBuilder s=new StringBuilder();for(byte v:MessageDigest.getInstance("SHA-256").digest(b))s.append(String.format(Locale.ROOT,"%02x",v&255));return s.toString();}
 public static void emit(Instrumentation test,Bundle args,File dir)throws Exception{
  if(!Boolean.parseBoolean(args.getString("device_evidence","false")))return;String id=args.getString("run_id");JSONObject files=new JSONObject();long total=0;
  File[] all=dir.listFiles();if(all==null)throw new IOException("Evidence directory missing");Arrays.sort(all,Comparator.comparing(File::getName));
  for(File f:all){if(!f.isFile()||!f.getName().matches("[A-Za-z0-9_.-]+\\.(json|png|txt|md)"))continue;
   if(f.length()>16*1024*1024||(total+=f.length())>64*1024*1024)throw new IOException("Evidence byte bound");byte[] bytes=Files.readAllBytes(f.toPath());files.put(f.getName(),new JSONObject().put("bytes",bytes.length).put("sha256",hash(bytes)));
   int count=Math.max(1,(bytes.length+32767)/32768);for(int n=0;n<count;n++){JSONObject chunk=new JSONObject().put("run_id",id).put("name",f.getName()).put("index",n).put("count",count).put("data",Base64.encodeToString(Arrays.copyOfRange(bytes,n*32768,Math.min(bytes.length,(n+1)*32768)),Base64.NO_WRAP));Bundle b=new Bundle();b.putString("pocketlore_chunk",chunk.toString());test.sendStatus(0,b);}
  }
  Bundle b=new Bundle();b.putString("pocketlore_manifest",new JSONObject().put("run_id",id).put("files",files).toString());test.sendStatus(0,b);
 }
}
