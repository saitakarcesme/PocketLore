package org.pocketlore.app;

import android.app.Activity;
import android.content.*;
import android.net.Uri;
import android.os.Bundle;
import android.widget.TextView;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.concurrent.*;

/** Shared async notebook IO and system export interaction. */
abstract class NotebookActivity extends Activity {
    static final int EXPORT_DOCUMENT=702;
    static final ExecutorService IO=Executors.newSingleThreadExecutor();
    TextView operation;
    String pendingExport;
    void message(String s){if(operation!=null){operation.setVisibility(android.view.View.VISIBLE);operation.setText(s);operation.post(()->operation.requestRectangleOnScreen(new android.graphics.Rect(0,0,operation.getWidth(),operation.getHeight()),false));}}
    @Override public void onCreate(Bundle state){super.onCreate(state);if(state!=null)pendingExport=state.getString("export");}
    @Override public void onSaveInstanceState(Bundle b){super.onSaveInstanceState(b);b.putString("export",pendingExport);}
    interface Task {void run()throws Exception;}
    void work(Task task){IO.execute(()->{try{task.run();}catch(Exception e){runOnUiThread(()->{if(!isDestroyed())message("Could not complete: "+e.getMessage());});}});}
    void export(List<NotebookStore.Entry> entries,boolean share){
        if(entries.isEmpty()){message("No saved records to export.");return;}
        message("Preparing local notebook export…");
        work(()->{
            File dir=new File(getCacheDir(),"notebook-exports");if(!dir.isDirectory()&&!dir.mkdirs())throw new IOException("Export directory unavailable");
            File[] old=dir.listFiles();long total=0;if(old!=null)for(File f:old){if(f.lastModified()<System.currentTimeMillis()-86400000L)f.delete();else total+=f.length();}
            if(total>32L*1024*1024)throw new IOException("Temporary exports exceed 32 MiB; try again after their 24-hour retention period.");
            File out=new File(dir,"notebook-"+UUID.randomUUID()+".md");
            try(Writer w=new OutputStreamWriter(new FileOutputStream(out),StandardCharsets.UTF_8)){
                w.write("# PocketLore notebook\n\nOffline snapshots and personal notes. Source rights and answer limitations remain attached; check them before redistribution.\n\n");
                long bytes=0;for(NotebookStore.Entry e:entries){String record=e.portable();bytes+=record.getBytes(StandardCharsets.UTF_8).length;if(bytes>16L*1024*1024)throw new IOException("Export exceeds 16 MiB. Export fewer records.");w.write(record);w.write("\n---\n\n");}
            }catch(Exception e){out.delete();throw e;}
            runOnUiThread(()->{if(isDestroyed())return;try{
                if(share){Uri uri=Uri.parse("content://"+getPackageName()+".notebook/"+out.getName());Intent send=new Intent(Intent.ACTION_SEND).setType("text/markdown").putExtra(Intent.EXTRA_STREAM,uri).addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);send.setClipData(ClipData.newRawUri("PocketLore notebook",uri));startActivity(Intent.createChooser(send,"Share notebook snapshot"));message("Choose a recipient in Android. Sharing does not verify source rights.");}
                else {pendingExport=out.getName();startActivityForResult(new Intent(Intent.ACTION_CREATE_DOCUMENT).addCategory(Intent.CATEGORY_OPENABLE).setType("text/markdown").putExtra(Intent.EXTRA_TITLE,"PocketLore-"+System.currentTimeMillis()+".md"),EXPORT_DOCUMENT);message("Choose where to save in Android.");}
            }catch(ActivityNotFoundException e){message("No compatible document or sharing app is installed. Saved records remain on this device.");}});
        });
    }
    @Override protected void onActivityResult(int request,int result,Intent data){super.onActivityResult(request,result,data);if(request!=EXPORT_DOCUMENT)return;
        if(result!=RESULT_OK||data==null||data.getData()==null){message("Export cancelled. Saved records are unchanged.");pendingExport=null;return;}
        String name=pendingExport;pendingExport=null;Uri uri=data.getData();if(name==null||!name.matches("notebook-[a-f0-9-]+\\.md")){message("Export expired. Prepare the notebook again.");return;}
        message("Writing document…");work(()->{try(InputStream in=new FileInputStream(new File(new File(getCacheDir(),"notebook-exports"),name));OutputStream out=getContentResolver().openOutputStream(uri,"wt")){if(out==null)throw new IOException("Document provider returned no output");byte[] bytes=new byte[16384];int n;while((n=in.read(bytes))!=-1)out.write(bytes,0,n);out.flush();}runOnUiThread(()->message("Notebook exported. Source metadata and notes are included."));});
    }
}
