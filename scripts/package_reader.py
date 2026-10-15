"""Package only the public reader, never private mappings or research source text."""
import sys,zipfile,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from physstyle.common import write_json,now
root=Path('reader');target=Path('deliverables/PhysWhen-anonymous-reader.zip');target.parent.mkdir(exist_ok=True)
files=sorted(p for p in root.rglob('*') if p.is_file() and not p.is_symlink() and p.name!='.DS_Store')
with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for p in files:
  name='PhysWhen-reader/'+p.relative_to(root).as_posix()
  info=zipfile.ZipInfo(name,date_time=(2026,10,14,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o644<<16
  z.writestr(info,p.read_bytes())
with zipfile.ZipFile(target) as z:
 assert z.testzip() is None
 assert all(n.startswith('PhysWhen-reader/') and '..' not in Path(n).parts for n in z.namelist())
 assert not any('private' in n or 'experiments/' in n or 'data/raw/' in n for n in z.namelist())
write_json('reports/reader_package.json',{'created_at':now(),'file':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'files':len(files),'bytes':target.stat().st_size,'includes':'public reader and bundled KaTeX 0.16.22 with LICENSE','excludes':'private mapping, reference answers, research source fulltext, real or test responses'})
print(target,target.stat().st_size)
