package org.pocketlore.app;

/** Local CPU runtime. Load/generate on a worker; cancel/close may run concurrently.
 * Reset cancellation only while idle, before enqueueing the next operation.
 * Tokens are UTF-8 bytes: accumulate before decoding to preserve split characters.
 * A negative generation result means cancelled; all other failures throw.
 */
public final class NativeRuntime {
    static { System.loadLibrary("pocketlore"); }
    private NativeRuntime() {}
    public interface Sink { void onToken(byte[] utf8); }
    public static native String identity();
    /** Observed GGUF metadata of the currently loaded model; no generation. */
    public static native String loadedModelIdentity(long session);
    /** Diagnostic counts: live lease, live contexts, model/KV/compute buffer bytes for the active context; not process RSS. */
    public static native long[] resourceState();
    /** Read-only diagnostics: phase (0 idle,1 preflight,2 load,3 context,4 prefill,5 decode),
     * load callbacks, abort callbacks, prompt tokens, context attempts/failures, estimated model/KV/compute bytes.
     * Counters are observations, not synchronization guarantees or process-memory measurements. */
    public static native long[] operationState();
    public static native long create();
    private static native boolean cancelled(long session);
    private static boolean verifyLargeProfile(byte[] path,long session)throws Exception {
        try(ResourceStorage.Reservation accounting=ResourceStorage.reserve(0)){
            return PinnedModelProfile.verify(new java.io.File(new String(path,java.nio.charset.StandardCharsets.UTF_8)),()->cancelled(session));
        }
    }
    public static native void load(long session, byte[] localPath);
    public static native int generate(long session, byte[] prompt, int maxTokens, Sink sink);
    /** Applies the loaded model's supported chat template before generation. */
    public static native int generateChat(long session, byte[] systemPrompt, byte[] userPrompt, int maxTokens, Sink sink);
    public static native int generateClaims(long session, byte[] systemPrompt, byte[] userPrompt, int maxTokens, Sink sink, int sources, boolean combined);
    public static native int countChatTokens(long session, byte[] systemPrompt, byte[] userPrompt);
    public static native void cancel(long session);
    public static native void reset(long session);
    public static native void close(long session);
}
