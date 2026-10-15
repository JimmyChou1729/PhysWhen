import io,json,os,tarfile,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
from physstyle.common import *
from physstyle.parse import parse_tex,extract_source,sentences
from physstyle.corpus import parse_abs,deduplicate
from physstyle.features import measure,freeze_split
from physstyle.network import Fetcher,retry_delay
from physstyle.annotations import validate_record
from physstyle.training import denoise,export_training
SYNTHETIC=r'''\documentclass{article}
\begin{document}
\title{Not body title}\maketitle
\begin{abstract}Short abstract.\end{abstract}
\section{Introduction}
We define $x$ as a parameter. Eq.\ \eqref{one} is useful because it sets the scale.
\begin{equation}\label{one}
x=1
\end{equation}
This is a simple illustrative equation. However, its scope is limited.

A new paragraph has \emph{English prose} and inline $y=x^2$ content.
\begin{align}
y&=2\\
z&=3
\end{align}
\begin{equation}w=4\end{equation}
\appendix
\section{Details}
These appendix words are separate.
\begin{thebibliography}{9}\bibitem{a}Polluting bibliography words.\end{thebibliography}
\end{document}
'''
class CoreTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
 def tearDown(self):self.tmp.cleanup()
 def parse(self):return parse_tex(SYNTHETIC.encode(),self.root/'source')
 def test_math_order_paragraphs_and_exclusions(self):
  d=self.parse();ps=d['paragraphs'];body=[p for p in ps if p['section_role']=='introduction'];self.assertEqual(len(body),2)
  self.assertEqual(sum(b['kind']=='display_math' for p in body for b in p['blocks']),3)
  self.assertIn('inline_math',[b['kind'] for b in body[0]['blocks']]);self.assertTrue(any(p['section_role']=='appendix' for p in ps))
  text=' '.join(b.get('text','') for p in ps for b in p['blocks']);self.assertNotIn('Polluting',text);self.assertNotIn('Not body title',text)
 def test_sentence_abbreviation(self):self.assertEqual(len(sentences('Eq. 3 holds. We use Fig. 2.')),2)
 def test_source_locations(self):
  d=self.parse()
  for p in d['paragraphs']:
   for b in p['blocks']:
    for s in b['source_spans']:
     lines=(Path(d['source_root'])/s['source_file']).read_text().splitlines();self.assertIn(b['raw'].strip().splitlines()[0], '\n'.join(lines[s['line_start']-1:s['line_end']]))
 def test_cutoff_latest_eligible(self):
  h=b'<div>[v1] Tue, 4 Jan 2011 00:00:00 UTC [v2] Wed, 4 Jan 2023 00:00:00 UTC</div>'
  self.assertEqual(parse_abs(h,'2021-12-31')['version'],1)
  with self.assertRaises(ValueError):parse_abs(b'[v1] Wed, 4 Jan 2023 00:00:00 UTC','2021-12-31')
 def test_crosslist_dedup(self):
  x={'paper_id':'1001.0001','categories':['gr-qc'],'sampling_stratum':'2010:gr-qc'};y={**x,'categories':['hep-th'],'sampling_stratum':'2010:hep-th'}
  z=deduplicate([x,y]);self.assertEqual(len(z),1);self.assertEqual(z[0]['categories'],['gr-qc','hep-th'])
 def archive(self,name,kind=None):
  b=io.BytesIO()
  with tarfile.open(fileobj=b,mode='w') as t:
   m=tarfile.TarInfo(name);m.size=1
   if kind:m.type=kind;m.linkname='/tmp/nope'
   t.addfile(m,io.BytesIO(b'x'))
  return b.getvalue()
 def test_archive_traversal_absolute_and_links(self):
  for name,kind in [('../x.tex',None),('/x.tex',None),('x.tex',tarfile.SYMTYPE),('x.tex',tarfile.LNKTYPE)]:
   with self.subTest(name=name,kind=kind),self.assertRaises(ValueError):extract_source(self.archive(name,kind),self.root/'a')
 def test_archive_bomb(self):
  with patch('physstyle.parse.MAX_EXPANDED',0),self.assertRaises(ValueError):extract_source(self.archive('a.tex'),self.root/'a')
 def test_include_cycle(self):
  b=io.BytesIO()
  with tarfile.open(fileobj=b,mode='w') as t:
   for name,s in [('main.tex',r'\begin{document}'+'\n'+r'\input{a}'+'\n'+r'\end{document}'),('a.tex',r'\input{main}')]:
    m=tarfile.TarInfo(name);raw=s.encode();m.size=len(raw);t.addfile(m,io.BytesIO(raw))
  with self.assertRaises(ValueError):parse_tex(b.getvalue(),self.root/'a')
 def test_missing_is_not_zero(self):
  d={'paper_id':'synthetic','version':1,'split':'discovery','paragraphs':[]};m=measure(d,{'D06':{'definition':[]}})
  self.assertIsNone(m['metrics']['D03_display_per_1000_words']);self.assertEqual(summary([None,0])['missing'],1)
 def test_adjacent_math_zero_and_boundary_na(self):
  d=self.parse();d.update(paper_id='synthetic',version=1,split='discovery');m=measure(d,{'D06':{}});r=[x for x in m['records'] if x['feature']=='D04']
  self.assertEqual(r[-1]['before'],0);self.assertIsNone(r[-1]['after'])
 def test_retry_after(self):
  self.assertEqual(retry_delay('8',0),8);self.assertEqual(retry_delay('Wed, 21 Oct 2015 07:28:00 GMT',0,lambda:1445412470),10)
 def test_cache_replay_no_network(self):
  u='https://example.org/a';b=b'cached';p=self.root/(digest(u.encode())+'.bin');p.write_bytes(b);write_json(p.with_suffix('.json'),{'sha256':digest(b)})
  with patch('urllib.request.urlopen',side_effect=AssertionError('network')):self.assertEqual(Fetcher(self.root).get(u)[0],b)
 def test_cache_corruption_rejected(self):
  u='https://example.org/a';p=self.root/(digest(u.encode())+'.bin');p.write_bytes(b'bad');write_json(p.with_suffix('.json'),{'sha256':digest(b'good')})
  with self.assertRaises(ValueError):Fetcher(self.root).get(u)
 def test_rate_limit_starts_and_retry(self):
  import urllib.error
  class Response:
   url='https://example.org/a';headers={};status=200
   def __enter__(self):return self
   def __exit__(self,*args):pass
   def read(self,n):return b'ok'
  clock=[100.];starts=[]
  def sleep(s):clock[0]+=s
  def call(*args,**kw):
   starts.append(clock[0])
   if len(starts)==1:raise urllib.error.HTTPError(Response.url,429,'slow',{'Retry-After':'7'},None)
   return Response()
  with patch('physstyle.network.time.time',side_effect=lambda:clock[0]),patch('physstyle.network.time.sleep',side_effect=sleep),patch('urllib.request.urlopen',side_effect=call):
   Fetcher(self.root).get(Response.url)
  self.assertGreaterEqual(starts[1]-starts[0],7)
 def test_annotation_wrong_window_and_quote(self):
  d=self.parse();p=d['paragraphs'][1];b=next(b for b in p['blocks'] if b['kind']=='display_math');span=b['source_spans'][0]
  w={'window_id':'w','paper_id':'synthetic','version':1,'split':'discovery','target_block_id':b['block_id'],'context':[p],'source_root':d['source_root'],'source_files':d['source_files']}
  r={k:w[k] for k in ('window_id','paper_id','version','split','target_block_id')};r.update(feature_id='S02',label='uncertain',confidence='low',annotation_method='host_agent',context_sufficient=False,rationale='test',evidence=[{**span,'exact_quote':b['raw'].strip()}])
  validate_record(r,{'w':w});r['evidence'][0]['exact_quote']='invented';
  with self.assertRaises(ValueError):validate_record(r,{'w':w})
 def test_denoise_math_exact(self):
  p=self.parse()['paragraphs'][1];i,t,ops=denoise(p,123)
  for b in p['blocks']:
   if b['kind']!='prose':self.assertIn(b['raw'],i)
  for op in ops:self.assertIn(op['original'],{'the','a','an'})
 def test_split_and_training_gates(self):
  cwd=os.getcwd()
  try:
   os.chdir(self.root);rows=[{'paper_id':str(i),'title':'Unique paper '+str(i)*10,'authors':['Author '+str(i)],'screening':'include','version':1,'training_eligible':'unreviewed','license_url':None} for i in range(10)]
   docs={r['paper_id']:{'usable':True,'normalized_body_sha256':digest(r['title'].encode()),'paragraphs':[]} for r in rows}
   split=freeze_split(rows,docs);self.assertEqual(collections_count(split,'heldout'),2);self.assertEqual(freeze_split(rows,docs),split)
   for pid,d in docs.items():d['split']=split[pid]
   self.assertEqual(export_training(rows,docs)['records_lm'],0)
   # Family-equivalent papers never cross split.
   rows.append({**rows[0],'paper_id':'duplicate'});docs['duplicate']={**docs['0']};sp=freeze_split(rows,docs);self.assertEqual(sp['duplicate'],sp['0'])
  finally:os.chdir(cwd)
