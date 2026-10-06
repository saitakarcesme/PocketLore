package org.pocketlore.app;
import java.io.IOException;
/** Provider MIME is an additional check, never a substitute for container validation. */
final class DocumentFormatPolicy {
 static void verifyMime(String ext,String mime)throws IOException {
  if(mime==null||mime.isEmpty()||mime.equals("application/octet-stream"))return;
  String expected;
  switch(ext){case "docx":expected="application/vnd.openxmlformats-officedocument.wordprocessingml.document";break;case "pptx":expected="application/vnd.openxmlformats-officedocument.presentationml.presentation";break;case "odt":expected="application/vnd.oasis.opendocument.text";break;case "odp":expected="application/vnd.oasis.opendocument.presentation";break;case "epub":expected="application/epub+zip";break;case "html":case "htm":expected="text/html";break;default:return;}
  PersonalText.require(mime.split(";",2)[0].trim().equalsIgnoreCase(expected),"Provider MIME differs from document format");
 }
 private DocumentFormatPolicy(){}
}
