package org.pocketlore.app;

import android.app.Activity;
import android.graphics.Color;
import android.view.View;
import android.view.WindowInsets;
import android.widget.*;

/** Shared native reading surfaces; no data or answer policy belongs here. */
final class ReaderUi {
    static final int TEAL = Color.rgb(36,91,67);
    static final int NAVY = Color.rgb(247,244,236), CREAM = Color.rgb(32,38,33);
    static int dp(Activity a, int n) { return Math.round(n*a.getResources().getDisplayMetrics().density); }
    static LinearLayout column(Activity a) {
        LinearLayout v=new LinearLayout(a);v.setOrientation(LinearLayout.VERTICAL);
        v.setPadding(dp(a,24),dp(a,16),dp(a,24),dp(a,32));return v;
    }
    static TextView text(Activity a,String value,int size) {
        TextView t=new TextView(a);t.setText(value);t.setTextSize(Math.max(16,size));t.setTextColor(CREAM);
        t.setPadding(0,dp(a,8),0,dp(a,8));t.setLineSpacing(dp(a,3),1.08f);return t;
    }
    static void heading(TextView t) { t.setAccessibilityHeading(true); }
    static void status(TextView t) { t.setAccessibilityLiveRegion(View.ACCESSIBILITY_LIVE_REGION_POLITE); }
    static void barAppearance(Activity a,boolean light){if(android.os.Build.VERSION.SDK_INT>=30){int mask=android.view.WindowInsetsController.APPEARANCE_LIGHT_STATUS_BARS|android.view.WindowInsetsController.APPEARANCE_LIGHT_NAVIGATION_BARS;a.getWindow().getInsetsController().setSystemBarsAppearance(light?mask:0,mask);}}
    static void insets(Activity a, View root) {
        if(android.os.Build.VERSION.SDK_INT>=30)a.getWindow().setDecorFitsSystemWindows(false);
        root.setBackgroundColor(NAVY);a.getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR|View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR);
        a.getWindow().setStatusBarColor(NAVY);a.getWindow().setNavigationBarColor(NAVY);
        barAppearance(a,true);root.setOnApplyWindowInsetsListener((v,i)->{
            if(android.os.Build.VERSION.SDK_INT>=30){android.graphics.Insets b=i.getInsets(WindowInsets.Type.systemBars()|WindowInsets.Type.ime());v.setPadding(b.left,b.top,b.right,b.bottom);View navigation=v.findViewWithTag("destination-nav");if(navigation!=null)navigation.setVisibility(i.isVisible(WindowInsets.Type.ime())?View.GONE:View.VISIBLE);}
            else v.setPadding(i.getSystemWindowInsetLeft(),i.getSystemWindowInsetTop(),i.getSystemWindowInsetRight(),i.getSystemWindowInsetBottom());
            return i;
        });
    }
    static void label(Activity a, LinearLayout box,EditText field,String title) {
        if(field.getId()==View.NO_ID)field.setId(View.generateViewId());
        TextView label=text(a,title,14);label.setLabelFor(field.getId());box.addView(label);
        field.setContentDescription(title);
    }
    static android.graphics.drawable.Drawable surface(Activity a,int color,int radius,boolean border) {
        android.graphics.drawable.GradientDrawable normal=new android.graphics.drawable.GradientDrawable();normal.setColor(color);normal.setCornerRadius(dp(a,radius));
        if(border)normal.setStroke(dp(a,1),Color.rgb(205,211,201));
        android.graphics.drawable.GradientDrawable focus=new android.graphics.drawable.GradientDrawable();focus.setColor(color);focus.setCornerRadius(dp(a,radius));focus.setStroke(dp(a,3),TEAL);
        android.graphics.drawable.StateListDrawable states=new android.graphics.drawable.StateListDrawable();states.addState(new int[]{android.R.attr.state_focused},focus);states.addState(new int[]{},normal);
        return new android.graphics.drawable.RippleDrawable(android.content.res.ColorStateList.valueOf(0x22245B43),states,null);
    }
    static void revealFocus(View view){for(android.view.ViewParent p=view.getParent();p!=null;p=p.getParent())if(p instanceof ScrollView){ScrollView scroll=(ScrollView)p;android.graphics.Rect r=new android.graphics.Rect(0,0,view.getWidth(),view.getHeight());scroll.offsetDescendantRectToMyCoords(view,r);int top=scroll.getScrollY()+scroll.getPaddingTop(),bottom=scroll.getScrollY()+scroll.getHeight()-scroll.getPaddingBottom();if(r.bottom>bottom)scroll.scrollBy(0,r.bottom-bottom);else if(r.top<top)scroll.scrollBy(0,r.top-top);break;}}
    static void styleButton(Activity a,Button b,boolean primary){
        b.setOnFocusChangeListener((v,focused)->{if(focused)v.post(()->{if(v.hasFocus())revealFocus(v);});});
        b.setBackground(surface(a,primary?TEAL:Color.TRANSPARENT,12,false));b.setBackgroundTintList(null);b.setTextColor(primary?NAVY:TEAL);b.setPadding(dp(a,12),dp(a,10),dp(a,12),dp(a,10));
        b.setSingleLine(false);b.setMaxLines(Integer.MAX_VALUE);b.setEllipsize(null);b.setHorizontallyScrolling(false);
        b.setStateListAnimator(null);b.setElevation(0);b.setMinHeight(dp(a,48));b.setMinWidth(dp(a,48));b.setAllCaps(false);b.setGravity(android.view.Gravity.CENTER_VERTICAL|android.view.Gravity.START);b.setTextSize(16);
    }
    static void card(Activity a, View view) {view.setBackground(surface(a,Color.rgb(238,238,229),16,false));view.setPadding(dp(a,20),dp(a,16),dp(a,20),dp(a,16));}
    static void entry(Activity a,LinearLayout box,String title,String detail,Runnable action){
        LinearLayout row=new LinearLayout(a);row.setOrientation(1);row.setBackground(surface(a,Color.TRANSPARENT,8,false));row.setPadding(0,dp(a,12),0,dp(a,12));row.setMinimumHeight(dp(a,64));
        TextView name=text(a,title,20);name.setTypeface(android.graphics.Typeface.create("sans-serif-medium",0));row.addView(name);TextView sub=text(a,detail,16);sub.setTextColor(Color.rgb(89,99,91));row.addView(sub);
        row.setFocusable(true);row.setClickable(true);row.setContentDescription(title+". "+detail);row.setOnClickListener(v->action.run());row.setAccessibilityDelegate(new View.AccessibilityDelegate(){@Override public void onInitializeAccessibilityNodeInfo(View host,android.view.accessibility.AccessibilityNodeInfo info){super.onInitializeAccessibilityNodeInfo(host,info);info.setClassName(Button.class.getName());}});name.setImportantForAccessibility(2);sub.setImportantForAccessibility(2);box.addView(row);
        View rule=new View(a);rule.setBackgroundColor(0xFFDADFD4);box.addView(rule,new LinearLayout.LayoutParams(-1,dp(a,1)));
    }
    static Button button(Activity a,LinearLayout box,String label,Runnable action) {
        Button b=new Button(a);b.setText(label);b.setAllCaps(false);b.setTextSize(16);b.setMinHeight(dp(a,48));b.setMinWidth(dp(a,48));
        styleButton(a,b,false);LinearLayout.LayoutParams params=new LinearLayout.LayoutParams(-1,-2);params.topMargin=dp(a,4);params.bottomMargin=dp(a,4);box.addView(b,params);b.setOnClickListener(v->action.run());return b;
    }
    static void title(Activity a,LinearLayout box,String title,String subtitle){TextView heading=text(a,title,32);heading.setTypeface(android.graphics.Typeface.create("serif",0));heading(heading);box.addView(heading);box.addView(text(a,subtitle,16));}
    static void navigate(Activity a,String destination){
        if(destination.equals("Research") && a instanceof MainActivity){((MainActivity)a).showResearch();return;}
        android.content.Intent intent;
        if(destination.equals("Research"))intent=new android.content.Intent(a,MainActivity.class).addFlags(android.content.Intent.FLAG_ACTIVITY_CLEAR_TOP|android.content.Intent.FLAG_ACTIVITY_SINGLE_TOP);
        else if(destination.equals("Saved"))intent=new android.content.Intent(a,SavedActivity.class);
        else intent=new android.content.Intent(a,ScaleActivity.class).putExtra("section",destination.equals("Explore")?"Places":"Knowledge");
        a.startActivity(intent);if(!(a instanceof MainActivity))a.finish();
    }
    static final class Icon extends android.graphics.drawable.Drawable {
        final String kind; final android.graphics.Paint p=new android.graphics.Paint(3); Icon(String k){kind=k;}
        public void draw(android.graphics.Canvas c){c.save();c.translate(getBounds().left,getBounds().top);c.scale(getBounds().width()/24f,getBounds().height()/24f);p.setColor(TEAL);p.setStyle(android.graphics.Paint.Style.STROKE);p.setStrokeWidth(1.7f);p.setStrokeCap(android.graphics.Paint.Cap.ROUND);p.setStrokeJoin(android.graphics.Paint.Join.ROUND);
            android.graphics.Path q=new android.graphics.Path();
            if(kind.equals("Research")){c.drawCircle(10,10,6,p);c.drawLine(15,15,21,21,p);}
            else if(kind.equals("Library")){q.moveTo(3,4);q.lineTo(10,4);q.lineTo(12,6);q.lineTo(14,4);q.lineTo(21,4);q.lineTo(21,20);q.lineTo(14,20);q.lineTo(12,22);q.lineTo(10,20);q.lineTo(3,20);q.close();c.drawPath(q,p);c.drawLine(12,6,12,21,p);}
            else if(kind.equals("Explore")){c.drawCircle(12,12,9,p);q.moveTo(16,8);q.lineTo(14,14);q.lineTo(8,16);q.lineTo(10,10);q.close();c.drawPath(q,p);}
            else if(kind.equals("Saved")){q.moveTo(6,3);q.lineTo(18,3);q.lineTo(18,21);q.lineTo(12,17);q.lineTo(6,21);q.close();c.drawPath(q,p);}
            else {c.drawLine(4,6,20,6,p);c.drawLine(4,12,20,12,p);c.drawLine(4,18,20,18,p);c.drawCircle(9,6,2,p);c.drawCircle(16,12,2,p);c.drawCircle(8,18,2,p);}c.restore();}
        public void setAlpha(int a){p.setAlpha(a);}public void setColorFilter(android.graphics.ColorFilter f){p.setColorFilter(f);}public int getOpacity(){return android.graphics.PixelFormat.TRANSLUCENT;}
    }
    static LinearLayout shell(Activity a,String selected){
        LinearLayout root=new LinearLayout(a);root.setOrientation(1);a.setContentView(root);insets(a,root);
        LinearLayout bar=new LinearLayout(a);bar.setGravity(android.view.Gravity.CENTER_VERTICAL);bar.setPadding(dp(a,24),dp(a,4),dp(a,16),dp(a,4));
        TextView brand=text(a,"PocketLore",20);brand.setTypeface(android.graphics.Typeface.create("serif",android.graphics.Typeface.BOLD));bar.addView(brand,new LinearLayout.LayoutParams(0,-2,1));
        TextView offline=text(a,"Offline",16);offline.setTextColor(TEAL);bar.addView(offline);
        android.widget.ImageButton settings=new android.widget.ImageButton(a);settings.setImageDrawable(new Icon("Settings"));settings.setPadding(dp(a,13),dp(a,13),dp(a,13),dp(a,13));settings.setContentDescription("Settings");settings.setBackground(surface(a,Color.TRANSPARENT,24,false));bar.addView(settings,new LinearLayout.LayoutParams(dp(a,48),dp(a,48)));settings.setOnClickListener(v->{if(a instanceof MainActivity)((MainActivity)a).showSettings();else a.startActivity(new android.content.Intent(a,MainActivity.class).addFlags(android.content.Intent.FLAG_ACTIVITY_CLEAR_TOP|android.content.Intent.FLAG_ACTIVITY_SINGLE_TOP).putExtra("settings",true));});root.addView(bar);
        LinearLayout nav=new LinearLayout(a);nav.setOrientation(1);nav.setTag("destination-nav");nav.setPadding(dp(a,12),dp(a,8),dp(a,12),dp(a,4));
        String[] names={"Research","Library","Explore","Saved"};int columns=a.getResources().getConfiguration().screenWidthDp>=600?4:(a.getResources().getConfiguration().fontScale>1.2?2:4);
        LinearLayout row=null;for(int n=0;n<names.length;n++){if(n%columns==0){row=new LinearLayout(a);nav.addView(row);}String name=names[n];Button b=new Button(a);b.setText(name);styleButton(a,b,false);b.setGravity(android.view.Gravity.CENTER);Icon icon=new Icon(name);icon.setBounds(0,0,dp(a,22),dp(a,22));b.setCompoundDrawables(null,icon,null,null);b.setCompoundDrawablePadding(dp(a,6));b.setBackground(surface(a,name.equals(selected)||name.equals("Explore")&&selected.equals("Places")?0xFFE1E9DD:Color.TRANSPARENT,16,false));b.setSelected(name.equals(selected));b.setContentDescription(name+(b.isSelected()?", selected":""));b.setOnClickListener(v->navigate(a,name));LinearLayout.LayoutParams np=new LinearLayout.LayoutParams(0,-2,1);np.setMargins(dp(a,2),0,dp(a,2),0);row.addView(b,np);}
        root.addView(nav);return root;
    }
    static void screen(Activity a,LinearLayout page,String selected){LinearLayout root=shell(a,selected);ScrollView scroll=new ScrollView(a);scroll.setSmoothScrollingEnabled(false);scroll.setFillViewport(true);scroll.addView(page);root.addView(scroll,1,new LinearLayout.LayoutParams(-1,0,1));}
    static void openSource(Activity a,String title,String detail,String provenance){
        NotebookActivity.IO.execute(()->{try(NotebookStore store=new NotebookStore(a)){long id=store.add("source",title,"",detail,provenance,false);a.runOnUiThread(()->{if(!a.isDestroyed())a.startActivity(new android.content.Intent(a,SourceReaderActivity.class).putExtra("record",id));});}
            catch(Exception e){a.runOnUiThread(()->new android.app.AlertDialog.Builder(a).setMessage("Could not save source history: "+e.getMessage()).setPositiveButton("Read without saving",(d,w)->reader(a,title,detail)).setNegativeButton("Close",null).show());}});
    }
    static void reader(Activity a,String title,String detail) {
        LinearLayout body=column(a);TextView name=text(a,title,24);heading(name);body.addView(name);
        TextView content=text(a,detail,18);content.setTextIsSelectable(true);body.addView(content);
        ScrollView scroll=new ScrollView(a);scroll.addView(body);
        new android.app.AlertDialog.Builder(a).setView(scroll).setPositiveButton("Close",null).show();
    }
}