def collections_count(d,v):return sum(x==v for x in d.values())
if __name__=='__main__':unittest.main()

class MacroTests(unittest.TestCase):
 def test_nested_wrapper_and_chain(self):
  source=r'''\documentclass{article}
\newcommand{\be}{\begin{equation}\begin{aligned}}
\newcommand{\ee}{\end{aligned}\end{equation}}
\def\ba{\begin{eqnarray}}\def\ea{\end{eqnarray}}\def\b{\ba}\def\e{\ea}
\newcommand{\aln}[1]{\begin{align}#1\end{align}}
\begin{document}\section{Introduction}
Here is prose.\be x=1\ee More prose.\b y=2\e More prose.\aln{z=3} Final prose.
\end{document}'''
  with tempfile.TemporaryDirectory() as t:d=parse_tex(source.encode(),Path(t)/'s')
  blocks=[b for p in d['paragraphs'] for b in p['blocks']]
  self.assertEqual(sum(b['kind']=='display_math' for b in blocks),3)
  self.assertNotIn('x',' '.join(b.get('text','') for b in blocks))
 def test_footnote_with_math_does_not_leak(self):
  source=r'\begin{document}\section{Introduction}Visible.\footnote{Secret $x$ leakage.} Visible again.\end{document}'
  with tempfile.TemporaryDirectory() as t:d=parse_tex(source.encode(),Path(t)/'s')
  text=' '.join(b.get('text','') for p in d['paragraphs'] for b in p['blocks']);self.assertNotIn('leakage',text)

