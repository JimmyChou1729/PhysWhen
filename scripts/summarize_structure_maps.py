"""Validate and summarize actual full-paper maps, independent of corpus downloading."""
import sys,collections
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from physstyle.common import *
from physstyle.structure import validate_map,map_descriptors
protocol=read_json('data/structure/protocol.json');records=[];descriptors=[];anchors=[]
for f in sorted(Path('data/structure/annotations').glob('*.json')):
 r=read_json(f);p=read_json('data/structure/papers/'+f.name);errors=validate_map(r,p,protocol)
 if errors:raise ValueError(f'{f}: {errors}')
 for filename,sha in p['source_files'].items():
  if digest((Path(p['source_root'])/filename).read_bytes())!=sha:raise ValueError('source file hash mismatch '+filename)
 d=map_descriptors(r,p);write_json('data/structure/features/'+f.name,d);records.append(r);descriptors.append(d)
 ps={x['paragraph_id']:x for x in p['paragraphs']}
 for n in r['nodes']:
  for o in n['occurrences']:
   anchors.append({'paper_id':r['paper_id'],'version':r['version'],'source_sha256':r['source_sha256'],'node_id':n['id'],'node_type':n['type'],**o,'source_spans':[s for b in ps[o['paragraph_id']]['blocks'] for s in b['source_spans']],'location_precision':'paragraph source container; exact_quote verified in comment-stripped raw paragraph; not a token-level line claim'})
write_jsonl('data/structure/source_anchors.jsonl',anchors)
qs=collections.Counter();et=collections.Counter();eb=collections.Counter();rr=collections.Counter();moves=collections.Counter();negative=[]
for r,d in zip(records,descriptors):
 qs.update(d['M01_question_status']);et.update(d['M02_edge_types']);eb.update(d['M02_edge_basis']);moves.update(m['role'] for m in r['moves']);rr.update(x['relation'] for x in r['recurrences'])
 negative.extend({'paper_id':r['paper_id'],**e} for e in d['M03_dependency_order'] if e['dependent_minus_prerequisite'] is not None and e['dependent_minus_prerequisite']<0)
result={'generated_at':now(),'protocol':protocol['version'],'papers_full_mainbody_read':len(records),'paper_ids':[r['paper_id'] for r in records],'main_paragraphs':sum(d['denominators']['main_body_paragraphs'] for d in descriptors),'main_prose_words':sum(d['denominators']['main_body_prose_words'] for d in descriptors),'selected_nodes':sum(len(r['nodes']) for r in records),'selected_edges':sum(len(r['edges']) for r in records),'question_status_counts':dict(qs),'edge_type_counts':dict(et),'edge_basis_counts':dict(eb),'move_span_counts':dict(moves),'selected_recurrence_pair_counts':dict(rr),'negative_dependency_order_edges':negative,'papers_with_claim_preview_and_development':sum(any(c['positions']['preview'] and c['positions']['development'] for c in d['M03_claim_staging']) for d in descriptors),'coverage':[{'paper_id':r['paper_id'],**r['coverage'],'quality_notes':r.get('quality_notes',[])} for r in records],'limits':['Host-agent interpretation, not human gold labels or scientific correctness verification.','Selected nodes/edges/recurrence pairs are not an exhaustive graph; counts cannot estimate whole-corpus prevalence.','All initial papers are discovery-only stratified feasible-length sample; no claim that all500 received semantic annotation.','Word positions ignore math tokens; source paragraph granularity can merge multiple functions.','Human readability effect is untested.']}
stages=[]
for sample_name in ['sample','additional_sample','supplement_sample']:
 sample=read_json(f'data/structure/{sample_name}.json')
 if not sample:continue
 chosen={p['paper_id'] for p in sample['papers']};done=[d for d in descriptors if d['paper_id'] in chosen]
 stages.append({'sample_file':f'data/structure/{sample_name}.json','selected_papers':len(chosen),'completed_papers':len(done),'main_body_paragraphs':sum(d['denominators']['main_body_paragraphs'] for d in done),'main_body_prose_words':sum(d['denominators']['main_body_prose_words'] for d in done),'selected_nodes':sum(d['denominators']['selected_nodes'] for d in done),'selected_edges':sum(d['denominators']['selected_edges'] for d in done)})
result['sampling_stages']=stages
result['annotation_manifest']=[{'path':str(path),'sha256':digest(path.read_bytes())} for path in sorted(Path('data/structure/annotations').glob('*.json'))]
write_json('reports/structure_semantic_results.json',result);print({k:result[k] for k in ['papers_full_mainbody_read','main_paragraphs','selected_nodes','selected_edges','edge_basis_counts']})
