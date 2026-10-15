"""Frozen science/length contract for free-structure round03; no style winner selection."""
import sys,re,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from physstyle.common import *
ROOT=Path('experiments/cosmology_skill_v3_papers')
MATH=r'\$\$.*?\$\$|\\\[.*?\\\]|\\\(.*?\\\)|(?<!\$)\$(?!\$).*?(?<!\$)\$(?!\$)'
def prose_count(text):
 return len(words(re.sub(MATH,' ',re.sub(r'^#{1,6} .*$', '',text,flags=re.M),flags=re.S)))
def inspect(text,brief,contract):
 errors=[];heads=re.findall(r'^## (.+)$',text,re.M)
 if re.findall(r'^# (.+)$',text,re.M)!=[brief['paper_title']]:errors.append('title')
 if not heads or heads[0]!='Abstract' or len(heads)<3:errors.append('abstract/body headings')
 if re.search(r'^###|^## (?:References|Reference)\s*$',text,re.M):errors.append('unsupported heading/reference duplication')
 chunks=re.split(r'^## .+$',text,flags=re.M);abstract=chunks[1] if len(chunks)>1 else '';n=prose_count(text);an=prose_count(abstract)
 if not contract['prose_word_range'][0]<=n<=contract['prose_word_range'][1]:errors.append('length')
 if not contract['abstract_word_range'][0]<=an<=contract['abstract_word_range'][1]:errors.append('abstract length')
 pc={q:text.count(q) for q in brief['protected_math']}
 if any(v!=1 for v in pc.values()):errors.append('protected math')
 if re.search(r'physics-paper-style|skill v3|control group|treatment group',text,re.I):errors.append('condition leakage')
 return {'prose_words':n,'abstract_words':an,'headings':heads,'protected_math_counts':pc,'errors':errors}
def main():
 contract=read_json(ROOT/'common_contract.json');rows=[];pairs=[]
 for cid in ['C1','C2','C3']:
  b=read_json(ROOT/'briefs'/f'{cid}.json');pair=[]
  for arm in ['A','B']:
   p=ROOT/'outputs'/arm/f'{cid}.md';text=p.read_text();job=read_json(ROOT/'jobs'/arm/f'{cid}.json')
   assert job['brief_sha256']==digest((ROOT/'briefs'/f'{cid}.json').read_bytes())
   assert job['contract_sha256']==digest((ROOT/'common_contract.json').read_bytes())
   x=inspect(text,b,contract);assert not x['errors'],(cid,arm,x)
   x.update(case_id=cid,arm=arm,output_sha256=digest(p.read_bytes()),brief_sha256=job['brief_sha256']);rows.append(x);pair.append(x)
  difference=abs(pair[0]['prose_words']-pair[1]['prose_words'])/min(x['prose_words'] for x in pair)
  assert difference<=contract['paired_relative_word_difference_max']
  pairs.append({'case_id':cid,'relative_word_difference':difference,'heading_sequences_identical':pair[0]['headings']==pair[1]['headings'],'interpretation':'Heading difference is observable formatting, not proof of improved logic or readability.'})
 write_json(ROOT/'mechanical_checks.json',{'checked_at':now(),'checks_passed':True,'outputs':rows,'pairs':pairs,'scientific_equivalence':'requires independent fact-level review','method':contract['word_count_method']});print([(r['case_id'],r['arm'],r['prose_words'],r['abstract_words']) for r in rows])
if __name__=='__main__':main()
