package org.pocketlore.app;
import java.nio.file.*;import java.util.*;
public final class FrameDraftHarness {
 public static void main(String[] args)throws Exception{
  Path input=Path.of(args[0]),out=Path.of(args[2]);Files.createDirectories(out);long session=NativeRuntime.create(),start=System.nanoTime();
  try{NativeRuntime.load(session,BindingHarness.b(args[1]));Files.writeString(out.resolve("load.json"),"{\"identity\":"+BindingHarness.q(NativeRuntime.identity())+",\"load_ms\":"+(System.nanoTime()-start)/1e6+"}",StandardOpenOption.CREATE_NEW);
   for(String row:Files.readAllLines(input.resolve("cases.tsv"))){String[] c=row.split("\t");String id=c[0],question=BindingHarness.decode(c[1]);BoundAnswer.Cancel cancel=new BoundAnswer.Cancel();BoundAnswer.Catalog catalog=BindingHarness.catalog(input,id,cancel);Files.writeString(out.resolve("active-case.txt"),id);
    BindingHarness.Stage draft=BindingHarness.generate(session,BoundAnswer.DRAFT_SYSTEM,BoundAnswer.prompt(question,catalog,cancel),320,out.resolve(id+".draft"));
    String result="{\"id\":"+BindingHarness.q(id)+",\"question\":"+BindingHarness.q(question)+",\"draft\":"+BindingHarness.json(draft)+",\"native_after\":"+Arrays.toString(NativeRuntime.resourceState())+"}\n";
    Files.writeString(out.resolve(id+".json"),result,StandardOpenOption.CREATE_NEW);System.out.println(id+" "+draft.tokens+" "+draft.failure);System.out.flush();
   }
  }finally{NativeRuntime.close(session);Files.writeString(out.resolve("closed.json"),Arrays.toString(NativeRuntime.resourceState()));}
 }
}
