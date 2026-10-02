package org.pocketlore.app;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.database.Cursor;
import android.net.Uri;
import android.provider.OpenableColumns;
import android.widget.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.StandardCopyOption;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** Optional experimental synthesis alongside the existing inspectable source list. */
final class NativePanel {
    static final int PICK_MODEL = 410;
    private final Activity activity;
    // Serialize file promotion and cleanup across Activity recreation.
    private static final ExecutorService worker = Executors.newSingleThreadExecutor();
    private final Button catalog, model, cancel, reload, unload, remove;
    private final TextView state, output, answerStatus;
    private final java.util.function.Consumer<Boolean> busyChanged;
    private final java.util.function.Consumer<String> inspectCitation;
    private volatile AnswerEngine.Outcome outcome;
    private long answerEpoch;
    private volatile boolean stopped, cancelled, memorySuspended;
    private volatile long session;
    private boolean busy, retrieving;
    NativePanel(Activity activity, LinearLayout layout, LinearLayout actions, TextView output, TextView answerStatus, java.util.function.Consumer<Boolean> busyChanged, java.util.function.Consumer<String> inspectCitation) {
        this.activity = activity; this.output = output; this.answerStatus = answerStatus; this.busyChanged = busyChanged; this.inspectCitation=inspectCitation;
        state = new TextView(activity);
        state.setText("Experimental local generation · Import a local GGUF (up to 2048 MiB). Small models may give incorrect answers. Inspect the retrieved sources.");
        layout.addView(state);
        model = new Button(activity); model.setText("Import local GGUF"); model.setContentDescription("Import local model"); layout.addView(model);
        catalog=new Button(activity);catalog.setText("Model catalog and selection");layout.addView(catalog);catalog.setOnClickListener(v->showCatalog());
        cancel = new Button(activity); cancel.setText("Cancel inference or import"); cancel.setEnabled(false); cancel.setContentDescription("Cancel current operation"); actions.addView(cancel);
        model.setOnClickListener(v -> activity.startActivityForResult(new Intent(Intent.ACTION_OPEN_DOCUMENT)
            .addCategory(Intent.CATEGORY_OPENABLE).setType("*/*").putExtra(Intent.EXTRA_LOCAL_ONLY, true), PICK_MODEL));
        cancel.setOnClickListener(v -> cancel());
        unload=new Button(activity);unload.setText("Unload model to free memory");layout.addView(unload);unload.setOnClickListener(v->lowMemory());
        reload=new Button(activity);reload.setText("Reload saved model");layout.addView(reload);reload.setOnClickListener(v->reloadSaved());
        remove=new Button(activity);remove.setText("Remove saved model");layout.addView(remove);
        remove.setOnClickListener(v->new AlertDialog.Builder(activity).setTitle("Remove saved model?")
            .setMessage("Unload and delete the app's saved GGUF. The original file remains. Offline source retrieval remains available.")
            .setNegativeButton("Keep",null).setPositiveButton("Remove",(d,w)->{
                if(busy||stopped)return;
                setBusy(true);worker.execute(()->{try{release();new ModelCatalog(activity.getFilesDir()).removeActive();ImportRecovery.finish(activity.getFilesDir(),"model");showState("Saved model removed. Source retrieval remains available.");}
                    catch(Exception error){showState("Model removal failed: "+error.getMessage());}finally{done();}});
            }).show());
        Button profile=new Button(activity);profile.setText("Model compatibility and limits");layout.addView(profile);
        profile.setOnClickListener(v->new AlertDialog.Builder(activity).setTitle("Current bounded CPU profile")
            .setMessage("GGUF file and native model: at most 2048 MiB. One session; 2048-token context; FP16 KV at most 768 MiB; compute buffers at most 1024 MiB; two CPU threads. Disk reserve: 256 MiB. These component caps do not prove total phone memory safety.\n\n4B, 7–8B and MoE: no measured admission profile is available. File size alone does not establish compatibility. A larger profile requires exact model hash/quantization, device and OS, context, native KV/compute peaks, Java memory, OS reserve and sustained measurements within 12 GB RAM and 50 GB installed assets. Host measurements are not phone proof.")
            .setPositiveButton("Close",null).show());
        if(ImportRecovery.pending(activity.getFilesDir(),"model"))state.setText("Previous model import interrupted or failed. Saved model retained; select the original file to restart verification.");
        // Only the serial import worker writes this app-owned staging path.
        worker.execute(() -> ResourceStorage.cleanupModelStage(activity.getFilesDir()));
        reloadSaved();
    }
    private void showCatalog(){
        if(busy||stopped)return;
        String[] names=new String[ModelCatalog.SPECS.length];for(int i=0;i<names.length;i++)names[i]=ModelCatalog.SPECS[i].name;
        new AlertDialog.Builder(activity).setTitle("Pinned local models").setItems(names,(d,index)->{
            ModelCatalog.Spec spec=ModelCatalog.SPECS[index];
            new AlertDialog.Builder(activity).setTitle(spec.name).setMessage(spec.description()+"\n\nResearch never downloads models. Setup may open an external browser, which uses its own network. Import the exact file afterward. Larger parameter counts do not establish better answers.")
                .setPositiveButton("Select installed",(a,b)->selectInstalled(spec))
                .setNeutralButton("Download in browser",(a,b)->new AlertDialog.Builder(activity).setTitle("Leave offline research for setup?").setMessage("Open the pinned model URL in another app? This requires that app's network connection. Return here to import and verify the file.").setNegativeButton("Cancel",null).setPositiveButton("Open browser",(x,y)->{try{activity.startActivity(new Intent(Intent.ACTION_VIEW,Uri.parse(spec.url())));}catch(android.content.ActivityNotFoundException e){showState("No browser installed. Copy the pinned model from another computer and use Import local GGUF.");}}).show())
                .setNegativeButton("Delete inactive copy",(a,b)->{if(busy)return;setBusy(true);worker.execute(()->{try{new ModelCatalog(activity.getFilesDir()).remove(spec);showState("Inactive catalog copy removed. Original files are unchanged.");}catch(Exception e){showState(e.getMessage());}finally{done();}});}).show();
        }).setNegativeButton("Close",null).show();
    }
    void selectInstalled(ModelCatalog.Spec spec){
        if(busy||stopped)return;setBusy(true);cancelled=false;memorySuspended=false;
        worker.execute(()->{try{
            ModelCatalog library=new ModelCatalog(activity.getFilesDir());
            if(library.active.exists())library.retainActive(()->cancelled||stopped);
            File file=library.object(spec);if(!file.isFile())throw new IOException("Not installed. Import the exact pinned GGUF first.");
            if(library.verify(file,()->cancelled||stopped)!=spec)throw new IOException("Model identity mismatch");
            ModelCatalog.admit(SharedShardUpdate.uniqueBytes(new File(activity.getApplicationInfo().dataDir))+new File(activity.getApplicationInfo().sourceDir).length(),0,activity.getFilesDir().getUsableSpace());
            loadSelection(file,library,spec);
        }catch(Exception|OutOfMemoryError e){release();restorePrevious("Selection failed: "+e.getMessage());}finally{done();}});
    }
    /** Called after identity/admission verification. Also exposes the native failure boundary to instrumentation. */
    boolean loadSelection(File file,ModelCatalog library,ModelCatalog.Spec spec){
        try {
            release();session=NativeRuntime.create();if(cancelled||stopped)NativeRuntime.cancel(session);
            NativeRuntime.load(session,file.getAbsolutePath().getBytes(StandardCharsets.UTF_8));
            if(cancelled||stopped)throw new IOException("Selection cancelled");
            library.activate(spec,()->cancelled||stopped);showState("Selected: "+spec.description()+"\n"+NativeRuntime.identity());return true;
        }catch(Exception|OutOfMemoryError e){release();restorePrevious("Native selection failed: "+e.getMessage());return false;}
    }
    private void restorePrevious(String reason){
        if(session!=0){showState(reason+" · Previous selection remains loaded.");return;}
        File previous;try{previous=new ModelCatalog(activity.getFilesDir()).active;}catch(IOException e){showState(reason+" · Cannot read saved selection: "+e.getMessage());return;}
        if(!cancelled&&!stopped&&!memorySuspended&&previous.isFile())try{session=NativeRuntime.create();NativeRuntime.load(session,previous.getAbsolutePath().getBytes(StandardCharsets.UTF_8));showState(reason+" · Previous saved model reloaded; SHA-256 "+BroadPack.hash(previous));return;}catch(Exception|OutOfMemoryError e){release();reason+=" · Previous model reload failed: "+e.getMessage();}
        showState(reason+" · Previous selection retained on disk; reload when memory is available.");
    }
    void reloadSaved() {
        if(busy || stopped || session!=0)return;
        File saved;try{saved=new ModelCatalog(activity.getFilesDir()).active;}catch(IOException e){state.setText("Saved selection unavailable: "+e.getMessage());return;}
        if(!saved.isFile()){state.setText(ImportRecovery.pending(activity.getFilesDir(),"model")?"Previous model import interrupted or failed. Select the original GGUF to restart verification.":"No saved model. Import a local GGUF first.");return;}
        memorySuspended=false;cancelled=false;setBusy(true);state.setText("Loading saved local model…");
        worker.execute(()->{
            try{if(stopped || memorySuspended)return;if(new File(activity.getFilesDir(),"model-selection").exists())new ModelCatalog(activity.getFilesDir()).verify(saved,()->cancelled||stopped);session=NativeRuntime.create();if(cancelled || stopped || memorySuspended)NativeRuntime.cancel(session);NativeRuntime.load(session,saved.getAbsolutePath().getBytes(StandardCharsets.UTF_8));if(cancelled || stopped || memorySuspended){release();return;}String hash=BroadPack.hash(saved);String label;try{label=ModelCatalog.identify(hash,saved.length()).name;}catch(IOException unknown){label="Legacy model outside pinned catalog; not qualified";}showState("Current model: "+label+" · "+saved.length()+" bytes · SHA-256 "+hash+"\n"+NativeRuntime.identity());}
            catch(Exception | OutOfMemoryError error){release();showState("Saved model could not load; retry with a smaller model: "+error.getMessage());}
            finally{done();}
        });
    }
    void lowMemory() {
        if(stopped)return;
        memorySuspended=true;cancel();++answerEpoch;retrieving=false;outcome=null;
        output.setText("Unverified draft discarded to release memory. Saved sources and model remain on disk.");
        answerStatus.setText("Memory pressure or manual unload · Releasing local model");setBusy(true);
        worker.execute(()->{release();showState("Model unloaded. Use Reload saved model when memory is available.");done();});
    }
    AnswerEngine.Outcome outcome() { return outcome; }
    boolean isBusy() { return busy; }
    boolean hasModel() { return session != 0; }
    void clearEvidence() { ++answerEpoch; outcome=null; retrieving=false; output.setText(""); }
    void searchFailed() { clearEvidence(); setBusy(false); }
    /** Complete an extractive operation without starting or crediting native generation. */
    void finishResearchBrief() { retrieving=false; setBusy(false); }
    void clearAnswer() { ++answerEpoch; outcome = null; cancelled = false; retrieving = true; output.setText(""); setBusy(true); }
    void cancel() {
        cancelled = true;
        long id = session;
        if (id != 0) {
            try { NativeRuntime.cancel(id); }
            catch (IllegalStateException closed) { /* A concurrent failed load can release the handle. */ }
        }
    }
    void selected(Uri uri) {
        if (uri == null || busy || stopped) return;
        long size = -1;
        try (Cursor c = activity.getContentResolver().query(uri, new String[]{OpenableColumns.SIZE}, null, null, null)) {
            if (c != null && c.moveToFirst() && !c.isNull(0)) size = c.getLong(0);
        } catch (Exception e) { state.setText("Cannot inspect local file: " + e.getMessage()); return; }
        if (size < 4 || size > ModelImport.MAX_BYTES) { state.setText("Choose a local GGUF with a known size, at most 2048 MiB."); return; }
        final long bytes = size;
        new AlertDialog.Builder(activity).setTitle("Copy model to app storage?")
            .setMessage("Required additional storage: " + bytes + " bytes plus a 256 MiB reserve. Only exact pinned catalog models are admitted. Native load is checked before changing selection. The original and previous saved model remain. Total app assets must fit the 50 GB hard limit (45 GB target).")
            .setNegativeButton("Cancel", null).setPositiveButton("Import", (d, which) -> importModel(uri, bytes)).show();
    }
    private void importModel(Uri uri, long size) {
        if (busy || stopped) return;
        setBusy(true); cancelled = false; memorySuspended=false; state.setText("Copying and verifying local model…");
        worker.execute(() -> {
            File stage = new File(activity.getFilesDir(), "model.partial");
            long candidate = 0;
            try {
                if (stopped) return;
                ImportRecovery.begin(activity.getFilesDir(),"model");
                ModelCatalog library=new ModelCatalog(activity.getFilesDir());
                long retained=SharedShardUpdate.uniqueBytes(new File(activity.getApplicationInfo().dataDir))+new File(activity.getApplicationInfo().sourceDir).length();
                long peak=ModelCatalog.admit(retained,size,activity.getFilesDir().getUsableSpace());
                if(library.active.exists())library.retainActive(()->cancelled||stopped);
                String hash;
                try (InputStream in = DocumentInput.open(activity.getContentResolver(),uri,()->cancelled || stopped)) {
                    if (in == null) throw new IOException("Cannot open model");
                    hash = ModelImport.copy(in, stage, size, activity.getFilesDir().getUsableSpace(), () -> cancelled || stopped);
                }
                if (cancelled || stopped) throw new IOException("Cancelled");
                ModelCatalog.Spec spec=ModelCatalog.identify(hash,size);
                release();
                candidate = NativeRuntime.create(); session = candidate;
                if (cancelled || stopped) NativeRuntime.cancel(candidate);
                NativeRuntime.load(candidate, stage.getAbsolutePath().getBytes(StandardCharsets.UTF_8));
                if (cancelled || stopped) throw new IOException("Cancelled");
                library.retainStage(stage,spec,()->cancelled||stopped);
                library.activate(spec,()->cancelled||stopped);
                ImportRecovery.finish(activity.getFilesDir(),"model");
                showState("Selected: "+spec.description()+"\nTransaction budget: "+peak+" bytes"+(peak>ModelCatalog.TARGET?" · above 45 GB target":"")+"\n"+NativeRuntime.identity());
            } catch (Exception | OutOfMemoryError e) { if (candidate != 0) release(); restorePrevious("Import failed: " + e.getMessage()); }
            finally { stage.delete(); done(); }
        });
    }
    void answer(String question, ResearchEngine.Result evidence) {
        if (!retrieving || stopped) return;
        retrieving = false;
        final long epoch = ++answerEpoch;
        final long id = session;
        if (id != 0 && !cancelled) NativeRuntime.reset(id);
        outcome = null; setBusy(true);
        output.setText("Preparing an offline answer…"); answerStatus.setText("Checking retrieved evidence…");
        worker.execute(() -> {
            try {
            AnswerEngine.Outcome result = AnswerEngine.answer(question, evidence,
                id == 0 ? null : new AnswerEngine.Generator() {
                    public int run(byte[] prompt,int limit,NativeRuntime.Sink sink) { return NativeRuntime.generateChat(id,EvidencePrompt.SYSTEM.getBytes(StandardCharsets.UTF_8),prompt,limit,sink); }
                    public int runWithSources(byte[] prompt,int limit,NativeRuntime.Sink sink,int sources,boolean combined) {return NativeRuntime.generateClaims(id,EvidencePrompt.SYSTEM.getBytes(StandardCharsets.UTF_8),prompt,limit,sink,sources,combined);}
                    public int countTokens(byte[] prompt) { return NativeRuntime.countChatTokens(id,EvidencePrompt.SYSTEM.getBytes(StandardCharsets.UTF_8),prompt); }
                },
                text -> activity.runOnUiThread(() -> {
                    if (!stopped && !cancelled && epoch == answerEpoch) {
                        answerStatus.setText("Generating locally · Citation checks pending");
                        output.setText("Unverified partial draft\n" + text);
                    }
                }), () -> cancelled || stopped);
            activity.runOnUiThread(() -> {
                if (stopped || epoch != answerEpoch) return;
                // A click can arrive after native completion but before this UI callback.
                AnswerEngine.Outcome visible = cancelled ? AnswerEngine.discardAfterCancel(result) : result;
                outcome = visible;
                output.setText(linkClaims(visible,inspectCitation));output.setMovementMethod(android.text.method.LinkMovementMethod.getInstance());
                String label;
                switch (visible.kind) {
                    case GENERATED: label = "Generated locally · Linked claims; inspect support and source differences"; break;
                    case FALLBACK: label = "Extractive fallback · " + visible.reason; break;
                    case ABSTAINED: label = "Abstained · " + visible.reason; break;
                    default: label = "Cancelled · Partial draft discarded";
                }
                answerStatus.setText(label + String.format(java.util.Locale.ROOT, " · %.0f ms", visible.totalMs));
                setBusy(false);
            });
            } catch(OutOfMemoryError exhausted) {
                release();memorySuspended=true;
                activity.runOnUiThread(()->{if(!stopped)lowMemory();});
            }
        });
    }
    static android.text.SpannableString linkClaims(AnswerEngine.Outcome visible,java.util.function.Consumer<String> inspect) {
        android.text.SpannableString linked=new android.text.SpannableString(visible.text);
        java.util.regex.Matcher citations=java.util.regex.Pattern.compile("\\[([^\\[\\]]+)\\]").matcher(visible.text);
        while(citations.find()) {
            String citation=citations.group(1);
            if(!visible.citedIds.contains(citation))continue;
            linked.setSpan(new android.text.style.ClickableSpan() {
                public void onClick(android.view.View view) { inspect.accept(citation); }
            },citations.start(),citations.end(),android.text.Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
        }
        return linked;
    }
    private void setBusy(boolean value) {
        busy = value; catalog.setEnabled(!value); model.setEnabled(!value); cancel.setEnabled(value);reload.setEnabled(!value);unload.setEnabled(!value);remove.setEnabled(!value);
        busyChanged.accept(value);
    }
    private void showState(String text) { activity.runOnUiThread(() -> { if (!stopped) state.setText(text+(ImportRecovery.pending(activity.getFilesDir(),"model")?"\nPrevious import interrupted or failed; select the original file to restart verification.":"")); }); }
    private void done() { activity.runOnUiThread(() -> { if (!stopped) setBusy(false); }); }
    private void release() { long id = session; session = 0; if (id != 0) NativeRuntime.close(id); }
    void destroy() {
        stopped = true; cancelled = true;
        long id = session; if (id != 0) NativeRuntime.close(id);
        // Queue cleanup after any loader has published its newly created session.
        worker.execute(this::release);
    }
}
