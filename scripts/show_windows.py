import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from physstyle.common import *
ws=read_jsonl('data/annotations/tasks.jsonl')
start=int(sys.argv[1]);end=int(sys.argv[2])
for n,w in enumerate(ws[start:end],start):
 print(f'\n=== {n} {w["window_id"]} target={w["target_block_id"]} role={w["section_role"]} ===')
 for p in w['context']:
  print('PARA',p['paragraph_id'],'TARGET' if p['paragraph_id']==w['target_paragraph_id'] else 'CONTEXT')
  for b in p['blocks']:
   loc=';'.join(f'{s["source_file"]}:{s["line_start"]}-{s["line_end"]}' for s in b['source_spans'])
   print(f'[{b["kind"]} {b["block_id"]} {loc}]',b['raw'])
