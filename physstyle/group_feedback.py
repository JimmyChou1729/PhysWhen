"""Offline subjective study: validated imports, revision reconciliation, descriptive results."""
import re,collections,csv,statistics
from pathlib import Path
from datetime import datetime
from .common import *
CASES={'C1','C2','C3'}
RATINGS={'','1','2','3','4','5','unfamiliar'}
def require(condition,message):
 if not condition:raise ValueError(message)
def short_text(s):return isinstance(s,str) and len(s)<=20000
def validate_v2(obj,manifest):
 require(isinstance(obj,dict) and obj.get('schema')=='physwhen.feedback.v2','unsupported feedback schema')
 require(obj.get('dataset_id')==manifest['dataset_id'],'wrong reader dataset')
 instrument=obj.get('instrument','ratings-v2');require(instrument in ('ratings-v2','pair-preference-v1'),'unsupported feedback instrument')
 require(obj.get('test_mode') is False,'test or unspecified provenance; not a real reader export')
 require(isinstance(obj.get('participant_id'),str) and bool(re.fullmatch('[a-f0-9]{32}',obj['participant_id'])),'invalid participant code')
 require(type(obj.get('revision')) is int and 1<=obj['revision']<=1000000,'invalid export revision')
 require(obj.get('prior_exposure') in ('','yes','no','unsure'),'invalid prior exposure')
 order=obj.get('case_order');require(isinstance(order,list) and len(order)==3 and all(isinstance(x,str) for x in order) and set(order)==CASES,'invalid case order')
 presentation=obj.get('presentation');require(isinstance(presentation,dict) and set(presentation)==CASES,'invalid assignment cases')
 for m in presentation.values():require(isinstance(m,dict) and set(m)=={'X','Y'} and all(isinstance(x,str) for x in m.values()) and set(m.values())=={'P','Q'},'invalid version assignment')
 texts=obj.get('texts');require(isinstance(texts,dict) and set(texts)<={f'{c}:{v}' for c in CASES for v in ['X','Y']},'invalid text identities')
 for r in texts.values():
  require(isinstance(r,dict) and set(r)=={'effort','naturalness','friction','complete'},'invalid text fields')
  require(isinstance(r['effort'],str) and r['effort'] in RATINGS and isinstance(r['naturalness'],str) and r['naturalness'] in RATINGS,'invalid rating')
  require(type(r['complete']) is bool and short_text(r['friction']),'invalid completion or comment')
  if instrument=='ratings-v2':require(not r['complete'] or bool(r['effort'] and r['naturalness']),'completed text lacks ratings')
  else:require(r['effort']==r['naturalness']==r['friction']=='','preference-only export must not contain text ratings')
 comps=obj.get('comparisons');require(isinstance(comps,dict) and set(comps)<=CASES,'invalid comparison cases')
 for r in comps.values():
  require(isinstance(r,dict) and set(r)=={'preference','note','familiarity'},'invalid comparison fields')
  require(r['preference'] in ('','X','Y','tie','uncertain') and r['familiarity'] in ('','unfamiliar','basic','familiar') and short_text(r['note']),'invalid comparison')
 if instrument=='pair-preference-v1':
  for cid in CASES:
   selected=bool(comps.get(cid,{}).get('preference'))
   require(all(bool(texts.get(cid+':'+v,{}).get('complete'))==selected for v in ['X','Y']),'preference and pair completion disagree')
 for key in ['created_at','updated_at','exported_at']:
  try:dt=datetime.fromisoformat(obj[key].replace('Z','+00:00'));require(dt.tzinfo is not None,'timezone required')
  except (KeyError,AttributeError,ValueError,TypeError):raise ValueError('invalid timestamp '+key) from None
 return obj

