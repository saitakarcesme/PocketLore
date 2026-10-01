package org.pocketlore.app;
import java.io.*;import java.nio.file.*;import java.util.function.BooleanSupplier;
/** Only the two declared optional assets are admitted. No downloader or automatic installation. */
final class AttachmentAssets {
 static final String OCR="7d4322bd2a7749724879683fc3912cb542f19906c83bcc1a52132556427170b2",SPEECH="921e4cf8686fdd993dcd081a5da5b6c365bfde1162e72b08d75ac75289920b1f";
 static long bytes(boolean speech){return speech?77704715L:4113088L;}
 static String hash(boolean speech){return speech?SPEECH:OCR;}
 static File file(File root,boolean speech){return new File(root,speech?"attachment-assets/ggml-tiny.en.bin":"attachment-assets/tessdata/eng.traineddata");}
 static boolean available(File root,boolean speech)throws Exception{File f=file(root,speech);return f.isFile()&&f.length()==bytes(speech)&&BroadPack.hash(f).equals(hash(speech));}
 static synchronized void install(File root,boolean speech,InputStream in,BooleanSupplier cancel)throws Exception{File dst=file(root,speech);dst.getParentFile().mkdirs();ResourceStorage.requireSpace(bytes(speech),root.getUsableSpace());File stage=File.createTempFile("attachment-",".partial",dst.getParentFile());try{ResourceStorage.copy(in,stage,bytes(speech),cancel);PersonalText.check(cancel);if(stage.length()!=bytes(speech)||!BroadPack.hash(stage).equals(hash(speech)))throw new IOException("Optional asset hash/size mismatch; installed asset retained");PersonalText.check(cancel);Files.move(stage.toPath(),dst.toPath(),StandardCopyOption.ATOMIC_MOVE,StandardCopyOption.REPLACE_EXISTING);}finally{stage.delete();}}
}
