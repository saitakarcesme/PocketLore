package org.pocketlore.app;
import java.nio.file.*;import java.util.*;
/** Native audit of unchanged historical claims in valid typed wrappers. Not new draft successes. */
public final class HistoryHarness {
 public static void main(String[] args)throws Exception{
  Path input=Path.of(args[0]),out=Path.of(args[2]);Files.createDirectories(out);long session=NativeRuntime.create();try{NativeRuntime.load(session,BindingHarness.b(args[1]));
   for(String row:Files.readAllLines(input.resolve("history.tsv"))){String[] f=row.split("\t");String id=f[0],question=ScaleHarness.decode(f[2]);BoundAnswer.Cancel cancel=new BoundAnswer.Cancel();BoundAnswer.Catalog catalog=BindingHarness.catalog(input,f[1],cancel);StringBuilder raw=new StringBuilder();
    for(String line:Files.readAllLines(input.resolve(id+".claims.tsv"))){String[] c=line.split("\t");List<String> refs=new ArrayList<>();for(String n:c[1].split(","))for(String label:catalog.spans.keySet())if(label.startsWith("P"+n+"."))refs.add(label);
     raw.append('O').append(c[0]).append('|').append(String.join(",",refs)).append('|').append(ScaleHarness.decode(c[2])).append('|').append(ScaleHarness.decode(c[3])).append('|').append(ScaleHarness.decode(c[4])).append('\n');}
    // The wrapper has no generated draft tokens; 1 is a parse-only non-truncation sentinel.
    BoundAnswer.Draft draft=BoundAnswer.parse(question,raw.toString(),catalog,1,cancel);BindingHarness.Stage audit=BindingHarness.generate(session,BoundAnswer.AUDIT_SYSTEM,BoundAnswer.auditPrompt(draft,cancel),192,out.resolve(id+".audit"));String failure=audit.failure.isEmpty()?BoundAnswer.auditFailure(draft,audit.raw,audit.tokens,cancel):audit.failure;
    String record="{\"id\":"+BindingHarness.q(id)+",\"wrapped_raw\":"+BindingHarness.q(raw.toString())+",\"claims\":"+BindingHarness.spans(draft)+",\"audit\":"+BindingHarness.json(audit)+",\"failure\":"+BindingHarness.q(failure)+",\"route\":"+BindingHarness.q(failure.isEmpty()?"SCREEN_ELIGIBLE":"WITHHELD")+"}\n";Files.writeString(out.resolve(id+".json"),record,StandardOpenOption.CREATE_NEW);System.out.println(id+" "+failure);System.out.flush();
   }
  }finally{NativeRuntime.close(session);}
 }
}
