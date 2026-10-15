"""Locate explicit host annotations; never infer semantic labels from lexical cues."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from physstyle.common import *
from physstyle.annotations import validate_record

def convert(suffix):
 root=Path('data/annotations_v2');ws=read_jsonl(root/f'tasks_{suffix}.jsonl');decisions=read_jsonl(root/f'decisions_{suffix}.jsonl');out=[];seen=set()
 for d in decisions:
  n=d['n']
  if type(n)is not int or n<0 or n>=len(ws) or n in seen:raise ValueError('invalid/duplicate window index')
  seen.add(n);w=ws[n]
  if len(d['answers'])!=6:raise ValueError('six explicit labels required')
  for i,answer in enumerate(d['answers'],1):
   label,quote,rationale=answer[:3];evidence=None
   for para in w['context']:
    if quote not in ''.join(b['raw'] for b in para['blocks']):continue
    spans=[sp for b in para['blocks'] for sp in b['source_spans']]
    for fn in sorted({sp['source_file'] for sp in spans}):
     a=min(sp['line_start'] for sp in spans if sp['source_file']==fn);z=max(sp['line_end'] for sp in spans if sp['source_file']==fn)
     region='\n'.join((Path(w['source_root'])/fn).read_text(errors='replace').splitlines()[a-1:z]);loc=region.find(quote)
     if loc>=0:
      line=a+region[:loc].count('\n');evidence={'source_file':fn,'line_start':line,'line_end':line+quote.count('\n'),'exact_quote':quote};break
    if evidence:break
   if not evidence:raise ValueError(f'{suffix}:{n}:S{i:02} exact quote missing: {quote}')
   if i in (2,3) and not w['has_target_display'] and label!='not_applicable':raise ValueError('prose target requires S02/S03 NA')
   r={**{k:w[k] for k in ['window_id','paper_id','version','split','target_block_id']},'feature_id':f'S{i:02}','label':label,'evidence':[evidence],'rationale':rationale,'context_sufficient':label!='uncertain','confidence':answer[3] if len(answer)>3 else 'medium','annotation_method':'host_agent','annotator_model':'unknown','annotator_batch':suffix,'annotated_at':now(),'audit_status':'not_audited','semantic_protocol_version':'semantic-v2-mixed-window','section_role':w['section_role'],'has_target_display':w['has_target_display']}
   if i==4:r['items']=[d.get('S04_item',{})]
   validate_record(r,{w['window_id']:w});out.append(r)
 if len(seen)!=len(ws):raise ValueError(f'incomplete: {len(seen)}/{len(ws)}')
 write_jsonl(root/f'labels_{suffix}.jsonl',out);return len(out)
if __name__=='__main__':print('validated records',convert(sys.argv[1]))
