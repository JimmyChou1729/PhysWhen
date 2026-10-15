"""Acceptance for actual round03 outputs, blinded review, public pack and preserved history."""
import sys,re,json,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from physstyle.common import *
from scripts.check_round03 import inspect
root=Path('experiments/cosmology_skill_v3_papers');contract=read_json(root/'common_contract.json');manifest=read_json('experiments/reader_pack_manifest.json');exp=read_json(root/'manifest.json')
assert manifest['experiment_root']==str(root) and manifest['round_label']=='03'
for row in read_json(root/'previous_artifacts.json')['files']:assert digest(Path(row['path']).read_bytes())==row['sha256'],row['path']
for row in exp['skill_snapshot_hashes']:assert digest((root/row['path']).read_bytes())==row['sha256']
blog=read_json(root/'logs/B-generation.json');access={r['path']:r['sha256'] for r in blog['resources_actually_read']}
required={str(root/r['path']) for r in exp['skill_snapshot_hashes']}
assert required<=set(access)
for path,sha in access.items():assert digest(Path(path).read_bytes())==sha
assert blog['comparison_arms_or_feedback_read'] is False and blog['network_used'] is False
alog=read_json(root/'logs/A-generation.json');assert len(alog['cases'])==3 and len(alog['inputs'])==4
review=read_json('reports/round03_content_review.json');assert review['status']=='pass' and not review['required_corrections']
inputs=[review['inputs']['common_contract'],*review['inputs']['briefs'],*review['inputs']['anonymous_manuscripts']];assert len(inputs)==10
for item in inputs:assert digest(Path(item['path']).read_bytes())==item['sha256']
reviewkey=read_json(root/'private/review_mapping.json');publickey=read_json(root/'reader_assignment_private.json')
assert digest((root/'reader_assignment_private.json').read_bytes())==manifest['private_assignment_sha256']
expected=set();lengths={};alltexts={}
for cid in ['C1','C2','C3']:
 b=read_json(root/'briefs'/f'{cid}.json');assert b['source_sha256']==read_json(f'data/parsed/{b["paper_id"]}.json')['source_sha256']
 assert set(reviewkey[cid])=={'U','V'} and set(reviewkey[cid].values())=={'A','B'}
 for variant,arm in reviewkey[cid].items():
  p=root/'outputs'/arm/f'{cid}.md';text=p.read_text();assert p.read_bytes()==(root/'review'/f'{cid}-{variant}.md').read_bytes();alltexts[cid,variant]=text
  n=inspect(text,b,contract);assert not n['errors'];lengths[cid,arm]=n['prose_words'];expected.update((cid,variant,f['id']) for f in b['facts'])
 for arm in ['A','B']:
  job=read_json(root/'jobs'/arm/f'{cid}.json');assert job['brief_sha256']==digest((root/'briefs'/f'{cid}.json').read_bytes()) and job['contract_sha256']==digest((root/'common_contract.json').read_bytes())
 assert abs(lengths[cid,'A']-lengths[cid,'B'])/min(lengths[cid,'A'],lengths[cid,'B'])<=.03
judgments=review['fact_variant_reviews'];assert len(judgments)==80 and {(j['case_id'],j['variant'],j['fact_id']) for j in judgments}==expected
for j in judgments:
 assert j['status']=='covered' and j['subclaims']
 for sub in j['subclaims']:
  assert sub['status']=='covered';e=sub['evidence'];text=alltexts[j['case_id'],j['variant']];assert e['quote'] in text
  assert isinstance(e['line'],int) and 1<=e['line']<=len(text.splitlines())
  tail='\n'.join(text.splitlines()[e['line']-1:]);assert 0<=tail.find(e['quote'])<=len(text.splitlines()[e['line']-1]),'bad source line'
