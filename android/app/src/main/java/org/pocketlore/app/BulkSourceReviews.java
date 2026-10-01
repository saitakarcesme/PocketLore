package org.pocketlore.app;
import java.io.*;import java.nio.charset.StandardCharsets;import java.util.*;import org.json.*;
/** Source review dispositions bundled with app code; imported manifests cannot grant approval. */
final class BulkSourceReviews {
 static ScaleAnswerAdapter.Ledger load(InputStream input)throws Exception {
  byte[] bytes;try(InputStream in=input;ByteArrayOutputStream out=new ByteArrayOutputStream()){byte[] block=new byte[4096];int n;while((n=in.read(block))!=-1){if(out.size()+n>131072)throw new IOException("Review ledger too large");out.write(block,0,n);}bytes=out.toByteArray();}if(bytes.length>131072)throw new IOException("Review ledger too large");
  JSONArray records=new JSONObject(new String(bytes,StandardCharsets.UTF_8)).getJSONArray("dispositions");Map<String,ScaleAnswerAdapter.Review> reviews=new HashMap<>();
  for(int i=0;i<records.length();i++){JSONObject r=records.getJSONObject(i);String key=r.getString("key");if(reviews.containsKey(key))throw new IOException("Conflicting review identity");
   boolean approved=r.getString("rights_status").equals("independently_approved")&&r.getString("fidelity_status").equals("independently_approved");
   reviews.put(key,new ScaleAnswerAdapter.Review(r.getString("snapshot_sha256"),r.getInt("start_utf16"),r.getInt("end_utf16"),r.getString("span_sha256"),r.optString("rights_receipt_sha256"),r.optString("fidelity_receipt_sha256"),approved));}
  return new ScaleAnswerAdapter.Ledger(reviews);
 }
}
