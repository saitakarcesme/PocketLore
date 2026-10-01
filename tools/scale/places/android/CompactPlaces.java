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
    public static final class Place {
        public String id,name,category,city,country,snapshotStatus;
        public double latitude,longitude,distanceKm;
        public long blockId,sourceOrdinal;
        private String entity;
    }
    public CompactPlaces(String path) {
        db=SQLiteDatabase.openDatabase(path,null,SQLiteDatabase.OPEN_READONLY);
        try(Cursor c=db.rawQuery("SELECT value FROM metadata WHERE key='schema_version'",null)) {
            if(!c.moveToFirst()||!"2".equals(c.getString(0))){db.close();throw new IllegalArgumentException("Unsupported compact schema");}
        }
    }
    private static String string(JSONObject o,String key){Object v=o==null?null:o.opt(key);return v instanceof String?(String)v:null;}
    private static boolean contains(JSONArray a,String value){if(a!=null)for(int i=0;i<a.length();i++)if(value.equals(a.optString(i,null)))return true;return false;}
    private JSONArray block(long id) throws IOException,JSONException {
        byte[] packed;String expected;
        try(Cursor c=db.rawQuery("SELECT length(payload),payload,sha256 FROM block WHERE id=?",new String[]{Long.toString(id)})) {
            if(!c.moveToFirst())throw new IOException("Missing source block");if(c.getLong(0)>1024*1024)throw new IOException("Compressed source block exceeds bound");packed=c.getBlob(1);expected=c.getString(2);
        }
        byte[] raw;
        try(InflaterInputStream in=new InflaterInputStream(new ByteArrayInputStream(packed));ByteArrayOutputStream out=new ByteArrayOutputStream()) {
            byte[] buffer=new byte[8192];int n;
            while((n=in.read(buffer))!=-1){if(out.size()+n>MAX_BLOCK)throw new IOException("Source block exceeds admission bound");out.write(buffer,0,n);}
            raw=out.toByteArray();
        }
        try {
            StringBuilder hex=new StringBuilder();for(byte b:MessageDigest.getInstance("SHA-256").digest(raw))hex.append(String.format(Locale.ROOT,"%02x",b&255));
            if(!hex.toString().equals(expected))throw new IOException("Source block hash mismatch");
        } catch(NoSuchAlgorithmException e){throw new IOException(e);}
        return new JSONArray(new String(raw,StandardCharsets.UTF_8));
    }
    /** Bounded radius/category query; no inferred diet, opening hours or live status. */
    public List<Place> nearby(double lat,double lon,double radius,String category,int limit) throws IOException,JSONException {
        if(!Double.isFinite(lat)||!Double.isFinite(lon)||!Double.isFinite(radius)||lat< -90||lat>90||lon< -180||lon>180||radius<=0||radius>100||limit<1||limit>100)throw new IllegalArgumentException("Invalid bounded query");
        if(category!=null&&category.isEmpty())category=null;
        double dy=Math.toDegrees(radius/6371.0088),dx=Math.abs(lat)+dy>=90?180:Math.toDegrees(Math.asin(Math.min(1,Math.sin(radius/6371.0088)/Math.cos(Math.toRadians(lat)))));
        ArrayList<double[]> spans=new ArrayList<>();spans.add(new double[]{Math.max(-180,lon-dx),Math.min(180,lon+dx)});
        if(lon-dx< -180)spans.add(new double[]{lon-dx+360,180});if(lon+dx>180)spans.add(new double[]{-180,lon+dx-360});
        ArrayList<Place> result=new ArrayList<>();Set<Long> visited=new HashSet<>();Comparator<Place> order=Comparator.comparingDouble((Place p)->p.distanceKm).thenComparing(p->p.id);
        for(double[] span:spans) {
            String sql="SELECT DISTINCT g.block FROM grid g WHERE g.gy BETWEEN ? AND ? AND g.gx BETWEEN ? AND ?";
            ArrayList<String> args=new ArrayList<>();args.add(Long.toString((long)Math.floor((Math.max(-90,lat-dy)+90)*10)));args.add(Long.toString((long)Math.floor((Math.min(90,lat+dy)+90)*10)));args.add(Long.toString((long)Math.floor((span[0]+180)*10)));args.add(Long.toString((long)Math.floor((span[1]+180)*10)));
            if(category!=null){sql+=" AND EXISTS(SELECT 1 FROM category c WHERE c.category=? AND c.block=g.block)";args.add(category);}
            try(Cursor cursor=db.rawQuery(sql,args.toArray(new String[0]))) {
                while(cursor.moveToNext()) {
                    long blockId=cursor.getLong(0);if(!visited.add(blockId))continue;JSONArray rows=block(blockId);
                    for(int i=0;i<rows.length();i++) {
                        JSONArray row=rows.getJSONArray(i);double a=row.getDouble(1),b=row.getDouble(2);JSONObject r=row.getJSONObject(4),tax=r.optJSONObject("taxonomy");
                        String primary=string(tax,"primary"),basic=string(r,"basic_category");if(primary==null||primary.isEmpty())primary=basic;
                        if(category!=null&&!category.equals(primary)&&!category.equals(basic)&&!contains(tax==null?null:tax.optJSONArray("hierarchy"),category)&&!contains(tax==null?null:tax.optJSONArray("alternates"),category))continue;
                        double distance=OfflinePlaces.distance(lat,lon,a,b);if(distance>radius)continue;
                        Place p=new Place();p.id=r.getString("id");p.name=r.getJSONObject("names").getString("primary");p.latitude=a;p.longitude=b;p.category=primary;p.snapshotStatus=string(r,"operating_status");p.distanceKm=distance;p.blockId=blockId;p.sourceOrdinal=row.getLong(0);
                        JSONArray addresses=r.optJSONArray("addresses");JSONObject address=addresses==null?null:addresses.optJSONObject(0);p.city=string(address,"locality");p.country=string(address,"country");
                        String nameKey=row.getString(3);p.entity=nameKey.length()+":"+nameKey+":"+Long.toHexString(Double.doubleToRawLongBits(a))+":"+Long.toHexString(Double.doubleToRawLongBits(b))+":"+(primary==null?-1:primary.length())+":"+primary;
                        Place previous=null;for(Place old:result)if(old.entity.equals(p.entity)){previous=old;break;}
                        if(previous!=null){if(previous.id.compareTo(p.id)<=0)continue;result.remove(previous);}
                        result.add(p);result.sort(order);if(result.size()>limit)result.remove(result.size()-1);
                    }
                }
            }
        }
        return result;
    }
    public String sourceJson(Place place) throws IOException,JSONException {
        JSONArray rows=block(place.blockId);
        for(int i=0;i<rows.length();i++){JSONArray row=rows.getJSONArray(i);JSONObject r=row.getJSONObject(4);if(row.getLong(0)==place.sourceOrdinal&&place.id.equals(r.getString("id")))return r.toString();}
        throw new IOException("Source identity does not match block pointer");
    }
    public String metadataJson(String key){try(Cursor c=db.rawQuery("SELECT value FROM metadata WHERE key=?",new String[]{key})){return c.moveToFirst()?c.getString(0):null;}}
    public void close(){db.close();}
}
