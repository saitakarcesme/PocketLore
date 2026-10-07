package org.pocketlore.app;
import android.database.Cursor;import android.database.sqlite.SQLiteDatabase;import java.util.*;import java.util.function.BooleanSupplier;import java.text.Normalizer;import org.pocketlore.places.*;
/** City lookup and source-specific deterministic merge; city coordinates are not boundaries. */
final class ScalePlaces {
 static final class City {String id,name,country,date,raw;double lat,lon;}
 static final class Hit {ScaleLibrary.Entry edition;String shard;CompactPlaces.Place place;String identity(){return PlacesBudget.identity(edition.id,shard,place.id,place.sourceOrdinal);}}
 static final Comparator<Hit> ORDER=(a,b)->PlacesBudget.compare(a.place.distanceKm,a.edition.id,a.shard,a.place.id,a.place.sourceOrdinal,b.place.distanceKm,b.edition.id,b.shard,b.place.id,b.place.sourceOrdinal);
 static List<City> cities(ScaleLibrary.Entry e,String name,BooleanSupplier cancel)throws Exception{try(PlacesBudget budget=new PlacesBudget(cancel)){return cities(e,name,budget);}}
 static List<City> cities(ScaleLibrary.Entry e,String name,PlacesBudget budget)throws Exception{
  budget.check();ScaleLibrary.check(name.length()<=200,"City query bound");String key=Normalizer.normalize(name,Normalizer.Form.NFKC).toLowerCase(Locale.ROOT).trim().replaceAll("\\s+"," ");budget.check();List<City> out=new ArrayList<>();
  try(SQLiteDatabase db=SQLiteDatabase.openDatabase(ScaleLibrary.resolve(e.directory,e.manifest.getString("cities")).getPath(),null,SQLiteDatabase.OPEN_READONLY)){
   budget.check();try(PlacesQuery q=new PlacesQuery(db,"SELECT c.id,c.name,c.country,c.lat,c.lon,c.modified,c.raw FROM city c JOIN alias a ON a.city_id=c.id WHERE a.name_key=? ORDER BY c.population DESC,c.id LIMIT 20",new String[]{key},budget)){
    Cursor c=q.cursor;while(q.next()){City city=new City();city.id=c.getString(0);city.name=c.getString(1);city.country=c.getString(2);city.lat=c.getDouble(3);city.lon=c.getDouble(4);city.date=c.getString(5);city.raw=c.getString(6);out.add(city);budget.check();}
   }
  }budget.check();return out;
 }
 static List<Hit> nearby(ScaleLibrary.Entry e,double lat,double lon,double radius,String category,BooleanSupplier cancel)throws Exception{try(PlacesBudget budget=new PlacesBudget(cancel)){return nearby(e,lat,lon,radius,category,budget);}}
 static List<Hit> nearby(ScaleLibrary.Entry e,double lat,double lon,double radius,String category,PlacesBudget budget)throws Exception{
  budget.check();List<Hit> out=new ArrayList<>();for(int i=0;i<e.manifest.getJSONArray("shards").length();i++){budget.check();String shard=e.manifest.getJSONArray("shards").getString(i);try(CompactPlaces reader=new CompactPlaces(ScaleLibrary.resolve(e.directory,shard).getPath(),budget)){for(CompactPlaces.Place p:reader.nearby(lat,lon,radius,category,30)){budget.check();Hit h=new Hit();h.edition=e;h.shard=shard;h.place=p;out.add(h);}}}budget.check();out.sort(ORDER);budget.check();return new ArrayList<>(out.subList(0,Math.min(30,out.size())));
 }
 static String detail(Hit h,BooleanSupplier cancel)throws Exception{try(PlacesBudget budget=new PlacesBudget(cancel)){return detail(h,budget);}}
 static String detail(Hit h,PlacesBudget budget)throws Exception{
  budget.check();try(CompactPlaces r=new CompactPlaces(ScaleLibrary.resolve(h.edition.directory,h.shard).getPath(),budget)){String detail=h.place.name+"\n"+h.place.category+"\nStraight-line distance: "+String.format(Locale.ROOT,"%.3f km",h.place.distanceKm)+"\nCurrent hours and diet suitability: unknown. Routing unavailable.\nSnapshot status is not live availability.\nEdition/source identity: "+h.identity()+"\nSource release: "+r.metadataJson("release")+"\nSource provenance and attribution (unaltered retained fields):\n"+r.sourceJson(h.place)+"\nGeoNames city lookup: CC BY 4.0; city proximity is not municipal containment.\nSource-specific terms are retained in collection notices; no generated answer clearance.";budget.check();return detail;}
 }
}
