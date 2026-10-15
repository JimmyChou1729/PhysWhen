"""Embed all fonts/scripts/styles in one transferable offline HTML; no private data."""
import re,base64,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from physstyle.common import *
cfg=read_json('configs/reader_current.json',{'standalone_name':'PhysWhen-group-study.html'});output_name=cfg['standalone_name']
assert Path(output_name).name==output_name and output_name.endswith('.html')
root=Path('reader');css=(root/'vendor/katex/dist/katex.min.css').read_text()
def font(m):
 path=(root/'vendor/katex/dist'/m[1].strip('\"\'')).resolve()
 if not path.is_relative_to((root/'vendor/katex/dist/fonts').resolve()):raise ValueError('unexpected CSS resource')
 mime={'.woff2':'font/woff2','.woff':'font/woff','.ttf':'font/ttf'}[path.suffix]
 return 'url(data:'+mime+';base64,'+base64.b64encode(path.read_bytes()).decode()+')'
css=re.sub(r'url\(([^)]+)\)',font,css)
html=(root/'index.html').read_text();html=re.sub(r'<link rel="stylesheet"[^>]+>', '',html);html=re.sub(r'<script defer src="[^"]+"></script>','',html)
html=html.replace('</head>','<style>'+css+'\n'+(root/'style.css').read_text()+'</style></head>')
js=''
for resource_name in ['vendor/katex/dist/katex.min.js','vendor/katex/dist/contrib/auto-render.min.js','data.js','app.js']:
 code=(root/resource_name).read_text();code=re.sub(r'//# sourceMappingURL=.*','',code);code=re.sub(r'</script',lambda m:'<\\/script',code,flags=re.I);js+='<script>'+code+'\n</script>\n'
license=(root/'vendor/katex/LICENSE').read_text()
html=html.replace('</body>','<!-- Bundled KaTeX 0.16.22 license:\n'+license+'\n-->\n'+js+'</body>')
require_no_external=re.findall(r'<(?:script|link)\b[^>]*\b(?:src|href)=',html,re.I)
assert not require_no_external
for path in [Path('deliverables')/output_name,root/output_name]:
 path.parent.mkdir(parents=True,exist_ok=True);path.write_text(html)
write_json('reports/standalone_reader_build.json',{'built_at':now(),'dataset_id':read_json('experiments/reader_pack_manifest.json')['dataset_id'],'path':str(Path('deliverables')/output_name),'bytes':len(html.encode()),'sha256':digest(html.encode()),'external_dependencies':False,'contents':'six unchanged masked generated texts, subjective ratings, randomization, offline export, bundled KaTeX MIT license','excluded':'condition key, knowledge questions, reference answers, historical corpus fulltexts, responses'})
print('Standalone HTML bytes:',len(html.encode()))
