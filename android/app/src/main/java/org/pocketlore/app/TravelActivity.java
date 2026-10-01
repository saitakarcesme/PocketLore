package org.pocketlore.app;

import android.app.*;
import android.os.Bundle;
import android.widget.*;
import java.io.InputStream;

/** Offline POIs and deterministic tools, independent of local model availability. */
public final class TravelActivity extends Activity {
    TravelCatalog catalog;
    EditText query,avoid,radius,command;
    Button search,plan,calculate;
    Spinner origin,category;
    TextView output;
    LinearLayout sources;
    String inspectedId="";
    @Override public void onCreate(Bundle saved){super.onCreate(saved);
        ScrollView scroll=new ScrollView(this);LinearLayout box=new LinearLayout(this);box.setOrientation(1);box.setPadding(24,24,24,24);scroll.addView(box);setContentView(scroll);
        getWindow().getDecorView().setSystemUiVisibility(android.view.View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR | android.view.View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR);
        scroll.setOnApplyWindowInsetsListener((view,insets)->{
            if(android.os.Build.VERSION.SDK_INT>=30){android.graphics.Insets bars=insets.getInsets(android.view.WindowInsets.Type.systemBars());view.setPadding(bars.left,bars.top,bars.right,bars.bottom);}
            else view.setPadding(insets.getSystemWindowInsetLeft(),insets.getSystemWindowInsetTop(),insets.getSystemWindowInsetRight(),insets.getSystemWindowInsetBottom());return insets;
        });
        label(box,"Offline travel · Central DC");label(box,"25 dated places across four editorial categories. Bounded central DC catalog, not a complete city guide.");label(box,TravelCatalog.WARNING);
        try(InputStream stream=getAssets().open("dc-monuments.tsv")){catalog=new TravelCatalog(stream);}catch(Exception error){label(box,"Travel pack rejected: "+error.getMessage());return;}
        label(box,"Category filter (all constraints apply to search and planning)");
        category=new Spinner(this);category.setContentDescription("POI category");category.setAdapter(new ArrayAdapter<>(this,android.R.layout.simple_spinner_dropdown_item,new String[]{"All categories","monument","museum","park-garden","civic","restaurant (not supplied)","hotel (not supplied)"}));box.addView(category);
        query=field(box,"Require phrase in name or description","");
        avoid=field(box,"Avoid phrase in name or description","");
        label(box,"Case-insensitive literal phrases, not inferred amenities. Conflicting filters return no candidates.");
        search=button(box,"Search places");
        origin=new Spinner(this);origin.setContentDescription("Starting place");origin.setAdapter(new ArrayAdapter<>(this,android.R.layout.simple_spinner_dropdown_item,catalog.pois.stream().map(p->p.name+" ["+p.id+"]").toArray(String[]::new)));box.addView(origin);
        label(box,"Maximum straight-line distance from starting place (km)");
        radius=field(box,"Straight-line radius in km (0–10)","2");plan=button(box,"Suggest up to three matching stops");
        label(box,"Tools: convert 1 mi km · convert 32 F C\nadd-days 2024-02-28 1 · days-between 2024-02-28 2024-03-01\ndistance Q178114 Q213559\nUnits: m, km, mi; C, F. Dates use ISO calendar days.");
        command=field(box,"Tool command","convert 1 mi km");calculate=button(box,"Calculate offline");
        output=label(box,"");output.setContentDescription("Travel result");output.setTextIsSelectable(true);
        sources=new LinearLayout(this);sources.setOrientation(1);box.addView(sources);
        search.setOnClickListener(v->{java.util.List<TravelCatalog.Poi> found=catalog.filter(selectedCategory(),query.getText().toString(),avoid.getText().toString());output.setText(found.size()+" matching places in this pack.\n"+TravelCatalog.WARNING);showSources(found);});
        plan.setOnClickListener(v->{try{String id=catalog.pois.get(origin.getSelectedItemPosition()).id;double km=Double.parseDouble(radius.getText().toString());String cat=selectedCategory(),yes=query.getText().toString(),no=avoid.getText().toString();
            output.setText(catalog.plan(id,km,3,cat,yes,no));java.util.List<TravelCatalog.Poi> selected=new java.util.ArrayList<>();selected.add(catalog.get(id));selected.addAll(catalog.nearby(id,km,3,cat,yes,no));showSources(selected);}catch(Exception error){output.setText("Cannot plan: "+error.getMessage());sources.removeAllViews();}});
        calculate.setOnClickListener(v->{try{output.setText(TravelCommands.run(command.getText().toString(),catalog));showSources(catalog.pois);}catch(Exception error){output.setText("Cannot calculate: "+error.getMessage());sources.removeAllViews();}});
        if(saved!=null){query.setText(saved.getString("query",""));avoid.setText(saved.getString("avoid",""));category.setSelection(saved.getInt("category",0));radius.setText(saved.getString("radius","2"));command.setText(saved.getString("command","convert 1 mi km"));origin.setSelection(saved.getInt("origin",0));}
        search.performClick();
    }
    private String selectedCategory(){int index=category.getSelectedItemPosition();return new String[]{"","monument","museum","park-garden","civic","restaurant","hotel"}[index];}
    private void showSources(java.util.List<TravelCatalog.Poi> pois){sources.removeAllViews();for(TravelCatalog.Poi p:pois){Button b=button(sources,"Inspect ["+p.id+"] "+p.name);b.setOnClickListener(v->{inspectedId=p.id;TextView detail=new TextView(this);detail.setText(p.evidence());detail.setTextIsSelectable(true);detail.setPadding(20,20,20,20);ScrollView scroll=new ScrollView(this);scroll.addView(detail);new AlertDialog.Builder(this).setTitle(p.name).setView(scroll).setPositiveButton("Close",null).show();});}}
    private TextView label(LinearLayout box,String text){TextView t=new TextView(this);t.setText(text);t.setTextSize(16);t.setPadding(0,10,0,10);box.addView(t);return t;}
    private EditText field(LinearLayout box,String hint,String value){EditText e=new EditText(this);e.setHint(hint);e.setContentDescription(hint);e.setText(value);e.setSingleLine(true);box.addView(e);return e;}
    private Button button(LinearLayout box,String text){Button b=new Button(this);b.setText(text);b.setAllCaps(false);box.addView(b);return b;}
    @Override public void onSaveInstanceState(Bundle state){super.onSaveInstanceState(state);if(catalog!=null){state.putString("query",query.getText().toString());state.putString("avoid",avoid.getText().toString());state.putInt("category",category.getSelectedItemPosition());state.putString("radius",radius.getText().toString());state.putString("command",command.getText().toString());state.putInt("origin",origin.getSelectedItemPosition());}}
}
