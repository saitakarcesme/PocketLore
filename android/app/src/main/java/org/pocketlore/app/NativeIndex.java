package org.pocketlore.app;
import java.io.IOException;import java.nio.charset.StandardCharsets;import java.util.function.BooleanSupplier;import org.json.JSONArray;
/** Isolated pinned FTS5 engine; never replaces platform SQLite or the inference runtime. */
final class NativeIndex {
 static {System.loadLibrary("pocketlore_index");}
 static native byte[] query(String path,String sql,String[] args,int maxRows,BooleanSupplier cancel)throws IOException;
 static native String identity();
 static JSONArray rows(String path,String sql,String[] args,int limit,BooleanSupplier cancel)throws Exception{return new JSONArray(new String(query(path,sql,args,limit,cancel),StandardCharsets.UTF_8));}
 private NativeIndex(){}
}
