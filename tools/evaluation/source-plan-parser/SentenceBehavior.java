package org.pocketlore.app;
import java.util.*;
public final class SentenceBehavior {
 static int checks;static void reject(Runnable r){try{r.run();}catch(IllegalArgumentException|IllegalStateException e){checks++;return;}throw new AssertionError("Unexpected sentence-plan approval");}
 public static void main(String[] a){BoundAnswer.Cancel cancel=new BoundAnswer.Cancel();BoundAnswer.Catalog c=FrameBehavior.catalog("New topic","Zorps require sorted inputs. When the interval is empty, no target remains.");SentenceEvidence e=new SentenceEvidence(c,cancel);if(e.sentences.size()!=c.spans.size()||!FactFrames.sources(c,cancel).isEmpty())throw new AssertionError("Unknown source sentences lost");checks++;
  if(!e.select("S1",cancel).get(0).text().equals("Zorps require sorted inputs."))throw new AssertionError("Source text changed");checks++;
  for(String ids:Arrays.asList("F1","P1.1","S0","S99","S1,S1","","S1,"))reject(()->e.select(ids,cancel));
  BoundAnswer.Cancel stopped=new BoundAnswer.Cancel();stopped.cancel();reject(()->new SentenceEvidence(c,stopped));reject(()->e.select("S1",stopped));e.select("S1",new BoundAnswer.Cancel());checks++;
  System.out.println("Sentence plan checks: "+checks);
 }
}
