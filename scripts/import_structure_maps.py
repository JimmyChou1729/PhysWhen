"""Import locally produced host-agent maps after identity, quote and coverage validation."""
import argparse,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from physstyle.common import *
from physstyle.structure import validate_map
p=argparse.ArgumentParser();p.add_argument('path');p.add_argument('--replace',action='store_true',help='Explicitly replace existing maps after successful validation');a=p.parse_args()
rows=read_jsonl(a.path) if Path(a.path).suffix=='.jsonl' else [read_json(a.path)];protocol=read_json('data/structure/protocol.json');pending=[]
for r in rows:
 pid=r.get('paper_id','')
 if not isinstance(pid,str) or not pid or Path(pid).name!=pid or '/' in pid or '\\' in pid:raise ValueError('invalid paper ID')
 packet=read_json(f'data/structure/papers/{pid}.json')
 if packet is None:raise ValueError('no frozen local task '+pid)
 errors=validate_map(r,packet,protocol)
 if errors:raise ValueError(f'{pid}: {errors}')
 dest=Path(f'data/structure/annotations/{pid}.json')
 if dest.exists() and read_json(dest)!=r and not a.replace:raise ValueError('existing annotation; review and use --replace explicitly')
 pending.append((dest,r))
if len({str(p) for p,r in pending})!=len(pending):raise ValueError('duplicate records in import')
for dest,r in pending:write_json(dest,r)
print('validated/imported',len(pending),'maps; semantic correctness not certified')
