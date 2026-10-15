"""Append immutable initial-map snapshots; never replace an earlier annotation."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from physstyle.common import *
from physstyle.structure import validate_map
manifest=Path('data/structure/initial_annotation_hashes.json');old=read_json(manifest,{'files':[]})
for row in old['files']:
 if digest(Path(row['path']).read_bytes())!=row['sha256']:raise ValueError('existing initial map hash changed')
protocol=read_json('data/structure/protocol.json');count=0;dest=Path('data/structure/initial_annotations');dest.mkdir(exist_ok=True)
for path in sorted(Path('data/structure/annotations').glob('*.json')):
 target=dest/path.name
 if target.exists():continue
 errors=validate_map(read_json(path),read_json('data/structure/papers/'+path.name),protocol)
 if errors:raise ValueError(f'{path}: {errors}')
 target.write_bytes(path.read_bytes());count+=1
write_json(manifest,{'files':[{'path':str(p),'sha256':digest(p.read_bytes())} for p in sorted(dest.glob('*.json'))]});print('new initial maps frozen:',count)
