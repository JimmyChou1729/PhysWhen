# 版本管理与发布范围

远程仓库为 `jimmychou1729/PhysWhen`，仍为私有。项目原创内容已按维护者要求采用 [MIT 许可证](../LICENSE)；改变可见性或发布站点仍需维护者明确授权。GitHub仓库本身不是盲测结果收集服务。

## 入库范围

代码、配置、测试、当前physwhen的完整skill资源、合成接口示例、使用与研究说明、匿名盲测前端及其可转发文件。旧版skill从当前分发入口移除；已经提交过的内容保留在 Git 历史中。本地研究阶段文件和冻结快照仍在原工作区保留，不随当前分发包上传。

根目录 `.gitignore` 采用显式允许范围；新建根目录默认忽略。`data/`、`experiments/`、`reports/`、`archives/`、`task_reference/`、本机依赖及临时计划均不入库，包括：

- 论文原始字节、解析全文和完整标注上下文；
- 生成条件、答案映射、解盲报告、浏览器QA结果；
- 参与者JSON、匿名代号与意见；
- 凭据、运行时目录、私人路径记录和临时缓存。

`.gitignore`只控制尚未跟踪的文件，不能清除已提交数据。提交前仍要审查实际暂存清单；不对受保护数据使用 `git add -f`。

## 修改与验证

使用README中的无需语料检查核验干净克隆。研究验收脚本需要本地研究输入，不能因为本地全套通过就声称克隆后也可完整重放。skill与科学材料的更新应有来源和证据；保留研究阶段快照，不改写已有实验记录。

## README 的组织参考

本项目参考了以下仓库的文档层次，只借鉴组织方式，没有复制其写作规则或效果结论：

- [blader/humanizer](https://github.com/blader/humanizer)：先说明用途，再给安装、调用示例与工作原理。
- [anthropics/skills](https://github.com/anthropics/skills)：简介、仓库内容、不同宿主的使用入口与限制。
- [openai/skills](https://github.com/openai/skills)：skill概念、安装入口与许可；该仓库现已标记deprecated，安装细节以当前官方文档为准。

因此README聚焦“项目做什么—快速开始—使用示例—工作原理—证据范围—开发入口”，把采集、研究重放和审查记录移到二级文档。Codex本地安装依据为 [Build skills](https://learn.chatgpt.com/docs/build-skills)，核查日期2026-10-15。

## 单一维护入口

只维护 `skills/physwhen/` 和 `deliverables/PhysWhen-skill.zip`。英文 README 为默认入口，`README.zh-CN.md` 为对应中文版；同步更新核心说明、命令和证据范围。用 Git 提交定位历史内容，不再新增带编号的对外skill目录。旧实验快照及协议标识保持原样，只用于追溯。

## MIT 许可随包分发

根目录 `LICENSE` 与 `skills/physwhen/LICENSE` 保持一致，打包校验会检查二者。skill ZIP 包含该许可；独立盲测 HTML 在源码注释中保留项目许可及 KaTeX 原许可。MIT 适用于本项目原创内容，不覆盖历史论文、完整语料或第三方权利。
