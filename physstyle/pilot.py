"""Enlarged-corpus analysis; preserve the frozen smoke experiment and skill."""
import collections
from pathlib import Path
from .common import *
from .parse import parse_tex
from .features import freeze_split,measure,aggregate
from .network import Fetcher
from .corpus import acquire

def enlarged_corpus():
    return sum(r.get("screening")=="include" and r.get("parse_status")=="usable" for r in read_jsonl("data/manifests/corpus.jsonl"))>30 and Path("reports/smoke_snapshot/frozen.json").exists()

@corpus_transaction
def analyze_pilot():
    if Path('reports/cohort210_snapshot/corpus.jsonl').exists():
        from .structure_corpus import analyze
        return analyze()
    rows=read_jsonl('data/manifests/corpus.jsonl');smoke=read_jsonl('reports/smoke_snapshot/corpus.jsonl');smoke_ids={r['paper_id'] for r in smoke if r['screening']=='include'};docs={};recoveries=list(read_json('reports/PILOT_RESULTS.json',{}).get('recovered_unsectioned_papers',[]))
    for r in rows:
     pid=r['paper_id'];r['cohort']='smoke' if pid in smoke_ids else 'pilot_extension'
     if r.get('version') is None and r.get('parse_status')=='failed':
      # Recover metadata discarded by the earlier collector after parse failures.
      # Fetcher is strictly offline: absent/failed acquisitions remain failures.
      try:
       recovered,_=acquire(Fetcher('data/raw/http',offline=True),r,read_json('configs/pilot.json'))
      except Exception:
       r['failure_stage']='acquire'
      else:
       recovered.update(parse_status='failed',failure_stage='parse',error=r.get('error'))
       r.update(recovered)
     if r.get('version') is None:
      if r.get('parse_status')=='usable':raise ValueError('usable row lacks version '+pid)
      continue
     p=Path(f'data/raw/papers/{pid}v{r["version"]}/source.bin')
     if not p.exists():
      if r.get('parse_status')=='usable':raise ValueError('usable row lacks source '+pid)
      continue
     if digest(p.read_bytes())!=r['source_sha256']:raise ValueError('source hash mismatch '+pid)
     if r.get('parse_status')=='low_prose':
      d=parse_tex(p.read_bytes(),p.parent/'source')
      if d['usable']:
       d.update(paper_id=pid,version=r['version'],source_sha256=r['source_sha256']);write_json(f'data/parsed/{pid}.json',d);r['parse_status']='usable';r['parser_warnings']=d['warnings'];recoveries.append(pid)
     d=read_json(f'data/parsed/{pid}.json')
     if r.get('parse_status')=='usable' and (not d or not d.get('usable')):raise ValueError('usable row lacks usable parse '+pid)
     if d and (d.get('source_sha256')!=r['source_sha256'] or d.get('version')!=r['version']):raise ValueError('parsed source identity mismatch '+pid)
     if d and r['screening']=='include' and r['parse_status']=='usable':docs[pid]=d
    for w in read_jsonl('data/annotations/tasks.jsonl'):
     d=docs.get(w['paper_id'])
     if not d or d['version']!=w['version']:raise ValueError('annotation source identity stale')
     expected={p['paragraph_id']:p for p in d['paragraphs']}
     if any(expected.get(p['paragraph_id'])!=p for p in w['context']):raise ValueError('annotation context stale')
    write_jsonl('data/manifests/corpus.jsonl',rows);splits=freeze_split(rows,docs);original=read_json('reports/smoke_snapshot/frozen.json')['assignments']
    assert all(splits[pid]==original[pid] for pid in smoke_ids),'smoke split changed'
    measures=[]
    for pid,d in docs.items():
     d['split']=splits[pid];write_json(f'data/parsed/{pid}.json',d);m=measure(d,read_json('configs/features.json'));write_json(f'data/features/{pid}.json',m);measures.append(m)
    profiles=aggregate(measures,rows);write_json('data/features/pilot/feature_profiles.json',profiles)
    write_jsonl('data/features/pilot/evidence_index.jsonl',[
     {'paper_id':pid,'version':d['version'],'source_sha256':d['source_sha256'],'split':splits[pid],
      'source_directory':f'data/raw/papers/{pid}v{d["version"]}/source',
      'parsed_file':f'data/parsed/{pid}.json','feature_file':f'data/features/{pid}.json',
      'location_method':'Feature records resolve paragraph_id/block_id to parsed source_spans; D03 uses all display blocks in main-body roles.'}
     for pid,d in docs.items()])
    active=[r for r in rows if r['paper_id'] in docs];bycategory=collections.Counter(r['sampling_category'] for r in active);years=collections.Counter(r['sampling_year'] for r in active);scope=collections.Counter(r['screening'] for r in read_jsonl('data/manifests/candidates.jsonl'));failures=[{'paper_id':r['paper_id'],'category':r['sampling_category'],'year':r['sampling_year'],'status':r['parse_status'],'reason':r.get('error',r.get('parser_warnings')),'failure_stage':r.get('failure_stage','parse'),'version':r.get('version')} for r in rows if r.get('parse_status')!='usable']
    result={'project':'PhysWhen','updated_at':now(),'papers_candidates':len(read_jsonl('data/manifests/candidates.jsonl')),'papers_acquired_attempted':len(rows),'source_versions_acquired':sum(bool(r.get('version')) for r in rows),'scope_excluded_after_acquisition':sum(r['screening']!='include' and bool(r.get('version')) for r in rows),'papers_included':len(active),'papers_parsed_usable':len(active),'category_counts':dict(bycategory),'year_counts':dict(sorted(years.items())),'split_counts':dict(collections.Counter(splits.values())),'selected_versions_verified':sum(bool(r.get('version_identity_verified')) for r in active),'scope_counts':dict(scope),'recovered_unsectioned_papers':recoveries,'failures':failures,'deterministic_features_papers':len(measures),'semantic_windows_completed':60,'semantic_papers':15,'semantic_scope':'frozen smoke only; no new semantic labels inferred','generation_cases_completed':3,'generation_scope':'frozen smoke only; originals unchanged','human_feedback_count':len(list(Path('data/human_feedback').glob('*.json'))),'human_readability_improvement':'not_established','weight_training_status':'not_run','profile_file':'data/features/pilot/feature_profiles.json','smoke_snapshot':'reports/smoke_snapshot','skill_status':'frozen; enlarged deterministic statistics do not automatically rewrite rules'}
    write_json('reports/PILOT_RESULTS.json',result)
    old=read_json('reports/RESULTS.json');old.update({k:result[k] for k in ['papers_included','papers_parsed_usable','category_counts','split_counts','selected_versions_verified']});old.update(engineering_status='enlarged_corpus_and_reader_run_with_documented_limits',pilot_200_status='corpus_complete' if len(active)>=200 else 'partial',current_corpus_report='reports/pilot_corpus_report.md',current_feature_profiles=result['profile_file'],smoke_experiment_report='reports/evaluation_report.md',reader_url='http://127.0.0.1:8765/',uncompleted=['New semantic coverage to120 windows and new generation cases to12 have not been run; original60/3 remain explicitly separate.','Reader exports, if any, await identity/content review; no readability improvement claim.'],papers_acquired_versions=sum(bool(r.get('version')) for r in rows),included_versions_verified=result['selected_versions_verified'],raw_cache_bytes=sum(p.stat().st_size for p in Path('data/raw').rglob('*') if p.is_file()))
    write_json('reports/RESULTS.json',old)
    lines=['# PhysWhen 扩充语料报告','',f'真实候选576；本轮新增范围审查530条。当前纳入 {len(active)} 篇、实际取得指定版本并通过解析；类别分布 {dict(bycategory)}，分组 {result["split_counts"]}。原30篇分组保持不变。','',f'共尝试 {len(rows)} 条，实际取得 {result["source_versions_acquired"]} 个指定版本，其中 {result["scope_excluded_after_acquisition"]} 条范围排除。共 {len(failures)} 条获取/解析未通过记录，逐项及年/类见PILOT_RESULTS.json。无章节标题的短论文修复后恢复 {len(recoveries)} 篇；PDF-only与仍无法解析的来源未混入干净文本。','', '采样仍来自原576条有界候选池，没有追随引用量或名人挑文。下载在已审查合格项中优先欠覆盖类别，目标权重0.4/0.3/0.3，按原抽样rank及年份顺序替补。摘要筛选属于agent范围审查，不是人工质量认证；未核查许可保持unreviewed。','', '新增确定性统计按完整论文等权汇总，定义和词表冻结。六项语义仍为原15篇的60窗口，三组A/B和skill仍采用原discovery证据；没有用新增规模冒充语义规模。','', '| 指标 | discovery论文数 | 中位数 | Q25–Q75 |','|---|---:|---:|---:|']
    for k,z in profiles['discovery'].items():lines.append(f'| {k} | {z["n"]} | {z["median"]:.3f} | {z["q25"]:.3f}–{z["q75"]:.3f} |')
    lines+=['','计算口径：D01为排除数学和引用键后的英文prose句长；D02为非空prose段长；D03为每千prose词的显示数学块数；D04为同节公式前/后最多两句的词数，相邻数学块记0，边界缺失不记0；D05为内部交叉引用而非文献引文；D06为configs/features.json中的固定词表出现率，不能代替语义判断。表中每项先在论文内计算，再跨discovery论文等权汇总；n为非缺失论文数。逐论文bootstrap区间、年份/类别分层和高频作者敏感性见profile JSON，均为描述性结果。', '', '每篇的版本、SHA-256、解析路径、逐条特征路径见data/features/pilot/evidence_index.jsonl；按paragraph_id/block_id可定位parsed文件中的source_spans及原TeX行。heldout仅用冻结定义做对照，不据此选择新的skill规则。历史年份是语料选择条件，不能证明某篇的实际创作过程。', '', '| 年份 | gr-qc | astro-ph.CO | hep-th |','|---|---:|---:|---:|']
    for year in sorted(years):
     c=collections.Counter(r['sampling_category'] for r in active if r['sampling_year']==year)
     lines.append(f'| {year} | {c["gr-qc"]} | {c["astro-ph.CO"]} | {c["hep-th"]} |')
    lines+=['','无正式section的恢复论文按Unsectioned body保留；段首明确致谢/资助语排除并保留源位置，针对性独立复核3篇通过。此类论文段内标题可能计入词数，章节角色未细分，不能用technical_body默认标签证明真实篇章角色。见unsectioned_parse_audit.json。', '', '解析审查的两项测量限制：1107.3324v1 paper.tex:375–406 的列表项合段影响段长；1303.3770v1 main.tex:37–146 的空编号块和分片导致显示块数不等于语义公式数。D03一直定义为显示块密度，未将其改称公式数量。', '', '本文统计是历史参考分布，不是理想写作配额。新语料抽查见pilot_parse_audit.json；失败样本会带来格式选择偏差，按类别、年份分布比较应结合上述失败清单。','', f'匿名阅读入口：reader/index.html，或本地 http://127.0.0.1:8765/。客户端无参考答案、条件映射或外网依赖。当前已导入 {result["human_feedback_count"]} 份正式入口反馈文件（不等于已验证人数/效果）；工程测试数据被明确拒绝导入。']
    Path('reports/pilot_corpus_report.md').write_text('\n'.join(lines)+'\n')
    Path('reports/corpus_report.md').write_text('扩充语料的当前报告见 [pilot_corpus_report.md](pilot_corpus_report.md)。原30篇记录见 [smoke_snapshot/corpus_report.md](smoke_snapshot/corpus_report.md)。\n')
    return result
