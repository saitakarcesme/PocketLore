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

    // Only files created by this Activity may be reclaimed; legacy/user files stay untouched.
    final Set<String> ownedExports=new HashSet<>();
    void discardOwned(String name){if(name!=null&&ownedExports.remove(name))new File(new File(getCacheDir(),"notebook-exports"),name).delete();}
    String pendingExport;
    void message(String s){if(operation!=null){operation.setVisibility(android.view.View.VISIBLE);operation.setText(s);operation.post(()->operation.requestRectangleOnScreen(new android.graphics.Rect(0,0,operation.getWidth(),operation.getHeight()),false));}}
    @Override public void onCreate(Bundle state){super.onCreate(state);if(state!=null){pendingExport=state.getString("export");ArrayList<String> owned=state.getStringArrayList("ownedExports");if(owned!=null)ownedExports.addAll(owned);}}
    @Override public void onSaveInstanceState(Bundle b){super.onSaveInstanceState(b);b.putString("export",pendingExport);b.putStringArrayList("ownedExports",new ArrayList<>(ownedExports));}
    interface Task {void run()throws Exception;}
    void work(Task task){IO.execute(()->{try{task.run();}catch(Exception e){runOnUiThread(()->{if(!isDestroyed())message("Could not complete: "+e.getMessage());});}});}
    interface ExportSource {void write(Writer out,java.util.function.BooleanSupplier cancelled)throws Exception;}
    void exportNotebook(){prepareExport((out,cancelled)->{try(NotebookStore store=new NotebookStore(this)){store.exportAll(out,cancelled);}},false);}
    void export(List<NotebookStore.Entry> entries,boolean share){
        if(entries.isEmpty()){message("No saved records to export.");return;}
        prepareExport((out,cancelled)->{out.write(NotebookStore.HEADER);long bytes=NotebookStore.HEADER.getBytes(StandardCharsets.UTF_8).length;for(NotebookStore.Entry e:entries)bytes=NotebookStore.writeRecord(out,e,bytes,cancelled);},share);
    }
    private void prepareExport(ExportSource source,boolean share){
        if(exportJob!=null){message("An export is still active. Cancel it or wait before retrying.");return;}
        ExportJob job=new ExportJob();exportJob=job;message("Preparing a consistent local notebook snapshot…");exportControl(true);
        IO.execute(()->{
            File out=null;String error=null;
            try(ResourceStorage.Reservation ignored=ResourceStorage.reserve(2*NotebookStore.MAX_DB_BYTES+NotebookStore.MAX_EXPORT_BYTES)){
                File dir=new File(getCacheDir(),"notebook-exports");if(!dir.isDirectory()&&!dir.mkdirs())throw new IOException("Export directory unavailable");
                NotebookShareLease.expire(dir,System.currentTimeMillis(),job.cancelled::get);
                long total=0;File[] files=dir.listFiles();if(files==null)throw new IOException("Export storage cannot be measured");for(File f:files)total=Math.addExact(total,f.length());
                if(total+NotebookStore.MAX_EXPORT_BYTES>64L*1024*1024)throw new IOException("Temporary export budget is 64 MiB. Existing files are retained.");
                PersonalText.check(job.cancelled::get);out=new File(dir,"notebook-"+UUID.randomUUID()+".md");
                try(FileOutputStream bytes=new FileOutputStream(out);Writer writer=new OutputStreamWriter(bytes,StandardCharsets.UTF_8)){source.write(writer,job.cancelled::get);writer.flush();PersonalText.check(job.cancelled::get);bytes.getFD().sync();}
                if(share)NotebookShareLease.record(out,System.currentTimeMillis(),job.cancelled::get);
            }catch(Exception e){error=job.cancelled.get()?"Export preparation cancelled. Saved records are unchanged.":"Export preparation failed: "+e.getMessage()+". Saved records are unchanged.";if(out!=null)out.delete();}
            File ready=out;String failure=error;
            runOnUiThread(()->{if(exportJob==job){exportJob=null;if(!isDestroyed())exportControl(false);}if(isDestroyed()||job.cancelled.get()){if(ready!=null){ready.delete();new File(ready.getPath()+NotebookShareLease.SUFFIX).delete();}if(!isDestroyed())message("Export preparation cancelled. Saved records are unchanged.");return;}if(failure!=null){message(failure);return;}try{
                if(share){Uri uri=Uri.parse("content://"+getPackageName()+".notebook/"+ready.getName());Intent send=new Intent(Intent.ACTION_SEND).setType("text/markdown").putExtra(Intent.EXTRA_STREAM,uri).addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);send.setClipData(ClipData.newRawUri("PocketLore notebook",uri));startActivity(Intent.createChooser(send,"Share notebook snapshot"));message("Choose a recipient in Android. This temporary share expires after 24 hours. Sharing does not verify source rights.");}
                else {ownedExports.add(ready.getName());pendingExport=ready.getName();startActivityForResult(new Intent(Intent.ACTION_CREATE_DOCUMENT).addCategory(Intent.CATEGORY_OPENABLE).setType("text/markdown").putExtra(Intent.EXTRA_TITLE,"PocketLore-"+System.currentTimeMillis()+".md"),EXPORT_DOCUMENT);message("Choose where to save in Android.");}
            }catch(ActivityNotFoundException e){message("No compatible document or sharing app is installed. Saved records remain on this device.");}});
        });
    }
    @Override protected void onActivityResult(int request,int result,Intent data){super.onActivityResult(request,result,data);if(request!=EXPORT_DOCUMENT)return;
        if(result!=RESULT_OK||data==null||data.getData()==null){message("Export cancelled. Saved records are unchanged.");discardOwned(pendingExport);pendingExport=null;return;}
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
            runOnUiThread(()->{discardOwned(source.getName());if(exportJob==job){exportJob=null;if(!isDestroyed()){exportControl(false);message(result);}}});
        });}catch(RejectedExecutionException e){exportJob=null;exportControl(false);message("Another export is still stopping. Try again after the document provider responds; saved records remain available.");}
    }
}
