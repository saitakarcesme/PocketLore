package org.pocketlore.app;

import android.app.Instrumentation;
import android.os.Bundle;
import android.os.Debug;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicLong;
import java.util.concurrent.atomic.AtomicReference;

/** Real JNI integration checks. Runs only in the separate instrumentation APK. */
public final class NativeSmokeInstrumentation extends Instrumentation {
    private final JSONObject report = new JSONObject();
    private final JSONArray checks = new JSONArray();
    private volatile boolean sampling;
    private final AtomicLong peakPss = new AtomicLong();
    private static byte[] utf8(String text) { return text.getBytes(StandardCharsets.UTF_8); }
    private static void require(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }
    private void rejects(String name, Runnable operation) throws Exception {
        try { operation.run(); } catch (IllegalStateException expected) {
            checks.put(name); return;
        }
        throw new AssertionError("Expected failure: " + name);
    }
    @Override public void onCreate(Bundle args) { super.onCreate(args); start(); }
    @Override public void onStart() {
        long session = 0;
        Bundle results = new Bundle();
        Thread memory = null;
        try {
            File model = new File(getTargetContext().getFilesDir(), "runtime-smoke.gguf");
            report.put("model_bytes", model.length());
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            try (InputStream in = new FileInputStream(model)) {
                byte[] block = new byte[65536]; int n;
                while ((n = in.read(block)) != -1) digest.update(block, 0, n);
            }
            StringBuilder hash = new StringBuilder();
            for (byte b : digest.digest()) hash.append(String.format(java.util.Locale.ROOT, "%02x", b & 255));
            require(hash.toString().equals("61c69fc5ce91982e26c625d43be5c3c7f0f774da22f4fa4e45c37a80a22ddad4"), "Wrong smoke model");
            report.put("model_sha256", hash.toString());
            report.put("runtime", NativeRuntime.identity());
            report.put("abi", android.os.Build.SUPPORTED_ABIS[0]);
            report.put("android", android.os.Build.VERSION.RELEASE);
            report.put("fingerprint", android.os.Build.FINGERPRINT);
            sampling = true;
            memory = new Thread(() -> {
                while (sampling) {
                    Debug.MemoryInfo info = new Debug.MemoryInfo(); Debug.getMemoryInfo(info);
                    peakPss.accumulateAndGet(info.getTotalPss(), Math::max);
                    try { Thread.sleep(50); } catch (InterruptedException e) { return; }
                }
            });
            memory.start();
            session = NativeRuntime.create(); final long id = session;
            File corrupt = new File(getTargetContext().getFilesDir(), "runtime-corrupt.gguf");
            try (FileOutputStream out = new FileOutputStream(corrupt)) { out.write(utf8("GGUFbroken")); }
            rejects("corrupt_model", () -> NativeRuntime.load(id, utf8(corrupt.getAbsolutePath())));
            rejects("missing_model", () -> NativeRuntime.load(id, utf8(corrupt.getAbsolutePath() + ".missing")));
            rejects("generation_without_model", () -> NativeRuntime.generate(id, utf8("Hello"), 1, b -> {}));
            long begin = System.nanoTime();
            NativeRuntime.load(id, utf8(model.getAbsolutePath()));
            report.put("first_load_ms", (System.nanoTime() - begin) / 1e6); checks.put("real_load");
            byte[] prompt = utf8("The capital of France is");
            report.put("prompt", new String(prompt, StandardCharsets.UTF_8));
            JSONArray runs = new JSONArray();
            String expectedText = null;
            for (int run = 0; run < 2; run++) {
                ByteArrayOutputStream generated = new ByteArrayOutputStream();
                AtomicLong first = new AtomicLong();
                final long start = System.nanoTime();
                int count = NativeRuntime.generate(id, prompt, 24, piece -> {
                    first.compareAndSet(0, System.nanoTime()); generated.write(piece, 0, piece.length);
                });
                double elapsed = (System.nanoTime() - start) / 1e6;
                String text = new String(generated.toByteArray(), StandardCharsets.UTF_8);
                require(count > 0 && !text.trim().isEmpty(), "Empty real generation");
                if (expectedText != null) require(expectedText.equals(text), "Greedy repeat changed output");
                expectedText = text;
                runs.put(new JSONObject().put("run", run).put("tokens", count).put("first_token_ms", (first.get() - start) / 1e6)
                    .put("total_ms", elapsed).put("tokens_per_second_including_prefill", count * 1000 / elapsed).put("text", text));
            }
            report.put("generation", runs); checks.put("real_generation"); checks.put("deterministic_reuse");
            ResearchEngine research = new ResearchEngine(new InputStreamReader(getTargetContext().getAssets().open("water-science.tsv"), StandardCharsets.UTF_8));
            String question = "Compare evaporation and condensation";
            String sourcePrompt = EvidencePrompt.build(question, research.research(question));
            ByteArrayOutputStream grounded = new ByteArrayOutputStream();
            long groundedStart = System.nanoTime();
            int groundedTokens = NativeRuntime.generate(id, utf8(sourcePrompt), 96, b -> grounded.write(b, 0, b.length));
            require(groundedTokens > 0, "No output from real source prompt");
            report.put("source_prompt", sourcePrompt).put("source_draft", new String(grounded.toByteArray(), StandardCharsets.UTF_8))
                .put("source_draft_tokens", groundedTokens).put("source_draft_ms", (System.nanoTime() - groundedStart) / 1e6);
            checks.put("source_prompt_generation");
            rejects("context_overflow", () -> NativeRuntime.generate(id, utf8("water ".repeat(600)), 24, b -> {}));
            rejects("invalid_output_limit", () -> NativeRuntime.generate(id, prompt, 257, b -> {}));
            rejects("callback_exception", () -> NativeRuntime.generate(id, prompt, 24, b -> { throw new IllegalStateException("Sink failure"); }));
            // Cancellation from another thread after inference has delivered its first token.
            CountDownLatch firstToken = new CountDownLatch(1), cancelSent = new CountDownLatch(1);
            AtomicReference<Throwable> cancellationError = new AtomicReference<>();
            AtomicLong cancelTime = new AtomicLong();
            Thread canceller = new Thread(() -> {
                try {
                    require(firstToken.await(30, TimeUnit.SECONDS), "No first token for cancellation");
                    rejects("reset_while_busy", () -> NativeRuntime.reset(id));
                    cancelTime.set(System.nanoTime()); NativeRuntime.cancel(id);
                } catch (Throwable error) { cancellationError.set(error); }
                finally { cancelSent.countDown(); }
            });
            canceller.start();
            int cancelled = NativeRuntime.generate(id, prompt, 256, b -> {
                firstToken.countDown();
                try { require(cancelSent.await(30, TimeUnit.SECONDS), "Cancellation not delivered"); }
                catch (InterruptedException e) { throw new IllegalStateException(e); }
            });
            canceller.join(30000);
            require(cancellationError.get() == null, "Cancellation worker failed: " + cancellationError.get());
            require(cancelled == -1, "Generation did not acknowledge cancellation");
            report.put("cancel_return_ms", (System.nanoTime() - cancelTime.get()) / 1e6); checks.put("cross_thread_cancel");
            require(NativeRuntime.generate(id, prompt, 1, b -> { throw new AssertionError("Cancelled session emitted token"); }) == -1, "Cancellation not sticky");
            checks.put("cancel_before_generation");
            NativeRuntime.reset(id);
            require(NativeRuntime.generate(id, prompt, 4, b -> {}) > 0, "Cannot reuse after cancellation");
            checks.put("reuse_after_cancel");
            // Close from inside a callback: the active call must retain native ownership.
            require(NativeRuntime.generate(id, prompt, 24, b -> NativeRuntime.close(id)) == -1, "Close did not abort active call");
            NativeRuntime.close(id); checks.put("close_during_generation");
            rejects("closed_handle", () -> NativeRuntime.generate(id, prompt, 1, b -> {}));
            session = 0;
            long preCancelled = NativeRuntime.create();
            try {
                NativeRuntime.cancel(preCancelled);
                rejects("cancel_before_load", () -> NativeRuntime.load(preCancelled, utf8(model.getAbsolutePath())));
            } finally { NativeRuntime.close(preCancelled); }
            testImport();
            String proc = new String(java.nio.file.Files.readAllBytes(new File("/proc/self/status").toPath()), StandardCharsets.UTF_8);
            for (String line : proc.split("\n")) if (line.startsWith("VmHWM:") || line.startsWith("VmRSS:")) report.put(line.split(":")[0], line.split(":")[1].trim());
            report.put("status", "pass");
        } catch (Throwable error) {
            try { report.put("status", "fail").put("error", android.util.Log.getStackTraceString(error)); }
            catch (Exception ignored) { }
        } finally {
            if (session != 0) NativeRuntime.close(session);
            sampling = false;
            if (memory != null) { memory.interrupt(); try { memory.join(2000); } catch (InterruptedException ignored) {} }
            try {
                report.put("checks", checks).put("sampled_peak_pss_kib", peakPss.get());
                try (FileOutputStream out = new FileOutputStream(new File(getTargetContext().getFilesDir(), "runtime-result.json"))) {
                    out.write(utf8(report.toString(2))); out.getFD().sync();
                }
                results.putString("stream", report.toString(2));
            } catch (Exception error) { results.putString("stream", "Cannot write report: " + error); }
            finish("pass".equals(report.optString("status")) ? ActivityResult.OK : ActivityResult.FAIL, results);
        }
    }
    private void testImport() throws Exception {
        File stage = new File(getTargetContext().getFilesDir(), "runtime-import.partial");
        byte[] input = utf8("GGUFtest");
        for (String mode : new String[]{"low_storage", "truncated_import", "oversized_import", "cancelled_import", "wrong_magic"}) {
            boolean rejected = false;
            try {
                ModelImport.copy(new ByteArrayInputStream(mode.equals("wrong_magic") ? utf8("BAD!test") : input), stage,
                    mode.equals("truncated_import") ? 12 : mode.equals("oversized_import") ? 4 : 8,
                    mode.equals("low_storage") ? 0 : ModelImport.MAX_BYTES,
                    () -> mode.equals("cancelled_import"));
            } catch (IOException expected) { rejected = true; }
            require(rejected && !stage.exists(), "Import guard failed: " + mode); checks.put(mode);
        }
        String hash = ModelImport.copy(new ByteArrayInputStream(input), stage, 8, ModelImport.MAX_BYTES, () -> false);
        require(stage.length() == 8 && hash.length() == 64, "Valid staging failed");
        require(stage.delete(), "Cannot remove test staging file"); checks.put("bounded_import");
    }
    private static final class ActivityResult { static final int OK = -1, FAIL = 0; }
}
