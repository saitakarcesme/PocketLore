package org.pocketlore.app;
/** Bundled CPU recognizers; never a platform/provider/network recognition service. */
final class AttachmentNative {
 static {System.loadLibrary("pocketlore_attachments");}
 static native int phase();static native void reset();static native void cancel();
 static native String ocr(String tessdata,byte[] gray,int width,int height,long remainingNanos)throws java.io.IOException;
 static native String speech(String model,float[] pcm)throws java.io.IOException;
 static final String IDENTITY="Tesseract5.5.3 db0ec62f81b0737fbbe184d8fea40af5738f8eef; Leptonica1.85.0 63aef18d98432b8582a1565e241f7bd2ee9cc8d9; whisper.cpp1.7.6 a8d002cfd879315632a579e73f0148d06959de36; CPU2 threads; English";
}