def import_one(path):
 p=Path(path);require(p.stat().st_size<=1000000,'feedback exceeds1MB');raw=p.read_bytes();obj=json.loads(raw)
 require(isinstance(obj,dict),'feedback must be an object')
 from .feedback import validate_feedback
 manifest=read_json('experiments/reader_pack_manifest.json')
 if not manifest or obj.get('dataset_id')!=manifest['dataset_id']:
  legacy=read_json('experiments/reader_pack_manifest_v1.json')
  if legacy and obj.get('dataset_id')==legacy['dataset_id']:manifest=legacy
  else:
   ds=obj.get('dataset_id');require(isinstance(ds,str) and re.fullmatch('[a-f0-9]{20}',ds),'unknown reader dataset')
   manifest=read_json(f'experiments/reader_pack_manifests/{ds}.json')
 require(bool(manifest),'reader manifest unavailable');validate_feedback(obj,manifest)
 sha=digest(raw);out=Path('data/human_feedback')/(sha+'.json');existed=out.exists()
 if not existed:write_json(out,{'received_at':now(),'source_sha256':sha,'provenance_status':'reader_export_unverified_identity','human_readability_improvement':'not_established','feedback':obj})
 return {'saved_to':str(out),'duplicate_file':existed,'schema':obj['schema'],'evaluation_status':'pending_review','human_readability_improvement':'not_established'}

def import_path(path):
 p=Path(path)
 if p.is_file():return import_one(p)
 require(p.is_dir(),'feedback path does not exist');out={'accepted':[],'rejected':[]}
 for f in sorted(p.iterdir()):
  if f.is_file() and f.suffix.lower() in ('.json','.txt'):
   try:out['accepted'].append({'file':f.name,**import_one(f)})
   except (ValueError,TypeError,KeyError,OSError) as e:out['rejected'].append({'file':f.name,'reason':str(e)})
 out['accepted_count']=len(out['accepted']);out['rejected_count']=len(out['rejected']);return out

def stable_signature(obj):return json.dumps({**{k:obj[k] for k in ['dataset_id','case_order','presentation','created_at']},'instrument':obj.get('instrument','ratings-v2')},sort_keys=True)
def content_signature(obj):return json.dumps({k:v for k,v in obj.items() if k not in ('exported_at','updated_at')},sort_keys=True)
def reconcile(records):
 groups=collections.defaultdict(list)
 for obj in records:groups[obj['participant_id']].append(obj)
 chosen=[];conflicts=[]
 for pid,items in sorted(groups.items()):
  if len({stable_signature(x) for x in items})!=1:
   conflicts.append({'participant_id':pid,'reason':'assignment/order/creation changed across exports'});continue
  revision=max(x['revision'] for x in items);latest=[x for x in items if x['revision']==revision]
  if len({content_signature(x) for x in latest})!=1:
   conflicts.append({'participant_id':pid,'reason':'conflicting content at highest revision','revision':revision});continue
  chosen.append(latest[0])
 return chosen,conflicts

