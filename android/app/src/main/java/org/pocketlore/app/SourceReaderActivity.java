package org.pocketlore.app;

import android.content.*;
import android.os.Bundle;
import android.graphics.Color;
import android.view.*;
import android.widget.*;
import java.util.*;

/** Full-screen, locally persisted source/result reading, separate from inference. */
public final class SourceReaderActivity extends NotebookActivity {
    long recordId,compareId; NotebookStore.Entry entry,other;
    LinearLayout body; android.widget.FrameLayout readerRoot; ScrollView scroll; TextView content; EditText note;
    boolean cream; int readingSize; String draft;
    @Override public void onCreate(Bundle state){super.onCreate(state);
        recordId=getIntent().getLongExtra("record",-1);compareId=getIntent().getLongExtra("compare",-1);
        cream=getPreferences(0).getBoolean("cream",true);readingSize=getPreferences(0).getInt("size",18);
        if(state!=null)draft=state.getString("note");
        body=ReaderUi.column(this);scroll=new ScrollView(this);scroll.setFillViewport(true);scroll.addView(body);readerRoot=new android.widget.FrameLayout(this);readerRoot.addView(scroll,new android.widget.FrameLayout.LayoutParams(-1,-1));setContentView(readerRoot);ReaderUi.insets(this,readerRoot);
        ReaderUi.button(this,body,"Close reader",this::finish);operation=ReaderUi.text(this,"Opening saved snapshot…",16);ReaderUi.status(operation);body.addView(operation);
        work(()->{try(NotebookStore store=new NotebookStore(this)){entry=store.get(recordId);String expected=getIntent().getStringExtra("snapshot_hash");if(expected!=null&&!ComparisonStore.identity(entry).equals(expected))throw new java.io.IOException("Unknown — saved source snapshot changed");if(compareId!=-1)other=store.get(compareId);}runOnUiThread(()->{if(!isDestroyed()){render();scroll.post(()->scroll.scrollTo(0,state!=null?state.getInt("scroll",0):getPreferences(0).getInt("position-"+recordId+"-"+compareId,0)));}});});
    }
    void render(){
        body.removeAllViews();ReaderUi.button(this,body,"Close reader",this::finish);
        TextView title=ReaderUi.text(this,other==null?entry.title:"Compare saved evidence",28);title.setTypeface(android.graphics.Typeface.create("serif",0));ReaderUi.heading(title);body.addView(title);
        body.addView(ReaderUi.text(this,entry.kind.equals("research")?"Saved research · Offline":"Source snapshot · Offline",16));
        LinearLayout appearance=new LinearLayout(this);appearance.setOrientation(LinearLayout.VERTICAL);ReaderUi.button(this,body,"Reading options",()->appearance.setVisibility(appearance.getVisibility()==8?0:8));body.addView(appearance);appearance.setVisibility(8);
        if(other==null){java.util.regex.Matcher date=java.util.regex.Pattern.compile("(?m)Source date(?: / retrieval)?: ([^\\n]*)").matcher(entry.body);appearance.addView(ReaderUi.text(this,"Source date: "+(date.find()&&!date.group(1).trim().isEmpty()?date.group(1):"Unknown")+"\nCapture time is not publication time. Edition and coverage remain in the source text.",16));}
        Spinner size=new Spinner(this);size.setMinimumHeight(ReaderUi.dp(this,48));size.setContentDescription("Reader font size");size.setAdapter(new ArrayAdapter<String>(this,android.R.layout.simple_spinner_dropdown_item,new String[]{"Reading size: 18sp","Reading size: 22sp","Reading size: 26sp"}));appearance.addView(size);size.setSelection(readingSize==26?2:readingSize==22?1:0);
        size.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener(){public void onNothingSelected(AdapterView<?> p){}public void onItemSelected(AdapterView<?> p,View v,int index,long id){readingSize=new int[]{18,22,26}[index];getPreferences(0).edit().putInt("size",readingSize).apply();if(content!=null)content.setTextSize(readingSize);if(v!=null)colors(v);}});
        ReaderUi.button(this,appearance,"Switch reading theme",()->{cream=!cream;getPreferences(0).edit().putBoolean("cream",cream).apply();colors(body);applyTheme();});
        operation=ReaderUi.text(this,"",16);ReaderUi.status(operation);operation.setVisibility(View.GONE);body.addView(operation);
        content=ReaderUi.text(this,other==null?readingText(entry):"Comparison of two saved records; no new synthesis or verdict.\n\n"+readingText(entry)+"\n────────────\n\n"+readingText(other),readingSize);content.setTextIsSelectable(true);body.addView(content);
        if(other==null){
            Button bookmark=ReaderUi.button(this,body,entry.bookmark?"Bookmarked · Remove bookmark":"Bookmark this record",()->{});
            bookmark.setOnClickListener(v->{boolean next=!entry.bookmark;String text=note==null?entry.note:note.getText().toString();work(()->{try(NotebookStore store=new NotebookStore(this)){store.update(entry.id,next,text);}runOnUiThread(()->{entry.bookmark=next;entry.note=text;bookmark.setText(next?"Bookmarked · Remove bookmark":"Bookmark this record");message(next?"Bookmark saved on this device.":"Bookmark removed; history retained.");});});});
        }

