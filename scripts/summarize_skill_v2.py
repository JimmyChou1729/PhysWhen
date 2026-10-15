"""Validate the added labels and report denominators separately from the initial study."""
import sys,collections
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from physstyle.common import *
from physstyle.annotations import validate_record,SEMANTIC

def summarize():
 root=Path('data/annotations_v2');tasks={w['window_id']:w for w in read_jsonl(root/'tasks.jsonl')};rows=read_jsonl(root/'labels_a.jsonl')+read_jsonl(root/'labels_b.jsonl');seen=set();split=read_json('data/splits/frozen.json')['assignments']
 changes=read_json(root/'adjudications.json',{}).get('updates',[])
 lookup={(r['window_id'],r['feature_id']):r for r in rows}
 for change in changes:
  key=(change['window_id'],change['feature_id'])
  if key not in lookup:raise ValueError('unknown adjudication')
  lookup[key].update(change['set']);lookup[key]['adjudicated']=True
 audited=set(read_json(root/'audit_selection.json',{}).get('window_ids',[])) if read_json('reports/skill_v2_semantic_audit.json',{}).get('completed_at') else set()
 for r in rows:
  if r['window_id'] in audited:r['audit_status']='agent_audited';r['audit_note']='Independent review with retained uncertainty; not a human gold standard.'
  validate_record(r,tasks);key=(r['window_id'],r['feature_id'])
  if key in seen:raise ValueError('duplicate label')
  seen.add(key)
  if split[r['paper_id']]!='discovery':raise ValueError('heldout leakage')
  w=tasks[r['window_id']];d=read_json(f'data/parsed/{w["paper_id"]}.json');ps={p['paragraph_id']:p for p in d['paragraphs']}
  if any(ps[p['paragraph_id']]!=p for p in w['context']):raise ValueError('stale context')
 if len(rows)!=len(tasks)*6:raise ValueError('incomplete semantic labels')
 out={'updated_at':now(),'annotation_method':'host_agent','human_gold_standard':False,'windows':len(tasks),'papers':len({w['paper_id'] for w in tasks.values()}),'formula_target_windows':sum(w['has_target_display'] for w in tasks.values()),'prose_target_windows':sum(not w['has_target_display'] for w in tasks.values()),'section_counts':dict(collections.Counter(w['section_role'] for w in tasks.values())),'features':{},'sampling':read_json(root/'sampling.json'),'initial_sample':{'windows':60,'papers':15,'formula_centered':True,'appendix_windows':1},'combined_inventory_only':{'windows':120,'papers':27,'labels':720},'warning':'Old formula-centered and new role-targeted samples are not pooled to estimate prevalence. Host labels are observations of textual organization, not proof of sound physics or human readability.'}
 for fid in SEMANTIC:
  rr=[r for r in rows if r['feature_id']==fid];by=collections.defaultdict(list)
  for r in rr:by[r['paper_id']].append(r)
  out['features'][fid]={'labels':dict(collections.Counter(r['label'] for r in rr)),'windows':len(rr),'papers':len(by),'label_papers':{label:len({r['paper_id'] for r in rr if r['label']==label}) for label in sorted({r['label'] for r in rr})},'applicable_yes_no_windows':sum(r['label'] in ('yes','no') for r in rr),'applicable_yes_no_papers':sum(any(r['label'] in ('yes','no') for r in rs) for rs in by.values()),'paper_yes_fraction':summary([sum(r['label']=='yes' for r in rs)/sum(r['label'] in ('yes','no') for r in rs) for rs in by.values() if any(r['label'] in ('yes','no') for r in rs)]) if fid!='S01' else None,'by_section':{role:dict(collections.Counter(r['label'] for r in rr if tasks[r['window_id']]['section_role']==role)) for role in sorted({w['section_role'] for w in tasks.values()})}}
 write_jsonl(root/'labels.jsonl',rows);write_json('reports/skill_v2_semantic_summary.json',out);return out
if __name__=='__main__':
 r=summarize();print({f:z['labels'] for f,z in r['features'].items()})