class FidelityRegressionTests(unittest.TestCase):
 def test_comment_line_does_not_split_paragraph(self):
  s=r'\begin{document}\section{Introduction}'+'\nThe model has one parameter.\n% comment\nThe solution is unique.\n'+r'\end{document}'
  with tempfile.TemporaryDirectory() as t:d=parse_tex(s.encode(),Path(t)/'s')
  self.assertEqual(len([p for p in d['paragraphs'] if p['section_role']=='introduction']),1)
 def test_denoise_ref_argument_protected(self):
  p={'blocks':[{'block_id':'b','kind':'prose','raw':r'\eqref{a} and the result.'}]}
  for seed in range(100):self.assertIn(r'\eqref{a}',denoise(p,seed)[0])
 def test_local_style_and_empheq(self):
  source=r'''\begin{document}\newcommand{\newc}{\newcommand}
\newc{\be}{\begin{equation}}\newc{\ee}{\end{equation}}
\section{Introduction}Before.\be x=1\ee After.
\begin{empheq}[box=\fbox]{align}y=2\end{empheq}\end{document}'''
  with tempfile.TemporaryDirectory() as t:d=parse_tex(source.encode(),Path(t)/'s')
  self.assertEqual(sum(b['kind']=='display_math' for p in d['paragraphs'] for b in p['blocks']),2)

class SplitRegressionTests(unittest.TestCase):
 def test_incremental_and_excluded(self):
  cwd=os.getcwd()
  with tempfile.TemporaryDirectory() as t:
   try:
    os.chdir(t);rows=[];docs={}
    for i in range(10):
     pid=str(i);r={'paper_id':pid,'title':'Title '+chr(65+i)*12,'authors':[],'screening':'include'};rows.append(r);docs[pid]={'usable':True,'normalized_body_sha256':digest(pid.encode())};sp=freeze_split(rows,docs)
    self.assertEqual(sum(x=='heldout' for x in sp.values()),2)
    rows[0]['screening']='exclude';self.assertNotIn('0',freeze_split(rows,docs))
   finally:os.chdir(cwd)

class IncludeLocationRegression(unittest.TestCase):
 def test_include_without_final_newline(self):
  b=io.BytesIO()
  with tarfile.open(fileobj=b,mode='w') as t:
   for name,s in [('main.tex','\\begin{document}\n\\section{Introduction}\n\\input{a}\n\\input{b}\n\\end{document}\n'),('a.tex','First paragraph without trailing newline.'),('b.tex','Second statement.\n\nThird statement.\n')]:
    m=tarfile.TarInfo(name);raw=s.encode();m.size=len(raw);t.addfile(m,io.BytesIO(raw))
  with tempfile.TemporaryDirectory() as td:
   d=parse_tex(b.getvalue(),Path(td)/'source')
   blocks=[x for p in d['paragraphs'] for x in p['blocks'] if 'Third statement' in x['raw']]
   self.assertTrue(any(s['source_file']=='b.tex' and s['line_start']<=3<=s['line_end'] for s in blocks[0]['source_spans']))

