package org.pocketlore.places;

import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import org.json.JSONArray;
import org.json.JSONObject;
import org.json.JSONException;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.*;
import java.util.zip.InflaterInputStream;

/** Schema-v2 lossless source blocks; caller verifies the sealed database hash. */
public final class CompactPlaces implements AutoCloseable {
    private static final int MAX_BLOCK=32*1024*1024;
    private final SQLiteDatabase db;
    private final PlacesBudget budget;
    private boolean closed;private final boolean ownsBudget;
    private void check() throws IOException { if(closed)throw new IOException("Places reader is closed");budget.check(); }
    public static final class Place {
        public String id,name,category,city,country,snapshotStatus;
        public double latitude,longitude,distanceKm;
        public long blockId,sourceOrdinal;
        public String sourceIdentity(){return PlacesBudget.identity(id,sourceOrdinal);}
    }
    public CompactPlaces(String path){this(path,new PlacesBudget(()->false),true);}
    public CompactPlaces(String path,java.util.function.BooleanSupplier cancel){this(path,new PlacesBudget(cancel),true);}
    public CompactPlaces(String path,PlacesBudget budget){this(path,budget,false);}
    private CompactPlaces(String path,PlacesBudget budget,boolean owns){
        this.budget=Objects.requireNonNull(budget);ownsBudget=owns;SQLiteDatabase opened=null;
        try{budget.check();opened=SQLiteDatabase.openDatabase(path,null,SQLiteDatabase.OPEN_READONLY);db=opened;budget.check();
            try(PlacesQuery q=new PlacesQuery(db,"PRAGMA cache_size=-4096",null,budget)){q.next();}
            try(PlacesQuery q=new PlacesQuery(db,"PRAGMA mmap_size=0",null,budget)){q.next();}
            try(PlacesQuery q=new PlacesQuery(db,"SELECT value FROM metadata WHERE key='schema_version'",null,budget)){if(!q.next()||!"2".equals(q.cursor.getString(0)))throw new IllegalArgumentException("Unsupported compact schema");}
            budget.check();
        }catch(IOException|RuntimeException|Error e){if(opened!=null)try{opened.close();}catch(Throwable close){e.addSuppressed(close);}if(owns)try{budget.close();}catch(Throwable close){e.addSuppressed(close);}if(e instanceof IOException)throw new IllegalStateException(e);if(e instanceof RuntimeException)throw (RuntimeException)e;throw (Error)e;}
    }
    private static String string(JSONObject o,String key){Object v=o==null?null:o.opt(key);return v instanceof String?(String)v:null;}
    private static List<String> strings(JSONArray a){List<String> out=new ArrayList<>();if(a!=null)for(int i=0;i<a.length();i++)out.add(a.optString(i,null));return out;}
    private JSONArray block(long id) throws IOException,JSONException {
        check();byte[] packed;String expected;
        try(PlacesQuery q=new PlacesQuery(db,"SELECT length(payload),payload,sha256 FROM block WHERE id=?",new String[]{Long.toString(id)},budget)) {
            Cursor c=q.cursor;if(!q.next())throw new IOException("Missing source block");if(c.getLong(0)>1024*1024)throw new IOException("Compressed source block exceeds bound");packed=c.getBlob(1);expected=c.getString(2);
        }
        byte[] raw;
        try(InflaterInputStream in=new InflaterInputStream(new ByteArrayInputStream(packed));ByteArrayOutputStream out=new ByteArrayOutputStream()) {
            byte[] buffer=new byte[8192];int n;
            while((n=in.read(buffer))!=-1){check();if(out.size()+n>MAX_BLOCK)throw new IOException("Source block exceeds admission bound");out.write(buffer,0,n);}
            check();raw=out.toByteArray();check();
        }
        if(!budget.hash(raw).equals(expected))throw new IOException("Source block hash mismatch");check();
        JSONArray decoded=new JSONArray(new String(raw,StandardCharsets.UTF_8));check();return decoded;
    }
    /** Bounded radius/category query; no inferred diet, opening hours or live status. */
    public List<Place> nearby(double lat,double lon,double radius,String category,int limit) throws IOException,JSONException {
        check();
        PlacesGeometry.validate(lat,lon,radius,limit);if(category!=null&&category.isEmpty())category=null;
        double dy=PlacesGeometry.latitudeDelta(radius);List<double[]> spans=PlacesGeometry.spans(lat,lon,radius);
        ArrayList<Place> result=new ArrayList<>();Set<Long> visited=new HashSet<>();Comparator<Place> order=Comparator.comparingDouble((Place p)->p.distanceKm).thenComparing(p->p.id).thenComparingLong(p->p.sourceOrdinal);
        for(double[] span:spans) {
            String sql="SELECT DISTINCT g.block FROM grid g WHERE g.gy BETWEEN ? AND ? AND g.gx BETWEEN ? AND ?";
            ArrayList<String> args=new ArrayList<>();args.add(Long.toString((long)Math.floor((Math.max(-90,lat-dy)+90)*10)));args.add(Long.toString((long)Math.floor((Math.min(90,lat+dy)+90)*10)));args.add(Long.toString((long)Math.floor((span[0]+180)*10)));args.add(Long.toString((long)Math.floor((span[1]+180)*10)));
            if(category!=null){sql+=" AND EXISTS(SELECT 1 FROM category c WHERE c.category=? AND c.block=g.block)";args.add(category);}
            try(PlacesQuery q=new PlacesQuery(db,sql,args.toArray(new String[0]),budget)) {
                Cursor cursor=q.cursor;while(q.next()) {
                    check();long blockId=cursor.getLong(0);if(visited.contains(blockId))continue;if(visited.size()>=2048)throw new IOException("Places query block budget exceeded; narrow the radius");visited.add(blockId);JSONArray rows=block(blockId);
                    for(int i=0;i<rows.length();i++) {
                        check();JSONArray row=rows.getJSONArray(i);double a=row.getDouble(1),b=row.getDouble(2);JSONObject r=row.getJSONObject(4),tax=r.optJSONObject("taxonomy");
                        String basic=string(r,"basic_category"),primary=PlacesGeometry.primary(string(tax,"primary"),basic);
                        if(!PlacesGeometry.category(category,primary,basic,strings(tax==null?null:tax.optJSONArray("hierarchy")),strings(tax==null?null:tax.optJSONArray("alternates"))))continue;
                        double distance=PlacesGeometry.distance(lat,lon,a,b);if(!PlacesGeometry.within(distance,radius))continue;
                        Place p=new Place();p.id=r.getString("id");p.name=r.getJSONObject("names").getString("primary");p.latitude=a;p.longitude=b;p.category=primary;p.snapshotStatus=string(r,"operating_status");p.distanceKm=distance;p.blockId=blockId;p.sourceOrdinal=row.getLong(0);
                        JSONArray addresses=r.optJSONArray("addresses");JSONObject address=addresses==null?null:addresses.optJSONObject(0);p.city=string(address,"locality");p.country=string(address,"country");
                        // Only identical source records are equivalent, never display fields.
                        boolean duplicate=false;for(Place old:result)if(old.sourceIdentity().equals(p.sourceIdentity())){if(old.blockId!=p.blockId)throw new IOException("Conflicting source block pointers");duplicate=true;break;}
                        if(duplicate)continue;
                        check();result.add(p);result.sort(order);check();if(result.size()>limit)result.remove(result.size()-1);
                    }
                }
            }
        }
        check();return result;
    }
    public String sourceJson(Place place) throws IOException,JSONException {
        check();JSONArray rows=block(place.blockId);
        for(int i=0;i<rows.length();i++){check();JSONArray row=rows.getJSONArray(i);JSONObject r=row.getJSONObject(4);if(row.getLong(0)==place.sourceOrdinal&&place.id.equals(r.getString("id"))){String source=r.toString();check();return source;}}
        throw new IOException("Source identity does not match block pointer");
    }
    public String metadataJson(String key)throws IOException{check();try(PlacesQuery q=new PlacesQuery(db,"SELECT value FROM metadata WHERE key=?",new String[]{key},budget)){String value=q.next()?q.cursor.getString(0):null;check();return value;}}
    public void close(){if(closed)return;closed=true;try{db.close();}catch(RuntimeException|Error e){if(ownsBudget)try{budget.close();}catch(Throwable close){e.addSuppressed(close);}throw e;}if(ownsBudget)budget.close();}
}
