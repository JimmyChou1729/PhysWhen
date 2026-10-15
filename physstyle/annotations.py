import collections, random
from pathlib import Path
from .common import *
from .features import main_paragraphs
from .parse import strip_comments
SEMANTIC=('S01','S02','S03','S04','S05','S06')
LABELS={'yes','no','uncertain','not_applicable'}
ROLES={'motivation','setup_definition','derivation','interpretation','limitation','transition','mixed','uncertain'}
def windows(docs,target=60,min_papers=15,seed=1729):
    eligible=[d for d in docs if d['split']=='discovery'];random.Random(seed).shuffle(eligible);eligible=eligible[:min_papers]
    candidates={}
    for d in eligible:
        ps=main_paragraphs(d);items=[]
        for i,p in enumerate(ps):
            math=[b for b in p['blocks'] if b['kind']=='display_math']
            if not math:continue
            context=[q for q in ps[max(0,i-1):i+2] if q['section_id']==p['section_id']]
            items.append({'window_id':f'{d["paper_id"]}v{d["version"]}:{p["paragraph_id"]}','paper_id':d['paper_id'],'version':d['version'],'split':d['split'],'target_paragraph_id':p['paragraph_id'],'target_block_id':math[0]['block_id'],'section_role':p['section_role'],'context':context,'source_root':d['source_root'],'source_files':d['source_files'],'feature_definition_version':'frozen-v1','annotation_status':'pending'})
        random.Random(f'{seed}:{d["paper_id"]}').shuffle(items);candidates[d['paper_id']]=items
    out=[]
    while len(out)<target:
        added=False
        for pid,items in candidates.items():
            if items and len(out)<target:out.append(items.pop(0));added=True
        if not added:break
    write_jsonl('data/annotations/tasks.jsonl',out);return out

def validate_record(r,tasks):
    if r.get('window_id') not in tasks:raise ValueError('unknown window')
    w=tasks[r['window_id']]
    for field in ('paper_id','version','split','target_block_id'):
        if r.get(field)!=w[field]:raise ValueError('identity/target mismatch: '+field)
    if r.get('feature_id') not in SEMANTIC:raise ValueError('unknown semantic feature')
    if r.get('label') not in (ROLES if r['feature_id']=='S01' else LABELS):raise ValueError('invalid label')
    if r.get('confidence') not in ('high','medium','low'):raise ValueError('invalid confidence')
    if r.get('annotation_method') not in ('host_agent','api_model','human'):raise ValueError('invalid annotation method')
    if not isinstance(r.get('context_sufficient'),bool) or not r.get('rationale'):raise ValueError('missing context/rationale')
    if not r.get('evidence'):raise ValueError('evidence required even for negative/uncertain labels')
    spans=[s for p in w['context'] for b in p['blocks'] for s in b['source_spans']]
    allowed=[]
    for sp in sorted(spans,key=lambda x:(x['source_file'],x['line_start'],x['line_end'])):
        if allowed and allowed[-1]['source_file']==sp['source_file'] and sp['line_start']<=allowed[-1]['line_end']+1:allowed[-1]['line_end']=max(allowed[-1]['line_end'],sp['line_end'])
        else:allowed.append(dict(sp))
    for e in r['evidence']:
        q=e.get('exact_quote','');a=e.get('line_start',0);b=e.get('line_end',0);fn=e.get('source_file')
        if not q or a<1 or b<a:raise ValueError('bad evidence range')
        if not any(s['source_file']==fn and s['line_start']<=a<=b<=s['line_end'] for s in allowed):raise ValueError('evidence outside window')
        p=safe_child(w['source_root'],fn);raw=p.read_bytes()
        if digest(raw)!=w['source_files'].get(fn):raise ValueError('source changed')
        lines=raw.decode(errors='replace').splitlines();excerpt='\n'.join(lines[a-1:b])
        if q not in excerpt:raise ValueError('quote not exact in source range')
        if q not in strip_comments(excerpt):raise ValueError('quote exists only in a TeX comment')
        # The line span may contain adjacent source; also require actual target-context block text.
        if not any(q in ''.join(blk['raw'] for blk in para['blocks']) for para in w['context']):raise ValueError('quote not in context block')
    return r

def import_annotations(path):
    tasks={w['window_id']:w for w in read_jsonl('data/annotations/tasks.jsonl')};existing=read_jsonl('data/annotations/labels.jsonl');merged={(r['window_id'],r['feature_id']):r for r in existing};batch=read_jsonl(path);seen=set()
    for r in batch:
        validate_record(r,tasks);key=(r['window_id'],r['feature_id'])
        if key in seen:raise ValueError('duplicate annotation in batch')
        seen.add(key);merged[key]=r
    write_jsonl('data/annotations/labels.jsonl',list(merged.values()));return len(batch)

def summarize_annotations():
    labels=read_jsonl('data/annotations/labels.jsonl');tasks=read_jsonl('data/annotations/tasks.jsonl');out={}
    for feature in SEMANTIC:
        rs=[r for r in labels if r['feature_id']==feature and r.get('section_role')!='appendix'];by_paper=collections.defaultdict(list)
        for r in rs:by_paper[r['paper_id']].append(r)
        rates=[]
        for pid,rr in by_paper.items():
            denom=sum(r['label'] in ('yes','no') for r in rr);rates.append(sum(r['label']=='yes' for r in rr)/denom if denom else None)
        out[feature]={'status':'annotated' if rs else 'not_run','windows':len(rs),'papers':len(by_paper),'labels':dict(collections.Counter(r['label'] for r in rs)),'missing_windows':sum(w['section_role']!='appendix' for w in tasks)-len(rs),'appendix_windows_separate':sum(r['feature_id']==feature and r.get('section_role')=='appendix' for r in labels),'paper_yes_fraction':summary(rates) if feature!='S01' else None,'unit':'paper; yes/(yes+no); uncertain and NA excluded, reported separately','agent_audited':sum(r.get('audit_status')=='agent_audited' for r in rs),'human_audited':sum(r.get('audit_status')=='human_audited' for r in rs)}
    write_json('data/features/semantic_summary.json',out);return out
