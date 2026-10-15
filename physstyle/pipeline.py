import collections, json, platform, shutil, traceback
from pathlib import Path
from .common import *
from .network import Fetcher
from .corpus import discover, acquire
from .parse import parse_tex
from .features import freeze_split,measure,aggregate
from .annotations import windows,summarize_annotations
from .training import export_training

def load_docs():return {p.stem:read_json(p) for p in Path('data/parsed').glob('*.json')}
@corpus_transaction
def run(cfg,offline=False):
    if Path('reports/cohort210_snapshot/corpus.jsonl').exists():
        if not offline:raise ValueError('Use scripts/collect_structure500.py for bounded expanded-corpus acquisition.')
        from .structure_corpus import analyze as analyze_structure
        return analyze_structure()
    fetch=Fetcher('data/raw/http',cfg['interval'],cfg['retries'],cfg['max_download_bytes'],cfg['max_raw_bytes'],offline)
    candidates=read_jsonl('data/manifests/candidates.jsonl')
    if not candidates and not offline:candidates=discover(fetch,cfg)
    rows=read_jsonl('data/manifests/corpus.jsonl');byid={r['paper_id']:r for r in rows}
    ordered=sorted(enumerate(candidates),key=lambda ir:(ir[1]['stratum_rank'],ir[0]))
    for _,c in ordered:
        if sum(r.get('parse_status')=='usable' and r.get('screening')=='include' for r in byid.values())>=cfg['target']:break
        if c['screening']!='include' or byid.get(c['paper_id'],{}).get('parse_status')=='usable':continue
        if offline:continue
        r=None;stage='acquire'
        try:
            r,p=acquire(fetch,c,cfg);stage='parse';d=parse_tex(p.read_bytes(),p.parent/'source');d.update(paper_id=r['paper_id'],version=r['version'],source_sha256=r['source_sha256']);r['parse_status']='usable' if d['usable'] else 'low_prose';r['parser_warnings']=d['warnings'];write_json('data/parsed/'+r['paper_id']+'.json',d)
            print('parsed',r['paper_id'],r['version'],d['main_prose_words'],flush=True)
        except Exception as e:
            r={**(r or c),'parse_status':'failed','failure_stage':stage,'error':f'{type(e).__name__}: {e}'};print('failed',r['paper_id'],r['error'],flush=True)
        byid[c['paper_id']]=r;write_jsonl('data/manifests/corpus.jsonl',list(byid.values()))
    # Rebuild derived parses from verified local source, including offline recovery.
    for r in byid.values():
        if r.get('parse_status')!='usable':continue
        p=Path('data/raw/papers')/f'{r["paper_id"]}v{r["version"]}'/'source.bin'
        if not p.exists():raise ValueError('missing local source: '+str(p))
        if digest(p.read_bytes())!=r['source_sha256']:raise ValueError('raw source digest mismatch')
        d=parse_tex(p.read_bytes(),p.parent/'source');d.update(paper_id=r['paper_id'],version=r['version'],source_sha256=r['source_sha256']);write_json('data/parsed/'+r['paper_id']+'.json',d)
    return analyze(cfg)

@corpus_transaction
def analyze(cfg):
    from .pilot import enlarged_corpus,analyze_pilot
    if enlarged_corpus():return analyze_pilot()
    rows=read_jsonl('data/manifests/corpus.jsonl');docs=load_docs();split=freeze_split(rows,docs,cfg['seed']);measures=[]
    for r in rows:
        pid=r['paper_id']
        if pid not in split or pid not in docs:continue
        d=docs[pid];d['split']=split[pid];write_json('data/parsed/'+pid+'.json',d);m=measure(d,read_json('configs/features.json'));measures.append(m);write_json('data/features/'+pid+'.json',m)
    for w in read_jsonl('data/annotations/tasks.jsonl'):
        d=docs.get(w['paper_id'])
        if not d or split.get(w['paper_id'])!=w['split'] or d['version']!=w['version']:raise ValueError('annotation corpus identity/split is stale')
        expected={p['paragraph_id']:p for p in d['paragraphs']}
        for p in w['context']:
            if expected.get(p['paragraph_id'])!=p:raise ValueError('annotation context is stale after parser change; explicit re-export/audit required')
    profiles=aggregate(measures,rows);write_json('data/features/feature_profiles.json',profiles)
    if not read_jsonl('data/annotations/tasks.jsonl'):windows([d for d in docs.values() if 'split' in d],cfg['semantic_windows'],cfg['semantic_papers'],cfg['seed'])
    sem=summarize_annotations();train=export_training(rows,docs,cfg['seed'])
    result={'task_id':'TPW-001','project':'PhysWhen','code_status':'partial','papers_candidate':len(read_jsonl('data/manifests/candidates.jsonl')),'papers_included':sum(r['screening']=='include' and r.get('parse_status')=='usable' for r in rows),'papers_parsed_usable':len(measures),'selected_versions_verified':sum(bool(r.get('version_date')) for r in rows),'split_counts':dict(collections.Counter(split.values())),'semantic_windows_completed':len({r['window_id'] for r in read_jsonl('data/annotations/labels.jsonl') if all(any(q['window_id']==r['window_id'] and q['feature_id']==s for q in read_jsonl('data/annotations/labels.jsonl')) for s in ['S01','S02','S03','S04','S05','S06'])}),'semantic_windows_agent_audited':len({r['window_id'] for r in read_jsonl('data/annotations/labels.jsonl') if r.get('audit_status')=='agent_audited'}),'features_status':{**{f'D{i:02}':'implemented_computed' if measures else 'implemented_no_data' for i in range(1,7)},**{k:v['status'] for k,v in sem.items()}},'generation_cases_completed':0,'evaluation_status':'not_run','human_readability_improvement':'not_established','weight_training_status':'not_run','training_eligible_papers':train['eligible_papers'],'blockers':[],'reproduce_commands':['python3 -m physstyle doctor','python3 -m unittest discover -s tests -v','python3 -m physstyle run --config configs/smoke.json --offline','python3 -m physstyle export-training --config configs/smoke.json']}
    write_json('reports/RESULTS.json',result)
    from .report import finalize_results
    return finalize_results()
