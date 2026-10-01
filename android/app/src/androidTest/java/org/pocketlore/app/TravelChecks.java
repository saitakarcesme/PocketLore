package org.pocketlore.app;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;

/** Frozen development assertions shared by host and Android. No model calls. */
public final class TravelChecks {
    static int checks;
    static void require(boolean ok,String message){checks++;if(!ok)throw new AssertionError(message);}
    interface Action {void run()throws Exception;}
    static void rejects(Action a)throws Exception{checks++;try{a.run();}catch(Exception expected){return;}throw new AssertionError("Invalid input was accepted");}
    public static String run(byte[] raw)throws Exception {
        checks=0;long start=System.nanoTime();TravelCatalog c=new TravelCatalog(new ByteArrayInputStream(raw));double load=(System.nanoTime()-start)/1e6;
        require(c.search("LiNcOlN").size()==1 && c.search("LiNcOlN").get(0).id.equals("Q213559"),"Search match");
        require(c.search("vegan restaurant").isEmpty(),"Invented venue");require(c.search("").size()==3,"Catalog coverage");
        for(TravelCatalog.Poi p:c.pois){require(p.evidence().contains(p.id)&&p.evidence().contains("CC0-1.0")&&p.evidence().contains(p.sourceHash)&&p.sourceHash.length()==64&&p.url.contains(p.revision),"Inspectable provenance");}
        java.util.List<TravelCatalog.Poi> list=c.nearby("Q178114",2,2);
        require(list.size()==2 && list.get(0).id.equals("Q326183") && list.get(1).id.equals("Q213559"),"Known geographic order");
        require(c.nearby("Q178114",0,2).isEmpty(),"Radius limit");
        String plan=c.plan("Q178114",2,2);require(plan.contains("[Q178114]")&&plan.contains("[Q326183]")&&plan.contains("[Q213559]")&&plan.contains("Not a route")&&plan.contains("hours may be stale")&&plan.contains("Routing and walking times are unavailable"),"Planning provenance and limitations");
        require(Math.abs(TravelTools.convert(1,"mi","km")-1.609344)<1e-12,"Mile conversion");require(TravelTools.convert(32,"F","C")==0,"Temperature");
        rejects(()->TravelTools.convert(1,"km","C"));rejects(()->TravelTools.convert(Double.NaN,"mi","km"));rejects(()->TravelTools.convert(Double.MAX_VALUE,"mi","m"));
        require(TravelTools.addDays("2024-02-28",1).equals("2024-02-29"),"Leap day");require(TravelTools.daysBetween("2024-02-28","2024-03-01")==2,"Calendar difference");rejects(()->TravelTools.addDays("2023-02-29",1));
        require(TravelTools.distanceKm(0,0,0,0)==0,"Identity distance");require(Math.abs(TravelTools.distanceKm(0,0,0,1)-111.19508)<0.001,"Equatorial distance");require(Math.abs(TravelTools.distanceKm(0,179,0,-179)-222.39016)<0.001,"Antimeridian");rejects(()->TravelTools.distanceKm(91,0,0,0));rejects(()->TravelTools.distanceKm(0,Double.NaN,0,0));
        require(TravelCommands.run("convert 1 mi km",c).contains("1.609344 km"),"Command conversion");require(TravelCommands.run("distance Q178114 Q213559",c).contains("routing and walking times unavailable"),"Distance disclosure");rejects(()->TravelCommands.run("open now",c));rejects(()->c.nearby("Q178114",-1,2));rejects(()->c.get("Q0"));
        byte[] bad=raw.clone();bad[0]^=1;rejects(()->new TravelCatalog(new ByteArrayInputStream(bad)));
        String text=new String(raw,StandardCharsets.UTF_8);String[] rows=text.split("\n");rejects(()->TravelCatalog.parse(rows[0]+"\n"+rows[0]+"\n"+rows[2]+"\n"));
        String[] cols=rows[0].split("\t");cols[3]="NaN";String nonfinite=String.join("\t",cols)+"\n"+rows[1]+"\n"+rows[2]+"\n";rejects(()->TravelCatalog.parse(nonfinite));
        cols[3]="0";String outside=String.join("\t",cols)+"\n"+rows[1]+"\n"+rows[2]+"\n";rejects(()->TravelCatalog.parse(outside));
        long timed=System.nanoTime();for(int i=0;i<1000;i++){c.search("Lincoln");c.plan("Q178114",2,2);}double mean=(System.nanoTime()-timed)/1e6/1000;
        return "PASS "+checks+" behavior assertions\nCatalog load ms: "+load+"\nMean search plus plan ms (1000 warm iterations): "+mean+"\nPack SHA-256: "+TravelCatalog.HASH+"\n"+plan;
    }
    public static void main(String[] args)throws Exception{System.out.println("Host JVM, not physical Android\n"+run(Files.readAllBytes(Paths.get(args[0]))));}
}
