import random, re, itertools, collections, difflib
from pathlib import Path
from .common import *
from .parse import sentences
BODY={'introduction','technical_body','discussion_conclusion','other'}
def main_paragraphs(doc):return [p for p in doc['paragraphs'] if p['section_role'] in BODY]
def ptext(p):return ' '.join(b.get('text','') for b in p['blocks'] if b['kind']=='prose')
def segments(p):
    out=[];cur=[]
    for b in p['blocks']:
        if b['kind']=='display_math':
            if cur:out.append({'kind':'prose','text':' '.join(x.get('text','') for x in cur),'blocks':cur});cur=[]
            out.append(b)
        elif b['kind']!='prose' or b.get('text','').strip():cur.append(b)
    if cur:out.append({'kind':'prose','text':' '.join(x.get('text','') for x in cur),'blocks':cur})
    return out

def measure(doc,lexicon):
    ps=main_paragraphs(doc);nwords=sum(p['word_count'] for p in ps);records=[];sentence_lengths=[];paragraph_lengths=[];refs=0;refp=0;math=0;adjbefore=[];adjafter=[];cues=collections.Counter();roles=collections.defaultdict(list)
    flattened=[]
    for p in ps:
        text=ptext(p);lens=[len(words(t)) for t in sentences(text)];sentence_lengths+=lens
        plen=p['word_count'];paragraph_lengths.append(plen if plen else None);roles[p['section_role']].append(plen if plen else None)
        records.append({'feature':'D01','paragraph_id':p['paragraph_id'],'section_role':p['section_role'],'lengths':lens,'sentences':sentences(text),'source_spans':[s for b in p['blocks'] for s in b['source_spans']],'mapping_type':'paragraph_container'})
        records.append({'feature':'D02','paragraph_id':p['paragraph_id'],'section_role':p['section_role'],'value':plen if plen else None,'missing_reason':None if plen else 'no_prose'})
        pr=0
        for b in p['blocks']:
            for ref in b.get('refs',[]):records.append({'feature':'D05','paragraph_id':p['paragraph_id'],**ref});refs+=1;pr+=1
            if b['kind']=='prose':
                # Printed numeric references only; these do not duplicate TeX reference markers.
                for m in re.finditer(r'\b(?:Eqs?\.|Secs?\.|Figs?\.|Table)\s*\(?\d+(?:\.\d+)*\)?',b['text']):
                    records.append({'feature':'D05','paragraph_id':p['paragraph_id'],'text':m[0],'source_spans':b['source_spans'],'mapping_type':'prose_block_container'});refs+=1;pr+=1
                for typ,phrases in lexicon['D06'].items():
                    for phrase in phrases:
                        for m in re.finditer(r'(?<!\w)'+re.escape(phrase)+r'(?!\w)',b['text'],re.I):
                            cues[typ]+=1;records.append({'feature':'D06','type':typ,'phrase':m[0],'paragraph_id':p['paragraph_id'],'source_spans':b['source_spans'],'mapping_type':'prose_block_container'})
        refp+=bool(pr)
        for b in segments(p):flattened.append((p,b))
    for j,(p,b) in enumerate(flattened):
        if b['kind']!='display_math':continue
        math+=1;v={}
        for side,k in [('before',j-1),('after',j+1)]:
            reason=None
            if k<0 or k>=len(flattened) or flattened[k][0]['section_id']!=p['section_id']:val=None;reason='section_boundary'
            elif flattened[k][1]['kind']=='display_math':val=0;reason='adjacent_math'
            else:
                ss=sentences(flattened[k][1]['text']);ss=ss[-2:] if side=='before' else ss[:2];val=len(words(' '.join(ss))) if ss else None
                if val is None:reason='no_parseable_prose'
            v[side]=val;v[side+'_missing_reason']=reason
            (adjbefore if side=='before' else adjafter).append(val)
        records.append({'feature':'D04','paragraph_id':p['paragraph_id'],'block_id':b['block_id'],'section_role':p['section_role'],'source_spans':b['source_spans'],**v})
    metrics={'D01_sentence_median':quantile(sentence_lengths,.5),'D01_sentence_iqr':quantile(sentence_lengths,.75)-quantile(sentence_lengths,.25) if sentence_lengths else None,'D01_sentence_p90':quantile(sentence_lengths,.9),'D02_paragraph_median':quantile([x for x in paragraph_lengths if x is not None],.5),'D03_display_per_1000_words':1000*math/nwords if nwords else None,'D04_before_median':quantile([x for x in adjbefore if x is not None],.5),'D04_after_median':quantile([x for x in adjafter if x is not None],.5),'D05_refs_per_1000_words':1000*refs/nwords if nwords else None,'D05_ref_paragraph_fraction':refp/len(ps) if ps else None}
    for t in lexicon['D06']:metrics['D06_'+t+'_per_1000_words']=1000*cues[t]/nwords if nwords else None
    return {'paper_id':doc['paper_id'],'version':doc['version'],'split':doc['split'],'metrics':metrics,'denominators':{'prose_words':nwords,'paragraphs':len(ps),'sentences':len(sentence_lengths),'display_blocks':math,'D04_before_applicable':len([x for x in adjbefore if x is not None]),'D04_after_applicable':len([x for x in adjafter if x is not None])},'by_role':{k:summary(v) for k,v in roles.items()},'records':records}

