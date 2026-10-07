package org.pocketlore.app;
import java.io.*;import java.nio.file.*;import java.util.function.BooleanSupplier;
/** Only the two declared optional assets are admitted. No downloader or automatic installation. */
final class AttachmentAssets {
 static final String OCR="7d4322bd2a7749724879683fc3912cb542f19906c83bcc1a52132556427170b2",SPEECH="921e4cf8686fdd993dcd081a5da5b6c365bfde1162e72b08d75ac75289920b1f";
 static long bytes(boolean speech){return speech?77704715L:4113088L;}
 static String hash(boolean speech){return speech?SPEECH:OCR;}
 static File file(File root,boolean speech){return new File(root,speech?"attachment-assets/ggml-tiny.en.bin":"attachment-assets/tessdata/eng.traineddata");}
 static boolean available(File root,boolean speech)throws Exception{File f=file(root,speech);return f.isFile()&&f.length()==bytes(speech)&&BroadPack.hash(f).equals(hash(speech));}
 static boolean available(File root,OcrDeadline deadline)throws Exception{
  deadline.check();File f=file(root,false);Path path=f.toPath();
  if(!Files.isRegularFile(path,LinkOption.NOFOLLOW_LINKS))return false;
  java.nio.file.attribute.BasicFileAttributes before=Files.readAttributes(path,java.nio.file.attribute.BasicFileAttributes.class,LinkOption.NOFOLLOW_LINKS);
  if(before.size()!=bytes(false))return false;
  String actual;try(InputStream in=Files.newInputStream(path,LinkOption.NOFOLLOW_LINKS)){deadline.check();actual=deadline.hash(in,bytes(false));}
  deadline.check();java.nio.file.attribute.BasicFileAttributes after=Files.readAttributes(path,java.nio.file.attribute.BasicFileAttributes.class,LinkOption.NOFOLLOW_LINKS);
  if(!after.isRegularFile()||!java.util.Objects.equals(before.fileKey(),after.fileKey())||before.size()!=after.size()||!before.lastModifiedTime().equals(after.lastModifiedTime()))throw new IOException("OCR asset changed during verification");
  deadline.check();return actual.equals(OCR);
 }
 static synchronized void install(File root,boolean speech,InputStream in,BooleanSupplier cancel)throws Exception{File dst=file(root,speech);dst.getParentFile().mkdirs();ResourceStorage.requireSpace(bytes(speech),root.getUsableSpace());try(ResourceStorage.Reservation reservation=ResourceStorage.reserve(ResourceStorage.stagePeak(bytes(speech)))){File stage=File.createTempFile("attachment-",".partial",dst.getParentFile());try{ResourceStorage.copy(in,stage,bytes(speech),cancel);PersonalText.check(cancel);if(stage.length()!=bytes(speech)||!BroadPack.hash(stage).equals(hash(speech)))throw new IOException("Optional asset hash/size mismatch; installed asset retained");PersonalText.check(cancel);Files.move(stage.toPath(),dst.toPath(),StandardCopyOption.ATOMIC_MOVE,StandardCopyOption.REPLACE_EXISTING);}finally{stage.delete();}}}
}
