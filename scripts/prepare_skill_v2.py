"""Freeze a broader discovery-only semantic sample without changing the initial study."""
import sys,random,collections
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from physstyle.common import *
from physstyle.features import main_paragraphs
root=Path('data/annotations_v2')
if (root/'tasks.jsonl').exists():raise SystemExit('v2 tasks already frozen; refusing to replace')
old={w['paper_id'] for w in read_jsonl('data/annotations/tasks.jsonl')};split=read_json('data/splits/frozen.json')['assignments'];rows=read_jsonl('data/manifests/corpus.jsonl');chosen=[];tasks=[]
for cat in ['gr-qc','astro-ph.CO','hep-th']:
 for lo,hi in [(2010,2012),(2013,2015),(2016,2018),(2019,2021)]:
  eligible=sorted([r for r in rows if r['screening']=='include' and r.get('parse_status')=='usable' and split.get(r['paper_id'])=='discovery' and r['paper_id'] not in old and r['sampling_category']==cat and lo<=r['sampling_year']<=hi],key=lambda r:r['paper_id'])
  random.Random(f'1729:v2:{cat}:{lo}').shuffle(eligible)
  for r in eligible:
   d=read_json(f'data/parsed/{r["paper_id"]}.json');ps=[p for p in main_paragraphs(d) if p['word_count']>=25]
   math=lambda p:any(b['kind']=='display_math' for b in p['blocks'])
   if len(ps)>=5 and sum(math(p) for p in ps)>=2:break
  else:raise ValueError('insufficient eligible papers '+cat+str(lo))
  rng=random.Random(f'1729:v2:{r["paper_id"]}');pool=ps[:];rng.shuffle(pool);selected=[]
  for predicate in [lambda p:p['section_role']=='introduction' and not math(p),lambda p:p['section_role']=='discussion_conclusion' and not math(p),lambda p:math(p),lambda p:math(p),lambda p:not math(p)]:
   hits=[p for p in pool if p not in selected and predicate(p)]
   if hits:selected.append(hits[0])
  selected+=(p for p in pool if p not in selected);selected=selected[:5]
  chosen.append({'paper_id':r['paper_id'],'sampling_category':cat,'sampling_year':r['sampling_year'],'version':d['version'],'source_sha256':d['source_sha256']})
  for p in selected:
   allps=main_paragraphs(d);i=allps.index(p);context=[q for q in allps[max(0,i-1):i+2] if q['section_id']==p['section_id']];target=next((b for b in p['blocks'] if b['kind']=='display_math'),next(b for b in p['blocks'] if b['kind']=='prose' and b['word_count']))
   tasks.append({'window_id':f'v2:{d["paper_id"]}v{d["version"]}:{p["paragraph_id"]}','paper_id':d['paper_id'],'version':d['version'],'split':'discovery','target_paragraph_id':p['paragraph_id'],'target_block_id':target['block_id'],'has_target_display':target['kind']=='display_math','section_role':p['section_role'],'context':context,'source_root':d['source_root'],'source_files':d['source_files'],'feature_definition_version':'frozen-v1','annotation_status':'pending'})
assert len(tasks)==60 and len(chosen)==12
write_jsonl(root/'tasks.jsonl',tasks)
for suffix,subset in [('a',tasks[:30]),('b',tasks[30:])]:write_jsonl(root/f'tasks_{suffix}.jsonl',subset)
protocol=read_json('configs/semantic_protocol.json');protocol.update(version='semantic-v2-mixed-window',frozen_at=now(),change_reason='Add prose-only windows for broader function coverage; S02/S03 are NA when target has no display. Keep initial protocol and labels unchanged.',sampling_warning='Purposive role quotas within12 category/year stratified discovery papers, five windows each; not a prevalence estimate or comparable pooled denominator with old formula-centered windows. Overlapping context permitted.',additional_requirements={'S02/S03':'No target display => not_applicable. For display targets retain prior before/after definitions.','S04':'Identify specific local item and timing; no global first-use inference.','S05':'Name the concrete reasoning transition and what textual support is present/missing. Mere connectives do not prove support.','S06':'Name principal claim and necessary/scope condition. Generic hedges do not count; no condition needed => NA.','S01':'Choose function of target paragraph only, not whole window.'})
write_json(root/'protocol.json',protocol);write_json(root/'sampling.json',{'frozen_at':now(),'seed':1729,'papers':chosen,'windows':60,'formula_targets':sum(w['has_target_display'] for w in tasks),'section_roles':dict(collections.Counter(w['section_role'] for w in tasks)),'selection':'one paper/category/yearband,5role-preferred targets; remaining slots fill shuffled eligible paragraphs; >=25prose words; excludes all initial semantic papers and all heldout','sampling_limits':protocol['sampling_warning']})
print(read_json(root/'sampling.json'))
