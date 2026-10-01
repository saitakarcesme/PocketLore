package org.pocketlore.app;
import java.io.*;import java.nio.charset.StandardCharsets;import java.util.*;import org.json.*;
/** Source review dispositions bundled with app code; imported manifests cannot grant approval. */
final class BulkSourceReviews {
 static byte[] readLimited(InputStream input,int limit)throws Exception {try(InputStream in=input;ByteArrayOutputStream out=new ByteArrayOutputStream()){byte[] b=new byte[4096];int n;while((n=in.read(b))!=-1){if(out.size()+n>limit)throw new IOException("Review artifact too large");out.write(b,0,n);}return out.toByteArray();}}
 static ScaleAnswerAdapter.Ledger loadAssets(android.content.res.AssetManager assets)throws Exception {return load(assets.open("bulk-source-reviews.json"),hash->readLimited(assets.open("bulk-reviews/"+hash+".json"),16384));}
 interface ReceiptSource { byte[] read(String sha256)throws Exception; }
 static ScaleAnswerAdapter.Ledger load(InputStream input)throws Exception {return load(input,hash->{throw new IOException("Independent review receipt unavailable");});}
 static void receipt(JSONObject record,String scope,ReceiptSource source)throws Exception {
  String hash=record.getString(scope+"_receipt_sha256");if(!hash.matches("[0-9a-f]{64}"))throw new IOException("Missing independent review receipt hash");
  byte[] bytes=source.read(hash);if(bytes==null||bytes.length>16384||!ScaleLibrary.hex(java.security.MessageDigest.getInstance("SHA-256").digest(bytes)).equals(hash))throw new IOException("Review receipt changed/missing");
  JSONObject review=new JSONObject(new String(bytes,StandardCharsets.UTF_8));
  if(!review.getBoolean("independent")||!review.getString("scope").equals(scope)||!review.getString("decision").equals("approved")||!review.getString("snapshot_sha256").equals(record.getString("snapshot_sha256"))||!review.getString("span_sha256").equals(record.getString("span_sha256"))||review.getInt("start_utf16")!=record.getInt("start_utf16")||review.getInt("end_utf16")!=record.getInt("end_utf16"))throw new IOException("Independent review scope mismatch");
 }
 static ScaleAnswerAdapter.Ledger load(InputStream input,ReceiptSource source)throws Exception {
  byte[] bytes;try(InputStream in=input;ByteArrayOutputStream out=new ByteArrayOutputStream()){byte[] block=new byte[4096];int n;while((n=in.read(block))!=-1){if(out.size()+n>131072)throw new IOException("Review ledger too large");out.write(block,0,n);}bytes=out.toByteArray();}if(bytes.length>131072)throw new IOException("Review ledger too large");
  JSONArray records=new JSONObject(new String(bytes,StandardCharsets.UTF_8)).getJSONArray("dispositions");Map<String,ScaleAnswerAdapter.Review> reviews=new HashMap<>();
  for(int i=0;i<records.length();i++){JSONObject r=records.getJSONObject(i);String key=r.getString("key");if(reviews.containsKey(key))throw new IOException("Conflicting review identity");
   boolean approved=r.getString("rights_status").equals("independently_approved")&&r.getString("fidelity_status").equals("independently_approved");
   if(approved){receipt(r,"rights",source);receipt(r,"fidelity",source);}
   reviews.put(key,new ScaleAnswerAdapter.Review(r.getString("snapshot_sha256"),r.getInt("start_utf16"),r.getInt("end_utf16"),r.getString("span_sha256"),r.optString("rights_receipt_sha256"),r.optString("fidelity_receipt_sha256"),approved));}
  return new ScaleAnswerAdapter.Ledger(reviews);
 }
}
