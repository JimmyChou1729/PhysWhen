"""Verify six genuine cosmology generations against pre-frozen briefs; no regeneration."""
import re,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from physstyle.common import *
root=Path('experiments/cosmology_v2');rows=[]
for cid in ['C1','C2','C3']:
 brief_path=root/'briefs'/f'{cid}.json';brief=read_json(brief_path);bh=digest(brief_path.read_bytes())
 for arm in ['A','B']:
  job=read_json(root/'jobs'/arm/f'{cid}.json');p=root/'outputs'/arm/f'{cid}.md';t=p.read_text()
  correction=read_json(root/'corrections'/f'{cid}.json')
  if correction:
   assert correction['before_brief_sha256']==job['brief_sha256'] and correction['after_brief_sha256']==bh
   assert job['brief']==read_json(root/'corrections'/cid/'brief_before.json')
   assert correction['outputs'][arm]['after_sha256']==digest(p.read_bytes())
  else:assert job['brief_sha256']==bh and job['brief']==brief
  prose=re.sub(r'\$\$.*?\$\$|\\\[.*?\\\]|\\\(.*?\\\)|(?<!\$)\$(?!\$).*?(?<!\$)\$(?!\$)',' ',t,flags=re.S)
  n=len(words(prose));counts={q:t.count(q) for q in brief['protected_math']}
  assert 250<=n<=350 and all(x==1 for x in counts.values()),(cid,arm,n,counts)
  rows.append({'case_id':cid,'arm':arm,'english_prose_words':n,'protected_math_counts':counts,'brief_sha256':bh,'output_sha256':digest(p.read_bytes()),'case_source':brief['paper_id'],'source_version':brief['source_version'],'split':brief['split']})
write_json(root/'mechanical_checks.json',{'checked_at':now(),'outputs':rows,'checks_passed':True,'model':'inherited host model; exact ID unknown','completed_generations':6,'human_effect':'not_established','semantic_review':'reports/cosmology_content_review.json'})
print([(r['case_id'],r['arm'],r['english_prose_words']) for r in rows])
