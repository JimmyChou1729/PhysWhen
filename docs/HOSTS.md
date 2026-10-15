# 宿主兼容与插件安装

PhysWhen 维护一份 `skills/physwhen/` 源码，提供两种分发包：

| 入口 | 内容 | 使用方式 |
| --- | --- | --- |
| `deliverables/PhysWhen-skill.zip` | 单独的 skill 文件夹 | Codex 或其他支持本地 Agent Skills 的宿主 |
| `deliverables/PhysWhen-plugin.zip` | 根 `plugin.json`、许可和同一份完整 skill | 支持 Agent Plugins 的账号插件入口，面向 ChatGPT 云端等宿主 |

**不要把 skill ZIP 当作插件 ZIP 上传。** 前者没有插件清单；GitHub 仓库公开也不等于插件已发布到 ChatGPT 公共目录。

## 网页版 ChatGPT

通过账号支持的插件创建/导入入口使用 `PhysWhen-plugin.zip`，或打开维护者在 Plugin Creator 保存后返回的私人插件链接，安装或启用 PhysWhen。选择插件，附上稿件或研究笔记，说“使用 PhysWhen 修改这篇论文”即可。

账号插件创建成功、宿主安装成功和实际写作调用成功是三个不同状态。套餐、工作区策略、灰度开放和插件支持范围仍可能影响入口。没有实际运行验证时，不声称某个网页模式已经兼容通过。

## Dot

官方说明：Dot 可以使用账号已安装、启用且受支持的插件；仅在本机安装的 skill 需要连接该电脑。因此应优先使用账号中的 PhysWhen 插件，不能假定 Dot 会读取你电脑上的 skill 目录。

在 Dot 的插件连接设置中确认能看到并启用 PhysWhen，再附上材料测试。插件没有加 `policy.products` 限制；这并不保证每个账号的 Dot 已支持它。尚未在 Dot 中实际调用验证。

## 文件和运行环境

- 云端任务应使用当前会话附件或宿主已授权的文档，不能假定能读取电脑上的绝对路径。
- 新写和修改均要求先检索相关文献与术语。插件本身不提供搜索服务器，使用宿主已有的检索工具；缺少工具时必须声明无法完成检索，不能把模型记忆当作实际检索证据。
- skill 指令和参考资料随包提供，不依赖本地论文库或单独购买的模型 API。
- 大纲检查脚本是可选辅助；仅在宿主提供兼容 Python 执行环境时运行。没有执行环境仍可写作，但不能声称已经运行脚本检查。
- 本插件不提供 MCP 工具、远程数据连接、交互页面或生命周期脚本，不申请额外服务权限。

## 维护

```bash
python3 scripts/package_plugin.py
python3 scripts/package_plugin.py --check
python3 -m unittest discover -s tests -p 'test_package_plugin.py' -v
```

插件从同一份已维护的skill固定文件清单构建，不复制另一套写作规则。`plugin.json` 的 SemVer 是宿主发布识别用的内部元数据；产品名称和调用始终为 `PhysWhen` / `physwhen`。源码变化后重新打包；账号中的插件是上传快照，不会随 Git 自动更新，须更新已有插件而不是创建同名副本。

当前包用于个人或工作区兼容验证，不是已获审核的公共插件目录发布包。公共目录提审另行准备展示素材和审核资料。

## 当前验证记录

插件包已通过独立审查、5项包装测试，并成功保存为当前创建者账号的私人插件。上传后回读了全部文件：skill的9个文件和根许可与源码一致；平台另生成了 `.codex-plugin/plugin.json` 兼容清单。该账号插件链接是私人安装入口，不作为公共README的通用安装链接。

创建后的一次插件目录搜索暂未列出新条目，未据此声称已安装或启用。网页ChatGPT和Dot的真实稿件调用仍待验证；不把包结构或回读成功等同于宿主执行通过。

## 官方依据

核查日期：2026-10-15。

- [插件清单与包结构](https://developers.openai.com/plugins/build/plugins)
- [无需 MCP 的 skills-only 插件](https://developers.openai.com/plugins/concepts/skills)
- [ChatGPT 插件支持范围](https://learn.chatgpt.com/docs/plugins)
- [Dot 的插件与本机技能连接](https://learn.chatgpt.com/docs/dots)
