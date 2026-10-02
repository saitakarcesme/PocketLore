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
    // Provider calls never occupy the notebook database/source executor. No queued or
    // unbounded replacement threads if a provider blocks inside openFileDescriptor.
    private static final ThreadPoolExecutor EXPORT_IO=new ThreadPoolExecutor(1,1,0L,TimeUnit.MILLISECONDS,new SynchronousQueue<>());
    static final class ExportJob {final java.util.concurrent.atomic.AtomicBoolean cancelled=new java.util.concurrent.atomic.AtomicBoolean();}
    volatile ExportJob exportJob;
    android.widget.Button cancelExport;
    TextView operation;
    void cancelExport(){ExportJob job=exportJob;if(job!=null){job.cancelled.set(true);message("Cancelling export… A partial destination may remain; saved records are unchanged.");}}
    private void exportControl(boolean visible){
        if(operation==null||!(operation.getParent() instanceof android.view.ViewGroup))return;
        android.view.ViewGroup parent=(android.view.ViewGroup)operation.getParent();
        if(cancelExport==null||cancelExport.getParent()!=parent){
            cancelExport=new android.widget.Button(this);cancelExport.setText("Cancel export");ReaderUi.styleButton(this,cancelExport,false);
            cancelExport.setOnClickListener(v->cancelExport());parent.addView(cancelExport,parent.indexOfChild(operation)+1);
        }
        cancelExport.setVisibility(visible?android.view.View.VISIBLE:android.view.View.GONE);
    }
    @Override protected void onDestroy(){ExportJob job=exportJob;if(job!=null)job.cancelled.set(true);super.onDestroy();}

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
        writeDocument(new File(new File(getCacheDir(),"notebook-exports"),name),uri);
    }
    void writeDocument(File source,Uri uri){
        if(exportJob!=null){message("An export is still stopping. Saved records remain available.");return;}
        ExportJob job=new ExportJob();exportJob=job;message("Writing document…");exportControl(true);
        try{EXPORT_IO.execute(()->{
            String outcome;
            try(InputStream in=new FileInputStream(source);OutputStream out=DocumentOutput.open(getContentResolver(),uri,job.cancelled::get)){
                byte[] bytes=new byte[16384];int n;while((n=in.read(bytes))!=-1){PersonalText.check(job.cancelled::get);out.write(bytes,0,n);}
                PersonalText.check(job.cancelled::get);out.flush();
                outcome="Notebook exported. Source metadata and notes are included.";
            }catch(Exception e){outcome=job.cancelled.get()?"Export cancelled. A partial destination may remain; saved records are unchanged.":"Export failed: "+e.getMessage()+". A partial destination may remain; saved records are unchanged.";}
            final String result=outcome;
            runOnUiThread(()->{if(exportJob==job){exportJob=null;if(!isDestroyed()){exportControl(false);message(result);}}});
        });}catch(RejectedExecutionException e){exportJob=null;exportControl(false);message("Another export is still stopping. Try again after the document provider responds; saved records remain available.");}
    }
}
