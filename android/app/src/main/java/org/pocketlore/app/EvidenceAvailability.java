package org.pocketlore.app;

import java.util.Arrays;
import java.util.HashSet;
import java.util.Locale;
import java.util.Set;

/** Conservative capability admission for dated public reference packs, not factual entailment. */
public final class EvidenceAvailability {
    public enum Scope { REFERENCE, PERSONAL, CURRENT, PREDICTIVE }
    private EvidenceAvailability() {}
    public static Scope scope(String question) {
        Set<String> words=new HashSet<>(Arrays.asList(question.toLowerCase(Locale.ROOT).split("[^a-z]+")));
        if(intersects(words,"my","mine","our","ours"))return Scope.PERSONAL;
        if(intersects(words,"current","currently","latest","today","tonight","tomorrow","now","presently","live")
                || question.toLowerCase(Locale.ROOT).matches("(?s).*\\bthis\\s+(morning|afternoon|evening|week)\\b.*"))return Scope.CURRENT;
        if(intersects(words,"predict","prediction","forecast","upcoming")
                || words.contains("next")&&intersects(words,"will","when","date","hour","time"))return Scope.PREDICTIVE;
        return Scope.REFERENCE;
    }
    private static boolean intersects(Set<String> words,String... choices){for(String s:choices)if(words.contains(s))return true;return false;}
    public static String reason(Scope scope){switch(scope){
        case PERSONAL:return "Personal evidence unavailable: these public reference collections do not contain an authenticated record for you.";
        case CURRENT:return "Current-status evidence unavailable: these dated reference collections do not provide a live status or alert feed.";
        case PREDICTIVE:return "Predictive evidence unavailable: these reference collections do not provide a validated forecast for the requested future event.";
        default:return "Reference evidence may be selected; relevance and completeness require inspection.";
    }}
    // Function words affect quotation relevance only. They never approve a factual relationship.
    private static final Set<String> FUNCTION=new HashSet<>(Arrays.asList(
        "some","every","each","any","all","only","under","rather","then","there","also","most","more","much","many",
        "should","must","give","show","report","tell","provide","explain","compare","contrast"));
    static Set<String> terms(String text){Set<String> words=new HashSet<>();for(String word:ResearchEngine.rankTerms(text))if(!FUNCTION.contains(word))words.add(word);return words;}
    static boolean relevant(String question,ResearchEngine.Hit hit,double leading){
        Set<String> query=terms(question),body=terms(hit.passage.title+" "+hit.passage.text);
        int required=Math.min(2,query.size());body.retainAll(query);
        return required>0 && body.size()>=required && hit.score>0 && hit.score>=leading*0.25;
    }
}
