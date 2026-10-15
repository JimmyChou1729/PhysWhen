"""Verify the current structured-paper round without generating or selecting variants."""
import sys,re
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from physstyle.common import *
cfg=read_json('configs/reader_current.json');root=Path(cfg['experiment_root']);rows=[]
expected=['Abstract','1. Introduction','2. Model and assumptions','3. Analysis and results','4. Discussion','5. Conclusion']
math=r'\$\$.*?\$\$|\\\[.*?\\\]|\\\(.*?\\\)|(?<!\$)\$(?!\$).*?(?<!\$)\$(?!\$)'
def count(s):return len(words(re.sub(math,' ',re.sub(r'^#{1,2} .*$', '',s,flags=re.M),flags=re.S)))
for cid in ['C1','C2','C3']:
 briefpath=root/'briefs'/f'{cid}.json';brief=read_json(briefpath);bh=digest(briefpath.read_bytes())
 for arm in ['A','B']:
  p=root/'outputs'/arm/f'{cid}.md';text=p.read_text();job=read_json(root/'jobs'/arm/f'{cid}.json')
  assert job['brief_sha256']==bh and job['brief']==brief
  assert re.findall(r'^# (.+)$',text,re.M)==[brief['paper_title']]
  assert re.findall(r'^## (.+)$',text,re.M)==expected,(cid,arm,'headings')
  abstract=text.split('## Abstract\n',1)[1].split('## 1. Introduction',1)[0];n=count(text);an=count(abstract)
  assert 800<=n<=1100 and 80<=an<=130,(cid,arm,n,an)
  pc={q:text.count(q) for q in brief['protected_math']};assert all(v==1 for v in pc.values())
  rows.append({'case_id':cid,'arm':arm,'prose_words':n,'abstract_words':an,'protected_math_counts':pc,'brief_sha256':bh,'output_sha256':digest(p.read_bytes()),'sections':expected})
write_json(root/'mechanical_checks.json',{'checked_at':now(),'checks_passed':True,'outputs':rows,'word_count_method':'English regex v1; title/headings and math excluded; abstract included','human_effect':'not_established'})
print([(r['case_id'],r['arm'],r['prose_words'],r['abstract_words']) for r in rows])
