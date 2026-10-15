"""Bounded serial pilot acquisition; incrementally consume independently reviewed scope decisions."""
import sys,time,collections
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from physstyle.common import *
from physstyle.corpus import acquire,import_screening
from physstyle.network import Fetcher
from physstyle.parse import parse_tex
with corpus_lock():
 cfg=read_json('configs/pilot.json');f=Fetcher('data/raw/http',cfg['interval'],cfg['retries']);started=time.time();seen_decisions={}
 while True:
  for suffix in ['a','b']:
   p=Path(f'data/manifests/review_decisions_{suffix}.jsonl')
   if p.exists() and seen_decisions.get(suffix)!=digest(p.read_bytes()):
    import_screening(p);seen_decisions[suffix]=digest(p.read_bytes())
  rows=read_jsonl('data/manifests/corpus.jsonl');by={r['paper_id']:r for r in rows};good=[r for r in rows if r['screening']=='include' and r.get('parse_status')=='usable'];counts=collections.Counter(r['sampling_category'] for r in good)
  write_json('reports/pilot_progress.json',{'included':len(good),'categories':dict(counts),'attempted':len(rows),'reviewed_new':sum(len(read_jsonl(f'data/manifests/review_decisions_{s}.jsonl')) for s in ['a','b']),'updated_at':now(),'target':200})
  if len(good)>=200:break
  candidates=[r for r in read_jsonl('data/manifests/candidates.jsonl') if r['screening']=='include' and r['paper_id'] not in by]
  if not candidates:
   if sum(len(read_jsonl(f'data/manifests/review_decisions_{s}.jsonl')) for s in ['a','b'])>=530 or time.time()-started>10800:break
   time.sleep(10);continue
  weights={'gr-qc':.4,'astro-ph.CO':.3,'hep-th':.3}
  c=min(candidates,key=lambda r:(counts[r['sampling_category']]/weights[r['sampling_category']],r['stratum_rank'],r['sampling_year'],r['paper_id']))
  r=None;stage='acquire'
  try:
   r,p=acquire(f,c,cfg);stage='parse';d=parse_tex(p.read_bytes(),p.parent/'source');d.update(paper_id=r['paper_id'],version=r['version'],source_sha256=r['source_sha256']);r.update(parse_status='usable' if d['usable'] else 'low_prose',parser_warnings=d['warnings'],cohort='pilot_extension');write_json('data/parsed/'+r['paper_id']+'.json',d)
   print('parsed',r['paper_id'],d['main_prose_words'],'count',len(good)+int(d['usable']),flush=True)
  except Exception as e:r={**(r or c),'parse_status':'failed','failure_stage':stage,'error':f'{type(e).__name__}: {e}','cohort':'pilot_extension'};print('failed',r['paper_id'],r['error'],flush=True)
  rows.append(r);write_jsonl('data/manifests/corpus.jsonl',rows)
 print('collection finished',flush=True)
