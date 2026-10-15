"""Rebuild a historical structure-stage summary without overwriting user-facing README."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from physstyle.common import *
v=read_json('reports/skill_v3_validation.json');r=read_json('reports/STRUCTURE_RESULTS.json');s=read_json('reports/structure_semantic_results.json')
assert v and v['status']=='passed' and v['wholepaper_maps']==30 and r['papers_usable']==500
assert Path('reports/SKILL_V3_REPORT.md').exists() and Path('deliverables/PhysWhen-skill-v3.zip').exists()
snapshot=Path('reports/cohort210_snapshot/README.md')
if not snapshot.exists():snapshot.write_bytes(Path('README.md').read_bytes())
text='''# PhysWhen

从历史英文理论物理原创研究论文的单一核验版本，提取可追溯的表达与论证组织特征，再形成可执行的候选写作skill。项目是本地研究CLI，不输出AI来源概率，不把历史习惯当最佳写法。

现已完成 **500篇可用论文（400 discovery /100 heldout）**：gr-qc200、astro-ph.CO150、hep-th150。新增全文结构标注 **30篇**，与既有27篇/120个局部窗口分别统计。四个synthetic写作任务完成并独立复核。**工程已跑通，人类阅读效果尚未验证。**

## 当前结果

- [500篇与结构skill报告](reports/SKILL_V3_REPORT.md)、[完整方法](reports/structure_method.md)。报告区分自动统计、全文语义判断、写作设计推断与未验证效果。
- [skill v3](skills/physics-paper-style-v3/SKILL.md)、[可分发ZIP](deliverables/PhysWhen-skill-v3.zip)。4条宏观操作加3条局部操作；允许不同章节路线与技术附录，不规定统一标题或句长配额。
- [语料结果](reports/STRUCTURE_RESULTS.json)、[全文结构结果](reports/structure_semantic_results.json)、[逐条来源索引](data/features/structure500/evidence_index.jsonl)。版本、哈希、paragraph和源行容器可回查。
- [语料验收](reports/structure_validation.json)、[skill验收](reports/skill_v3_validation.json)、[独立代码审查](reports/structure_code_review.json)、[补充审查](reports/structure_code_review_followup.json)、[发布验收审查](reports/structure_release_review.json)。

原skill [v1](skills/physics-paper-style/SKILL.md)、[v2](skills/physics-paper-style-v2/SKILL.md)与既有生成/盲测文件保持原hash。此前 [论文式宇宙学盲测02](deliverables/PhysWhen-Blind-Test-02.html) 仍可按[原回收说明](GROUP_STUDY_ROUND02.md)回收，它评估的是v2，不能作为v3效果证据。本机127.0.0.1预览地址不是可分享公网地址。本轮没有生成新盲测。

## 本地复现

在本目录运行，Python3.10+，运行代码仅用标准库：

```bash
# Run from the PhysWhen repository root
python3 -m unittest discover -s tests -v
python3 scripts/analyze_structure_corpus.py
python3 scripts/apply_structure_adjudications.py
python3 scripts/summarize_structure_maps.py
python3 scripts/check_near_duplicates.py
python3 scripts/validate_structure_stage.py
python3 scripts/build_structure_skill_evidence.py
python3 scripts/package_skill_v3.py
python3 scripts/validate_skill_v3.py
```

这些命令离线重算已有数据，不重新调用模型。当前`python3 -m physstyle analyze`、`report`以及`run --offline`同样路由到独立的structure500统计，保护旧210统计与实验；本阶段不会自动重解析旧上下文。需要变更parser时必须重新导出并审查相关标注，不能静默复用旧窗口。

下载入口为`python3 scripts/collect_structure500.py`；达到500后立即退出，不再联网。恢复时使用已缓存字节、原版本核验和稳定的追加审查批次；新候选必须经过实际范围阅读及哈希绑定导入。网络入口执行单连接、至少3.1秒间隔、有限重试与Retry-After、50MiB单下载/3GiB HTTP缓存限制。采集/写入分析共享事务锁。

## 全文结构任务与来源

`data/structure/papers/*.json`是本地完整主文阅读任务；三个采样阶段分别保存在sample.json、additional_sample.json与supplement_sample.json。初标在initial_annotations，当前裁决结果在annotations，独立复核在reports/structure_*audit*.json，字段修改和理由在adjudications.jsonl。第二批是在初批探索后的继续发现，不冒称独立确认。

```bash
python3 scripts/show_structure_paper.py PAPER_ID START END
python3 scripts/import_structure_maps.py incoming.jsonl
```

导入检查版本、discovery身份、完整段落覆盖、关系类型和原文短引；替换已有结果需要显式`--replace`。自动检查不能证明语义正确，更不能证明物理正确。宿主模型具体ID、温度、种子未知，重新调用不保证同样输出；已保存判断、输入输出与裁决可重放。

30篇全文图是显著论证的选择性图，不是500篇的完整逻辑标注。图、图注和附录阅读覆盖逐篇声明；误入正文的附录、致谢与排版残留均保留说明。章节导航包括各级标题而非顶级章数，显示数学环境也不等于语义公式数。所有分布是描述性参考，不用于“人味”评分。

## 数据保护与训练准备

`data/raw`、`data/parsed`、标注任务及逐字证据包含受保护全文，仅留本地，不公开上传。source作为数据读取，不执行TeX或嵌入命令。可分发skill只包含指令、描述性统计、组织性转述/引文hash/位置与标准库helper，不包含全文或完整标注上下文。

现有[训练导出接口](reports/TRAINING_READINESS.md)仍受许可及heldout门控：

```bash
python3 -m physstyle export-training --config configs/smoke.json
```

扩大语料不等于获得新增训练许可；未核查许可和heldout不得导出训练全文。没有购买算力、调用付费模型API或进行权重微调，没有全局安装skill。

早期阶段可查[30篇快照](reports/smoke_snapshot)、[210篇快照](reports/cohort210_snapshot)、[v2报告](reports/SKILL_V2_REPORT.md)。当前目录没有Git仓库，本轮未初始化、commit、push或发布。
'''
Path('reports/structure_stage_summary.md').write_text(text)
current={'project':'PhysWhen','updated_at':now(),'current_stage':'structure500_skill_v3','engineering_status':'corpus_structure_maps_skill_and_forward_checks_complete_with_documented_limits','current_corpus_report':'reports/SKILL_V3_REPORT.md','current_stage_results':'reports/STRUCTURE_RESULTS.json','current_feature_profiles':r['profile_file'],'papers_candidate':r['candidates'],'papers_acquired_attempted':r['attempted'],'papers_acquired_versions':r['acquired_versions'],'papers_included':500,'papers_parsed_usable':500,'included_versions_verified':500,'category_counts':r['category_counts'],'split_counts':r['split_counts'],'deterministic_features_papers':500,'wholepaper_semantic_papers':30,'wholepaper_semantic_report':'reports/structure_semantic_results.json','legacy_local_semantic_samples':[{'papers':15,'windows':60,'labels':360},{'papers':12,'windows':60,'labels':360}],'current_skill':'skills/physics-paper-style-v3/SKILL.md','synthetic_forward_cases':4,'human_readability_improvement':'not_established','v3_blind_study':'not_run_this_stage','weight_training_status':'not_run','paid_external_model_api_spend_usd':0,'token_count':None,'historical_210_results':'reports/cohort210_snapshot/RESULTS.json','historical_studies':['experiments/cosmology_v2','experiments/cosmology_skill_v2_papers'],'uncompleted':['Human reading effects of v3 and structural causal/ablation comparisons have not been evaluated.'],'limitations':['Historical availability is not proof of human-only authorship.','Full-paper maps describe selected salient arguments, not verified physics or exhaustive proof graphs.','Sampling, parsing and model annotation limits are documented in the release report.']}
write_json('reports/RESULTS.json',current)
print('structure-stage summary/results updated; user-facing README unchanged')
