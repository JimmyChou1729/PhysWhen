import html, re, random, urllib.parse, xml.etree.ElementTree as ET, email.utils
from datetime import datetime, timezone
from pathlib import Path
from .common import *
NS={'a':'http://www.w3.org/2005/Atom','o':'http://a9.com/-/spec/opensearch/1.1/'}
def atom(b):
    root=ET.fromstring(b);out=[]
    for e in root.findall('a:entry',NS):
        identity=e.findtext('a:id','',NS).split('/')[-1];pid=re.sub(r'v\d+$','',identity)
        if not re.fullmatch(r'\d{4}\.\d{4,5}',pid):continue
        out.append({'paper_id':pid,'title':' '.join(e.findtext('a:title','',NS).split()),'abstract':' '.join(e.findtext('a:summary','',NS).split()),'authors':[x.findtext('a:name','',NS) for x in e.findall('a:author',NS)],'categories':[x.attrib['term'] for x in e.findall('a:category',NS)],'first_submission':e.findtext('a:published','',NS),'metadata_latest':identity})
    return int(root.findtext('o:totalResults','0',NS)),out

@corpus_transaction
def discover(fetch,cfg):
    path=Path('data/manifests/candidates.jsonl');rows=read_jsonl(path);done=read_json('data/manifests/sampling.json',{})
    strata=[(y,c) for y in cfg['years'] for c in cfg['categories']];random.Random(cfg['seed']).shuffle(strata)
    for y,c in strata:
        key=f'{y}:{c}'
        if key in done:continue
        query=f'cat:{c} AND submittedDate:[{y}01010000 TO {y}12312359]'
        base='https://export.arxiv.org/api/query?'+urllib.parse.urlencode({'search_query':query,'sortBy':'submittedDate','sortOrder':'ascending'})
        total,_=atom(fetch.get(base+'&start=0&max_results=1')[0])
        n=min(cfg['per_stratum'],total);rng=random.Random(f'{cfg["seed"]}:{key}');start=rng.randrange(max(1,total-n+1))
        _,batch=atom(fetch.get(base+f'&start={start}&max_results={n}')[0]) if n else (0,[])
        for i,r in enumerate(batch):r.update(sampling_stratum=key,sampling_year=y,sampling_category=c,stratum_rank=i,screening='unresolved',screening_reason='pending content screening',training_eligible='unreviewed',redistribution_eligible='unreviewed')
        rows.extend(batch);rows=deduplicate(rows)[:cfg['candidate_cap']]
        done[key]={'total':total,'random_block_start':start,'returned':len(batch),'method':'uniform contiguous block within year/category; clustered time sample'}
        write_jsonl(path,rows);write_json('data/manifests/sampling.json',done)
        print('metadata',key,len(batch),'unique',len(rows),flush=True)
    return rows

def deduplicate(rows):
    found={}
    for r in rows:
        if r['paper_id'] in found:
            old=found[r['paper_id']];old['categories']=sorted(set(old['categories']+r['categories']))
            old.setdefault('also_sampled_in',[]).append(r['sampling_stratum'])
        else:found[r['paper_id']]=dict(r)
    return list(found.values())

def parse_abs(b,cutoff):
    s=b.decode('utf-8',errors='replace');plain=html.unescape(re.sub('<[^>]+>',' ',s));plain=' '.join(plain.split())
    versions=[]
    for m in re.finditer(r'\[v(\d+)\]\s*(?:[^\d\[]{0,12})?(\d{1,2}\s+[A-Z][a-z]{2}\s+\d{4}\s+\d\d:\d\d:\d\d\s+(?:UTC|GMT))',plain):
        d=datetime.strptime(m[2].replace('GMT','UTC'),'%d %b %Y %H:%M:%S UTC').replace(tzinfo=timezone.utc)
        versions.append({'version':int(m[1]),'date':d.isoformat(),'evidence':m[0]})
    eligible=[v for v in versions if '2010-01-01'<=v['date'][:10]<=cutoff]
    if not eligible:raise ValueError('no verified historical version date')
    v=max(eligible,key=lambda x:x['version'])
    licenses=re.findall(r'href=["\'](https?://(?:creativecommons\.org|arxiv\.org/licenses)/[^"\']+)',s)
    v['license_url']=licenses[0] if licenses else None
    return v

