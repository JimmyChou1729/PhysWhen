"""Print bounded, lossless main-body source chunks for semantic reading."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from physstyle.common import read_json
from physstyle.parse import strip_comments
p=read_json(f'data/structure/papers/{sys.argv[1]}.json');start=int(sys.argv[2]);end=min(int(sys.argv[3]),len(p['paragraphs']))
print(p['paper_id'],p['title'],'MAIN PARAGRAPHS',len(p['paragraphs']),'show',start,end)
if start==0:print('ABSTRACT',p['abstract'])
for i in range(start,end):
 q=p['paragraphs'][i]
 print('\nPARAGRAPH',i,q['paragraph_id'],'SECTION',q['section_id'],q['section_title'])
 print(''.join(strip_comments(b['raw']) for b in q['blocks']))