        if(other==null){
            note=new EditText(this);ReaderUi.label(this,body,note,"Personal note");note.setMinLines(3);note.setGravity(Gravity.TOP);note.setInputType(android.text.InputType.TYPE_CLASS_TEXT|android.text.InputType.TYPE_TEXT_FLAG_MULTI_LINE);note.setFilters(new android.text.InputFilter[]{new android.text.InputFilter.LengthFilter(20000)});note.setText(draft==null?entry.note:draft);body.addView(note);
            ReaderUi.button(this,body,"Save note",()->{String value=note.getText().toString();work(()->{try(NotebookStore store=new NotebookStore(this)){store.note(entry.id,value);}runOnUiThread(()->{entry.note=value;content.setText(readingText(entry));message("Personal note saved. It is not source evidence.");});});});
        }
        ReaderUi.button(this,body,"Export snapshot",()->export(current(),false));
        ReaderUi.button(this,body,"Share snapshot",()->export(current(),true));
        colors(body);applyTheme();
    }
    private String readingText(NotebookStore.Entry e){return (e.question.isEmpty()?"":"Question\n"+e.question+"\n")+e.body+"\n\nSource and coverage\n"+e.provenance+"\n\nCaptured on this device: "+android.text.format.DateFormat.format("yyyy-MM-dd HH:mm",e.created)+"\nCapture time is not the source publication date.";}
    private void applyTheme(){getWindow().setBackgroundDrawable(new android.graphics.drawable.ColorDrawable(cream?ReaderUi.NAVY:ReaderUi.CREAM));ReaderUi.barAppearance(this,cream);scroll.setBackgroundColor(cream?ReaderUi.NAVY:ReaderUi.CREAM);readerRoot.setBackgroundColor(cream?ReaderUi.NAVY:ReaderUi.CREAM);getWindow().setStatusBarColor(cream?ReaderUi.NAVY:ReaderUi.CREAM);getWindow().setNavigationBarColor(cream?ReaderUi.NAVY:ReaderUi.CREAM);getWindow().getDecorView().setSystemUiVisibility(cream?View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR|View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR:0);}
    private List<NotebookStore.Entry> current(){if(note!=null)entry.note=note.getText().toString();return other==null?Collections.singletonList(entry):Arrays.asList(entry,other);}
    private void colors(View v){
        if(v instanceof TextView){TextView t=(TextView)v;t.setTextColor(cream?ReaderUi.CREAM:ReaderUi.NAVY);t.setHintTextColor(cream?Color.rgb(23,95,88):Color.rgb(188,203,211));}
        if(v instanceof Button)v.setBackgroundTintList(android.content.res.ColorStateList.valueOf(cream?Color.rgb(225,223,210):Color.rgb(27,45,62)));
        if(v instanceof ViewGroup)for(int i=0;i<((ViewGroup)v).getChildCount();i++)colors(((ViewGroup)v).getChildAt(i));
    }
    @Override protected void onPause(){super.onPause();if(scroll!=null)getPreferences(0).edit().putInt("position-"+recordId+"-"+compareId,scroll.getScrollY()).apply();if(note!=null&&entry!=null){String value=note.getText().toString();long id=entry.id;work(()->{try(NotebookStore store=new NotebookStore(this)){store.note(id,value);}});}}
    @Override public void onSaveInstanceState(Bundle b){super.onSaveInstanceState(b);if(note!=null)b.putString("note",note.getText().toString());if(scroll!=null)b.putInt("scroll",scroll.getScrollY());}
}
