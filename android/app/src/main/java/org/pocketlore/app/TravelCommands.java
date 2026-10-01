package org.pocketlore.app;

import java.util.Locale;

/** Explicit tool syntax keeps numeric operations separate from model generation. */
public final class TravelCommands {
    public static String run(String input,TravelCatalog catalog) {
        String[] v=input.trim().split("\\s+");
        if(v.length==4 && v[0].equals("convert"))return String.format(Locale.ROOT,"%.6f %s (deterministic conversion)",TravelTools.convert(Double.parseDouble(v[1]),v[2],v[3]),v[3]);
        if(v.length==3 && v[0].equals("add-days"))return TravelTools.addDays(v[1],Long.parseLong(v[2]))+" (calendar date; no timezone or opening-hours inference)";
        if(v.length==3 && v[0].equals("days-between"))return TravelTools.daysBetween(v[1],v[2])+" calendar days (end minus start; not elapsed flight time)";
        if(v.length==3 && v[0].equals("distance")){TravelCatalog.Poi a=catalog.get(v[1]),b=catalog.get(v[2]);return String.format(Locale.ROOT,"%.3f km straight-line [%s] to [%s]. Spherical Earth; routing and walking times unavailable.",TravelCatalog.distance(a,b),a.id,b.id);}
        throw new IllegalArgumentException("Use convert VALUE UNIT UNIT; add-days YYYY-MM-DD DAYS; days-between DATE DATE; or distance POI-ID POI-ID");
    }
    private TravelCommands() {}
}
