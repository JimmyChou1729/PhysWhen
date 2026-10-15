import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from physstyle.common import read_jsonl
from physstyle.parse import strip_comments
ws=read_jsonl(f'data/annotations_v2/tasks_{sys.argv[1]}.jsonl')
for n in range(int(sys.argv[2]),min(int(sys.argv[3]),len(ws))):
 w=ws[n];print('\nWINDOW',n,w['window_id'],'target',w['target_paragraph_id'],w['target_block_id'],'display',w['has_target_display'],'role',w['section_role'])
 for p in w['context']:
  print('TARGET' if p['paragraph_id']==w['target_paragraph_id'] else 'CONTEXT',p['paragraph_id'],p['section_title'])
  for b in p['blocks']:print(b['block_id'],b['kind'],b['source_spans'],strip_comments(b['raw']))
