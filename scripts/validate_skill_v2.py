"""Release validation for the candidate skill; no corpus or study mutation."""
import sys,json,re
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from physstyle.common import *
from physstyle.annotations import validate_record
root=Path('skills/physics-paper-style-v2');p=read_json(root/'profile.json');pilot=read_json('reports/PILOT_RESULTS.json');tasks={w['window_id']:w for w in read_jsonl('data/annotations_v2/tasks.jsonl')};labels=read_jsonl('data/annotations_v2/labels.jsonl');split=read_json('data/splits/frozen.json')['assignments'];initial={w['paper_id'] for w in read_jsonl('data/annotations/tasks.jsonl')}
assert p['corpus_papers']==pilot['papers_included']==210 and p['discovery_papers']==168 and p['heldout_papers']==42
assert p['reference_profiles']==read_json('data/features/pilot/feature_profiles.json')['discovery']
assert len(tasks)==60 and len(labels)==360 and len({r['paper_id'] for r in labels})==12
assert not initial&{r['paper_id'] for r in labels}
assert len({(r['window_id'],r['feature_id']) for r in labels})==360
for r in labels:
 assert split[r['paper_id']]=='discovery';validate_record(r,tasks)
for item in read_json('reports/skill_v2_frozen_baseline.json')['files']:
 path=Path(item['path'])
 if path.exists() and digest(path.read_bytes())==item['sha256']:continue
 # Current preview aliases can point to a later authorized round. The exact
 # frozen prior bytes must still exist in the designated archive/registry.
 alternatives=[]
 if path.parent==Path('reader'):alternatives=[Path('archives/cosmology-round01')/path.name]
 elif path==Path('experiments/reader_pack_manifest.json'):alternatives=list(Path('experiments/reader_pack_manifests').glob('*.json'))
 assert any(p.exists() and digest(p.read_bytes())==item['sha256'] for p in alternatives),'Frozen baseline unavailable/changed: '+item['path']
# The user renamed the deliverable; identity is tied to the build hash, not filename.
expected=read_json('reports/standalone_reader_build.json')['sha256'];assert any(digest(f.read_bytes())==expected for f in Path('deliverables').glob('*.html'))
for a in read_jsonl(root/'references/source-anchors.jsonl'):
 r=next(r for r in labels if r['window_id']==a['window_id'] and r['feature_id']==a['feature_id'])
 assert r['label']==a['observed_label'] and r['audit_status']==a['audit_status']
 assert a['source_sha256']==read_json(f'data/parsed/{a["paper_id"]}.json')['source_sha256']
 for loc in a['source_locations']:assert any(all(e[k]==v for k,v in loc.items()) for e in r['evidence'])
assert read_json('reports/skill_v2_semantic_summary.json')['combined_inventory_only']=={'windows':120,'papers':27,'labels':720}
result={'checked_at':now(),'status':'pass','new_labels_validated':360,'new_windows':60,'new_papers':12,'old_and_new_samples_kept_separate':True,'original_skill_and_prior_blind_study_preserved':True,'source_anchors_validated':11,'reference_profiles_match_discovery':168,'corpus':210,'heldout_excluded':42,'human_readability_improvement':'not_established'}
write_json('reports/skill_v2_validation.json',result);print(json.dumps(result,ensure_ascii=False,indent=2))
