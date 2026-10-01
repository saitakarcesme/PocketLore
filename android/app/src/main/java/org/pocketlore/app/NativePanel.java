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
    private final Button model, cancel, reload, unload, remove;
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
                setBusy(true);worker.execute(()->{try{release();Files.deleteIfExists(new File(activity.getFilesDir(),"model.gguf").toPath());ImportRecovery.finish(activity.getFilesDir(),"model");showState("Saved model removed. Source retrieval remains available.");}
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
    void reloadSaved() {
        if(busy || stopped || session!=0)return;
        File saved=new File(activity.getFilesDir(),"model.gguf");
        if(!saved.isFile()){state.setText(ImportRecovery.pending(activity.getFilesDir(),"model")?"Previous model import interrupted or failed. Select the original GGUF to restart verification.":"No saved model. Import a local GGUF first.");return;}
        memorySuspended=false;cancelled=false;setBusy(true);state.setText("Loading saved local model…");
        worker.execute(()->{
            try{if(stopped || memorySuspended)return;session=NativeRuntime.create();if(cancelled || stopped || memorySuspended)NativeRuntime.cancel(session);NativeRuntime.load(session,saved.getAbsolutePath().getBytes(StandardCharsets.UTF_8));if(cancelled || stopped || memorySuspended){release();return;}showState("Local model ready · "+saved.length()+" bytes · SHA-256 "+BroadPack.hash(saved)+"\n"+NativeRuntime.identity());}
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
            .setMessage("Required additional storage: " + bytes + " bytes plus a 256 MiB reserve. The original file remains. SHA-256 is calculated during import; it is an identity, not a trust guarantee.")
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
                String hash;
                try (InputStream in = DocumentInput.open(activity.getContentResolver(),uri,()->cancelled || stopped)) {
                    if (in == null) throw new IOException("Cannot open model");
                    hash = ModelImport.copy(in, stage, size, activity.getFilesDir().getUsableSpace(), () -> cancelled || stopped);
                }
                if (cancelled || stopped) throw new IOException("Cancelled");
                release();
                candidate = NativeRuntime.create(); session = candidate;
                if (cancelled || stopped) NativeRuntime.cancel(candidate);
                NativeRuntime.load(candidate, stage.getAbsolutePath().getBytes(StandardCharsets.UTF_8));
                if (cancelled || stopped) throw new IOException("Cancelled");
                Files.move(stage.toPath(), new File(activity.getFilesDir(), "model.gguf").toPath(),
                    StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING);
                ImportRecovery.finish(activity.getFilesDir(),"model");
                showState("Local model ready · SHA-256 " + hash + "\n" + NativeRuntime.identity());
            } catch (Exception | OutOfMemoryError e) { if (candidate != 0) release(); showState("Import failed: " + e.getMessage()); }
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
        busy = value; model.setEnabled(!value); cancel.setEnabled(value);reload.setEnabled(!value);unload.setEnabled(!value);remove.setEnabled(!value);
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
