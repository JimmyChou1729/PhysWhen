"""Offline source/cohort/map preservation acceptance checks for the500-paper stage."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from physstyle.common import *
from physstyle.features import main_paragraphs
from physstyle.structure import validate_map

def validate():
 with corpus_lock():
  rows=read_jsonl('data/manifests/corpus.jsonl');active=[r for r in rows if r.get('screening')=='include' and r.get('parse_status')=='usable'];result=read_json('reports/STRUCTURE_RESULTS.json');split=read_json('data/splits/frozen.json')['assignments']
  assert len(active)==result['papers_usable']==result['automatic_navigation_papers']==500
  for r in active:
   pid=r['paper_id'];d=read_json(f'data/parsed/{pid}.json');f=read_json(f'data/features/structure500/papers/{pid}.json');nav=read_json(f'data/features/structure500/navigation/{pid}.json');raw=Path(f'data/raw/papers/{pid}v{r["version"]}/source.bin')
   assert r['version_identity_verified'] and '2010-01-01'<=r['version_date'][:10]<='2021-12-31'
   assert digest(raw.read_bytes())==r['source_sha256']==d['source_sha256']==nav['source_sha256']
   assert digest((raw.parent/'metadata.html').read_bytes())==r['selected_metadata_sha256']
   for name,sha in d['source_files'].items():assert digest((Path(d['source_root'])/name).read_bytes())==sha
   assert f['version']==d['version']==r['version']==nav['version']
   assert f['denominators']['prose_words']==d['main_prose_words']==sum(p['word_count'] for p in main_paragraphs(d))==nav['main_prose_words']
   assert d['split']==f['split']==nav['split']==split[pid]
  old=read_json('reports/cohort210_snapshot/frozen.json')['assignments'];assert all(split[k]==v for k,v in old.items())
  assert read_json('data/features/pilot/feature_profiles.json')==read_json('reports/cohort210_snapshot/feature_profiles.json')
  assert read_json('reports/PILOT_RESULTS.json')==read_json('reports/cohort210_snapshot/PILOT_RESULTS.json')
  for item in read_json('reports/structure_stage_baseline.json')['files']:
   path=Path(item['path'])
   if path.exists() and digest(path.read_bytes())==item['sha256']:continue
   # Authorized later rounds may replace preview aliases; exact frozen bytes remain required.
   alternatives=[]
   if path.parent==Path('reader'):alternatives=[Path('archives/reader-round02')/path.name]
   elif path==Path('experiments/reader_pack_manifest.json'):alternatives=list(Path('experiments/reader_pack_manifests').glob('*.json'))
   assert any(p.exists() and digest(p.read_bytes())==item['sha256'] for p in alternatives),item['path']
  protocol=read_json('data/structure/protocol.json');maps=list(Path('data/structure/annotations').glob('*.json'))
  for path in maps:
   packet=read_json('data/structure/papers/'+path.name);r=read_json(path);assert not validate_map(r,packet,protocol)
   d=read_json('data/parsed/'+path.name);assert main_paragraphs(d)==packet['paragraphs'] and d['source_sha256']==packet['source_sha256'] and split[r['paper_id']]=='discovery'
  near=read_json('data/splits/body_near_duplicates.json');assert near['papers']==500 and near['pairs_checked']==124750 and not near['candidate_pairs']
  out={'stage_input_sha256':digest(Path('reports/STRUCTURE_RESULTS.json').read_bytes()),'semantic_input_sha256':digest(Path('reports/structure_semantic_results.json').read_bytes()),'checked_at':now(),'status':'passed','usable_papers':500,'source_version_metadata_hashes_and_denominators':'passed','all_prior_split_assignments':'preserved','frozen_skills_studies_reader_and_pilot_profiles':'preserved','full_mainbody_maps_validated':len(maps),'lexical_pairs_checked':124750,'human_readability_effect':'not_established','validation_scope':'Structural/provenance integrity, not semantic accuracy or scientific truth.'};write_json('reports/structure_validation.json',out);return out
if __name__=='__main__':print(validate())