class ExportProvenanceTests(unittest.TestCase):
 def test_scope_version_and_frozen_split(self):
  cwd=os.getcwd()
  with tempfile.TemporaryDirectory() as t:
   try:
    os.chdir(t);paragraph={'paragraph_id':'p0','section_id':'s1','section_title':'Theory','section_role':'technical_body','word_count':4,'blocks':[{'block_id':'b0','kind':'prose','raw':'The result is exact.','source_spans':[{'source_file':'synthetic.tex','line_start':1,'line_end':1}]}]}
    r={'paper_id':'synthetic','version':2,'screening':'include','training_eligible':'yes','license_url':'https://creativecommons.org/licenses/by/4.0/','source_url':'https://example.org/synthetic','source_sha256':'hash'}
    d={'paper_id':'synthetic','version':2,'source_sha256':'hash','split':'discovery','usable':True,'paragraphs':[paragraph]}
    write_json('data/splits/frozen.json',{'assignments':{'synthetic':'discovery'}});write_jsonl('data/manifests/license_reviews.jsonl',[{'paper_id':'synthetic','version':2,'training_eligible':'yes','license_url':r['license_url'],'review_basis':'Synthetic fixture, not a real license review'}])
    self.assertEqual(export_training([r],{'synthetic':d})['records_lm'],1)
    self.assertEqual(export_training([{**r,'screening':'exclude'}],{'synthetic':d})['records_lm'],0)
    self.assertEqual(export_training([r],{'synthetic':{**d,'usable':False}})['records_lm'],0)
    with self.assertRaises(ValueError):export_training([r],{'synthetic':{**d,'version':1}})
    write_json('data/splits/frozen.json',{'assignments':{'synthetic':'heldout'}})
    with self.assertRaises(ValueError):export_training([r],{'synthetic':d})
   finally:os.chdir(cwd)
 def test_comments_removed_math_and_refs_retained(self):
  from physstyle.parse import strip_comments
  p={'blocks':[{'block_id':'b0','kind':'prose','raw':'The result. % hidden old claim\n'+r'\eqref{a}'},{'block_id':'b1','kind':'display_math','raw':'\\[x=1 % obsolete x=2\n\\]'}]}
  a,b,ops=denoise(p,1);self.assertNotIn('hidden old claim',b);self.assertNotIn('obsolete',b);self.assertIn(r'\eqref{a}',a);self.assertIn('x=1',a);self.assertEqual(a[a.index('\\['):],b[b.index('\\['):])

class ParserBoundaryTests(unittest.TestCase):
 def test_commented_include_no_final_newline(self):
  b=io.BytesIO()
  with tarfile.open(fileobj=b,mode='w') as t:
   for name,s in [('main.tex','\\begin{document}\n\\section{Introduction}\n\\input{a}% comment\n\\end{document}'),('a.tex','Included prose survives.')]:
    m=tarfile.TarInfo(name);raw=s.encode();m.size=len(raw);t.addfile(m,io.BytesIO(raw))
  with tempfile.TemporaryDirectory() as td:d=parse_tex(b.getvalue(),Path(td)/'source')
  self.assertIn('Included prose survives.',' '.join(b.get('text','') for p in d['paragraphs'] for b in p['blocks']));self.assertNotIn('inline_include_unexpanded',d['warnings'])
 def test_appendix_environment(self):
  s=r'\begin{document}\section{Main}Main prose.\begin{appendix}\section{Derivation}Separate appendix.\end{appendix}\end{document}'
  with tempfile.TemporaryDirectory() as td:d=parse_tex(s.encode(),Path(td)/'source')
  self.assertEqual(d['paragraphs'][-1]['section_role'],'appendix')
 def test_comment_between_equations_is_not_prose(self):
  s='\\begin{document}\\section{Main}\n\\[x=1\\]\n%comment\n\\[y=2\\]\n\\end{document}'
  with tempfile.TemporaryDirectory() as td:d=parse_tex(s.encode(),Path(td)/'source')
  d.update(paper_id='synthetic',version=1,split='discovery');r=[x for x in measure(d,{'D06':{}})['records'] if x['feature']=='D04'];self.assertEqual(r[0]['after'],0)

class ScreeningImportTests(unittest.TestCase):
 def test_exclusion_updates_cached_manifest(self):
  from physstyle.corpus import import_screening
  cwd=os.getcwd()
  with tempfile.TemporaryDirectory() as td:
   try:
    os.chdir(td);row={'paper_id':'synthetic','title':'A test','abstract':'A synthetic fixture','screening':'include'};write_jsonl('data/manifests/candidates.jsonl',[row]);write_jsonl('data/manifests/corpus.jsonl',[row]);decision={'paper_id':'synthetic','screening':'exclude','screening_reason':'fixture only','screening_source_sha256':digest((row['title']+'\n'+row['abstract']).encode())};write_jsonl('decision.jsonl',[decision]);self.assertEqual(import_screening('decision.jsonl'),1);self.assertEqual(read_jsonl('data/manifests/corpus.jsonl')[0]['screening'],'exclude')
    decision['screening_source_sha256']='bad';write_jsonl('decision.jsonl',[decision])
    with self.assertRaises(ValueError):import_screening('decision.jsonl')
   finally:os.chdir(cwd)
