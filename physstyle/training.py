import random,re
from pathlib import Path
from .common import *
from .parse import group,arguments,strip_comments
# Controlled masking never alters math, numbers, named entities or scientific predicates.
SAFE_NOISE={'the','a','an'}
def denoise(paragraph,seed):
    rng=random.Random(seed);inputs=[];targets=[];ops=[]
    for b in paragraph['blocks']:
        raw=strip_comments(b['raw']).replace('\u2060',' ');targets.append(raw)
        if b['kind']!='prose':inputs.append(raw);continue
        hits=[m for m in re.finditer(r'\b(?:the|a|an)\b',raw) if m[0] in SAFE_NOISE]
        protected=[]
        for command in re.finditer(r'\\[A-Za-z]+\*?',raw):
            end=command.end()
            while True:
                k=end
                while k<len(raw) and raw[k].isspace():k+=1
                if k<len(raw) and raw[k] in '{[':
                    _,end=group(raw,k,raw[k],'}' if raw[k]=='{' else ']')
                else:break
            protected.append((command.start(),end))
        protected.extend((m.start(),m.end()) for m in re.finditer(r'(?<!\\)%[^\n]*',raw))
        chosen=[m for m in hits if not any(a<=m.start()<z for a,z in protected) and rng.random()<.15]
        text=raw
        for m in reversed(chosen):text=text[:m.start()]+'<MASK>'+text[m.end():]
        inputs.append(text)
        ops.extend({'block_id':b['block_id'],'start':m.start(),'end':m.end(),'operation':'mask_article','original':m[0]} for m in chosen)
    return ''.join(inputs),''.join(targets),ops

def export_training(rows,docs,seed=1729):
    lm=[];dn=[];skips=[];eligible=[]
    reviews={r['paper_id']:r for r in read_jsonl('data/manifests/license_reviews.jsonl')}
    for r in rows:
        pid=r['paper_id'];d=docs.get(pid);review=reviews.get(pid,{})
        if not d or d.get('split')!='discovery' or r.get('screening')!='include' or not d.get('usable'):skips.append({'paper_id':pid,'reason':'not_discovery'});continue
        if r.get('training_eligible')!='yes' or review.get('training_eligible')!='yes' or review.get('version')!=r.get('version') or not review.get('review_basis') or review.get('license_url')!=r.get('license_url'):
            skips.append({'paper_id':pid,'reason':'license_not_verified_for_training'});continue
        if d.get('paper_id')!=pid or d.get('version')!=r.get('version') or d.get('source_sha256')!=r.get('source_sha256'):
            raise ValueError('training manifest/document provenance mismatch: '+pid)
        frozen=read_json('data/splits/frozen.json',{}).get('assignments',{})
        if frozen.get(pid)!='discovery':raise ValueError('training split not frozen discovery: '+pid)
        eligible.append(pid)
        for p in d['paragraphs']:
            if p['section_role'] not in ('introduction','technical_body','discussion_conclusion','other'):continue
            base={'paper_id':pid,'version':r['version'],'split':'discovery','source_span':[s for b in p['blocks'] for s in b['source_spans']],'license':r['license_url'],'training_eligibility':'yes','license_review':review,'paragraph_id':p['paragraph_id'],'section':p['section_title'],'section_id':p['section_id'],'prose_word_count':p['word_count'],'normalization':'TeX comments removed; ordered raw blocks otherwise preserved; no TeX execution','source_url':r['source_url'],'source_sha256':r['source_sha256']}
            inp,target,ops=denoise(p,f'{seed}:{pid}:{p["paragraph_id"]}')
            lm.append({**base,'text':target});dn.append({**base,'input':inp,'target':target,'seed':seed,'noise_operations':ops,'protected_policy':'Only lowercase English articles in prose; raw math and all other bytes unchanged.'})
    write_jsonl('data/training_exports/lm_corpus.jsonl',lm);write_jsonl('data/training_exports/denoise.jsonl',dn);write_jsonl('data/training_exports/skipped.jsonl',skips)
    result={'eligible_papers':len(eligible),'records_lm':len(lm),'records_denoise':len(dn),'english_words':sum(x['prose_word_count'] for x in lm),'tokenizer':'none; English regex words in parsed prose only, excluding math and TeX commands; NOT tokens','weight_training_status':'not_run','skipped':len(skips)}
    write_json('data/training_exports/status.json',result);return result
