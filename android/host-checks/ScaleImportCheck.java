package org.pocketlore.app;
import java.io.*;
import java.nio.file.*;
import java.util.*;
public final class ScaleImportCheck {
    static int checks;
    static void check(boolean ok){if(!ok)throw new AssertionError();checks++;}
    interface Attempt { void run() throws Exception; }
    static void rejected(Attempt a)throws Exception{try{a.run();throw new AssertionError("Accepted invalid input");}catch(IOException expected){checks++;}}
    public static void main(String[] args)throws Exception {
        File dir=Files.createTempDirectory("scale-import-").toFile(),stage=new File(dir,"model.partial");
        byte[] good="GGUFfixture".getBytes(java.nio.charset.StandardCharsets.UTF_8);
        long space=ResourceStorage.RESERVE_BYTES+good.length;
        String hash=ModelImport.copy(new ByteArrayInputStream(good),stage,good.length,space,()->false);
        check(hash.equals("006770b014ffd382cd06d5148bb662d33f0b7448a316d85bfd415356b5f2aef1"));
        rejected(()->ModelImport.copy(new ByteArrayInputStream(good),stage,-1,space,()->false));
        rejected(()->ModelImport.copy(new ByteArrayInputStream(good),stage,ModelImport.MAX_BYTES+1,Long.MAX_VALUE,()->false));
        rejected(()->ModelImport.copy(new ByteArrayInputStream(good),stage,good.length,space-1,()->false));
        rejected(()->ModelImport.copy(new ByteArrayInputStream(good),stage,good.length+1,space+1,()->false));check(!stage.exists());
        rejected(()->ModelImport.copy(new ByteArrayInputStream(good),stage,good.length,space,()->true));check(!stage.exists());
        rejected(()->ModelImport.copy(new ByteArrayInputStream("BAD!".getBytes()),stage,4,space,()->false));check(!stage.exists());
        ImportRecovery.begin(dir,"model");check(ImportRecovery.pending(dir,"model"));
        Files.write(stage.toPath(),good);File saved=new File(dir,"model.gguf");Files.write(saved.toPath(),good);
        check(ResourceStorage.cleanupModelStage(dir)==1);check(saved.exists());check(ImportRecovery.pending(dir,"model"));
        ImportRecovery.finish(dir,"model");ImportRecovery.finish(dir,"model");check(!ImportRecovery.pending(dir,"model"));
        rejected(()->ResourceStorage.requireSpace(Long.MAX_VALUE,Long.MAX_VALUE));
        System.out.println("PASS "+checks+" host import/recovery assertions; no device acceptance");
    }
}
