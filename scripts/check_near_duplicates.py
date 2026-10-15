import sys,collections,itertools
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from physstyle.common import *
from physstyle.pipeline import load_docs
from physstyle.features import main_paragraphs,ptext
rows=[r for r in read_jsonl('data/manifests/corpus.jsonl') if r['screening']=='include' and r.get('parse_status')=='usable'];docs=load_docs();vectors={}
for r in rows:
 d=docs[r['paper_id']];tokens=words(' '.join(ptext(p) for p in main_paragraphs(d)).lower());vectors[r['paper_id']]={tuple(tokens[i:i+5]) for i in range(len(tokens)-4)}
pairs=[];largest=[]
for a,b in itertools.combinations(vectors,2):
 x,y=vectors[a],vectors[b];j=len(x&y)/len(x|y) if x|y else None
 if j is not None:largest.append((j,a,b))
 if j is not None and j>=.8:pairs.append({'paper_ids':[a,b],'jaccard_5gram':j,'splits':[docs[a]['split'],docs[b]['split']],'status':'needs_family_review'})
write_json('data/splits/body_near_duplicates.json',{'method':'exact normalized prose word5-gram set Jaccard, all included paper pairs','threshold':.8,'papers':len(vectors),'pairs_checked':len(largest),'candidate_pairs':pairs,'largest_similarities':sorted(largest,reverse=True)[:5],'limits':'Detects substantial lexical overlap; semantic paraphrases and mathematical similarity can be missed.'})
if pairs:raise SystemExit('Near-duplicate candidates need review before release')
print('near-duplicate pairs checked:',len(largest),'candidates:',len(pairs))
