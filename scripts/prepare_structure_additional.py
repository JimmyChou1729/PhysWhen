"""Second, prespecified-rank paper per original whole-paper stratum, exploratory only."""
import sys,random
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from physstyle.common import *
from physstyle.features import main_paragraphs
root=Path('data/structure')
if (root/'additional_sample.json').exists():raise SystemExit('additional sample already frozen')
local={w['paper_id'] for f in ['data/annotations/tasks.jsonl','data/annotations_v2/tasks.jsonl'] for w in read_jsonl(f)};first={r['paper_id'] for r in read_json(root/'sample.json')['papers']};rows=read_jsonl('reports/cohort210_snapshot/corpus.jsonl');split=read_json('reports/cohort210_snapshot/frozen.json')['assignments'];sample=[]
for cat in ['gr-qc','astro-ph.CO','hep-th']:
 for lo,hi in [(2010,2012),(2013,2015),(2016,2018),(2019,2021)]:
  eligible=[]
  for r in rows:
   if r.get('screening')!='include' or r.get('parse_status')!='usable' or split.get(r['paper_id'])!='discovery' or r['paper_id'] in local or r['sampling_category']!=cat or not lo<=r['sampling_year']<=hi:continue
   d=read_json(f'data/parsed/{r["paper_id"]}.json')
   if 800<=d['main_prose_words']<=12000:eligible.append(r)
  eligible.sort(key=lambda r:r['paper_id']);random.Random(f'1729:wholepaper:{cat}:{lo}').shuffle(eligible)
  assert eligible[0]['paper_id'] in first
  if len(eligible)<2:raise ValueError('no second paper in stratum')
  r=eligible[1];pid=r['paper_id'];d=read_json(f'data/parsed/{pid}.json');ps=main_paragraphs(d)
  packet={'paper_id':pid,'version':d['version'],'source_sha256':d['source_sha256'],'source_root':d['source_root'],'source_files':d['source_files'],'title':r['title'],'abstract':r['abstract'],'split':'discovery','category':cat,'year':r['sampling_year'],'main_prose_words':d['main_prose_words'],'main_body_paragraph_ids':[p['paragraph_id'] for p in ps],'paragraphs':ps,'sections':d['sections'],'parser_warnings':d['warnings'],'coverage_note':'All parsed main-body prose/math; actual figures/appendices coverage must be declared.'}
  write_json(root/'papers'/f'{pid}.json',packet);sample.append({**{k:packet[k] for k in ['paper_id','version','source_sha256','split','category','year','main_prose_words']},'eligible_ids_in_seed_order':[q['paper_id'] for q in eligible],'selected_rank':1})
write_json(root/'additional_sample.json',{'frozen_at':now(),'phase':'additional12 existing-cohort exploratory maps, selected after initial12 audit; no outcome-based paper selection','papers':sample,'selection':'second ranked paper under unchanged original seed/eligibility per3categories×4yearbands;800–12000prosewords','limits':'Continued discovery after candidate skill design, not independent heldout confirmation; report sampling stages separately.'})
for i,suffix in enumerate(['a','b','c']):write_json(root/f'additional_assignment_{suffix}.json',{'paper_ids':[r['paper_id'] for r in sample[i::3]]})
print([(r['paper_id'],r['main_prose_words']) for r in sample])
