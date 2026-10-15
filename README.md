# PhysWhen

**让 AI 辅助撰写的英文理论物理论文，更容易让读者跟上论证。**

论文难读，往往不只是句子生硬：研究问题和结论对不上、关键条件出现得太晚、推导与解释脱节，都会让读者失去线索。PhysWhen 从历史研究论文中分析这些表达和组织方式，把有来源依据的观察转成 agent 可以执行的写作 skill。

你提供科学内容、推导与目标读者，skill 帮助安排论证路线、交代适用条件、解释关键公式，并调整局部表达。它不替你发明结果，也不要求所有论文采用同一种章节模板。

当前推荐版本：**[physics-paper-style-v3](skills/physics-paper-style-v3/SKILL.md)**。这是指令与参考资料组成的 skill，不是微调模型；使用时不需要下载论文语料或配置额外模型 API。

[快速开始](#快速开始) · [使用示例](#使用示例) · [工作原理](#工作原理) · [开发与验证](docs/DEVELOPMENT.md)

## 能帮你做什么

| 场景 | skill 的工作 |
| --- | --- |
| 从研究笔记写初稿 | 根据问题、结果与依赖关系组织大纲，再展开正文 |
| 修改整篇论文 | 调整论证顺序，区分预告、推导、解释与回顾，保留必要条件 |
| 润色局部段落 | 改善公式前后的衔接与结果解释，不擅自重写整篇 |
| 检查论证安排 | 找出没有交代的前提、缺少支持的主张、重复却没有新增作用的段落 |

适用对象是已有科学材料的英文理论物理研究写作。它不是 AI 检测器，不输出“AI 撰写概率”或“人味分数”，也不代替物理正确性审查。

## 快速开始

### 1. 获取 skill

克隆本仓库（私有仓库需要访问权限），或直接取得 [skill ZIP](deliverables/PhysWhen-skill-v3.zip)：

```bash
git clone https://github.com/jimmychou1729/PhysWhen.git
cd PhysWhen
```

必须保留整个 `skills/physics-paper-style-v3/` 文件夹，包括 `references/`、`profile.json` 和 `scripts/`；只复制 `SKILL.md` 会丢失证据与辅助工具。

### 2. 在 Codex 中使用

最直接的方式是在能访问本仓库的会话中发送：

```text
请读取 skills/physics-paper-style-v3/SKILL.md，按需要加载它引用的资料。
使用这个 skill 修改我提供的英文物理论文，保持公式、数值和物理结论不变。
```

若希望 Codex 在其他项目也能发现它，可将整个文件夹复制到个人 skill 目录。在仓库根目录运行；目标已存在时停止，避免覆盖已有版本：

```bash
mkdir -p "$HOME/.agents/skills"
if [ -e "$HOME/.agents/skills/physics-paper-style-v3" ]; then
  echo "目标已存在，请先检查已有版本。"
else
  cp -R skills/physics-paper-style-v3 "$HOME/.agents/skills/"
fi
```

然后在 skill 选择器中选择 `physics-paper-style-v3`；Codex CLI／IDE 中也可用 `$physics-paper-style-v3` 显式调用。未出现时重启客户端。项目级安装可以改为论文项目下的 `.agents/skills/`。发现路径与调用方式见 [OpenAI 官方说明](https://learn.chatgpt.com/docs/build-skills)。

其他支持 Agent Skills 的工具可按其本地安装方式放入完整文件夹；这里尚未逐一验证所有客户端。普通聊天环境如果不能读取本地文件及引用资料，不应声称已经完整加载了 skill。

### 3. 提供足够的科学材料

至少给出：研究问题、已有结论或推导、近似与适用范围、目标读者，以及允许修改的范围。缺少的信息会被指出，不应由模型补造。

## 使用示例

**先审结构，再改全文：**

```text
使用 physics-paper-style-v3 阅读 draft.tex。
读者是熟悉宇宙学但不熟悉本模型的研究生。
先给出当前的“问题—条件—推导—结果”路线和主要断点，再提出新大纲。
允许改变章节顺序和标题；保留所有公式、引用和结论的限定条件。
这一步不要修改文件。
```

**依据已有材料写初稿：**

```text
使用 physics-paper-style-v3，根据 notes.md 写一篇约 2500 词的英文初稿。
以我提供的计算结果为依据，自主选择章节结构。
不要补造文献、数值结果或新颖性声明；材料不足的地方单独列出。
输出到 draft.md。
```

**只润色一段：**

```text
使用 physics-paper-style-v3 润色下面两段英文。
只处理局部表达和公式解释，保留符号、正负号、适用条件与结论强度。
不要扩写成完整论文。
[粘贴段落]
```

更多输入要求与可选的大纲检查工具见 [使用指南](docs/USAGE.md)。

## 工作原理

历史论文 → 文本与源位置解析 → 自动特征统计／局部与全文标注 → 独立复核 → 候选写作操作 → 写作对照与读者盲测。

当前 v3 包含四类整体组织操作：问题与结论对齐、按依赖和分支安排内容、区分预告与展开及回顾、把篇幅分配给关键推理；同时保留公式任务、结果解释、条件随结论出现三类局部操作。

每条操作都强调何时适用、何时跳过。历史论文中的常见做法提供参考，不能直接证明某种写法更好。数据、定义和局限见 [研究方法](docs/RESEARCH.md)，具体来源位置在 skill 的 `references/` 中。

## 当前进展

| 项目 | 已完成范围 |
| --- | --- |
| 历史语料 | 500 篇，2010–2021 年；400 篇 discovery、100 篇 heldout |
| 领域分布 | gr-qc 200 篇、astro-ph.CO 150 篇、hep-th 150 篇 |
| 全文结构标注 | 30 篇完整主文的选择性论证图，并非 500 篇全部语义标注 |
| 局部标注 | 27 篇论文、120 个窗口，与全文结构样本分别统计 |
| 写作与工程验证 | 独立复核、可执行检查工具、匿名对照与离线结果回收 |
| 人类阅读效果 | **尚未证实，正在通过盲测评估** |

[宇宙学盲测 HTML](deliverables/PhysWhen-Blind-Test-03.html) 包含三组论文式材料，左右并排，每组只选一次整体偏好。下载 HTML 后用电脑浏览器打开，结束后导出 JSON 交给组织者。它不会自动上传；仅仅把 HTML 推到 GitHub 不会启用在线收集。

## 仓库内容

```text
skills/physics-paper-style-v3/   当前可独立使用的 skill
examples/                       合成的大纲示例，不计入研究数据
physstyle/                      采集、解析、特征与反馈工具
scripts/                        研究流程和校验脚本
tests/                          单元测试与本地研究验收测试
reader/                         盲测前端和匿名材料
deliverables/                   可转发的 skill 与盲测文件
docs/                           使用、研究、开发和发布说明
```

只使用 skill 无需安装 Python。运行辅助工具和研究代码需要 Python 3.10+；Python 运行代码使用标准库。先从 [开发指南](docs/DEVELOPMENT.md) 的无需语料检查开始；完整历史研究重放依赖本地数据，不随 Git 仓库分发。

## 数据与许可

论文全文、原始缓存、完整标注上下文、实验答案映射和读者回收结果不入库。skill 保留描述性统计、来源标识和位置索引，不包含论文全文。

项目尚未指定开源许可证；私有仓库访问不等于获得任意再分发授权。第三方组件见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。协作和发布边界见 [发布说明](docs/PUBLISHING.md)。
