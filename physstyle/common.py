import hashlib, json, os, re
from pathlib import Path
from datetime import datetime, timezone

def now(): return datetime.now(timezone.utc).isoformat()
def digest(b): return hashlib.sha256(b).hexdigest()
def read_json(p, default=None): return json.loads(Path(p).read_text()) if Path(p).exists() else default
def write_json(p, obj):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_suffix(p.suffix+'.tmp'); tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n'); tmp.replace(p)
def read_jsonl(p): return [json.loads(x) for x in Path(p).read_text().splitlines() if x.strip()] if Path(p).exists() else []
def write_jsonl(p, rows):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in rows));tmp.replace(p)
def append_jsonl(p,obj):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('a') as f:f.write(json.dumps(obj,ensure_ascii=False)+'\n')
def words(s): return re.findall(r"[A-Za-z]+(?:['’-][A-Za-z]+)*",s)
def quantile(a,q):
    if not a:return None
    a=sorted(a);x=(len(a)-1)*q;i=int(x);return a[i]+(a[min(i+1,len(a)-1)]-a[i])*(x-i)
def summary(a):
    v=[x for x in a if x is not None]
    return {'n':len(v),'missing':len(a)-len(v),'q25':quantile(v,.25),'median':quantile(v,.5),'q75':quantile(v,.75),'p90':quantile(v,.9)}
def safe_child(root,name):
    root=Path(root).resolve();p=(root/name).resolve()
    if Path(name).is_absolute() or not p.is_relative_to(root):raise ValueError('unsafe path')
    return p

# Whole read/modify/write transactions share one process lock. Atomic file replacement
# alone does not protect against concurrent writers using stale manifest snapshots.
from contextlib import contextmanager
from functools import wraps
import fcntl
_lock_depth=0
@contextmanager
def corpus_lock():
    global _lock_depth
    if _lock_depth:
        _lock_depth+=1
        try:yield
        finally:_lock_depth-=1
        return
    with Path('.physwhen-corpus.lock').open('a+') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise RuntimeError('Corpus is being collected or analyzed by another process; retry after it finishes.') from None
        _lock_depth=1
        try:yield
        finally:
            _lock_depth=0
            fcntl.flock(lock,fcntl.LOCK_UN)
def corpus_transaction(fn):
    @wraps(fn)
    def wrapped(*args,**kwargs):
        with corpus_lock():return fn(*args,**kwargs)
    return wrapped
