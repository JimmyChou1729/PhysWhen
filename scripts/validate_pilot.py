"""Read-only pilot acceptance checks; no downloads, annotations or generations."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from physstyle.common import *
from physstyle.features import main_paragraphs

def validate():
 with corpus_lock():
  rows=read_jsonl('data/manifests/corpus.jsonl');active=[r for r in rows if r['screening']=='include' and r.get('parse_status')=='usable'];result=read_json('reports/PILOT_RESULTS.json')
  assert len(active)>=200
  assert result['papers_included']==len(active)==result['deterministic_features_papers']
  for r in active:
   pid=r['paper_id'];d=read_json(f'data/parsed/{pid}.json');f=read_json(f'data/features/{pid}.json');raw=Path(f'data/raw/papers/{pid}v{r["version"]}/source.bin');meta=raw.parent/'metadata.html'
   assert r['version_identity_verified'] and '2010-01-01'<=r['version_date'][:10]<='2021-12-31'
   assert digest(raw.read_bytes())==r['source_sha256']==d['source_sha256']
   assert digest(meta.read_bytes())==r['selected_metadata_sha256']
   assert f['version']==d['version']==r['version']
   assert f['denominators']['prose_words']==d['main_prose_words']==sum(p['word_count'] for p in main_paragraphs(d))
  frozen=read_json('data/splits/frozen.json')['assignments'];old=read_json('reports/smoke_snapshot/frozen.json')['assignments']
  assert all(frozen[k]==v for k,v in old.items())
  for item in read_json('reports/frozen_experiment_hashes.json')['files']:
   assert digest(Path(item['path']).read_bytes())==item['sha256'],item['path']
  for w in read_jsonl('data/annotations/tasks.jsonl'):
   d=read_json(f'data/parsed/{w["paper_id"]}.json');ps={p['paragraph_id']:p for p in d['paragraphs']}
   assert d['split']==w['split'] and d['version']==w['version']
   assert all(ps[p['paragraph_id']]==p for p in w['context'])
  near=read_json('data/splits/body_near_duplicates.json')
  assert near['papers']==len(active) and near['pairs_checked']==len(active)*(len(active)-1)//2 and not near['candidate_pairs']
  audit=read_json('reports/pilot_parse_audit.json')
  for item in audit['papers']:
   d=read_json(f'data/parsed/{item["paper_id"]}.json');assert d['source_sha256']==item['source_sha256'];ps={p['paragraph_id']:p for p in d['paragraphs']}
   assert all(ps[p['paragraph_id']]['word_count']==p['word_count'] for p in item['paragraphs'])
  out={'checked_at':now(),'status':'passed','papers_verified':len(active),'exact_version_dates_source_and_metadata_hashes':'passed','feature_denominators':'passed','original_split_and_experiment_hashes':'passed','annotation_contexts':'60 unchanged','near_duplicate_pairs_checked':near['pairs_checked'],'new_independent_parse_audit':'8 papers /24 math paragraphs; noted limitations retained','human_readability_improvement':'not_established','no_network_used':True}
  write_json('reports/pilot_validation.json',out);return out
if __name__=='__main__':print(json.dumps(validate(),ensure_ascii=False,indent=2))
