# 开发与复现

## 不需要论文语料的检查

在仓库根目录运行。Python 3.10+，运行依赖仅为标准库；下面命令不会联网下载论文或调用模型。

```bash
python3 -m physstyle doctor
python3 skills/physwhen/scripts/check_outline.py examples/outline.json
python3 -m unittest discover -s tests -p 'test_core.py' -v
python3 -m unittest discover -s tests -p 'test_outline.py' -v
```

仅使用skill时不需要运行这些命令。`doctor`只检查本机环境，不验证网络或模型服务。

`tests/`还包含依赖本地语料、旧skill版本、实验输出和报告的验收测试。**干净克隆不应直接把全量 `unittest discover` 当作可运行的公开测试集。** 原始研究工作区具备这些输入时才运行全套；缺失输入不是允许用mock补齐的理由。

## 打包当前 skill

`python3 scripts/package_skill.py` 从固定文件清单构建 `deliverables/PhysWhen-skill.zip`；`--check` 检查现有 ZIP 与源码逐字一致，不改写文件。该检查不证明策略改善了阅读效果。

## 本地研究数据齐备后的重放

下面保留的是历史阶段命令，读取旧名称的冻结快照，不用于构建当前 `physwhen`。以下输入不随Git仓库分发：`data/`、`experiments/`、`reports/`及历史归档。当前skill可以独立使用，但这些研究命令需要原工作区的实际源文件、标注和审查记录。

```bash
python3 scripts/analyze_structure_corpus.py
python3 scripts/apply_structure_adjudications.py
python3 scripts/summarize_structure_maps.py
python3 scripts/check_near_duplicates.py
python3 scripts/validate_structure_stage.py
python3 scripts/build_structure_skill_evidence.py
python3 scripts/package_skill_v3.py
python3 scripts/validate_skill_v3.py
```

已有判断和裁决可离线重放；重新调用模型不能保证相同输出。解析器变更后须重新导出并审查相关标注，不能静默套用旧段落索引。部分早期验收脚本依赖本机的skill验证器与旧阶段资料，移植前需检查，不把它们作为新用户安装步骤。`finalize_structure_docs.py`只把历史结构阶段说明写入 `reports/structure_stage_summary.md`，不覆盖仓库首页。

原工作区的下载入口为 `scripts/collect_structure500.py`，达到500篇后退出。采集使用单连接、至少3.1秒间隔、有限重试与Retry-After；单下载50MiB、HTTP缓存3GiB上限。不执行下载的TeX或嵌入命令。全新克隆不包含人工范围审查输入，不能依靠一条采集命令重建全部研究判断。

## 盲测维护与回收

可直接分发已经构建的 `deliverables/PhysWhen-Blind-Test-03.html`。前端源码在 `reader/`；其中 `data.js`只含匿名材料。KaTeX第三方许可随资源保留。

重新生成匿名材料需要组织者本地的科学简报、生成文本与私有映射，不包含在克隆中。不要通过猜测映射恢复或解盲。组织者在原工作区可运行：

```bash
python3 scripts/build_reader.py
python3 scripts/build_standalone_reader.py
python3 scripts/validate_round03.py
python3 -m physstyle import-feedback data/feedback_inbox/round03
python3 -m physstyle summarize-feedback
```

汇总按dataset和问卷类型隔离，同代号取最新修订，冲突隔离，QA测试文件拒收。人类身份未核实。原始反馈及解盲统计不得加入Git或发给未参加者。

## 训练导出

`python3 -m physstyle export-training --config configs/smoke.json` 是本地许可门控的导出接口，要求真实数据、许可审查和分组记录。未经核查的许可不自动放行，heldout不能进入训练集。本项目没有启动权重微调或购买算力。
