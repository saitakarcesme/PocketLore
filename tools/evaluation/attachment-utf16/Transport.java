import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
public final class Transport {
    static native String convert(byte[] input, int mode) throws java.io.IOException;
    static String hex(byte[] b) { return HexFormat.of().formatHex(b); }
    static String units(String s) { StringJoiner j=new StringJoiner(","); for(char c:s.toCharArray()) j.add(Integer.toString(c)); return j.toString(); }
    static void require(boolean b) { if(!b) throw new AssertionError("Transport mismatch"); }
    static void positive() throws Exception { require(convert(new byte[]{65,(byte)0xf0,(byte)0x9f,(byte)0x98,(byte)0x80},0).equals("A\ud83d\ude00")); }
    static void refusal(String name, byte[] bytes, int mode, Class<?> type) throws Exception {
        positive(); boolean refused=false;
        try { convert(bytes,mode); } catch(Exception e) { require(e.getClass()==type); if(mode==5)require(e.getMessage().equals("original pending exception")); refused=true; }
        require(refused); positive();
        System.out.println("REFUSE\t"+name+"\t"+type.getName());
    }
    public static void main(String[] args) throws Exception {
        System.load(Path.of(args[0]).toAbsolutePath().toString());
        for(int round=0;round<3;round++) {
            for(String row:Files.readAllLines(Path.of(args[1]),StandardCharsets.UTF_8)) {
                String[] f=row.split("\t",-1);byte[] b=HexFormat.of().parseHex(f[1]);
                if(f[2].equals("INVALID")) {refusal(f[0],b,0,java.io.IOException.class);continue;}
                String prior=convert(b,0);require(units(prior).equals(f[2]));require(Arrays.equals(prior.getBytes(StandardCharsets.UTF_8),b));
                if(!f[0].equals("nul"))require(convert(b,1).equals(prior));
                refusal("invalid-after-"+f[0],new byte[]{(byte)0xff},0,java.io.IOException.class);
                require(units(prior).equals(f[2]));
                System.out.println("VALID\t"+f[0]+"\t"+units(prior)+"\t"+hex(prior.getBytes(StandardCharsets.UTF_8)));
            }
            byte[] edge=new byte[65536];Arrays.fill(edge,(byte)'x');
            require(convert(edge,0).length()==65536);require(convert(edge,1).length()==65536);
            System.out.println("BOUNDARY\t65536\t65536");
            refusal("oversize",new byte[65537],0,java.io.IOException.class);
            refusal("missing-terminator",edge,2,java.io.IOException.class);
            refusal("null-producer",new byte[0],3,java.io.IOException.class);
            refusal("cancel",edge,4,java.io.IOException.class);
            refusal("pending-exception",new byte[0],5,IllegalStateException.class);
        }
        System.out.println("COMPLETE\t3");
    }
}
