"""Build a strictly local anonymous reading pack; never embeds answers or arm mapping."""
import sys,random,secrets
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from physstyle.common import *
cfg=read_json('configs/reader_current.json',{'experiment_root':'experiments/cosmology_v2','round_label':'01','protocol':'cosmology-subjective-v2'})
experiment=Path(cfg['experiment_root']);private=experiment/'reader_assignment_private.json';mapping=read_json(private)
if not mapping:
 choices=['A','B','A'];random.SystemRandom().shuffle(choices);mapping={f'C{i+1}':{'P':a,'Q':'B' if a=='A' else 'A'} for i,a in enumerate(choices)};write_json(private,mapping)
pack={'schema':'physwhen.reader.v2','title':'PhysWhen 宇宙学阅读对照','round_label':cfg['round_label'],'cases':[]}
for i,cid in enumerate(['C1','C2','C3']):
 case={'id':cid,'name':['宇宙背景膨胀','原初扰动与引力波','暗物质与结构形成'][i],'versions':{}}
 if cfg.get('paper_format'):
  brief=read_json(experiment/'briefs'/f'{cid}.json');case.update(paper_title=brief['paper_title'],reference=brief['reference'])
 for alias,arm in mapping[cid].items():case['versions'][alias]=(experiment/'outputs'/arm/f'{cid}.md').read_text()
 pack['cases'].append(case)
pack['dataset_id']=digest(json.dumps(pack,sort_keys=True).encode())[:20]
Path('reader/data.js').write_text('window.READING_PACK='+json.dumps(pack,ensure_ascii=False).replace('<','\\u003c')+';\n')
previous=read_json('experiments/reader_pack_manifest.json')
if previous:write_json(f'experiments/reader_pack_manifests/{previous["dataset_id"]}.json',previous)
write_json('experiments/reader_pack_manifest.json',{'dataset_id':pack['dataset_id'],'built_at':now(),'cases':3,'texts':6,'private_assignment':str(private),'private_assignment_sha256':digest(private.read_bytes()),'public_files':['reader/index.html','reader/app.js','reader/style.css','reader/data.js'],'answers_embedded':False,'network_dependencies':False,'protocol':cfg['protocol'],'round_label':cfg['round_label'],'experiment_root':str(experiment),'randomization':'case order and X/Y to P/Q assignment, saved per anonymous participant','prior_exposure':'self-report optional; condition labels masked, full blinding not guaranteed','knowledge_questions':False})
write_json(f'experiments/reader_pack_manifests/{pack["dataset_id"]}.json',read_json('experiments/reader_pack_manifest.json'))
print(pack['dataset_id'])
