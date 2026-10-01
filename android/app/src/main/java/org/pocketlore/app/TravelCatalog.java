package org.pocketlore.app;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.*;

/** A small bundled, pinned catalog; no network or live operational information. */
public final class TravelCatalog {
    public static final String HASH="2240dbd96698266eb27a3f892e346b2e2154c186c097f8ebf79d3f8ede086a8e";
    public static final String WARNING="Offline dated snapshot. Opening hours are unavailable and any saved hours may be stale. Routing and walking times are unavailable. Current access, closures, accessibility and bookings are unverified. Check current official information before travel.";
    public static final class Poi {
        public final String id,name,description,date,revision,sourceHash,url,license,retrieved,category,coordinateClaim,precision,coordinateCandidates;
        public final double lat,lon;
        Poi(String[] v){id=v[0];name=v[1];description=v[2];lat=Double.parseDouble(v[3]);lon=Double.parseDouble(v[4]);date=v[5];revision=v[6];sourceHash=v[7];url=v[8];license=v[9];retrieved=v[10];category=v[11];coordinateClaim=v[12];precision=v[13];coordinateCandidates=v[14];}
        public String evidence(){return "["+id+"] "+name+"\n"+description+"\nCoordinates: "+lat+", "+lon+"\nCoordinate statement: "+coordinateClaim+"\nSource precision (degrees): "+precision+"; non-deprecated coordinate statements: "+coordinateCandidates+"\nCategory: "+category+" (editorial grouping from source label/description; not an amenity guarantee)\nSource revision: "+revision+"\nModified: "+date+"\nRetrieved: "+retrieved+"\n"+url+"\nWikidata contributors · "+license+"\nRaw source SHA-256: "+sourceHash+"\n\n"+WARNING;}
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
            String[] v=row.split("\t",-1);if(v.length!=15)throw new IOException("Invalid travel row");
            for(String field:v)if(field.isEmpty())throw new IOException("Missing provenance");
            Poi p=new Poi(v);TravelTools.coordinate(p.lat,p.lon);
            if(!ids.add(p.id) || !p.id.matches("Q[0-9]+") || p.lat<38.87 || p.lat>38.91 || p.lon< -77.06 || p.lon> -77.0 || !p.license.equals("CC0-1.0"))throw new IOException("Invalid region or identity");
            if(!Arrays.asList("monument","museum","park-garden","civic").contains(p.category) || !p.coordinateClaim.startsWith(p.id+"$") || !p.sourceHash.matches("[0-9a-f]{64}"))throw new IOException("Invalid category or provenance");
            rows.add(p);
        }
        if(rows.size()!=25)throw new IOException("Expected 25 bounded POIs");return rows;
    }
    public Poi get(String id){for(Poi p:pois)if(p.id.equals(id))return p;throw new IllegalArgumentException("Unknown place ID");}
    private static String normalized(String s){return s.trim().toLowerCase(Locale.ROOT);}
    public List<Poi> search(String query){return filter("",query,"");}
    /** All constraints are ANDed; unknown categories yield no matches, never relaxed. */
    public List<Poi> filter(String category,String required,String avoided){
        String cat=normalized(category),yes=normalized(required),no=normalized(avoided);List<Poi> result=new ArrayList<>();
        for(Poi p:pois){String text=normalized(p.name+" "+p.description);
            if((cat.isEmpty()||p.category.equals(cat))&&text.contains(yes)&&(no.isEmpty()||!text.contains(no)))result.add(p);
        }return result;
    }
    public List<Poi> nearby(String origin,double radius,int limit){return nearby(origin,radius,limit,"","","");}
    public List<Poi> nearby(String origin,double radius,int limit,String category,String required,String avoided){
        TravelTools.finite(radius);if(radius<0||radius>10||limit<1||limit>5)throw new IllegalArgumentException("Radius must be 0–10 km and stops 1–5");
        Poi start=get(origin);List<Poi> list=new ArrayList<>();
        for(Poi p:filter(category,required,avoided))if(!p.id.equals(origin)&&distance(start,p)<=radius)list.add(p);
        list.sort(Comparator.comparingDouble((Poi p)->distance(start,p)).thenComparing(p->p.id));
        return new ArrayList<>(list.subList(0,Math.min(limit,list.size())));
    }
    public static double distance(Poi a,Poi b){return TravelTools.distanceKm(a.lat,a.lon,b.lat,b.lon);}
    public String plan(String origin,double radius,int limit){return plan(origin,radius,limit,"","","");}
    public String plan(String origin,double radius,int limit,String category,String required,String avoided){
        Poi start=get(origin);StringBuilder s=new StringBuilder("Distance-based candidate stops from "+start.name+" ["+start.id+"]. Not a route or timed itinerary.\n");
        s.append("Filters: category=").append(category.isEmpty()?"all":category).append("; require=").append(required).append("; avoid=").append(avoided).append(". All filters must match; none are relaxed.\n");
        List<Poi> list=nearby(origin,radius,limit,category,required,avoided);
        if(list.isEmpty())s.append("No matching candidates in this bounded pack. Conflicting or unavailable preferences are not relaxed.\n");
        for(Poi p:list)s.append(String.format(Locale.ROOT,"\n%s [%s] — %.3f km straight-line from [%s]\n%s\nMatched category: %s; selection uses the pinned label/description and coordinates.\n",p.name,p.id,distance(start,p),start.id,p.description,p.category));
        return s+"\nSpherical Earth estimate; ignores paths, barriers and elevation. Source buttons show dated coordinates and descriptions.\n"+WARNING;
    }
}
