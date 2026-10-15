# PhysWhen

> AI can code. AI can do math. Physics when?

**帮助 agent 写出更易读的英文理论物理论文，从整篇结构到局部润色表达。**

[English](README.md) | 简体中文

论文难读，往往不只是句子生硬：关键条件出现得太晚、推导和研究问题脱节、结论超出证据，都会降低可读性。PhysWhen 从历史研究论文中分析这些表达与组织方式，把有来源依据的观察转成 agent 可以执行的写作 skill。

## 快速开始

克隆仓库，或下载[可分发 skill ZIP](deliverables/PhysWhen-skill.zip)。

```bash
git clone https://github.com/jimmychou1729/PhysWhen.git
cd PhysWhen
```

使用 Codex 时，把**整个** `skills/physwhen/` 文件夹复制到个人 skill 目录。以下命令适用于首次安装，不覆盖已有安装：

```bash
mkdir -p "$HOME/.agents/skills"
if [ ! -e "$HOME/.agents/skills/physwhen" ]; then
  cp -R skills/physwhen "$HOME/.agents/skills/"
else
  echo "physwhen 已安装，更新方法见 docs/USAGE.md。"
fi
```

在 skill 选择器中选择 `physwhen`；Codex CLI／IDE 也支持 `$physwhen`。未出现时重启客户端。发现路径见 [OpenAI 官方说明](https://learn.chatgpt.com/docs/build-skills)。其他兼容工具按其自身方式安装完整文件夹；本项目未逐一测试所有客户端。

### 网页版 ChatGPT 与 Dot

请通过宿主支持的账号插件导入入口使用[插件 ZIP](deliverables/PhysWhen-plugin.zip)，不要把单独的 skill ZIP 当作插件。两种包使用同一份 skill；插件只增加清单，不需要 MCP 服务器。是否可用仍取决于宿主和账号，打包成功不代表已经通过 ChatGPT 或 Dot 的实际调用验证。详见[宿主安装与验证说明](docs/HOSTS.md)。

## 如何使用

参考用法：

> 请使用 physwhen 修改这篇论文。

> 请使用 physwhen，根据这些研究笔记写一篇宇宙学论文。

> 请使用 physwhen 润色这一段。

> 使用 physwhen 审阅 draft.tex，先提出新大纲，不改文件。读者了解宇宙学，但不熟悉这个模型。

> 使用 physwhen，根据 notes.md 写约 2500 词的英文初稿，保留已有结果，缺失材料单独列出。

> 使用 physwhen 只润色这两段，保留符号和假设。

这些附加要求是可选的。完整论文组织、局部编辑和大纲检查工具见[使用指南](docs/USAGE.md)。

## 能帮你做什么

| 任务 | PhysWhen 关注什么 |
| --- | --- |
| 规划论文 | 研究问题、已有结果、前提和可能的论证路线 |
| 修改初稿 | 依赖关系、分支情形、预告、展开和有用的回顾 |
| 分配篇幅 | 主文需要交代的逻辑桥梁，以及可以后置的技术细节 |
| 润色段落 | 公式承担的任务、结果解释和结论的适用条件 |

科学内容始终优先。它不补造证据、文献、新颖性或缺失证明；也不是 AI 检测器，不能代替物理正确性审查。

## 工作原理

历史论文 → 带源位置的解析 → 自动特征与语义标注 → 独立复核 → 候选写作操作 → 写作对照与读者盲测。

skill 包含四类整体组织操作和三类局部表达操作，每类都有适用条件和例外。历史出现频率是描述性证据，不能直接证明某种写法最优。详见[研究方法](docs/RESEARCH.md)和 skill 的[结构证据](skills/physwhen/references/structure-evidence.md)。

| 证据 | 当前范围 |
| --- | --- |
| 历史语料 | 500 篇，2010–2021 年；400 discovery / 100 heldout |
| 领域分布 | gr-qc 200 篇、astro-ph.CO 150 篇、hep-th 150 篇 |
| 全文结构标注 | 30 篇完整主文的选择性论证图，并非 500 篇全部语义标注 |
| 局部标注 | 27 篇、120 个窗口，与全文结构样本分别统计 |
| 人类阅读效果 | **尚未证实，读者评估仍在进行** |

[宇宙学盲测](deliverables/PhysWhen-Blind-Test-03.html) 包含三组论文式材料，每组选择一次整体偏好。下载 HTML 后用电脑浏览器打开，结果导出为 JSON 交给组织者，不自动上传。它是冻结的实验材料，不会随当前 skill 的更新自动重写。

## 开发

使用 skill 不需要 Python；运行可选检查工具与研究代码需要 Python 3.10+，Python 依赖仅为标准库。

```bash
python3 skills/physwhen/scripts/check_outline.py examples/outline.json
python3 -m unittest discover -s tests -p 'test_outline.py' -v
python3 scripts/package_skill.py --check
```

示例是合成的接口演示。检查通过只代表结构引用完整，不代表物理正确或可读性改善。无需语料的基础测试和历史研究重放的本地数据要求见[开发指南](docs/DEVELOPMENT.md)。

```text
skills/physwhen/   唯一维护的 skill 与参考资料
examples/         合成接口示例
physstyle/        研究与反馈工具
scripts/          打包、分析和校验脚本
reader/           匿名阅读实验前端
deliverables/     可分发的 skill 与盲测文件
docs/             使用、研究、开发和发布说明
```

## 数据与许可

论文全文、原始缓存、完整标注上下文、实验条件映射和读者反馈不进入 Git。skill 保留描述性统计和来源位置，不包含论文全文。

PhysWhen 的原创代码、skill 指令、文档和生成的实验材料采用 [MIT 许可证](LICENSE)。允许使用、修改、再分发和商业使用，需保留版权与许可声明；软件不提供担保。

该许可不改变历史论文或第三方组件的原有许可。详见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) 和[发布说明](docs/PUBLISHING.md)。
