"""Serialized public requests; disk cache, verified TLS, bounded retries."""
import email.utils, fcntl, json, ssl, time, urllib.request, urllib.error
from pathlib import Path
from .common import digest, now, read_json, write_json, append_jsonl
class Fetcher:
    def __init__(self,root,interval=3.1,retries=3,max_bytes=50*1024**2,cache_limit=3*1024**3,offline=False):
        self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True)
        self.interval=max(3.1,interval);self.retries=retries;self.max_bytes=max_bytes;self.cache_limit=cache_limit;self.offline=offline
    def get(self,url):
        if not url.startswith('https://'):raise ValueError('HTTPS required')
        key=digest(url.encode());p=self.root/(key+'.bin');meta=self.root/(key+'.json')
        with (self.root/'network.lock').open('a+') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            if p.exists() and meta.exists():
                b=p.read_bytes();m=read_json(meta)
                if digest(b)!=m['sha256']:raise ValueError('cache digest mismatch')
                return b,m
            if self.offline:raise RuntimeError('offline cache miss: '+url)
            used=sum(x.stat().st_size for x in self.root.rglob('*') if x.is_file())
            for attempt in range(self.retries+1):
                state=read_json(self.root/'rate.json',{})
                time.sleep(max(0,state.get('next_start',0)-time.time()))
                write_json(self.root/'rate.json',{'next_start':time.time()+self.interval})
                req=urllib.request.Request(url,headers={'User-Agent':'PhysWhen/0.1 (bounded local research; single connection)'})
                try:
                    ctx=ssl.create_default_context(cafile='/etc/ssl/cert.pem')
                    with urllib.request.urlopen(req,timeout=45,context=ctx) as r:
                        b=r.read(self.max_bytes+1);final=r.url
                        if len(b)>self.max_bytes or used+len(b)>self.cache_limit:raise ValueError('download/cache size limit')
                        if not final.startswith('https://'):raise ValueError('insecure redirect')
                        m={'url':url,'final_url':final,'retrieved_at':now(),'sha256':digest(b),'bytes':len(b),'content_type':r.headers.get('Content-Type'),'status':r.status}
                    p.write_bytes(b);write_json(meta,m);append_jsonl(self.root/'requests.jsonl',m);return b,m
                except urllib.error.HTTPError as e:
                    append_jsonl(self.root/'requests.jsonl',{'url':url,'time':now(),'status':e.code,'attempt':attempt})
                    if e.code not in (429,500,502,503,504) or attempt==self.retries:raise
                    delay=retry_delay(e.headers.get('Retry-After'),attempt);e.close()
                    if delay>900:raise RuntimeError('Retry-After exceeds bounded run; defer without retrying early')
                    write_json(self.root/'rate.json',{'next_start':time.time()+max(self.interval,delay)})
                except (urllib.error.URLError,TimeoutError) as e:
                    append_jsonl(self.root/'requests.jsonl',{'url':url,'time':now(),'error':str(e),'attempt':attempt})
                    if attempt==self.retries:raise
                    write_json(self.root/'rate.json',{'next_start':time.time()+max(self.interval,2**attempt)})
def retry_delay(value,attempt,clock=time.time):
    if value:
        try:return max(0,float(value))
        except ValueError:
            try:return max(0,email.utils.parsedate_to_datetime(value).timestamp()-clock())
            except (ValueError,TypeError):pass
    return 2**attempt
