package org.pocketlore.app;

import android.app.AlertDialog;
import android.content.Intent;
import android.os.Bundle;
import android.widget.*;
import java.util.*;

public final class SavedActivity extends NotebookActivity {
    LinearLayout records;EditText filter;boolean bookmarks;long generation;int pageNumber,totalPages=1;Button previous,next;TextView pageState,selectionState;
    final LinkedHashSet<Long> selected=new LinkedHashSet<>();
    @Override public void onCreate(Bundle state){super.onCreate(state);
        if(state==null){state=new Bundle();android.content.SharedPreferences prefs=getPreferences(0);state.putString("filter",prefs.getString("filter",""));state.putBoolean("bookmarks",prefs.getBoolean("bookmarks",false));state.putInt("page",prefs.getInt("page",0));String saved=prefs.getString("selected","");java.util.ArrayList<Long> ids=new java.util.ArrayList<>();for(String id:saved.split(","))try{if(ids.size()<2)ids.add(Long.parseLong(id));}catch(NumberFormatException ignored){}state.putLongArray("selected",ids.stream().mapToLong(Long::longValue).toArray());}
        LinearLayout page=ReaderUi.column(this);ReaderUi.screen(this,page,"Saved");
        ReaderUi.title(this,page,"Your notebook","History, bookmarks and notes stay on this device.");
        filter=new EditText(this);ReaderUi.label(this,page,filter,"Find saved research");filter.setHint("Search titles, questions or notes");page.addView(filter);
        if(state!=null){filter.setText(state.getString("filter",""));bookmarks=state.getBoolean("bookmarks");pageNumber=state.getInt("page",0);long[] ids=state.getLongArray("selected");if(ids!=null)for(long id:ids)selected.add(id);}
        filter.setImeOptions(android.view.inputmethod.EditorInfo.IME_ACTION_SEARCH);filter.setSingleLine(true);filter.setOnEditorActionListener((v,action,event)->{pageNumber=0;refresh();return true;});
        filter.addTextChangedListener(new android.text.TextWatcher(){public void beforeTextChanged(CharSequence s,int start,int count,int after){}public void onTextChanged(CharSequence s,int start,int before,int count){pageNumber=0;refresh();}public void afterTextChanged(android.text.Editable e){}});
        Switch only=new Switch(this);only.setText("Bookmarks only");only.setTextSize(16);only.setMinHeight(ReaderUi.dp(this,48));only.setChecked(bookmarks);page.addView(only);only.setOnCheckedChangeListener((v,on)->{bookmarks=on;pageNumber=0;refresh();});
        LinearLayout actions=ReaderUi.column(this);ReaderUi.button(this,page,"Notebook actions",()->actions.setVisibility(actions.getVisibility()==8?0:8));page.addView(actions);actions.setVisibility(8);
        ReaderUi.button(this,actions,"Compare selected (2)",()->{if(selected.size()!=2){message("Select exactly two SOURCE snapshots to compare.");return;}Long[] ids=selected.toArray(new Long[0]);startActivity(new Intent(this,ComparisonActivity.class).putExtra("left",ids[0].longValue()).putExtra("right",ids[1].longValue()));});
        ReaderUi.button(this,actions,"Open saved comparisons",()->work(()->{ComparisonStore store=new ComparisonStore(this);List<String> ids=store.list();List<String> titles=new ArrayList<>();for(String id:ids)try{{org.json.JSONObject c=store.load(id);titles.add(c.getString("title")+" · "+c.getJSONArray("subjects").getJSONObject(0).getString("label")+" / "+c.getJSONArray("subjects").getJSONObject(1).getString("label"));}}catch(Exception e){titles.add("Unavailable comparison — "+id);}runOnUiThread(()->new AlertDialog.Builder(this).setTitle("Saved manual comparisons").setItems(titles.toArray(new String[0]),(d,w)->startActivity(new Intent(this,ComparisonActivity.class).putExtra("comparison",ids.get(w)))).setNegativeButton("Close",null).show());}));
        ReaderUi.button(this,actions,"Export notebook",this::exportNotebook);
        selectionState=ReaderUi.text(this,"Selected source snapshots: none",16);page.addView(selectionState);
        previous=ReaderUi.button(this,page,"Previous page",()->{if(pageNumber>0){pageNumber--;refresh();}});pageState=ReaderUi.text(this,"Page 1",16);page.addView(pageState);next=ReaderUi.button(this,page,"Next page",()->{if(pageNumber+1<totalPages){pageNumber++;refresh();}});
        operation=ReaderUi.text(this,"Loading saved history…",16);ReaderUi.status(operation);page.addView(operation);records=new LinearLayout(this);records.setOrientation(1);page.addView(records);
    }
    @Override protected void onResume(){super.onResume();refresh();}
    void refresh(){long epoch=++generation;String query=filter.getText().toString();boolean only=bookmarks;int requested=pageNumber;work(()->{NotebookStore.Page result;try(NotebookStore store=new NotebookStore(this)){result=store.page(query,only,requested);}runOnUiThread(()->{if(isDestroyed()||epoch!=generation||records==null)return;records.removeAllViews();pageNumber=result.number;totalPages=result.pages();previous.setEnabled(pageNumber>0);next.setEnabled(pageNumber+1<totalPages);pageState.setText("Page "+(pageNumber+1)+" of "+totalPages+" · "+result.total+" results");selectionText();if(operation.getText().toString().startsWith("Loading saved")||operation.getText().toString().startsWith("Showing ")||operation.getText().toString().startsWith("No saved records match"))message(result.total==0?"No saved records match. Existing history and selections are retained.":"Showing "+result.entries.size()+" of "+result.total+" saved records");for(NotebookStore.Summary e:result.entries){
        LinearLayout card=ReaderUi.column(this);card.setPadding(0,ReaderUi.dp(this,8),0,ReaderUi.dp(this,8));LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);lp.bottomMargin=ReaderUi.dp(this,12);records.addView(card,lp);
        ReaderUi.entry(this,card,e.title,e.hasNote?"Includes your note · Open full snapshot":"Open full saved snapshot",()->startActivity(new Intent(this,SourceReaderActivity.class).putExtra("record",e.id)));
        card.addView(ReaderUi.text(this,e.kind+" · "+android.text.format.DateFormat.format("yyyy-MM-dd HH:mm",e.created)+(e.bookmark?" · Bookmarked":" · History"),16));
        LinearLayout details=new LinearLayout(this);details.setOrientation(1);ReaderUi.button(this,card,"Record actions",()->details.setVisibility(details.getVisibility()==8?0:8));card.addView(details);details.setVisibility(8);
        CheckBox select=new CheckBox(this);select.setText("Select for comparison");select.setTextSize(16);select.setMinHeight(ReaderUi.dp(this,48));select.setEnabled(e.kind.equals("source"));select.setChecked(selected.contains(e.id));details.addView(select);select.setOnCheckedChangeListener((v,on)->{if(on&&selected.size()>=2&&!selected.contains(e.id)){select.setChecked(false);message("Choose at most two records.");}else if(on)selected.add(e.id);else selected.remove(e.id);selectionText();});
        ReaderUi.button(this,details,"Remove saved record",()->new AlertDialog.Builder(this).setTitle("Remove saved record?").setMessage("Deletes this history snapshot, bookmark and note. Installed sources remain. Export first if you need a copy.").setNegativeButton("Keep",null).setPositiveButton("Remove",(d,w)->work(()->{try(NotebookStore store=new NotebookStore(this)){store.remove(e.id);}runOnUiThread(()->{selected.remove(e.id);refresh();});})).show());
    }});});}
    @Override protected void onPause(){super.onPause();if(filter!=null){StringBuilder ids=new StringBuilder();for(long id:selected)ids.append(id).append(",");getPreferences(0).edit().putString("filter",filter.getText().toString()).putBoolean("bookmarks",bookmarks).putInt("page",pageNumber).putString("selected",ids.toString()).apply();}}
    void selectionText(){if(selectionState!=null)selectionState.setText("Selected source snapshots ("+selected.size()+"/2): "+(selected.isEmpty()?"none":selected.toString())+". Selections remain across pages and filters.");}
    @Override public void onSaveInstanceState(Bundle b){super.onSaveInstanceState(b);b.putInt("page",pageNumber);b.putString("filter",filter.getText().toString());b.putBoolean("bookmarks",bookmarks);b.putLongArray("selected",selected.stream().mapToLong(Long::longValue).toArray());}
}