def summarize():
 manifest=read_json('experiments/reader_pack_manifest.json');require(bool(manifest),'reader manifest unavailable')
 mapping_path=Path(manifest['private_assignment']);mapping=read_json(mapping_path)
 if manifest.get('private_assignment_sha256'):require(digest(mapping_path.read_bytes())==manifest['private_assignment_sha256'],'private assignment hash changed')
 records=[];skipped=collections.Counter();active_instrument=read_json('configs/reader_current.json',{}).get('feedback_instrument','ratings-v2')
 for p in Path('data/human_feedback').glob('*.json'):
  r=read_json(p).get('feedback',{})
  if r.get('schema')!='physwhen.feedback.v2' or r.get('dataset_id')!=manifest['dataset_id']:skipped['other_protocol_or_dataset']+=1;continue
  try:validate_v2(r,manifest)
  except (ValueError,TypeError):skipped['invalid']+=1;continue
  if r.get('instrument','ratings-v2')!=active_instrument:skipped['other_instrument']+=1;continue
  records.append(r)
 chosen,conflicts=reconcile(records);pairs=[];ratings=[]
 for r in chosen:
  for cid in r['case_order']:
   for v in ['X','Y']:
    t=r['texts'].get(cid+':'+v)
    if t:
     ratings.append({'participant_id':r['participant_id'],'revision':r['revision'],'case_id':cid,'visible_version':v,'arm':mapping[cid][r['presentation'][cid][v]],'complete':t['complete'],'effort':t['effort'],'naturalness':t['naturalness']})
   if not all(r['texts'].get(cid+':'+v,{}).get('complete') for v in ['X','Y']):continue
   byarm={mapping[cid][r['presentation'][cid][v]]:r['texts'][cid+':'+v] for v in ['X','Y']};comp=r['comparisons'].get(cid,{});pref=comp.get('preference','')
   row={'participant_id':r['participant_id'],'case_id':cid,'preference':mapping[cid][r['presentation'][cid][pref]] if pref in ('X','Y') else pref,'prior_exposure':r['prior_exposure'],'familiarity':comp.get('familiarity','')}
   for metric in ['effort','naturalness']:
    a,b=byarm['A'][metric],byarm['B'][metric];row[metric+'_B_minus_A']=int(b)-int(a) if a in {'1','2','3','4','5'} and b in {'1','2','3','4','5'} else None
   pairs.append(row)
 bycase={cid:{'complete_pairs':sum(p['case_id']==cid for p in pairs),'preferences':dict(collections.Counter(p['preference'] or 'not_selected' for p in pairs if p['case_id']==cid))} for cid in sorted(CASES)}
 metric_summary={}
 for metric in ['effort','naturalness']:
  per_id=collections.defaultdict(list)
  for p in pairs:
   value=p[metric+'_B_minus_A']
   if value is not None:per_id[p['participant_id']].append(value)
  medians=[statistics.median(v) for v in per_id.values()]
  metric_summary[metric]={'reader_codes_with_numeric_pairs':len(medians),'median_of_within_reader_median_paired_differences':statistics.median(medians) if medians else None,'direction':'B minus A; lower effort / higher naturalness preferred','method':'Within each code take median paired ordinal difference across completed cases, then median across codes. Descriptive only, no independence or causal claim.'}
 out={'generated_at':now(),'dataset_id':manifest['dataset_id'],'protocol':manifest.get('protocol','subjective-reading-v2'),'instrument':active_instrument,'imported_export_files':len(records),'retained_reader_codes':len(chosen),'verified_human_participants':None,'revision_conflicts':conflicts,'skipped':dict(skipped),'prior_exposure':dict(collections.Counter(r['prior_exposure'] or 'not_reported' for r in chosen)),'completed_pairs':len(pairs),'by_case':bycase,'paired_ratings':metric_summary,'pairs':pairs,'measurement_note':('Pair-level preference only; blank per-text ratings are unmeasured, not inability-to-judge. Pair completion is self-reported by choosing a preference, not verified reading.' if active_instrument=='pair-preference-v1' else 'Per-text ratings and pair preference.'),'interpretation':'Subjective ease/naturalness/preference only. No comprehension questions or correctness measure. Labels/order randomized per browser, not guaranteed balanced. Self-reported identities and exposure; a code is not a verified unique person. Repeated cases are not independent readers. Partial pairs and nonnumeric ratings excluded only from their applicable summaries. No readability improvement claim.'}
 write_json('reports/group_feedback_summary.json',out)
 with Path('reports/group_feedback_ratings.csv').open('w',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=['participant_id','revision','case_id','visible_version','arm','complete','effort','naturalness']);writer.writeheader();writer.writerows(ratings)
 lines=['# PhysWhen 组内阅读体验回收','',f'导入文件 {len(records)} 份；按代号保留最新版本 {len(chosen)} 份；冲突代号 {len(conflicts)} 个（排除并待人工处理）。代号数不等于已核实的真人数。',f'完成配对 {len(pairs)} 组。当前问卷 {active_instrument}；不同问卷与旧版知识问答数据不混合。','', '| 案例 | 完成配对 | 偏好计数（私有条件解码） |','|---|---:|---|']
 for cid,z in bycase.items():lines.append(f'| {cid} | {z["complete_pairs"]} | {z["preferences"]} |')
 lines+=['','这份报告仅供组织者使用，不发给尚未参加的同学。当前协议只能比较主观阅读体验，不能证明理解正确率改善；不报告因果效应或显著性。原始意见在data/human_feedback中保留，未粘贴进公开报告。']
 Path('reports/group_feedback_summary.md').write_text('\n'.join(lines)+'\n');return out
