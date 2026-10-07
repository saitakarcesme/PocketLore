package org.pocketlore.app;
import android.Manifest;import android.app.*;import android.content.pm.PackageManager;import android.location.*;import android.os.*;import android.widget.*;import java.util.*;import org.json.*;import org.pocketlore.places.*;
/** One foreground GPS request or explicit manual coordinates; no network provider or background tracking. */
final class NearbyTravel {
 final ScaleActivity a;EditText lat,lon;Spinner diet;LocationManager manager;LocationListener listener;final Handler timer=new Handler(android.os.Looper.getMainLooper());
 NearbyTravel(ScaleActivity activity,LinearLayout box){a=activity;
  lat=new EditText(a);ReaderUi.label(a,box,lat,"Latitude");lat.setHint("Latitude, −90 to 90");lat.setInputType(12290);box.addView(lat);lon=new EditText(a);ReaderUi.label(a,box,lon,"Longitude");lon.setHint("Longitude, −180 to 180");lon.setInputType(12290);box.addView(lon);
  diet=new Spinner(a);diet.setContentDescription("Diet evidence filter");diet.setAdapter(new ArrayAdapter<>(a,android.R.layout.simple_spinner_dropdown_item,new String[]{"Any diet · unknown allowed","Explicit saved vegan tag only","Explicit saved vegetarian tag only"}));box.addView(diet);
  ReaderUi.button(a,box,"Find nearby from coordinates",()->{try{search(Double.parseDouble(lat.getText().toString()),Double.parseDouble(lon.getText().toString()),null);}catch(Exception e){a.status.setText("Enter valid coordinates and radius. No location was inferred.");}});
  ReaderUi.button(a,box,"Use GPS once",this::gps);
 }
 static void coordinates(double lat,double lon,double radius){if(!Double.isFinite(lat)||!Double.isFinite(lon)||!Double.isFinite(radius)||lat< -90||lat>90||lon< -180||lon>180||radius<=0||radius>100)throw new IllegalArgumentException("Coordinates or radius out of bounds");}
 static String dietEvidence(JSONObject source,String key){JSONObject tags=source.optJSONObject("tags");Object value=tags==null?null:tags.opt("diet:"+key);return value instanceof String&&value.equals("yes")?"Explicit saved "+key+" tag: yes (not current verification)":"unknown";}
 void search(double latitude,double longitude,ScalePlaces.City city){stop();
  final double km=Double.parseDouble(a.radius.getText().toString());coordinates(latitude,longitude,km);final String category=a.category.getText().toString().trim();final int filter=diet.getSelectedItemPosition();
  a.runPlaces(budget->{budget.check();List<ScaleLibrary.Entry> editions=a.library.entries();budget.check();List<ScalePlaces.Hit> hits=new ArrayList<>();for(ScaleLibrary.Entry e:editions){budget.check();if(e.active&&e.kind().equals("places"))hits.addAll(ScalePlaces.nearby(e,latitude,longitude,km,category,budget));}budget.check();hits.sort(ScalePlaces.ORDER);budget.check();
   Set<String> seen=new HashSet<>();List<ScalePlaces.Hit> shown=new ArrayList<>();List<String> details=new ArrayList<>();
   for(ScalePlaces.Hit h:hits){budget.check();if(shown.size()==30)break;if(!seen.add(h.identity()))continue;String detail=ScalePlaces.detail(h,budget);String tag="unknown";
    try(org.pocketlore.places.CompactPlaces reader=new org.pocketlore.places.CompactPlaces(ScaleLibrary.resolve(h.edition.directory,h.shard).getPath(),budget)){JSONObject source=new JSONObject(reader.sourceJson(h.place));budget.check();if(filter>0)tag=dietEvidence(source,filter==1?"vegan":"vegetarian");}
    if(filter>0&&tag.equals("unknown"))continue;shown.add(h);details.add(detail+"\nRequested diet evidence: "+tag);}
   budget.check();List<TravelCatalog.Poi> guides=new ArrayList<>();try(java.io.InputStream in=a.getAssets().open("dc-monuments.tsv")){budget.check();TravelCatalog catalog=new TravelCatalog(in);budget.check();if(filter==0)for(TravelCatalog.Poi p:catalog.pois)if((category.isEmpty()||p.category.equals(category))&&TravelTools.distanceKm(latitude,longitude,p.lat,p.lon)<=km)guides.add(p);}catch(java.io.FileNotFoundException unavailable){/* No substitute guide is invented. */}
   budget.check();a.placesUi(budget,()->{a.results.removeAllViews();a.status.setText(shown.size()+" nearby candidates; "+guides.size()+" dated regional source descriptions. Current hours and unrecorded diet tags unknown. Straight-line distance; no routing. Separate source records are not verified unique venues.");if(city!=null)reviewed(city);
    for(int i=0;i<shown.size();i++){ScalePlaces.Hit h=shown.get(i);String detail=details.get(i);ReaderUi.entry(a,a.results,h.place.name,String.format(Locale.ROOT,"%s · %.3f km straight-line",h.place.category,h.place.distanceKm),()->a.runPlaces(inspect->{String current=ScalePlaces.detail(h,inspect);inspect.check();a.showPlaces(h.place.name,current,inspect);}));}
    for(TravelCatalog.Poi p:guides)ReaderUi.entry(a,a.results,p.name,"Dated regional source · "+p.date,()->ReaderUi.openSource(a,p.name,p.evidence(),"Saved regional description, not a route or current availability."));
   });
  });
 }
 void reviewed(ScalePlaces.City city){try{JSONObject payload=ReviewedCities.load(a);JSONObject card=ReviewedCities.match(payload,city);if(card==null)return;
  ReaderUi.button(a,a.results,"Reviewed city source: "+city.name,()->{try{ReaderUi.openSource(a,city.name+" · six reviewed fields",ReviewedCities.render(payload,card,-1),"Extractive saved metadata only; no generated answer or venue clearance.");}catch(Exception e){a.status.setText("Reviewed source unavailable; ordinary browsing remains available.");}});
  for(int i=0;i<6;i++){final int field=i;ReaderUi.button(a,a.results,"Inspect city field: "+ReviewedCities.FIELDS[i],()->{try{ReaderUi.openSource(a,"City field · "+ReviewedCities.FIELDS[field],ReviewedCities.render(payload,card,field),"Exact approved UTF-16 field slice, with attribution and offline license.");}catch(Exception e){a.status.setText("Reviewed field unavailable.");}});}
 }catch(Exception e){a.status.append(" Reviewed city card unavailable: verification failed. Ordinary place browsing is unchanged.");}}
 void gps(){stop();if(a.checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION)!=PackageManager.PERMISSION_GRANTED){a.requestPermissions(new String[]{Manifest.permission.ACCESS_FINE_LOCATION,Manifest.permission.ACCESS_COARSE_LOCATION},360);return;}
  manager=(LocationManager)a.getSystemService(android.content.Context.LOCATION_SERVICE);if(!manager.isProviderEnabled(LocationManager.GPS_PROVIDER)){a.status.setText("GPS unavailable. Enter coordinates or choose a city manually.");return;}
  listener=new LocationListener(){public void onLocationChanged(Location l){if(listener!=this)return;long age=(SystemClock.elapsedRealtimeNanos()-l.getElapsedRealtimeNanos())/1000000000L;stop();if(age<0||age>120){a.status.setText("GPS fix is stale. Enter coordinates manually or request a fresh fix.");return;}lat.setText(Double.toString(l.getLatitude()));lon.setText(Double.toString(l.getLongitude()));a.status.setText("GPS fix age "+age+" seconds; accuracy "+(l.hasAccuracy()?l.getAccuracy()+" m":"unknown")+". Review coordinates, then Find nearby.");}};
  try{manager.requestLocationUpdates(LocationManager.GPS_PROVIDER,1000,0,listener);a.status.setText("Waiting up to 30 seconds for offline GPS. Manual coordinates remain available.");timer.postDelayed(()->{stop();a.status.setText("No GPS fix received. Enter coordinates or choose a city manually.");},30000);}catch(SecurityException e){stop();a.status.setText("Location permission unavailable. Use manual coordinates.");}
 }
 void stop(){a.cancelPlaces();timer.removeCallbacksAndMessages(null);if(manager!=null&&listener!=null)manager.removeUpdates(listener);listener=null;}
}