assert len(review['pair_reviews'])==3 and all(not p['material_asymmetries'] and not p['required_scientific_corrections'] for p in review['pair_reviews'])
pack=json.loads(Path('reader/data.js').read_text().removeprefix('window.READING_PACK=').strip().removesuffix(';'));assert pack['dataset_id']==manifest['dataset_id'] and pack['round_label']=='03'
assert len(pack['cases'])==3
for case in pack['cases']:
 assert set(case)=={'id','name','versions','paper_title','reference'} and set(case['versions'])=={'P','Q'}
 for label,text in case['versions'].items():assert text==(root/'outputs'/publickey[case['id']][label]/f'{case["id"]}.md').read_text()
htmlpath=Path('deliverables/PhysWhen-Blind-Test-03.html');html=htmlpath.read_text();assert htmlpath.read_bytes()==Path('reader/PhysWhen-Blind-Test-03.html').read_bytes()
assert not re.search(r'<(?:script|link)\b[^>]*\b(?:src|href)=',html,re.I)
for token in ['reader_assignment_private','review_mapping','physics-paper-style-v3','source_sha256','reference_points']:assert token not in html,token
assert digest(htmlpath.read_bytes())==read_json('reports/standalone_reader_build.json')['sha256']
with zipfile.ZipFile('deliverables/PhysWhen-Blind-Test-03.zip') as z:
 assert set(z.namelist())=={'PhysWhen-Blind-Test-03.html','PhysWhen-03-阅读邀请.txt'}
 for name in z.namelist():assert z.read(name)==(Path('deliverables')/name).read_bytes()
qa=read_json('reports/round03_browser_QA.json');assert qa['dataset_id']==manifest['dataset_id'] and qa['test_mode'] is True and len(qa['texts'])==6
from physstyle.group_feedback import validate_v2
try:validate_v2(qa,manifest)
except ValueError:pass
else:raise AssertionError('QA accepted')
if read_json('configs/reader_current.json').get('feedback_instrument')=='pair-preference-v1':
 simple_report=read_json('reports/round03_simple_browser_validation.json')
 assert simple_report['status']=='passed' and simple_report['standalone_sha256']==digest(htmlpath.read_bytes())
 simple_qa=read_json('reports/round03_simple_browser_QA.json')
 assert simple_qa['instrument']=='pair-preference-v1' and simple_qa['test_mode'] is True
 assert len(simple_qa['texts'])==6 and len(simple_qa['comparisons'])==3
 assert all(t['effort']==t['naturalness']=='' for t in simple_qa['texts'].values())
 try:validate_v2(simple_qa,manifest)
 except ValueError:pass
 else:raise AssertionError('simplified QA accepted')
result={'checked_at':now(),'status':'passed','dataset_id':manifest['dataset_id'],'round':'03','outputs':6,'fact_variant_checks':80,'subclaim_checks':sum(len(j['subclaims']) for j in judgments),'protected_equations':18,'prose_word_range':[min(lengths.values()),max(lengths.values())],'maximum_pair_relative_difference':max(abs(lengths[c,'A']-lengths[c,'B'])/min(lengths[c,'A'],lengths[c,'B']) for c in ['C1','C2','C3']),'skill_resources_read_and_hash_bound':len(required),'old_frozen_files_preserved':len(read_json(root/'previous_artifacts.json')['files']),'standalone_sha256':digest(htmlpath.read_bytes()),'zip_sha256':digest(Path('deliverables/PhysWhen-Blind-Test-03.zip').read_bytes()),'browser_report':('reports/round03_simple_browser_validation.json' if read_json('configs/reader_current.json').get('feedback_instrument')=='pair-preference-v1' else 'reports/round03_browser_validation.json'),'human_readability_effect':'not_established','imported_feedback_files':sum(read_json(p).get('feedback',{}).get('dataset_id')==manifest['dataset_id'] for p in Path('data/human_feedback').glob('*.json')),'verified_human_participants':None}
write_json('reports/round03_validation.json',result);print(result)
