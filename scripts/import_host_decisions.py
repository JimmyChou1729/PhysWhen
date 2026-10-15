"""Convert explicit host-agent decisions into fully located, validated annotations.
No labels are inferred by this helper. Quotes must match raw source and the frozen window.
"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from physstyle.common import *
from physstyle.annotations import import_annotations
ws=read_jsonl('data/annotations/tasks.jsonl');out=[]
for decision in read_jsonl(sys.argv[1]):
 w=ws[decision['n']]
 for i,answer in enumerate(decision['answers'],1):
  label,quote,rationale=answer[:3];evidence=None
  for p in w['context']:
   for b in p['blocks']:
    if quote not in b['raw']:continue
    for sp in b['source_spans']:
     lines=(Path(w['source_root'])/sp['source_file']).read_text(errors='replace').splitlines()
     region='\n'.join(lines[sp['line_start']-1:sp['line_end']]);loc=region.find(quote)
     if loc<0:continue
     a=sp['line_start']+region[:loc].count('\n');z=a+quote.count('\n');evidence={'source_file':sp['source_file'],'line_start':a,'line_end':z,'exact_quote':quote};break
    if evidence:break
   if evidence:break
  if evidence is None:
   for para in w['context']:
    if quote not in ''.join(b['raw'] for b in para['blocks']):continue
    spans=[sp for b in para['blocks'] for sp in b['source_spans']]
    for fn in sorted({sp['source_file'] for sp in spans}):
     a=min(sp['line_start'] for sp in spans if sp['source_file']==fn);z=max(sp['line_end'] for sp in spans if sp['source_file']==fn)
     lines=(Path(w['source_root'])/fn).read_text(errors='replace').splitlines();region='\n'.join(lines[a-1:z]);loc=region.find(quote)
     if loc>=0:
      start=a+region[:loc].count('\n');evidence={'source_file':fn,'line_start':start,'line_end':start+quote.count('\n'),'exact_quote':quote};break
    if evidence:break
  if evidence is None:raise ValueError(f'quote missing window {decision["n"]} S{i}: {quote}')
  out.append({**{k:w[k] for k in ('paper_id','version','split','window_id','target_block_id')},'feature_id':f'S{i:02}','label':label,'evidence':[evidence],'context_sufficient':label!='uncertain','confidence':answer[3] if len(answer)>3 else 'medium','rationale':rationale,'annotation_method':'host_agent','annotator_model':'unknown','annotated_at':now(),'audit_status':'not_audited','scope':'target paragraph and same-section immediate neighbors only; S04 limited to explicitly identified items, not all symbols','checked_paragraph_ids':[p['paragraph_id'] for p in w['context']]})
for record in out:
 if record['feature_id']=='S04':
  decision=next(d for d in read_jsonl(sys.argv[1]) if ws[d['n']]['window_id']==record['window_id'])
  item=decision.get('S04_item',{}).copy();item['definition_evidence']=record['evidence'];record['items']=[item];record['scope']='one explicit local item in full window; not exhaustive symbol coverage; global novelty unverified'
 record['semantic_protocol_version']='semantic-v1.1'
 record['section_role']=tasks_role=next(w['section_role'] for w in ws if w['window_id']==record['window_id'])
previous={(r['window_id'],r['feature_id']):r for r in read_jsonl('data/annotations/labels.jsonl')}
for r in out:
 old=previous.get((r['window_id'],r['feature_id']),{})
 if old.get('audit_status')=='agent_audited':r['audit_status']='agent_audited';r['audit_note']=old.get('audit_note')
 if old.get('annotated_at'):r['annotated_at']=old['annotated_at']
write_jsonl('data/annotations/host_batch.jsonl',out);print({'records_imported':import_annotations('data/annotations/host_batch.jsonl')})
