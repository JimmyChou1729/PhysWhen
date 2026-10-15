"""Freeze six discovery full-paper tasks from newly acquired500-stage papers."""
import sys,random
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from physstyle.common import *
from physstyle.features import main_paragraphs
with corpus_lock():
 root=Path('data/structure')
 if (root/'supplement_sample.json').exists():raise SystemExit('supplement already frozen')
 result=read_json('reports/STRUCTURE_RESULTS.json')
 if not result or result['papers_usable']!=500:raise ValueError('complete500-stage analysis first')
 old={r['paper_id'] for r in read_jsonl('reports/cohort210_snapshot/corpus.jsonl')};rows=read_jsonl('data/manifests/corpus.jsonl');split=read_json('data/splits/frozen.json')['assignments'];sample=[]
 active=[r for r in rows if r.get('screening')=='include' and r.get('parse_status')=='usable']
 if len(active)!=500:raise ValueError('current corpus does not match complete500 report')
 if any(r['paper_id'] not in split for r in active):raise ValueError('current corpus split is not frozen')
 for cat in ['gr-qc','astro-ph.CO','hep-th']:
  for lo,hi in [(2010,2015),(2016,2021)]:
   eligible=[]
   for r in rows:
    if r['paper_id'] in old or r.get('screening')!='include' or r.get('parse_status')!='usable' or split.get(r['paper_id'])!='discovery' or r['sampling_category']!=cat or not lo<=r['sampling_year']<=hi:continue
    d=read_json(f'data/parsed/{r["paper_id"]}.json')
    if 800<=d['main_prose_words']<=8000:eligible.append(r)
   eligible.sort(key=lambda r:r['paper_id']);random.Random(f'1729:structure-new:{cat}:{lo}').shuffle(eligible)
   if not eligible:raise ValueError('no eligible paper '+cat+str(lo))
   r=eligible[0];pid=r['paper_id'];d=read_json(f'data/parsed/{pid}.json');ps=main_paragraphs(d)
   if d['version']!=r['version'] or d['source_sha256']!=r['source_sha256'] or d.get('split')!='discovery':raise ValueError('selected source/split identity mismatch')
   if digest(Path(f'data/raw/papers/{pid}v{r["version"]}/source.bin').read_bytes())!=r['source_sha256']:raise ValueError('selected raw source hash mismatch')
   packet={'paper_id':pid,'version':d['version'],'source_sha256':d['source_sha256'],'source_root':d['source_root'],'source_files':d['source_files'],'title':r['title'],'abstract':r['abstract'],'split':'discovery','category':cat,'year':r['sampling_year'],'main_prose_words':d['main_prose_words'],'main_body_paragraph_ids':[p['paragraph_id'] for p in ps],'paragraphs':ps,'sections':d['sections'],'parser_warnings':d['warnings'],'coverage_note':'All parsed main-body prose/math; figures/captions/appendices coverage must be declared.'}
   write_json(root/'papers'/f'{pid}.json',packet);sample.append({k:packet[k] for k in ['paper_id','version','source_sha256','split','category','year','main_prose_words']})
 write_json(root/'supplement_sample.json',{'frozen_at':now(),'phase':'six newly acquired discovery papers after500complete; prior210attempts excluded','papers':sample,'selection':'one random paper per category × two year bands; seed1729;800–8000parsedprosewords feasible-length subset','limits':'Supplementary exploration, not heldout validation; selected after initial12maps; report separate sample design.'})
 for i,suffix in enumerate(['a','b','c']):write_json(root/f'supplement_assignment_{suffix}.json',{'paper_ids':[r['paper_id'] for r in sample[i::3]]})
 print(sample)
