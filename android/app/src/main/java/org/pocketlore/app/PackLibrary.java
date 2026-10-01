package org.pocketlore.app;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import java.util.function.BooleanSupplier;
import org.json.*;

/** Content-addressed editions with one atomically committed active catalog.
 * An archive rename precedes catalog commit; a crash can leave an unreferenced archive,
 * which is removed only within this library's owned directory on the next operation.
 */
public final class PackLibrary {
    public static final int MAX_COLLECTIONS=8, MAX_DOCUMENTS=1000, MAX_PASSAGES=5000;
    public static final long MAX_ARCHIVES=16L*1024*1024,MAX_EXPANDED=16L*1024*1024,
        MAX_MANIFESTS=2L*1024*1024,MAX_TEXT=1000000,MAX_TOKENS=200000;
    public static final class Entry {
        public final String hash,id;public final boolean active;
        Entry(String hash,String id,boolean active){this.hash=hash;this.id=id;this.active=active;}
    }
    public static final class Snapshot {
        public final List<Entry> entries;public final ResearchEngine engine;
        public final int distinctDocuments;public final long archiveBytes;
        Snapshot(List<Entry> entries,ResearchEngine engine,int docs,long bytes){this.entries=Collections.unmodifiableList(entries);this.engine=engine;distinctDocuments=docs;archiveBytes=bytes;}
        public String description(){int n=0;for(Entry e:entries)if(e.active)n++;return n+" of "+entries.size()+" collections active · "+distinctDocuments+" distinct source documents · "+engine.size()+" searchable passages";}
    }
    private final File directory,catalog;
    public PackLibrary(File files)throws IOException {directory=new File(files,"pack-library");if(!directory.isDirectory()&&!directory.mkdirs())throw new IOException("Cannot create library directory");catalog=new File(directory,"catalog.json");}
    static void require(boolean ok,String why)throws IOException{if(!ok)throw new IOException(why);}
    public static void admit(long archives,long expanded,long manifests,long documents,long count,long passages,long text,long tokens)throws IOException {
        require(archives<=MAX_ARCHIVES&&expanded<=MAX_EXPANDED&&manifests<=MAX_MANIFESTS&&documents<=MAX_DOCUMENTS&&count<=MAX_COLLECTIONS,"Combined collection storage limit exceeded");
        require(passages<=MAX_PASSAGES&&text<=MAX_TEXT&&tokens<=MAX_TOKENS,"Active collection index limit exceeded; disable collections before adding more");
    }
    static void admitHeap(long estimate,long available)throws IOException {
        require(estimate>=0&&available>=estimate+32L*1024*1024,"Not enough Java heap to rebuild the active index; retained catalog unchanged (estimate="+estimate+", available="+available+")");
    }
    private List<Entry> entries()throws Exception {
        List<Entry> result=new ArrayList<>();if(!catalog.exists())return result;
        require(catalog.length()<=65536,"Catalog too large");JSONObject root=new JSONObject(new String(Files.readAllBytes(catalog.toPath()),StandardCharsets.UTF_8));
        require(root.getInt("schema")==1,"Unsupported library catalog");JSONArray list=root.getJSONArray("collections");Set<String> seen=new HashSet<>();require(list.length()<=MAX_COLLECTIONS,"Too many collections");
        for(int i=0;i<list.length();i++){JSONObject e=list.getJSONObject(i);String hash=e.getString("sha256"),id=e.getString("id");require(hash.matches("[0-9a-f]{64}")&&seen.add(hash)&&id.matches("[a-z0-9-]{1,80}")&&e.get("active") instanceof Boolean,"Invalid catalog entry");result.add(new Entry(hash,id,e.getBoolean("active")));}
        return result;
    }
    private void cleanup(List<Entry> entries)throws IOException {
        Set<String> saved=new HashSet<>();for(Entry e:entries)saved.add(e.hash+".plpack");
        File[] files=directory.listFiles();if(files==null)throw new IOException("Cannot list library");
        for(File f:files)if(f.getName().matches("pack-[0-9]+\\.partial|catalog-[0-9]+\\.partial") || (f.getName().matches("[0-9a-f]{64}\\.plpack")&&!saved.contains(f.getName()))) require(f.delete(),"Cannot clean abandoned library stage");
        for(File f:files)if(f.getName().matches("[0-9a-f]{64}\\.sqlite(?:\\.partial)?")){String h=f.getName().substring(0,64);if(f.getName().endsWith(".partial")||!saved.contains(h+".plpack"))require(f.delete(),"Cannot clean abandoned broad index");}
    }
    private KnowledgePack read(File file)throws Exception {try(InputStream in=new FileInputStream(file)){return KnowledgePack.read(in,false);}}
    private Snapshot build(List<Entry> entries,KnowledgePack incoming,BooleanSupplier cancel)throws Exception {
        long bytes=0,expanded=0,manifests=0,docs=0,chars=0,tokens=0,provenanceChars=0;
        long broadBytes=0;int broadDocs=0,broadCount=0;List<ResearchEngine> diskEngines=new ArrayList<>();
        Set<String> documents=new HashSet<>();Map<String,String[]> rows=new LinkedHashMap<>();Map<String,StringBuilder> provenance=new HashMap<>();
        for(Entry entry:entries){if(cancel.getAsBoolean()||Thread.currentThread().isInterrupted())throw new InterruptedIOException("Library operation cancelled");
            File savedArchive=new File(directory,entry.hash+".plpack");
            if(incoming==null||!incoming.sha256.equals(entry.hash))if(BroadPack.isBroad(savedArchive)){
                require(++broadCount<=1&&entries.size()<=MAX_COLLECTIONS,"Only one bounded broad edition can be retained");
                File database=new File(directory,entry.hash+".sqlite");BroadPack broad=new BroadPack(savedArchive,database,entry.hash);
                require(database.isFile()&&database.length()==broad.manifest.getLong("db_bytes")&&BroadPack.hash(database).equals(broad.manifest.getString("db_sha256")),"Saved broad index missing or size changed; reimport required");
                broadBytes+=savedArchive.length()+database.length();require(broadBytes<=BroadPack.MAX_ARCHIVE+BroadPack.MAX_DATABASE,"Broad storage admission exceeded");
                if(entry.active){diskEngines.add(broad.engine());broadDocs+=broad.manifest.getInt("documents");}continue;
            }
            KnowledgePack p=incoming!=null&&incoming.sha256.equals(entry.hash)?incoming:read(new File(directory,entry.hash+".plpack"));
            require(p.sha256.equals(entry.hash)&&p.id.equals(entry.id),"Saved collection identity mismatch");
            bytes+=p.archiveBytes;expanded+=p.expandedBytes;manifests+=p.manifestBytes;docs+=p.documentCount;
            admit(bytes,expanded,manifests,docs,entries.size(),rows.size(),chars,tokens);
            if(!entry.active)continue;
            for(String[] row:p.rows){documents.add(p.documentKeys.get(row[0]));
                // Same source snapshot, text and all displayed rights/date metadata: one indexed copy,
                // with every active edition's provenance retained. Different versions/rights stay distinct.
                String key=KnowledgePack.hash((p.documentKeys.get(row[0])+"\n"+String.join("\t",Arrays.copyOfRange(row,1,6))).getBytes(StandardCharsets.UTF_8));
                String source="Collection: "+p.id+"\nEdition SHA-256: "+p.sha256+"\n"+p.provenance.get(row[0])+"\nEdition notice (may describe an older app version): "+p.warning+"\nThis app retains imported collections; Choose collections controls which are searched.";
                provenanceChars+=source.length();require(provenanceChars<=MAX_TEXT,"Active provenance metadata limit exceeded");
                if(rows.containsKey(key)){provenance.get(key).append("\n\nAlso retained in:\n").append(source);continue;}
                chars+=row[5].length();tokens+=ResearchEngine.tokenize(row[1]+" "+row[5]).size();
                admit(bytes,expanded,manifests,docs,entries.size(),rows.size()+1,chars,tokens);
                String[] namespaced=row.clone();namespaced[0]="p"+p.sha256+"_"+row[0];rows.put(key,namespaced);provenance.put(key,new StringBuilder(source));
            }
        }
        // No per-pack index exists here; admission completes before the one combined index allocation.
        long estimate=16L*1024*1024+tokens*256+chars*4+provenanceChars*4+rows.size()*2048L;
        Runtime runtime=Runtime.getRuntime();long available=runtime.maxMemory()-(runtime.totalMemory()-runtime.freeMemory());
        // One collection request prevents short-lived validation garbage from masquerading
        // as live index memory. Admission still fails if the reserve is unavailable.
        if(available<estimate+32L*1024*1024){System.gc();available=runtime.maxMemory()-(runtime.totalMemory()-runtime.freeMemory());}
        admitHeap(estimate,available);
        List<ResearchEngine.Passage> passages=new ArrayList<>();for(String key:rows.keySet())passages.add(new ResearchEngine.Passage(rows.get(key),provenance.get(key).toString()));
        ResearchEngine small=new ResearchEngine(passages);if(diskEngines.isEmpty())return new Snapshot(new ArrayList<>(entries),small,documents.size(),bytes);
        diskEngines.add(small);return new Snapshot(new ArrayList<>(entries),ResearchEngine.combined(diskEngines),documents.size()+broadDocs,bytes+broadBytes);
    }
    private void commit(List<Entry> entries,BooleanSupplier cancel)throws Exception {
        JSONArray list=new JSONArray();for(Entry e:entries)list.put(new JSONObject().put("id",e.id).put("sha256",e.hash).put("active",e.active));
        byte[] bytes=new JSONObject().put("schema",1).put("collections",list).toString(2).getBytes(StandardCharsets.UTF_8);
        File stage=File.createTempFile("catalog-",".partial",directory);
        try{try(FileOutputStream out=new FileOutputStream(stage)){out.write(bytes);out.getFD().sync();}
            if(cancel.getAsBoolean()||Thread.currentThread().isInterrupted())throw new InterruptedIOException("Library operation cancelled");
            Files.move(stage.toPath(),catalog.toPath(),StandardCopyOption.ATOMIC_MOVE,StandardCopyOption.REPLACE_EXISTING);
        }finally{stage.delete();}
    }
    public synchronized Snapshot load()throws Exception {List<Entry> es=entries();cleanup(es);return build(es,null,()->false);}
    public synchronized Snapshot select(Set<String> active)throws Exception {
        List<Entry> old=entries(),es=new ArrayList<>();Set<String> known=new HashSet<>();for(Entry e:old){known.add(e.hash);es.add(new Entry(e.hash,e.id,active.contains(e.hash)));}require(known.containsAll(active),"Unknown active collection");
        Snapshot next=build(es,null,()->false);commit(es,()->false);return next;
    }
    public synchronized Snapshot install(InputStream in,BooleanSupplier cancel)throws Exception {
        return install(in,cancel,-1);
    }
    public synchronized Snapshot install(InputStream in,BooleanSupplier cancel,long expected)throws Exception {
        require(expected==-1 || expected>0&&expected<=BroadPack.MAX_ARCHIVE,"Invalid declared archive size");
        List<Entry> es=entries();cleanup(es);ResourceStorage.requireSpace(expected<0?BroadPack.MAX_ARCHIVE:expected,directory.getUsableSpace());
        File stage=File.createTempFile("pack-",".partial",directory);File moved=null;boolean committed=false;
        try{ResourceStorage.copy(in,stage,expected<0?BroadPack.MAX_ARCHIVE:expected,cancel);
            require(expected<0||stage.length()==expected,"Archive length differs from declared size");
            if(BroadPack.isBroad(stage)){
                String hash=BroadPack.hash(stage);for(Entry e:es)if(e.hash.equals(hash))return build(es,null,cancel);
                for(Entry e:es)require(!BroadPack.isBroad(new File(directory,e.hash+".plpack")),"Disable/remove previous broad edition before importing another; no duplicate broad indexes");
                BroadPack broad=BroadPack.prepare(stage,directory,hash,cancel);File db=broad.database;
                try{es.add(new Entry(hash,broad.id,true));moved=new File(directory,hash+".plpack");Files.move(stage.toPath(),moved.toPath(),StandardCopyOption.ATOMIC_MOVE);Snapshot next=build(es,null,cancel);commit(es,cancel);committed=true;return next;}finally{if(!committed)db.delete();}
            }
            KnowledgePack p=read(stage);
            for(Entry e:es)if(e.hash.equals(p.sha256))return build(es,null,cancel);
            es.add(new Entry(p.sha256,p.id,true));Snapshot next=build(es,p,cancel);
            if(cancel.getAsBoolean()||Thread.currentThread().isInterrupted())throw new InterruptedIOException("Pack import cancelled");
            moved=new File(directory,p.sha256+".plpack");Files.move(stage.toPath(),moved.toPath(),StandardCopyOption.ATOMIC_MOVE);
            commit(es,cancel);committed=true;return next;
        }finally{stage.delete();if(!committed&&moved!=null)moved.delete();}
    }
    /** Commit the retained catalog before deleting owned bytes; an interrupted cleanup is retried on load. */
    public synchronized Snapshot remove(String hash)throws Exception {
        List<Entry> es=entries();
        require(es.removeIf(e->e.hash.equals(hash)),"Unknown collection edition");
        Snapshot next=build(es,null,()->false);
        commit(es,()->false);
        // Cleanup failure does not roll back an already committed removal.
        try { cleanup(es); } catch(IOException ignored) { /* Next load retries owned cleanup. */ }
        return next;
    }
    /** Legacy source is retained, never deleted or rewritten. Catalog commit is idempotent. */
    public synchronized Snapshot loadMigrating(File legacy)throws Exception {
        if(!catalog.exists()&&legacy.exists())try(InputStream in=new FileInputStream(legacy)){return install(in,()->false);}
        return load();
    }
}
