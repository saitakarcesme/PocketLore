package org.pocketlore.app;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.*;

/** A small bundled, pinned catalog; no network or live operational information. */
public final class TravelCatalog {
    public static final String HASH="6cb245864d7b42facc8b987d7e4843f795b87912062d09a8bbddcdc034877924";
    public static final String WARNING="Offline dated snapshot. Opening hours are unavailable and any saved hours may be stale. Routing and walking times are unavailable. Current access, closures, accessibility and bookings are unverified. Check current official information before travel.";
    public static final class Poi {
        public final String id,name,description,date,revision,sourceHash,url,license,retrieved;
        public final double lat,lon;
        Poi(String[] v){id=v[0];name=v[1];description=v[2];lat=Double.parseDouble(v[3]);lon=Double.parseDouble(v[4]);date=v[5];revision=v[6];sourceHash=v[7];url=v[8];license=v[9];retrieved=v[10];}
        public String evidence(){return "["+id+"] "+name+"\n"+description+"\nCoordinates: "+lat+", "+lon+"\nSource revision: "+revision+"\nModified: "+date+"\nRetrieved: "+retrieved+"\n"+url+"\nWikidata contributors · "+license+"\nRaw source SHA-256: "+sourceHash+"\n\n"+WARNING;}
    }
    public final List<Poi> pois;
    public TravelCatalog(InputStream stream)throws Exception {
        ByteArrayOutputStream out=new ByteArrayOutputStream();byte[] buffer=new byte[4096];int n;
        while((n=stream.read(buffer))!=-1){out.write(buffer,0,n);if(out.size()>65536)throw new IOException("Travel pack too large");}
        byte[] raw=out.toByteArray();StringBuilder hex=new StringBuilder();for(byte b:MessageDigest.getInstance("SHA-256").digest(raw))hex.append(String.format(Locale.ROOT,"%02x",b&255));
        if(!HASH.equals(hex.toString()))throw new IOException("Travel pack hash mismatch");
        pois=Collections.unmodifiableList(parse(new String(raw,StandardCharsets.UTF_8)));
    }
    static List<Poi> parse(String text)throws Exception {
        List<Poi> rows=new ArrayList<>();Set<String> ids=new HashSet<>();
        for(String row:text.split("\n")){
            String[] v=row.split("\t",-1);if(v.length!=11)throw new IOException("Invalid travel row");
            for(String field:v)if(field.isEmpty())throw new IOException("Missing provenance");
            Poi p=new Poi(v);TravelTools.coordinate(p.lat,p.lon);
            if(!ids.add(p.id) || !p.id.matches("Q[0-9]+") || p.lat<38.87 || p.lat>38.90 || p.lon< -77.06 || p.lon> -77.02 || !p.license.equals("CC0-1.0"))throw new IOException("Invalid region or identity");
            rows.add(p);
        }
        if(rows.size()!=3)throw new IOException("Expected three bounded POIs");return rows;
    }
    public Poi get(String id){for(Poi p:pois)if(p.id.equals(id))return p;throw new IllegalArgumentException("Unknown place ID");}
    public List<Poi> search(String query){String q=query.trim().toLowerCase(Locale.ROOT);List<Poi> result=new ArrayList<>();for(Poi p:pois)if((p.name+" "+p.description).toLowerCase(Locale.ROOT).contains(q))result.add(p);return result;}
    public List<Poi> nearby(String origin,double radius,int limit){TravelTools.finite(radius);if(radius<0 || radius>10 || limit<1 || limit>2)throw new IllegalArgumentException("Radius must be 0–10 km and stops 1–2");Poi start=get(origin);List<Poi> list=new ArrayList<>();for(Poi p:pois)if(!p.id.equals(origin)&&distance(start,p)<=radius)list.add(p);list.sort(Comparator.comparingDouble((Poi p)->distance(start,p)).thenComparing(p->p.id));return new ArrayList<>(list.subList(0,Math.min(limit,list.size())));}
    public static double distance(Poi a,Poi b){return TravelTools.distanceKm(a.lat,a.lon,b.lat,b.lon);}
    public String plan(String origin,double radius,int limit){Poi start=get(origin);StringBuilder s=new StringBuilder("Distance-based candidate stops from "+start.name+" ["+start.id+"]. Not a route or timed itinerary.\n");List<Poi> list=nearby(origin,radius,limit);if(list.isEmpty())s.append("No other matching places in this bounded pack.\n");for(Poi p:list)s.append(String.format(Locale.ROOT,"\n%s [%s] — %.3f km straight-line from [%s]\n%s\n",p.name,p.id,distance(start,p),start.id,p.description));return s+"\nSpherical Earth estimate; ignores paths, barriers and elevation. Source buttons show dated coordinates and descriptions.\n"+WARNING;}
}
