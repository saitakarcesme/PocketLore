package org.pocketlore.places;
import java.util.*;
/** Existing spherical geometry and literal category semantics, independent of Android. */
public final class PlacesGeometry {
 private PlacesGeometry(){}
 public static void validate(double lat,double lon,double radius,int limit){if(!Double.isFinite(lat)||!Double.isFinite(lon)||!Double.isFinite(radius)||lat< -90||lat>90||lon< -180||lon>180||radius<=0||radius>100||limit<1||limit>100)throw new IllegalArgumentException("Invalid bounded query");}
 public static double latitudeDelta(double radius){return Math.toDegrees(radius/6371.0088);}
 public static List<double[]> spans(double lat,double lon,double radius){validate(lat,lon,radius,1);double dy=latitudeDelta(radius),dx=Math.abs(lat)+dy>=90?180:Math.toDegrees(Math.asin(Math.min(1,Math.sin(radius/6371.0088)/Math.cos(Math.toRadians(lat)))));ArrayList<double[]> out=new ArrayList<>();out.add(new double[]{Math.max(-180,lon-dx),Math.min(180,lon+dx)});if(lon-dx< -180)out.add(new double[]{lon-dx+360,180});if(lon+dx>180)out.add(new double[]{-180,lon+dx-360});return out;}
 public static double distance(double lat,double lon,double a,double b){double x=Math.sin(Math.toRadians(a-lat)/2),y=Math.sin(Math.toRadians(b-lon)/2);return 12742.0176*Math.asin(Math.min(1,Math.sqrt(x*x+Math.cos(Math.toRadians(lat))*Math.cos(Math.toRadians(a))*y*y)));}
 public static boolean within(double distance,double radius){return distance<=radius;}
 public static String primary(String primary,String basic){return primary==null||primary.isEmpty()?basic:primary;}
 public static boolean category(String requested,String primary,String basic,List<String> hierarchy,List<String> alternates){return requested==null||requested.isEmpty()||requested.equals(primary)||requested.equals(basic)||hierarchy.contains(requested)||alternates.contains(requested);}
}
