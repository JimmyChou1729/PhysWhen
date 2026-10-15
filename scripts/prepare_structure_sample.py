"""Freeze a feasible, stratified whole-paper discovery sample and lossless source-located reading packets."""
import sys,random,collections
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from physstyle.common import *
from physstyle.features import main_paragraphs
root=Path('data/structure');old={w['paper_id'] for f in ['data/annotations/tasks.jsonl','data/annotations_v2/tasks.jsonl'] for w in read_jsonl(f)}
if (root/'sample.json').exists():raise SystemExit('sample already frozen')
rows=read_jsonl('reports/cohort210_snapshot/corpus.jsonl');splits=read_json('reports/cohort210_snapshot/frozen.json')['assignments'];sample=[]
for cat in ['gr-qc','astro-ph.CO','hep-th']:
 for lo,hi in [(2010,2012),(2013,2015),(2016,2018),(2019,2021)]:
  eligible=[]
  for r in rows:
   if r['screening']!='include' or r.get('parse_status')!='usable' or splits.get(r['paper_id'])!='discovery' or r['paper_id'] in old or r['sampling_category']!=cat or not lo<=r['sampling_year']<=hi:continue
   d=read_json(f'data/parsed/{r["paper_id"]}.json')
   if 800<=d['main_prose_words']<=12000:eligible.append(r)
  eligible.sort(key=lambda r:r['paper_id']);random.Random(f'1729:wholepaper:{cat}:{lo}').shuffle(eligible)
  if not eligible:raise ValueError('empty selection cell')
  r=eligible[0];pid=r['paper_id'];d=read_json(f'data/parsed/{pid}.json');ps=main_paragraphs(d)
  packet={'paper_id':pid,'version':d['version'],'source_sha256':d['source_sha256'],'source_root':d['source_root'],'source_files':d['source_files'],'title':r['title'],'abstract':r['abstract'],'split':'discovery','category':cat,'year':r['sampling_year'],'main_prose_words':d['main_prose_words'],'main_body_paragraph_ids':[p['paragraph_id'] for p in ps],'paragraphs':ps,'sections':d['sections'],'parser_warnings':d['warnings'],'coverage_note':'All parsed main-body prose/math supplied. Figures/captions and appendices are not automatically covered; annotate access limits and inspect raw source if needed.'}
  write_json(root/'papers'/f'{pid}.json',packet);sample.append({k:packet[k] for k in ['paper_id','version','source_sha256','split','category','year','main_prose_words']})
write_json(root/'sample.json',{'frozen_at':now(),'phase':'initial12 from existing210cohort, all discovery, prior local semantic papers excluded','papers':sample,'selection':'one random paper per category × four year bands; seed1729,800–12000parsedmainprosewords for full-read feasibility; not quality-based selection','limits':'Purposive stratification and length eligibility;12wholepapers do not represent500-paper full semantic annotation.'})
for i,suffix in enumerate(['a','b','c']):write_json(root/f'assignment_{suffix}.json',{'paper_ids':[r['paper_id'] for r in sample[i::3]]})
print([(r['paper_id'],r['main_prose_words']) for r in sample])
