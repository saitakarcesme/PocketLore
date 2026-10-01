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

/** Offline compact OSM reader. Caller verifies the sealed file hash before opening. */
public final class OsmPlaces implements AutoCloseable {
    private final SQLiteDatabase db;
    private static final int MAX_BLOCK=32*1024*1024;
    public static final class Place {
        public String type,name,hours,vegan,vegetarian;
        public long id;
        public double latitude,longitude,distanceKm;
    }
    public OsmPlaces(String path) {
        db=SQLiteDatabase.openDatabase(path,null,SQLiteDatabase.OPEN_READONLY);
        try(Cursor c=db.rawQuery("SELECT value FROM metadata WHERE key='schema_version'",null)) {
            if(!c.moveToFirst()||!"2".equals(c.getString(0))){db.close();throw new IllegalArgumentException("Unsupported OSM schema");}
        }
    }
    private static String value(JSONObject o,String key){Object v=o.opt(key);return v instanceof String?(String)v:null;}
    private JSONArray block(long id) throws IOException,JSONException {
        byte[] packed;String expected;
        try(Cursor c=db.rawQuery("SELECT length(payload),payload,sha256 FROM block WHERE id=?",new String[]{Long.toString(id)})) {
            if(!c.moveToFirst())throw new IOException("Missing source block");if(c.getLong(0)>1024*1024)throw new IOException("Compressed source block exceeds bound");packed=c.getBlob(1);expected=c.getString(2);
        }
        byte[] raw;
        try(InflaterInputStream in=new InflaterInputStream(new ByteArrayInputStream(packed));ByteArrayOutputStream out=new ByteArrayOutputStream()) {
            byte[] buffer=new byte[8192];int n;
            while((n=in.read(buffer))!=-1){if(out.size()+n>MAX_BLOCK)throw new IOException("Source block exceeds bound");out.write(buffer,0,n);}raw=out.toByteArray();
        }
        try {
            StringBuilder hex=new StringBuilder();for(byte b:MessageDigest.getInstance("SHA-256").digest(raw))hex.append(String.format(Locale.ROOT,"%02x",b&255));
            if(!expected.equals(hex.toString()))throw new IOException("Source block hash mismatch");
        } catch(NoSuchAlgorithmException e){throw new IOException(e);}
        return new JSONArray(new String(raw,StandardCharsets.UTF_8));
    }
    /** Return the retained source object, coordinates, and dated snapshot attribution. */
    public JSONObject source(String type,long id) throws IOException,JSONException {
        long block;int slot;Double lat,lon;
        try(Cursor c=db.rawQuery("SELECT block,slot,lat,lon FROM osm WHERE type=? AND id=?",new String[]{type,Long.toString(id)})) {
            if(!c.moveToFirst())throw new IOException("Unknown source identity");block=c.getLong(0);slot=c.getInt(1);lat=c.isNull(2)?null:c.getDouble(2);lon=c.isNull(3)?null:c.getDouble(3);
        }
        JSONArray row=block(block).getJSONArray(slot);JSONObject raw=row.getJSONObject(2);
        if(!type.equals(raw.getString("type"))||id!=raw.getLong("id"))throw new IOException("Source pointer identity mismatch");
        if((lat==null)!=row.isNull(0)||(lon==null)!=row.isNull(1)||(lat!=null&&lat.doubleValue()!=row.getDouble(0))||(lon!=null&&lon.doubleValue()!=row.getDouble(1)))throw new IOException("Coordinate pointer mismatch");
        JSONObject result=new JSONObject();result.put("record",raw);result.put("latitude",lat==null?JSONObject.NULL:lat);result.put("longitude",lon==null?JSONObject.NULL:lon);result.put("live_status",JSONObject.NULL);
        try(Cursor c=db.rawQuery("SELECT sha256,url,retrieved,base_timestamp,copyright FROM snapshot",null)) {
            if(!c.moveToFirst())throw new IOException("Missing snapshot provenance");JSONObject snapshot=new JSONObject();String[] keys={"sha256","url","retrieved","base_timestamp","copyright"};for(int i=0;i<keys.length;i++)snapshot.put(keys[i],c.isNull(i)?JSONObject.NULL:c.getString(i));result.put("snapshot",snapshot);
        }
        return result;
    }
    /** Explicit yes/only tags only. Hours are literal source text, never evaluated as live status. */
    public List<Place> nearby(double lat,double lon,double radius,String diet,int limit) throws IOException,JSONException {
        if(!Double.isFinite(lat)||!Double.isFinite(lon)||!Double.isFinite(radius)||lat< -90||lat>90||lon< -180||lon>180||radius<=0||radius>100||limit<1||limit>100)throw new IllegalArgumentException("Invalid bounded query");
        if(diet!=null&&!diet.equals("vegan")&&!diet.equals("vegetarian"))throw new IllegalArgumentException("Unsupported diet");
        String sql="SELECT type,id,lat,lon FROM osm WHERE lat BETWEEN ? AND ?";if(diet!=null)sql+=" AND "+diet+" IN ('yes','only')";
        ArrayList<Place> result=new ArrayList<>();Comparator<Place> order=Comparator.comparingDouble((Place p)->p.distanceKm).thenComparing(p->p.type).thenComparingLong(p->p.id);
        try(Cursor c=db.rawQuery(sql,new String[]{Double.toString(lat-radius/110),Double.toString(lat+radius/110)})) {
            while(c.moveToNext()) {
                if(c.isNull(2)||c.isNull(3))continue;double a=c.getDouble(2),b=c.getDouble(3),distance=OfflinePlaces.distance(lat,lon,a,b);if(distance>radius)continue;
                Place p=new Place();p.type=c.getString(0);p.id=c.getLong(1);p.latitude=a;p.longitude=b;p.distanceKm=distance;result.add(p);result.sort(order);if(result.size()>limit)result.remove(result.size()-1);
            }
        }
        for(Place p:result){JSONObject tags=source(p.type,p.id).getJSONObject("record").getJSONObject("tags");p.name=value(tags,"name");p.hours=value(tags,"opening_hours");p.vegan=value(tags,"diet:vegan");p.vegetarian=value(tags,"diet:vegetarian");}
        return result;
    }
    public void close(){db.close();}
}
