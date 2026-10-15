"""Package only the portable skill resources, after actual source-map/review gates."""
import sys,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from physstyle.common import read_json,read_jsonl
from physstyle.release import check_semantic_bundle,check_forward_bundle
root=Path('skills/physics-paper-style-v3');profile=read_json(root/'profile.json');sem=read_json('reports/structure_semantic_results.json')
assert profile['corpus_papers']==500 and profile['structure_semantic']['papers_full_mainbody_read']==30
selected=[p['paper_id'] for f in profile['structure_sample_files'] for p in read_json(f)['papers']]
check_semantic_bundle(sem,selected);check_forward_bundle(read_json('experiments/structure_skill_v3_validation/provenance.json'))
for row in read_jsonl(root/'references/structure-source-anchors.jsonl'):assert 'exact_quote' not in row
files=['SKILL.md','profile.json','references/structure-evidence.md','references/structure-source-anchors.jsonl','references/local-evidence.md','references/local-source-anchors.jsonl','references/outline-contract.md','scripts/check_outline.py']
assert all((root/f).is_file() for f in files)
out=Path('deliverables/PhysWhen-skill-v3.zip');tmp=out.with_suffix('.zip.tmp')
with zipfile.ZipFile(tmp,'w',compression=zipfile.ZIP_DEFLATED) as z:
 for name in files:z.write(root/name,root.name+'/'+name)
tmp.replace(out);print(out,len(files),'portable files; no corpus/context files')
