package org.pocketlore.app;

import java.time.LocalDate;
import java.time.temporal.ChronoUnit;

/** Deterministic tools. Distances use a spherical Earth, not a road graph. */
public final class TravelTools {
    public static void finite(double n) { if(!Double.isFinite(n))throw new IllegalArgumentException("Enter a finite number"); }
    public static double convert(double n,String from,String to) {
        finite(n);
        String[] length={"m","km","mi"};double[] scale={1,1000,1609.344};
        int a=-1,b=-1;for(int i=0;i<length.length;i++){if(length[i].equals(from))a=i;if(length[i].equals(to))b=i;}
        double result;
        if(a>=0 && b>=0) result=n*scale[a]/scale[b];
        else if(from.equals("C") && to.equals("F"))result=n*9/5+32;
        else if(from.equals("F") && to.equals("C"))result=(n-32)*5/9;
        else if((from.equals("C") || from.equals("F")) && from.equals(to))result=n;
        else throw new IllegalArgumentException("Supported units: m, km, mi or C, F; dimensions must match");
        finite(result);return result;
    }
    public static String addDays(String date,long days) {return LocalDate.parse(date).plusDays(days).toString();}
    public static long daysBetween(String first,String last) {return ChronoUnit.DAYS.between(LocalDate.parse(first),LocalDate.parse(last));}
    static void coordinate(double lat,double lon){finite(lat);finite(lon);if(Math.abs(lat)>90 || Math.abs(lon)>180)throw new IllegalArgumentException("Coordinates outside Earth bounds");}
    public static double distanceKm(double lat1,double lon1,double lat2,double lon2) {
        coordinate(lat1,lon1);coordinate(lat2,lon2);
        double a=Math.pow(Math.sin(Math.toRadians(lat2-lat1)/2),2)+Math.cos(Math.toRadians(lat1))*Math.cos(Math.toRadians(lat2))*Math.pow(Math.sin(Math.toRadians(lon2-lon1)/2),2);
        return 6371.0088*2*Math.asin(Math.sqrt(Math.max(0,Math.min(1,a))));
    }
    private TravelTools() {}
}
