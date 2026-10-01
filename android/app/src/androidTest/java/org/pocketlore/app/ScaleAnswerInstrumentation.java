package org.pocketlore.app;
import android.app.Instrumentation;import android.os.Bundle;import java.util.*;import java.nio.file.*;import java.nio.charset.StandardCharsets;import org.json.*;
/** Real sealed bulk records on the supervised full-inventory emulator; no inference. */
public final class ScaleAnswerInstrumentation extends Instrumentation {
 @Override public void onCreate(Bundle b){super.onCreate(b);start();}
 @Override public void onStart(){Bundle status=new Bundle();try{
  ScaleLibrary library=new ScaleLibrary(getTargetContext().getFilesDir());ScaleLibrary.Entry wiki=null;for(ScaleLibrary.Entry e:library.entries())if(e.active&&e.kind().equals("wiki")){wiki=e;break;}if(wiki==null)throw new AssertionError("No installed active wiki collection");
  ScaleAnswerAdapter.Ledger ledger=BulkSourceReviews.load(getTargetContext().getAssets().open("bulk-source-reviews.json"));
  String[][] ids={{"000_00000","4456695"},{"000_00002","1910"},{"000_00008","1419"},{"000_00008","1909"},{"000_00011","1566"},{"000_00012","586"},{"000_00013","991"},{"000_00014","656"}};JSONArray results=new JSONArray();
  for(String[] id:ids){long start=System.nanoTime();ScaleWiki.Hit hit=ScaleWiki.byId(wiki,id[0],id[1],()->false);ScaleWiki.Read read=ScaleWiki.read(hit,getTargetContext().getCacheDir(),()->false);ScaleAnswerAdapter.Snapshot source=ScaleWiki.answerSnapshot(hit,read);ScaleAnswerAdapter.Review review=ledger.get(source);if(review==null||!review.snapshot.equals(source.fingerprint()))throw new AssertionError("Installed snapshot does not match disposition");
   try{ScaleAnswerAdapter.admit(source,review.start,review.end,ledger,()->false);throw new AssertionError("Unreviewed source admitted");}catch(IllegalArgumentException expected){if(!expected.getMessage().contains("independent rights/fidelity"))throw expected;}
   JSONObject row=new JSONObject().put("id",id[1]).put("shard",id[0]).put("snapshot_sha256",source.fingerprint()).put("text_sha256",source.textHash).put("record_sha256",source.recordHash).put("raw_scope",source.rawScope).put("preview_truncated",read.previewTruncated).put("elapsed_ns",System.nanoTime()-start).put("status",ScaleWiki.answerReview(hit,read,ledger)).put("route","withheld_pending_source_review");results.put(row);
  }
  JSONObject receipt=new JSONObject().put("environment","emulator-5562 Android full-inventory reader; no inference").put("records",results).put("independently_cleared",0).put("published_claims",0);
  Files.write(getTargetContext().getFilesDir().toPath().resolve("scale-answer-results.json"),receipt.toString(2).getBytes(StandardCharsets.UTF_8));status.putString("stream","8 real cross-shard adapter denials pass; no claims published\n");finish(-1,status);
 }catch(Throwable e){status.putString("stream",android.util.Log.getStackTraceString(e));finish(1,status);}}
}
