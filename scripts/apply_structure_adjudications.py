"""Replay explicitly approved parent adjudications from immutable initial maps."""
import sys,copy,collections
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from physstyle.common import *
from physstyle.structure import validate_map
ops=collections.defaultdict(list)
for row in read_jsonl('data/structure/adjudications.jsonl'):
 if row['decision']=='accept':
  if row.get('operation') not in {'replace','remove','splice','append'}:raise ValueError('unknown adjudication operation')
  if not isinstance(row.get('path'),str) or not row['path'].startswith('/'):raise ValueError('invalid adjudication path')
  if row['operation']=='splice' and not isinstance(row.get('suggested'),list):raise ValueError('splice requires a list')
  ops[row['paper_id']].append(row)
protocol=read_json('data/structure/protocol.json');expected={x['path']:x['sha256'] for x in read_json('data/structure/initial_annotation_hashes.json')['files']};pending=[]
for pid,changes in ops.items():
 path=Path(f'data/structure/initial_annotations/{pid}.json')
 if digest(path.read_bytes())!=expected[str(path)]:raise ValueError('initial map changed '+pid)
 r=read_json(path)
 def locate(pointer):
  parts=pointer.strip('/').split('/');obj=r
  for part in parts[:-1]:obj=obj[int(part)] if isinstance(obj,list) else obj[part]
  key=(len(obj) if parts[-1]=='-' else int(parts[-1])) if isinstance(obj,list) else parts[-1]
  return obj,key
 # Check all old values against the immutable base before making any changes.
 for op in changes:
  obj,key=locate(op['path'])
  if op.get('operation')=='append':
   if not isinstance(obj,list) or key!=len(obj) or op['original'] is not None:raise ValueError('invalid append')
  elif obj[key]!=op['original']:raise ValueError('adjudication original mismatch '+pid+op['path'])
 # Scalar/object replacements precede list edits; list edits run descending indices.
 ordinary=[o for o in changes if o.get('operation','replace')=='replace']
 list_edits=[o for o in changes if o.get('operation') in {'remove','splice'}]
 for op in ordinary:
  obj,key=locate(op['path']);obj[key]=copy.deepcopy(op['suggested'])
 for op in [o for o in changes if o.get('operation')=='append']:
  obj,key=locate(op['path']);obj.append(copy.deepcopy(op['suggested']))
 for op in sorted(list_edits,key=lambda x:(x['path'].rsplit('/',1)[0],int(x['path'].rsplit('/',1)[1])),reverse=True):
  obj,key=locate(op['path'])
  if op['operation']=='remove':del obj[key]
  else:obj[key:key+1]=copy.deepcopy(op['suggested'])
 errors=validate_map(r,read_json(f'data/structure/papers/{pid}.json'),protocol)
 if errors:raise ValueError(f'{pid}: {errors}')
 pending.append((Path(f'data/structure/annotations/{pid}.json'),r))
for path,r in pending:write_json(path,r)
print('replayed',sum(map(len,ops.values())),'approved changes in',len(pending),'maps; original maps preserved')
