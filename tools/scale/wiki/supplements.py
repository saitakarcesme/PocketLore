"""Exact source ranges for templates, math context and recognized notice paragraphs.

This is storage extraction, not template expansion or rights clearance. Ambiguous
brace/tag structures fall back to the complete original wikitext.
"""
import re
TOKENS=re.compile(r'\{\{+|\}\}+')
PROTECTED=re.compile(r'<(math|chem|nowiki|pre|source|syntaxhighlight)\b[^>]*>.*?</\1\s*>',re.I|re.S)
PARAGRAPHS=re.compile(r'\S(?:.*?\S)?(?=\n\s*\n|\Z)',re.S)
NOTICE_WORDS=('copyright','attribut','public domain','public-domain','incorporat','cc-by','cc by','gfdl','permission','1911','dnb','danfs','nuttall','catholic encyclopedia','jewish encyclopedia','cia world factbook','cia factbook','usgs','taken from','adapted from','text from')
ORDINARY_CITATIONS={'cite web','cite book','cite journal','cite news','cite encyclopedia','citation','cite thesis','cite conference','cite report'}
BOILERPLATE={'short description','use dmy dates','use mdy dates','reflist','refbegin','refend','authority control','commons category','portal','main','see also','sfn','harv','harvnb','efn','notelist','clear','reflist-talk'}
NOTICE_PROSE=re.compile(r'this\s+(?:article|page)\s+(?:incorporates|contains|is\s+based)|(?:text|material|content)\s+(?:was\s+)?(?:incorporat|taken|adapted|copied|reproduced)|public[\s-]+domain|creative\s+commons|cc[\s-]*by|gfdl|used\s+with\s+permission|(?:copyright|attribution|permission)\s*(?:notice|permission|licen[cs]e|:|©|\(c\)|[0-9]|by\b)',re.I)
def extract(wiki,lean=False,has_math=False,preserve_empty_candidate=False):
    spans=[];stack=[];outer=None;templates=[]
    protected=list(PROTECTED.finditer(wiki));masked=PROTECTED.sub(lambda m:' '*len(m.group()),wiki)
    for token in TOKENS.finditer(masked):
        opening=token.group()[0]=='{';remaining=len(token.group());pos=token.start()
        while remaining>=2:
            if opening:
                width=3 if remaining==3 else 2
                if not stack:outer=pos
                stack.append((width,pos))
            else:
                if not stack or remaining<stack[-1][0]:return wiki,[[0,len(wiki)]],'complete_ambiguous_markup'
                width,start=stack.pop();templates.append((start,pos+width))
                if not stack:spans.append((outer,pos+width))
            pos+=width;remaining-=width
        if remaining and not opening:return wiki,[[0,len(wiki)]],'complete_ambiguous_markup'
    if stack:return wiki,[[0,len(wiki)]],'complete_ambiguous_markup'
    ignored=[];kept_math=False
    if lean:
        spans=[]
        for a,b in templates:
            raw=wiki[a:b];name=re.split(r'[|}\n]',raw[2:],maxsplit=1)[0].strip().replace('_',' ').casefold()
            notice_field=bool(re.search(r'\|\s*(?:copyright|permission|attribution|license)\s*=',raw,re.I))
            ordinary=name in ORDINARY_CITATIONS or name in BOILERPLATE or name.startswith(('infobox','taxobox','automatic taxobox','speciesbox')) or name.endswith('-stub')
            if ordinary and not notice_field:ignored.append((a,b))
            else:
                spans.append((a,b));kept_math=kept_math or bool(re.search(r'math|chem|frac|sqrt|convert|cvt|val|physconst|equation|formula',name))
    # A source math tag lacking a matched closing tag is never silently discarded.
    math_opens=len(re.findall(r'<(?:math|chem)\b',wiki,re.I))
    math_matched=sum(m.group(1).lower() in ('math','chem') for m in protected)
    if math_opens!=math_matched:return wiki,[[0,len(wiki)]],'complete_ambiguous_math'
    math_ranges=[(m.start(),m.end()) for m in protected if m.group(1).lower() in ('math','chem')]
    if lean and has_math and not math_ranges and not kept_math:
        return wiki,[[0,len(wiki)]],'complete_unresolved_math_source'
    notice_text=wiki
    if lean and ignored:
        merged_ignored=[]
        for a,b in sorted(ignored):
            if merged_ignored and a<=merged_ignored[-1][1]:merged_ignored[-1][1]=max(b,merged_ignored[-1][1])
            else:merged_ignored.append([a,b])
        parts=[];last=0
        for a,b in merged_ignored:parts.extend((wiki[last:a],' '*(b-a)));last=b
        parts.append(wiki[last:]);notice_text=''.join(parts)
    math_index=0
    for para in PARAGRAPHS.finditer(wiki):
        while math_index<len(math_ranges) and math_ranges[math_index][1]<=para.start():math_index+=1
        has_math=math_index<len(math_ranges) and math_ranges[math_index][0]<para.end()
        lower=para.group().lower()
        notice=bool(NOTICE_PROSE.search(notice_text[para.start():para.end()])) if lean else any(x in lower for x in NOTICE_WORDS)
        if notice or has_math:spans.append((para.start(),para.end()))
    if not spans and lean:
        if preserve_empty_candidate:return wiki,[[0,len(wiki)]],'complete_empty_notice_candidate_fallback'
        return '',[],'no_detected_supplement'
    if not spans:
        # A triggered supplement with no safely recognized ranges remains whole.
        return wiki,[[0,len(wiki)]],'complete_no_safe_ranges'
    merged=[]
    for a,b in sorted(spans):
        if merged and a<=merged[-1][1]:merged[-1][1]=max(b,merged[-1][1])
        else:merged.append([a,b])
    return '\n\n'.join(wiki[a:b] for a,b in merged),merged,'notice_math_unit_ranges' if lean else 'notice_math_template_ranges'
