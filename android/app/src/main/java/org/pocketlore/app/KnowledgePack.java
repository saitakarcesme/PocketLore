package org.pocketlore.app;

import java.io.*;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.*;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import java.util.zip.*;
import org.json.*;

/** Bounded, verified pack ingestion. Hashes detect corruption, not publisher authenticity. */
public final class KnowledgePack {
    public static final int LIMIT = 16 * 1024 * 1024;
    public final ResearchEngine engine;
    public final String id, warning, sha256;
    final List<String[]> rows;
    final Map<String,String> provenance, documentKeys;
    final long archiveBytes, expandedBytes, manifestBytes;
    final int documentCount;
    KnowledgePack(ResearchEngine engine, String id, String warning, String hash, List<String[]> rows,
            Map<String,String> provenance, Map<String,String> documentKeys,long archiveBytes,long expandedBytes,long manifestBytes,int documentCount) {
        this.engine=engine; this.id=id; this.warning=warning; this.sha256=hash; this.rows=rows;
        this.provenance=provenance;this.documentKeys=documentKeys;this.archiveBytes=archiveBytes;
        this.expandedBytes=expandedBytes;this.manifestBytes=manifestBytes;this.documentCount=documentCount;
    }
    static String hash(byte[] bytes) throws Exception {
        StringBuilder s=new StringBuilder();
        for(byte b:MessageDigest.getInstance("SHA-256").digest(bytes)) s.append(String.format(Locale.ROOT,"%02x",b & 255));
        return s.toString();
    }
    private static byte[] bounded(InputStream in, int limit) throws IOException {
        ByteArrayOutputStream out=new ByteArrayOutputStream(); byte[] buffer=new byte[8192]; int n;
        while((n=in.read(buffer))!=-1) {
            if(Thread.currentThread().isInterrupted()) throw new InterruptedIOException("Pack import interrupted");
            if(out.size()+n>limit) throw new IOException("Pack exceeds size limit");
            out.write(buffer,0,n);
        }
        return out.toByteArray();
    }
    private static String utf8(byte[] b) throws CharacterCodingException {
        return StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
            .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(b)).toString();
    }
    private static String field(JSONObject o,String key) throws Exception {
        Object value=o.get(key);
        if(!(value instanceof String)) throw new IOException("Invalid metadata type: "+key);
        String s=(String)value;
        if(s.trim().isEmpty() || s.length()>2048 || s.matches("(?s).*[\\p{Cntrl}].*")) throw new IOException("Invalid metadata: "+key);
        return s;
    }
    private static void require(boolean ok,String why) throws IOException { if(!ok) throw new IOException(why); }
    public static KnowledgePack read(InputStream source) throws Exception {
        return read(source,true);
    }
    static KnowledgePack read(InputStream source,boolean index) throws Exception {
        byte[] archive=bounded(source,LIMIT); KnowledgePack personal=PersonalDocuments.decode(archive,index); if(personal!=null)return personal; Map<String,byte[]> files=new HashMap<>(); int total=0;
        try(ZipInputStream zip=new ZipInputStream(new ByteArrayInputStream(archive))) {
            ZipEntry entry;
            while((entry=zip.getNextEntry())!=null) {
                String name=entry.getName();
                require((name.equals("manifest.json") || name.equals("passages.tsv")) && !entry.isDirectory() && !files.containsKey(name),"Unexpected or duplicate ZIP entry");
                byte[] bytes=bounded(zip,Math.min(LIMIT-total,name.equals("manifest.json")?2*1024*1024:LIMIT));
                total+=bytes.length; files.put(name,bytes); zip.closeEntry();
            }
        }
        require(files.size()==2,"Missing pack entries");
        // ZipFile also requires an intact central directory; streaming ZIP alone accepts truncation.
        require(archive.length>=22,"Truncated ZIP");
        int end=archive.length-22;
        require(archive[end]==80 && archive[end+1]==75 && archive[end+2]==5 && archive[end+3]==6,
            "ZIP must end with a complete, comment-free directory");
        ByteBuffer directory=ByteBuffer.wrap(archive).order(ByteOrder.LITTLE_ENDIAN);
        require(directory.getShort(end+4)==0 && directory.getShort(end+6)==0
            && directory.getShort(end+8)==2 && directory.getShort(end+10)==2 && directory.getShort(end+20)==0,
            "Unsupported ZIP directory");
        int offset=directory.getInt(end+16), length=directory.getInt(end+12);
        require(offset>=0 && length>=0 && (long)offset+length==end,"Invalid ZIP directory bounds");
        Set<String> names=new HashSet<>();
        for(int i=0;i<2;i++) {
            require(offset<=end-46 && directory.getInt(offset)==0x02014b50,"Invalid ZIP directory entry");
            int nameLength=Short.toUnsignedInt(directory.getShort(offset+28));
            int extraLength=Short.toUnsignedInt(directory.getShort(offset+30));
            int commentLength=Short.toUnsignedInt(directory.getShort(offset+32));
            require((long)offset+46+nameLength+extraLength+commentLength<=end,"Truncated ZIP directory entry");
            String name=utf8(Arrays.copyOfRange(archive,offset+46,offset+46+nameLength));
            require(files.containsKey(name) && names.add(name),"ZIP directory name mismatch");
            CRC32 crc=new CRC32();crc.update(files.get(name));
            require(directory.getInt(offset+24)==files.get(name).length
                && Integer.toUnsignedLong(directory.getInt(offset+16))==crc.getValue(),"ZIP directory integrity mismatch");
            offset+=46+nameLength+extraLength+commentLength;
        }
        require(offset==end,"Unexpected ZIP directory data");
        JSONObject m=new JSONObject(utf8(files.get("manifest.json")));
        require(m.get("schema").equals(1) && field(m,"language").equals("en"),"Unsupported pack schema or language");
        String id=field(m,"id"), warning=field(m,"warning"); field(m,"transformation");
        require(id.matches("[a-z0-9-]{1,80}"),"Invalid pack ID");
        require(hash(files.get("passages.tsv")).equals(field(m,"passages_sha256")),"Passage payload hash mismatch");
        Map<String,String> provenance=new HashMap<>(),documentKeys=new HashMap<>();
        Map<String,String[]> expected=new HashMap<>(); Map<String,String[]> originalSpans=new HashMap<>(); Set<String> documentIds=new HashSet<>();
        JSONArray docs=m.getJSONArray("documents"); require(docs.length()>0 && docs.length()<=1000,"Document count out of range");
        for(int i=0;i<docs.length();i++) {
            JSONObject d=docs.getJSONObject(i);String did=field(d,"id");
            require(did.matches("[a-z0-9-]{1,64}") && documentIds.add(did),"Invalid or duplicate document ID");
            String title=field(d,"title"), url=field(d,"url"), date=field(d,"source_date")+"; retrieved "+field(d,"retrieved_date");
            require(url.startsWith("https://") && field(d,"license_url").startsWith("https://"),"Invalid provenance URL");
            require(field(d,"retrieved_date").matches("[0-9]{4}-[0-9]{2}-[0-9]{2}") && field(d,"raw_sha256").matches("[0-9a-f]{64}"),"Invalid source date or hash");
            require(field(d,"language").equals("en"),"Non-English document metadata");field(d,"category");
            String rights=field(d,"attribution")+"; "+field(d,"license")+"; "+field(d,"license_url");
            JSONArray passages=d.getJSONArray("passages");require(passages.length()>0,"Empty document");
            for(int j=0;j<passages.length();j++) {
                JSONObject p=passages.getJSONObject(j);String digest=field(p,"sha256"), citation=field(p,"id");
                require(digest.matches("[0-9a-f]{64}") && citation.equals(did+"-"+digest.substring(0,16)),"Invalid stable citation ID");
                provenance.put(citation,"Original citation: "+citation+"\nSource document ID: "+did+"\nSource SHA-256: "+field(d,"raw_sha256")+"\nPassage SHA-256: "+digest);
                if(p.has("source_utf16_start") || p.has("source_utf16_end")) {
                    long start=p.getLong("source_utf16_start"), finish=p.getLong("source_utf16_end");
                    require(start>=0 && finish>start && finish-start<=20000,"Invalid original source span");
                    String originalHash=field(p,"source_span_sha256");
                    require(originalHash.matches("[0-9a-f]{64}"),"Invalid original span hash");
                    originalSpans.put(citation,new String[]{Long.toString(finish-start),originalHash});
                    provenance.put(citation,provenance.get(citation)+"\n"+(d.has("source_text_format")?"Source text ("+field(d,"source_text_format")+")":"Original Markdown")+" UTF-16 range: ["+start+", "+finish+")\nOriginal span SHA-256: "+originalHash+"\n"+field(m,"transformation"));
                }
                if(d.has("license_text")) {
                    String legal=d.getString("license_text");
                    require(!legal.trim().isEmpty() && legal.length()<=24000,"Invalid offline license text");
                    provenance.put(citation,provenance.get(citation)+"\nRights basis: "+field(d,"rights_basis")+"\nRights limits: "+field(d,"rights_disposition")+"\nOffline license text:\n"+legal);
                }
                documentKeys.put(citation,url+"\n"+field(d,"raw_sha256"));
                require(expected.put(citation,new String[]{title,url,date,rights,digest})==null,"Duplicate citation");
                require(expected.size()<=20000,"Too many passages");
            }
        }
        String text=utf8(files.get("passages.tsv"));require(text.endsWith("\n"),"Truncated passage payload");
        String[] rows=text.split("\n",-1);require(m.get("passage_count") instanceof Integer,"Invalid passage count type");require(rows.length-1==m.getInt("passage_count") && expected.size()==rows.length-1,"Passage count mismatch");
        List<String[]> verifiedRows=new ArrayList<>();
        for(int i=0;i<rows.length-1;i++) {
            String[] r=rows[i].split("\t",-1); require(r.length==6,"Invalid passage row");String[] e=expected.remove(r[0]);require(e!=null,"Unknown or duplicate citation");
            for(int j=1;j<=4;j++) require(r[j].equals(e[j-1]),"Provenance does not match manifest");
            require(!r[5].trim().isEmpty() && r[5].length()<=20000 && !r[5].matches("(?s).*[\\p{Cntrl}].*"),"Invalid passage text");
            require(hash(r[5].getBytes(StandardCharsets.UTF_8)).equals(e[4]),"Passage hash mismatch");
            if(originalSpans.containsKey(r[0])) {
                String[] span=originalSpans.get(r[0]);String original=r[5].replace('\u2028','\n').replace('\u2409','\t');
                require(original.length()==Long.parseLong(span[0]) && hash(original.getBytes(StandardCharsets.UTF_8)).equals(span[1]),"Original Markdown span mismatch");
            }
            verifiedRows.add(r);
        }
        return new KnowledgePack(index?new ResearchEngine(new StringReader(text)):null,id,warning,hash(archive),verifiedRows,provenance,documentKeys,archive.length,total,files.get("manifest.json").length,docs.length());
    }
    public static KnowledgePack load(File file) throws Exception {
        try(InputStream in=new FileInputStream(file)){return read(in);}
    }
    /** Validation and index creation precede atomic replacement; failures preserve the old pack. */
    public static synchronized KnowledgePack install(InputStream in, File directory) throws Exception {
        return install(in,directory,()->false);
    }
    public static synchronized KnowledgePack install(InputStream in,File directory,java.util.function.BooleanSupplier cancelled)throws Exception {
        ResourceStorage.cleanupPackStages(directory);
        ResourceStorage.requireSpace(LIMIT,directory.getUsableSpace());
        File temporary=File.createTempFile("pack-", ".partial",directory);
        try {
            ResourceStorage.copy(in,temporary,LIMIT,cancelled);
            KnowledgePack pack=load(temporary);
            if(cancelled.getAsBoolean() || Thread.currentThread().isInterrupted())throw new InterruptedIOException("Pack import cancelled");
            Files.move(temporary.toPath(),new File(directory,"knowledge.plpack").toPath(),StandardCopyOption.ATOMIC_MOVE,StandardCopyOption.REPLACE_EXISTING);
            return pack;
        } finally {temporary.delete();}
    }
}
