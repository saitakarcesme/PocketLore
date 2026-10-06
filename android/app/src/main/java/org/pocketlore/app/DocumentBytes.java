package org.pocketlore.app;
import java.io.*;import java.util.function.BooleanSupplier;
/** Bounded reads never allocate from provider or ZIP declarations. */
final class DocumentBytes {
 static byte[] read(InputStream in,int limit,BooleanSupplier cancel)throws IOException{ByteArrayOutputStream out=new ByteArrayOutputStream();byte[] b=new byte[8192];int n;while(true){PersonalText.check(cancel);n=in.read(b);if(n==-1)break;PersonalText.check(cancel);if(out.size()+n>limit)throw new IOException("Document exceeds size limit");out.write(b,0,n);}PersonalText.check(cancel);return out.toByteArray();}
 private DocumentBytes(){}
}
