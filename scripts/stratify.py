import sys,collections,random
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from physstyle.common import *
from physstyle.features import measure,main_paragraphs
from physstyle.pipeline import load_docs
rows={r['paper_id']:r for r in read_jsonl('data/manifests/corpus.jsonl') if r['screening']=='include' and r['parse_status']=='usable'};docs=load_docs();dis=[d for pid,d in docs.items() if pid in rows and d['split']=='discovery'];lex=read_json('configs/features.json')
def summarize_papers(ms):
 keys=sorted({k for m in ms for k in m['metrics']});return {'papers':len(ms),'support':'low' if len(ms)<5 else 'descriptive_only','metrics':{k:summary([m['metrics'][k] for m in ms]) for k in keys}}
out={'unit':'paper, equal weight','year_bands':{},'section_roles':{},'semantic_by_role':{},'S01_paper_role_fractions':{},'S01_adjacent_target_transitions':[]}
for low,high in [(2010,2013),(2014,2017),(2018,2021)]:out['year_bands'][f'{low}-{high}']=summarize_papers([measure(d,lex) for d in dis if low<=rows[d['paper_id']]['sampling_year']<=high])
for role in ['introduction','technical_body','discussion_conclusion']:
 ms=[]
 for d in dis:
  ps=[p for p in d['paragraphs'] if p['section_role']==role]
  if ps:ms.append(measure({**d,'paragraphs':ps},lex))
 out['section_roles'][role]=summarize_papers(ms)
labels=read_jsonl('data/annotations/labels.jsonl');tasks={w['window_id']:w for w in read_jsonl('data/annotations/tasks.jsonl')}
for role in ['introduction','technical_body','appendix']:
 rr=[r for r in labels if tasks[r['window_id']]['section_role']==role];out['semantic_by_role'][role]={}
 for fid in ['S01','S02','S03','S04','S05','S06']:
  f=[r for r in rr if r['feature_id']==fid];out['semantic_by_role'][role][fid]={'windows':len(f),'papers':len({r['paper_id'] for r in f}),'counts':dict(collections.Counter(r['label'] for r in f)),'support':'low' if len({r['paper_id'] for r in f})<5 else 'descriptive_only'}
s01=[r for r in labels if r['feature_id']=='S01' and tasks[r['window_id']]['section_role']!='appendix'];byp=collections.defaultdict(list)
for r in s01:byp[r['paper_id']].append(r)
for label in sorted({r['label'] for r in s01}):out['S01_paper_role_fractions'][label]=summary([sum(r['label']==label for r in rr)/len(rr) for rr in byp.values()])
for pid,rr in byp.items():
 ordered=sorted(rr,key=lambda r:int(tasks[r['window_id']]['target_paragraph_id'][1:]))
 for a,b in zip(ordered,ordered[1:]):
  wa,wb=tasks[a['window_id']],tasks[b['window_id']];pa=next(p for p in wa['context'] if p['paragraph_id']==wa['target_paragraph_id']);pb=next(p for p in wb['context'] if p['paragraph_id']==wb['target_paragraph_id'])
  if int(pb['paragraph_id'][1:])==int(pa['paragraph_id'][1:])+1 and pa['section_id']==pb['section_id']:out['S01_adjacent_target_transitions'].append({'paper_id':pid,'from':wa['window_id'],'to':wb['window_id'],'roles':[a['label'],b['label']]})
out['transition_warning']='Only actually adjacent annotated target paragraphs; sparse selection cannot estimate full discourse sequences.'
write_json('data/features/stratified_summary.json',out)
print({k:v['papers'] for k,v in out['year_bands'].items()})
