package org.pocketlore.places;

import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.zip.InflaterInputStream;

/** Offline schema-v1 reader. Caller verifies sealed artifact SHA-256 before opening. */
public final class OfflinePlaces implements AutoCloseable {
    private final SQLiteDatabase db;
    public static final class Place {
        public byte[] id, entityKey;
        public String name, category, city, snapshotStatus;
        public double latitude, longitude, distanceKm;
    }
    public OfflinePlaces(String path) {
        db = SQLiteDatabase.openDatabase(path, null, SQLiteDatabase.OPEN_READONLY);
        try (Cursor c = db.rawQuery("SELECT value FROM progress WHERE key='schema_version'", null)) {
            if (!c.moveToFirst() || !"1".equals(c.getString(0))) {
                db.close(); throw new IllegalArgumentException("Unsupported places schema");
            }
        }
    }
    public static double distance(double lat, double lon, double a, double b) {
        double x = Math.sin(Math.toRadians(a-lat)/2), y = Math.sin(Math.toRadians(b-lon)/2);
        return 12742.0176 * Math.asin(Math.min(1, Math.sqrt(x*x + Math.cos(Math.toRadians(lat))*Math.cos(Math.toRadians(a))*y*y)));
    }
    /** Snapshot category membership only; no hours, dietary or live status inference. */
    public List<Place> nearby(double lat, double lon, double radius, String category, int limit) {
        if (!Double.isFinite(lat) || !Double.isFinite(lon) || !Double.isFinite(radius) || lat < -90 || lat > 90 || lon < -180 || lon > 180 || radius <= 0 || radius > 100 || limit < 1 || limit > 100)
            throw new IllegalArgumentException("Invalid bounded query");
        double dy = Math.toDegrees(radius/6371.0088);
        double dx = Math.abs(lat)+dy>=90 ? 180 : Math.toDegrees(Math.asin(Math.min(1,Math.sin(radius/6371.0088)/Math.cos(Math.toRadians(lat)))));
        ArrayList<double[]> spans = new ArrayList<>();
        spans.add(new double[]{Math.max(-180,lon-dx),Math.min(180,lon+dx)});
        if (lon-dx < -180) spans.add(new double[]{lon-dx+360,180});
        if (lon+dx > 180) spans.add(new double[]{-180,lon+dx-360});
        ArrayList<Place> result = new ArrayList<>();
        Comparator<Place> order = Comparator.comparingDouble((Place p)->p.distanceKm).thenComparing(p->hex(p.id));
        for (double[] span : spans) {
            String sql="SELECT id,name,lat,lon,category,city,status,entity_key FROM place p WHERE gy BETWEEN ? AND ? AND gx BETWEEN ? AND ?";
            ArrayList<String> args=new ArrayList<>();
            args.add(Long.toString((long)Math.floor((Math.max(-90,lat-dy)+90)*100)));
            args.add(Long.toString((long)Math.floor((Math.min(90,lat+dy)+90)*100)));
            args.add(Long.toString((long)Math.floor((span[0]+180)*100)));
            args.add(Long.toString((long)Math.floor((span[1]+180)*100)));
            if(category!=null){sql+=" AND EXISTS(SELECT 1 FROM category c WHERE c.place_id=p.id AND c.category=?)";args.add(category);}
            try(Cursor c=db.rawQuery(sql,args.toArray(new String[0]))) {
                while(c.moveToNext()) {
                    double d=distance(lat,lon,c.getDouble(2),c.getDouble(3)); if(d>radius)continue;
                    Place p=new Place();p.id=c.getBlob(0);p.name=c.getString(1);p.latitude=c.getDouble(2);p.longitude=c.getDouble(3);p.category=c.getString(4);p.city=c.getString(5);p.snapshotStatus=c.getString(6);p.entityKey=c.getBlob(7);p.distanceKm=d;
                    Place old=null;for(Place r:result)if(java.util.Arrays.equals(p.entityKey,r.entityKey)){old=r;break;}
                    if(old!=null){if(hex(old.id).compareTo(hex(p.id))<=0)continue;result.remove(old);}
                    result.add(p);result.sort(order);if(result.size()>limit)result.remove(result.size()-1);
                }
            }
        }
        return result;
    }
    /** Source JSON retains IDs, property-specific licenses, timestamps and source conflicts. */
    public byte[] sourceJson(byte[] id) throws IOException {
        if(id.length!=16)throw new IllegalArgumentException("UUID must contain 16 bytes");
        try(Cursor c=db.rawQuery("SELECT detail FROM place WHERE id=X'"+hex(id)+"'",null)) {
            if(!c.moveToFirst())return null;
            try(InflaterInputStream in=new InflaterInputStream(new ByteArrayInputStream(c.getBlob(0)));ByteArrayOutputStream out=new ByteArrayOutputStream()) {
                byte[] buffer=new byte[8192];int n;
                while((n=in.read(buffer))!=-1){if(out.size()+n>2097152)throw new IOException("Source exceeds bound");out.write(buffer,0,n);}
                return out.toByteArray();
            }
        }
    }
    /** Returns the stored JSON value for release, source hash or other provenance. */
    public String metadataJson(String key) {
        try(Cursor c=db.rawQuery("SELECT value FROM progress WHERE key=?",new String[]{key})) {
            return c.moveToFirst()?c.getString(0):null;
        }
    }
    /** Exact-group source siblings; bounded list, not a claim of resolved identity. */
    public List<byte[]> relatedIds(byte[] id) {
        if(id.length!=16)throw new IllegalArgumentException("UUID must contain 16 bytes");
        ArrayList<byte[]> result=new ArrayList<>();
        String sql="SELECT id FROM place WHERE entity_key=(SELECT entity_key FROM place WHERE id=X'"+hex(id)+"') ORDER BY id LIMIT 100";
        try(Cursor c=db.rawQuery(sql,null)){while(c.moveToNext())result.add(c.getBlob(0));}
        return result;
    }
    private static String hex(byte[] b){StringBuilder s=new StringBuilder();for(byte v:b)s.append(String.format(java.util.Locale.ROOT,"%02X",v&255));return s.toString();}
    public void close(){db.close();}
}
