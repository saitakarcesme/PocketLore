package org.pocketlore.app;
import android.app.Instrumentation;
import android.os.Bundle;
import java.io.File;
/** Isolated real JNI subset. Does not import or replace the saved user model/pack. */
public final class CompleteClaimInstrumentation extends Instrumentation {
 @Override public void onCreate(Bundle args){super.onCreate(args);start();}
 @Override public void onStart(){Bundle result=new Bundle();
  try {File dir=new File(getTargetContext().getFilesDir(),"complete-claims");
   CompleteClaimHarness.main(new String[]{new File(dir,"inputs").getAbsolutePath(),new File(dir,"model.gguf").getAbsolutePath(),new File(dir,"results").getAbsolutePath()});
   result.putString("result","Real JNI outputs in files/complete-claims/results");finish(-1,result);
  }catch(Throwable e){result.putString("failure",e.toString());finish(1,result);}
 }
}
