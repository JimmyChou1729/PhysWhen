import sys,re,random
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from physstyle.common import *
from physstyle.parse import words
checks=[];mapping={};choices=['A','B','A'];random.Random(1729).shuffle(choices)
for i,c in enumerate(['C1','C2','C3']):
 brief=read_json(f'experiments/briefs/{c}.json');bh=digest(Path(f'experiments/briefs/{c}.json').read_bytes());mapping[c]={'X':choices[i],'Y':'B' if choices[i]=='A' else 'A'}
 write_json(f'experiments/anonymous/{c}_questions.json',{'case_id':c,'function':brief['function'],'questions':[x['question'] for x in brief['questions']]})
 for arm in ['A','B']:
  p=Path(f'experiments/outputs/{arm}/{c}.md');text=p.read_text();job=read_json(f'experiments/jobs/{arm}/{c}.json');assert job['brief_sha256']==bh,'different or changed fact brief'
  math=re.findall(r'\$\$.*?\$\$|\\\[.*?\\\]|\\\(.*?\\\)|(?<!\$)\$(?!\$).*?(?<!\$)\$(?!\$)',text,re.S)
  prose=re.sub(r'\$\$.*?\$\$|\\\[.*?\\\]|\\\(.*?\\\)|(?<!\$)\$(?!\$).*?(?<!\$)\$(?!\$)',' ',text,flags=re.S)
  counts={q:text.count(q) for q in brief['protected_equations']};n=len(words(prose))
  checks.append({'case_id':c,'arm':arm,'word_count_prose_excluding_math':n,'word_counter':'English regex v1, math excluded','within_word_budget':300<=n<=700,'protected_equation_counts':counts,'protected_equations_pass':all(v==1 for v in counts.values()),'brief_sha256':bh,'output_sha256':digest(p.read_bytes()),'citation_commands_found':re.findall(r'\\cite\w*\{[^}]*\}',text),'content_semantics_status':'requires_agent_review; byte preservation is insufficient','extra_context_characters':job['extra_context_characters'],'observed_math_blocks':len(math)})
 for alias,arm in mapping[c].items():
  p=Path(f'experiments/anonymous/{c}_{alias}.md');p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(Path(f'experiments/outputs/{arm}/{c}.md').read_bytes())
write_json('experiments/anonymous_mapping_private.json',mapping);write_json('experiments/mechanical_checks.json',checks)
print([{k:r[k] for k in ['case_id','arm','word_count_prose_excluding_math','within_word_budget','protected_equations_pass']} for r in checks])
