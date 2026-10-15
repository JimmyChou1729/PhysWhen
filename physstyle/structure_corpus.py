"""Offline analysis of expanded corpus; preserve frozen210 profiles and old studies."""
import sys,collections
from pathlib import Path
from .common import *
from .features import freeze_split,measure,aggregate
from .structure import inventory

def analyze():
 with corpus_lock():
  rows=read_jsonl('data/manifests/corpus.jsonl');active=[r for r in rows if r.get('screening')=='include' and r.get('parse_status')=='usable'];docs={}
  for r in active:
   pid=r['paper_id'];d=read_json(f'data/parsed/{pid}.json');source=Path(f'data/raw/papers/{pid}v{r["version"]}/source.bin')
   if not d or not d['usable'] or d['version']!=r['version'] or d['source_sha256']!=r['source_sha256'] or digest(source.read_bytes())!=r['source_sha256']:raise ValueError('source/parse identity mismatch '+pid)
   if not r.get('version_identity_verified'):raise ValueError('version not verified '+pid)
   docs[pid]=d
  splits=freeze_split(rows,docs);old=read_json('reports/cohort210_snapshot/frozen.json')['assignments']
  ledger=read_json('data/splits/frozen.json')['assignments']
  if any(ledger.get(pid)!=s for pid,s in old.items()):raise ValueError('existing cohort split changed')
  measures=[];inv=[];index=[];dest=Path('data/features/structure500')
  for pid,d in docs.items():
   if d.get('split')!=splits[pid]:d['split']=splits[pid];write_json(f'data/parsed/{pid}.json',d)
   m=measure(d,read_json('configs/features.json'));write_json(dest/'papers'/f'{pid}.json',m);measures.append(m)
   item=inventory(d);write_json(dest/'navigation'/f'{pid}.json',item);inv.append(item)
   index.append({'paper_id':pid,'version':d['version'],'source_sha256':d['source_sha256'],'split':splits[pid],'feature_file':str(dest/'papers'/f'{pid}.json'),'navigation_file':str(dest/'navigation'/f'{pid}.json'),'parsed_file':f'data/parsed/{pid}.json','source_directory':d['source_root']})
  profiles=aggregate(measures,rows);profiles['cohort']='structure500';write_json(dest/'feature_profiles.json',profiles);write_jsonl(dest/'evidence_index.jsonl',index)
  sampling=read_json('data/manifests/structure_sampling.json',{});sampling_failures={key:value for key,value in sampling.items() if value.get('status')!='complete'}
  result={'project':'PhysWhen','generated_at':now(),'target':500,'papers_usable':len(active),'attempted':len(rows),'acquired_versions':sum(bool(r.get('version')) for r in rows),'scope_excluded_after_acquisition':sum(r.get('screening')!='include' and bool(r.get('version')) for r in rows),'category_counts':dict(collections.Counter(r['sampling_category'] for r in active)),'year_counts':dict(sorted(collections.Counter(r['sampling_year'] for r in active).items())),'split_counts':dict(collections.Counter(splits.values())),'source_versions_verified':len(docs),'candidates':len(read_jsonl('data/manifests/candidates.jsonl')),'scope_counts':dict(collections.Counter(r['screening'] for r in read_jsonl('data/manifests/candidates.jsonl'))),'failures':[{'paper_id':r['paper_id'],'status':r.get('parse_status'),'stage':r.get('failure_stage'),'reason':r.get('error',r.get('parser_warnings'))} for r in rows if r.get('parse_status')!='usable'],'automatic_navigation_papers':len(inv),'semantic_maps_file':'reports/structure_semantic_results.json','discovery_navigation':{'section_count':summary([len(x['sections']) for x in inv if x['split']=='discovery']),'largest_section_word_share':summary([max((s['word_share'] for s in x['sections']),default=None) for x in inv if x['split']=='discovery'])},'profile_file':str(dest/'feature_profiles.json'),'feature_definitions':'D01–D06 frozen; M01–M04 exploratory semantic protocol, navigation inventory only supports positioning','sampling_extension_status_counts':dict(collections.Counter(v.get('status','unknown') for v in sampling.values())),'sampling_extension_failures':sampling_failures,'sampling_limits':'Disjoint random contiguous metadata blocks per year/category; actual extension failures are recorded separately. Scope and parse selection bias; not iid representative sampling. Per-paper bootstrap is descriptive and ignores block/author dependence.','human_readability_improvement':'not_established','weight_training':'not_run','paid_model_calls':0,'previous_cohort':'reports/cohort210_snapshot'}
  write_json('reports/STRUCTURE_RESULTS.json',result)
  print({k:result[k] for k in ['papers_usable','attempted','category_counts','split_counts']})
  return result