def acquire(fetch,candidate,cfg):
    r=dict(candidate);pid=r['paper_id']
    b,m=fetch.get(f'https://export.arxiv.org/abs/{pid}')
    v=parse_abs(b,cfg['cutoff']);identity=f'{pid}v{v["version"]}'
    # Read selected version page separately: licenses can differ between versions.
    selected,sm=fetch.get(f'https://export.arxiv.org/abs/{identity}')
    selected_html=selected.decode(errors='replace')
    if not re.search(r'<title[^>]*>\s*\['+re.escape(identity)+r'\]',selected_html,re.I):raise ValueError('selected version page identity mismatch')
    if not urllib.parse.urlparse(sm['final_url']).path.rstrip('/').endswith('/'+identity):raise ValueError('selected page redirect lost version')
    sv=parse_abs(selected,cfg['cutoff']);license_urls=re.findall(r'href=["\'](https?://(?:creativecommons\.org|arxiv\.org/licenses)/[^"\']+)',selected.decode(errors='replace'))
    body,bm=fetch.get(f'https://export.arxiv.org/src/{identity}')
    if urllib.parse.urlparse(bm['final_url']).path.rstrip('/') not in ('/src/'+identity,'/e-print/'+identity):raise ValueError('source redirect lost exact version')
    if bm['content_type'] and 'html' in bm['content_type']:raise ValueError('HTML error instead of source')
    r.update(version_identity_verified=True,version=v['version'],version_date=v['date'],version_evidence=v['evidence'],version_metadata_sha256=m['sha256'],selected_metadata_sha256=sm['sha256'],source_url=bm['url'],source_sha256=bm['sha256'],retrieved_at=bm['retrieved_at'],license_url=license_urls[0] if license_urls else None,license_evidence={'url':sm['url'],'sha256':sm['sha256'],'scope':'selected version page'},parse_status='pending')
    p=Path('data/raw/papers')/identity;p.mkdir(parents=True,exist_ok=True);(p/'source.bin').write_bytes(body);(p/'metadata.html').write_bytes(selected)
    return r,p/'source.bin'

@corpus_transaction
def import_screening(path):
    """Import only scope decisions, bound to the frozen candidate title/abstract."""
    rows=read_jsonl('data/manifests/candidates.jsonl');lookup={r['paper_id']:r for r in rows};batch=read_jsonl(path);seen=set()
    for decision in batch:
        pid=decision['paper_id']
        if pid in seen or pid not in lookup:raise ValueError('duplicate/unknown screening identity')
        seen.add(pid);r=lookup[pid]
        expected=digest((r['title']+'\n'+r['abstract']).encode())
        if decision.get('screening_source_sha256')!=expected:raise ValueError('screening source snapshot mismatch')
        if decision.get('screening') not in ('include','exclude','unresolved') or not decision.get('screening_reason'):raise ValueError('invalid scope decision')
        for key in ('screening','screening_reason','screening_method','screening_model','scope_body_audit'):
            if key in decision:r[key]=decision[key]
    write_jsonl('data/manifests/candidates.jsonl',rows)
    corpus=read_jsonl('data/manifests/corpus.jsonl')
    for r in corpus:
        if r['paper_id'] in seen:
            for key in ('screening','screening_reason','screening_method','screening_model','scope_body_audit'):
                if key in lookup[r['paper_id']]:r[key]=lookup[r['paper_id']][key]
    if corpus:write_jsonl('data/manifests/corpus.jsonl',corpus)
    return len(batch)
