"""Validate the portablev3 release against its actual source evidence and package."""
import sys,re,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from physstyle.common import *
from physstyle.structure import norm
from physstyle.release import check_semantic_bundle,check_forward_bundle
from physstyle.parse import strip_comments
root=Path('skills/physics-paper-style-v3');p=read_json(root/'profile.json');stage=read_json('reports/STRUCTURE_RESULTS.json');sem=read_json('reports/structure_semantic_results.json');split=read_json('data/splits/frozen.json')['assignments']
assert p['corpus_papers']==stage['papers_usable']==500
assert p['discovery_papers']==stage['split_counts']['discovery'] and p['heldout_papers']==stage['split_counts']['heldout']
assert p['reference_distributions']==read_json(stage['profile_file'])['discovery']
assert p['structure_semantic']['papers_full_mainbody_read']==sem['papers_full_mainbody_read']==30
for key in p['structure_semantic']:assert p['structure_semantic'][key]==sem[key]
selected=[]
for f in p['structure_sample_files']:selected.extend(x['paper_id'] for x in read_json(f)['papers'])
assert len(selected)==len(set(selected))==30 and all(split[x]=='discovery' for x in selected)
semantic_check=check_semantic_bundle(sem,selected)
local={w['paper_id'] for f in ['data/annotations/tasks.jsonl','data/annotations_v2/tasks.jsonl'] for w in read_jsonl(f)};assert not set(selected)&local
anchors=read_jsonl(root/'references/structure-source-anchors.jsonl');canonical=read_jsonl('data/structure/source_anchors.jsonl')
assert anchors and len(anchors)==p['structural_anchor_count'] and {a['rule'] for a in anchors}=={'G1','G2','G3','G4'}
assert digest((root/'references/structure-source-anchors.jsonl').read_bytes())==p['structural_anchor_sha256']
for a in anchors:
 packet=read_json(f'data/structure/papers/{a["paper_id"]}.json');assert packet['version']==a['version'] and packet['source_sha256']==a['source_sha256']
 para=next(x for x in packet['paragraphs'] if x['paragraph_id']==a['paragraph_id']);raw=norm(''.join(strip_comments(b['raw']) for b in para['blocks']));matches=[x for x in canonical if all(x[k]==a[k] for k in ['paper_id','node_id','paragraph_id','role']) and digest(x['exact_quote'].encode())==a['exact_quote_sha256']];assert matches and norm(matches[0]['exact_quote']) in raw
 assert a['source_spans']==[s for b in para['blocks'] for s in b['source_spans']]
 node=next(n for n in read_json(f'data/structure/annotations/{a["paper_id"]}.json')['nodes'] if n['id']==a['node_id'])
 assert any(o['paragraph_id']==a['paragraph_id'] and o['role']==a['role'] and digest(o['exact_quote'].encode())==a['exact_quote_sha256'] for o in node['occurrences']), 'anchor not in current map'
for f in root.rglob('*.md'):
 for target in re.findall(r'\]\(([^)]+)\)',f.read_text()):
  if '://' not in target:assert (f.parent/target.split('#')[0]).exists(),(f,target)
prov=read_json('experiments/structure_skill_v3_validation/provenance.json');assert prov['cases']==4
forward_check=check_forward_bundle(prov)
for item in prov['files']:assert digest(Path(item['path']).read_bytes())==item['sha256']
assert digest(Path(prov['initial_tested_skill_snapshot']).read_bytes())==prov['skill_entry_sha256']
assert digest((root/'SKILL.md').read_bytes())==prov['appendix_task_skill_entry_sha256']
expected={str(f):f for f in root.rglob('*') if f.is_file() and '__pycache__' not in f.parts and f.suffix!='.pyc'}
with zipfile.ZipFile('deliverables/PhysWhen-skill-v3.zip') as z:
 wanted={str(f.relative_to(root.parent)):f for f in expected.values()};assert set(z.namelist())==set(wanted)
 for name,f in wanted.items():assert z.read(name)==f.read_bytes()
out={'checked_at':now(),'status':'passed','corpus':500,'discovery':p['discovery_papers'],'heldout':p['heldout_papers'],'independently_reviewed_maps':semantic_check['papers'],'reviewed_original_edges':semantic_check['original_edges'],'wholepaper_maps':30,'structural_source_anchors':len(anchors),'source_identity_quotes_positions':'passed','skill_links':'passed','package_files':len(expected),'forward_tasks':4,'initial_and_current_tested_entry_hashes':'passed','training_or_fulltext_in_package':False,'human_readability_effect':'not_established'};write_json('reports/skill_v3_validation.json',out);print(out)
