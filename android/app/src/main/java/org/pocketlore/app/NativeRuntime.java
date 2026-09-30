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
    public static native long create();
    public static native void load(long session, byte[] localPath);
    public static native int generate(long session, byte[] prompt, int maxTokens, Sink sink);
    /** Applies the loaded model's supported chat template before generation. */
    public static native int generateChat(long session, byte[] systemPrompt, byte[] userPrompt, int maxTokens, Sink sink);
    public static native int countChatTokens(long session, byte[] systemPrompt, byte[] userPrompt);
    public static native void cancel(long session);
    public static native void reset(long session);
    public static native void close(long session);
}