@corpus_transaction
def freeze_split(rows,docs,seed=1729):
    path=Path('data/splits/frozen.json');state=read_json(path,{'seed':seed,'assignments':{},'frozen_at':now(),'family_matches':[]});assign=state['assignments']
    usable=[r for r in rows if r['paper_id'] in docs and docs[r['paper_id']]['usable'] and r['screening']=='include']
    new=[r for r in usable if r['paper_id'] not in assign];random.Random(seed).shuffle(new)
    next_index=state.get('next_family_index',len(assign)-len(state['family_matches']))
    for i,r in enumerate(new):
        pid=r['paper_id'];family=None
        for q in usable:
            if q['paper_id']==pid or q['paper_id'] not in assign:continue
            t1=re.sub(r'\W','',r['title'].lower());t2=re.sub(r'\W','',q['title'].lower())
            same=docs[pid]['normalized_body_sha256']==docs[q['paper_id']]['normalized_body_sha256']
            if same or difflib.SequenceMatcher(None,t1,t2).ratio()>.97:
                family=q['paper_id'];state['family_matches'].append([pid,family]);break
        assign[pid]=assign[family] if family else ('heldout' if next_index%5==0 else 'discovery')
        if family is None:next_index+=1
    state['next_family_index']=next_index;state['cohort_size']=len(usable);write_json(path,state)
    authors=collections.defaultdict(set)
    for r in usable:
        for a in r['authors']:authors[a].add(assign[r['paper_id']])
    write_json('data/splits/author_overlap.json',{'authors_crossing_groups':sorted(a for a,s in authors.items() if len(s)>1),'method':'exact normalized API author strings; no identity disambiguation','near_duplicate_method':'exact normalized body hash or normalized title similarity >0.97; paraphrased body near-duplicates not fully detected'})
    return {r['paper_id']:assign[r['paper_id']] for r in usable}

def aggregate(measures,rows):
    discovery=[x for x in measures if x['split']=='discovery'];heldout=[x for x in measures if x['split']=='heldout'];lookup={r['paper_id']:r for r in rows}
    def agg(ms):
        keys=sorted({k for m in ms for k in m['metrics']});out={}
        for k in keys:
            v=[m['metrics'].get(k) for m in ms];z=summary(v);valid=[x for x in v if x is not None]
            if len(valid)>=5:
                rng=random.Random(1729);boots=[quantile(rng.choices(valid,k=len(valid)),.5) for _ in range(1000)];z['median_bootstrap_95']=[quantile(boots,.025),quantile(boots,.975)]
            else:z['median_bootstrap_95']=None
            z['support']='low' if len(valid)<5 else 'descriptive';out[k]=z
        return out
    strat={}
    for field in ('sampling_category','sampling_year'):
        for v in sorted({lookup[m['paper_id']][field] for m in discovery}):strat[f'{field}:{v}']=agg([m for m in discovery if lookup[m['paper_id']][field]==v])
    counts=collections.Counter(a for m in discovery for a in lookup[m['paper_id']]['authors']);freq=[a for a,n in counts.items() if n>=3]
    sensitivity=[m for m in discovery if not set(lookup[m['paper_id']]['authors'])&set(freq)]
    return {'feature_definition_version':'frozen-v1','statistical_unit':'paper; equal weight','discovery':agg(discovery),'heldout_frozen_check':agg(heldout),'strata_discovery':strat,'author_sensitivity':{'excluded_authors':freq,'remaining_papers':len(sensitivity),'summary':agg(sensitivity)},'new_exploratory_features':0,'readability_effect':'not_established'}
