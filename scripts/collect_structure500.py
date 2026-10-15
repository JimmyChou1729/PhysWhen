"""Bounded metadata extension and serial acquisition to the explicitly requested500 papers."""
import sys,time,random,collections,urllib.parse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from physstyle.common import *
from physstyle.network import Fetcher
from physstyle.corpus import atom,deduplicate,acquire,import_screening
from physstyle.parse import parse_tex
with corpus_lock():
 cfg=read_json('configs/structure500.json')
 if sum(r.get('screening')=='include' and r.get('parse_status')=='usable' for r in read_jsonl('data/manifests/corpus.jsonl'))>=cfg['target']:
  print('COLLECTION_ALREADY_COMPLETE',flush=True);raise SystemExit(0)
 fetch=Fetcher('data/raw/http',cfg['interval'],cfg['retries'],cfg['max_download_bytes'],cfg['max_raw_bytes']);started=time.time()
 original=read_json('data/manifests/sampling.json');extension_path=Path('data/manifests/structure_sampling.json');extension=read_json(extension_path,{})
 candidates_path=Path('data/manifests/candidates.jsonl');candidates=read_jsonl(candidates_path)
 strata=[(y,c) for y in cfg['years'] for c in cfg['categories']];random.Random(1729).shuffle(strata)
 for year,cat in strata:
  key=f'{year}:{cat}'
  if key in extension and extension[key].get('status')=='complete':continue
  old=original[key];total=old['total'];n=min(cfg['extension_per_stratum'],total);o=old['random_block_start'];end=o+old['returned']
  starts=[x for x in range(max(1,total-n+1)) if x+n<=o or x>=end]
  if not starts:extension[key]={'status':'complete','returned':0,'reason':'no disjoint block'};write_json(extension_path,extension);continue
  start=random.Random(f'1729:structure500:{key}').choice(starts)
  query=f'cat:{cat} AND submittedDate:[{year}01010000 TO {year}12312359]'
  url='https://export.arxiv.org/api/query?'+urllib.parse.urlencode({'search_query':query,'sortBy':'submittedDate','sortOrder':'ascending'})+f'&start={start}&max_results={n}'
  try:
   returned_total,batch=atom(fetch.get(url)[0])
  except Exception as e:
   extension[key]={'status':'failed','error':f'{type(e).__name__}: {e}','start':start};write_json(extension_path,extension);print('metadata failed',key,str(e),flush=True);continue
  for i,r in enumerate(batch):r.update(sampling_stratum=key,sampling_year=year,sampling_category=cat,stratum_rank=16+i,sampling_cohort='structure500_extension',screening='unresolved',screening_reason='pending actual title/abstract content review',training_eligible='unreviewed',redistribution_eligible='unreviewed')
  candidates=deduplicate(candidates+batch)
  if len(candidates)>cfg['candidate_cap']:raise ValueError('candidate cap exceeded')
  write_jsonl(candidates_path,candidates);extension[key]={'status':'complete','start':start,'returned':len(batch),'observed_total':returned_total,'initial_block':[o,end],'method':'second uniformly chosen disjoint contiguous block per stratum; seed1729; still clustered time sampling'};write_json(extension_path,extension);print('metadata added',key,'total',len(candidates),flush=True)
 # Frozen review lists exclude original rows; hash-bound screening imports cannot alter identity.
 new=[r for r in candidates if r.get('sampling_cohort')=='structure500_extension']
 # Append newly recovered strata to stable existing task batches on resume.
 batches={suffix:read_jsonl(f'data/manifests/structure_scope_batch_{suffix}.jsonl') for suffix in ['a','b','c']}
 assigned={r['paper_id'] for batch in batches.values() for r in batch}
 for row in new:
  if row['paper_id'] not in assigned:
   suffix=min(batches,key=lambda k:len(batches[k]));batches[suffix].append(row);assigned.add(row['paper_id'])
 for suffix,batch in batches.items():write_jsonl(f'data/manifests/structure_scope_batch_{suffix}.jsonl',batch)
 print('REVIEW_BATCHES_READY',len(new),flush=True)
 seen={}
 while True:
  for p in sorted(Path('data/manifests').glob('structure_scope_decisions_*.jsonl')):
   sha=digest(p.read_bytes())
   if seen.get(str(p))!=sha:import_screening(p);seen[str(p)]=sha
  rows=read_jsonl('data/manifests/corpus.jsonl');by={r['paper_id']:r for r in rows};good=[r for r in rows if r['screening']=='include' and r.get('parse_status')=='usable'];counts=collections.Counter(r['sampling_category'] for r in good)
  write_json('reports/structure500_progress.json',{'included':len(good),'target':500,'categories':dict(counts),'attempted':len(rows),'candidates':len(candidates),'updated_at':now(),'new_reviewed':sum(len(read_jsonl(p)) for p in Path('data/manifests').glob('structure_scope_decisions_*.jsonl'))})
  if len(good)>=cfg['target']:break
  options=[r for r in read_jsonl(candidates_path) if r['screening']=='include' and r['paper_id'] not in by]
  if not options:
   if time.time()-started>14400:print('bounded review wait exhausted',flush=True);break
   if sum(len(read_jsonl(p)) for p in Path('data/manifests').glob('structure_scope_decisions_*.jsonl'))>=len(new):print('reviewed candidate pool exhausted',flush=True);break
   time.sleep(10);continue
  weights={'gr-qc':.4,'astro-ph.CO':.3,'hep-th':.3};c=min(options,key=lambda r:(counts[r['sampling_category']]/weights[r['sampling_category']],r['stratum_rank'],r['sampling_year'],r['paper_id']))
  r=None;stage='acquire'
  try:
   r,p=acquire(fetch,c,cfg);stage='parse';d=parse_tex(p.read_bytes(),p.parent/'source');d.update(paper_id=r['paper_id'],version=r['version'],source_sha256=r['source_sha256']);r.update(parse_status='usable' if d['usable'] else 'low_prose',parser_warnings=d['warnings'],cohort='structure500_extension');write_json(f'data/parsed/{r["paper_id"]}.json',d);print('parsed',r['paper_id'],d['main_prose_words'],'included',len(good)+int(d['usable']),flush=True)
  except Exception as e:r={**(r or c),'parse_status':'failed','failure_stage':stage,'error':f'{type(e).__name__}: {e}','cohort':'structure500_extension'};print('failed',r['paper_id'],r['error'],flush=True)
  rows.append(r);write_jsonl('data/manifests/corpus.jsonl',rows)
 print('COLLECTION_FINISHED',flush=True)
