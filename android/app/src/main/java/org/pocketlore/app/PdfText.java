package org.pocketlore.app;
import android.graphics.pdf.PdfRenderer;import android.graphics.pdf.content.PdfPageTextContent;import android.os.*;import java.io.*;import java.nio.file.*;import java.util.*;import java.util.function.BooleanSupplier;
/** Local platform extraction only. No OCR and no claim that page layout is lossless. */
final class PdfText {
 static final class Result {final String text;final List<PersonalText.Span> spans;Result(String t,List<PersonalText.Span>s){text=t;spans=s;}}
 static Result extract(byte[] raw,File cache,BooleanSupplier cancel)throws Exception {
  if(Build.VERSION.SDK_INT<35)throw new IOException("Text PDF import requires Android15 or later; convert locally to UTF-8 text on older devices");
  PersonalText.check(cancel);File stage=File.createTempFile("personal-pdf-",".partial",cache);
  try{Files.write(stage.toPath(),raw);try(ParcelFileDescriptor fd=ParcelFileDescriptor.open(stage,ParcelFileDescriptor.MODE_READ_ONLY);PdfRenderer pdf=new PdfRenderer(fd)){
   PersonalText.require(pdf.getPageCount()>0&&pdf.getPageCount()<=100,"PDF requires1–100 pages");StringBuilder text=new StringBuilder();List<PersonalText.Span> spans=new ArrayList<>();
   for(int page=0;page<pdf.getPageCount();page++){PersonalText.check(cancel);try(PdfRenderer.Page p=pdf.openPage(page)){int block=0;for(PdfPageTextContent content:p.getTextContents()){PersonalText.check(cancel);block++;String t=content.getText();if(t.trim().isEmpty())continue;PersonalText.require(text.length()+t.length()+1<=PersonalText.MAX_TEXT,"PDF extracted text exceeds limit");int a=text.length();text.append(t);PersonalText.add(spans,a,text.length(),"PDF page "+(page+1)+", text block "+block+"; extraction order may differ from visual layout");text.append('\n');}}}
   PersonalText.require(!spans.isEmpty(),"PDF has no extractable text; empty or scanned/image-only PDFs need external OCR (not provided)");PersonalText.check(cancel);return new Result(text.toString(),spans);
  }}catch(SecurityException e){throw new IOException("Password-protected PDF cannot be imported; provide an unlocked local copy",e);}finally{stage.delete();}
 }
}
