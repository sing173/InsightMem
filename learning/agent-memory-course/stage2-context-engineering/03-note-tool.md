# 03 NoteTool：结构化任务笔记

> 上一章：[02 GSSC 流水线](02-gssc-pipeline.md) · 下一章：[04 TerminalTool：安全的文件系统探索](04-terminal-tool.md)
> 对应 Hello Agents 第 9 章的 9.4：NoteTool 设计、存储格式、核心操作与 ContextBuilder 集成。

## 本章你会得到什么

- 一份 V0.2.8 的笔记文件与索引格式；
- 七种 NoteTool 操作及其真实返回类型；
- 两个集成断裂点；
- 一个更可靠的笔记 schema 与实验设计。

## 先看为什么需要笔记

聊天历史适合记录“说过什么”，但不适合承担长期项目状态：

- 关键 blocker 埋在长对话里；
- 已完成事项与下一步计划容易混淆；
- 重启进程后历史可能丢失；
- 人类难以快速审阅。

NoteTool 把项目状态写成人类可读、Git 友好的 Markdown 文件：

```text
task_state：当前目标与进度
blocker：当前阻塞
action：下一步行动
conclusion：已确认结论
reference：参考资料
general：其他
```

它不是向量记忆，也不替代原始日志。它保存的是**可复用、可审阅的任务外部状态**。

## V0.2.8 存储格式

每个笔记是：

```text
<workspace>/<note_id>.md
```

示例：

```markdown
---
id: note_20260101_120000_1
title: Parser 丢失反斜杠
type: blocker
tags: ["parser", "windows"]
created_at: 2026-01-01T12:00:00
updated_at: 2026-01-01T12:00:00
---

# Parser 丢失反斜杠

parse_path 在 Windows 路径下丢失反斜杠。
需要保留原始 separators，并补充回归测试。
```

ID 格式：

```text
note_YYYYMMDD_HHMMSS_count
```

`tags` 实际写成 JSON 数组字符串，属于 YAML 可接受形式。

### status 并不在 front matter

V0.2.8 的 `status="active"` 只存在于运行时 metadata，不是文件字段，也没有 resolved/archived 生命周期。教程正文展示的完整状态机属于设计建议，不是当前实现。

## notes_index.json

实际索引结构：

```json
{
  "notes": [
    {
      "id": "note_20260101_120000_1",
      "title": "Parser 丢失反斜杠",
      "type": "blocker",
      "tags": ["parser", "windows"],
      "created_at": "2026-01-01T12:00:00"
    }
  ],
  "metadata": {
    "created_at": "2026-01-01T12:00:00",
    "total_notes": 1
  }
}
```

教程正文提到的字典索引、`updated_at/file_path` 和完整性校验，在 V0.2.8 中并不存在。

## 七种操作

构造：

```python
NoteTool(workspace="./notes", auto_backup=True, max_notes=1000)
```

| 操作 | 签名 | 行为 |
|---|---|---|
| create | `create(title, content, note_type="general", tags=[])` | 创建文件与索引项 |
| read | `read(note_id)` | 读取正文 |
| update | `update(note_id, title?, content?, note_type?, tags?)` | 更新文件与索引 |
| search | `search(query, limit=10)` | 标题、正文、标签子串匹配 |
| list | `list(note_type?, limit=10)` | 按索引插入顺序列出 |
| summary | `summary()` | 返回总数与类型统计文本 |
| delete | `delete(note_id)` | 删除文件与索引项 |

### 返回类型陷阱

V0.2.8 的 `run()` **始终返回字符串**，不是教程示例中的字典列表。

这导致 `04_note_tool_integration.py` 中的 JSON 解析失败后返回空列表，笔记可能根本没有进入 ContextBuilder。

**核心思想：** 工具返回类型是接口契约的一部分，不能只看函数名。

## 当前实现的可靠性缺口

- `list` 不按更新时间排序；
- `summary` 没有 `recent_notes`；
- 不支持 list 的标签过滤；
- `auto_backup` 参数存在，但没有实现备份；
- 删除后 ID 的 count 可能复用；
- 并发创建可能碰撞；
- `note_id` 没有路径安全校验；
- 标题含冒号等特殊字符时，手写 front matter 可能解析失败；
- 类型值只当字符串，不校验枚举。

这些问题不是“细节”，而是跨进程恢复和审计的基础。

## 与 ContextBuilder 的集成

第 9 章示例的流程：

```text
列出 blocker
  → 搜索相关笔记
  → 去重
  → 转 ContextPacket
  → ContextBuilder.build
  → 可选保存新笔记
```

设计意图的相关性映射：

```text
blocker     0.9
action      0.8
task_state  0.75
conclusion  0.7
other       0.6
```

但 Select 会覆盖这些分数，所以设计意图不等于实际排序。

### 两个断裂点

1. `_ensure_list_of_dicts()` 收到人类可读文本，JSON 解析失败后返回 `[]`；
2. 笔记包的 `metadata.type="note"` 不在 Structure 的展示分类中。

因此可能出现：

```text
笔记创建成功
  → 搜索成功
  → 转包失败或未展示
  → Agent 仍然不知道 blocker
```

## 更可靠的教学 schema

如果重新实现，建议至少增加：

```yaml
---
id: note_20260101_120000_1
title: Parser 丢失反斜杠
type: blocker
status: open
tags: [parser, windows]
created_at: 2026-01-01T12:00:00
updated_at: 2026-01-01T12:05:00
version: 2
source:
  - src/insightmem/coding/parse.py
  - tests/test_coding.py
---
```

并定义状态：

```text
open → in_progress → resolved → archived
```

实现约束：

- ID 使用 UUID 或原子计数，避免碰撞；
- 路径来自内部 ID，不接受任意文件路径；
- 写入采用临时文件 + rename；
- 索引与正文不一致时允许重建；
- 更新保留版本历史；
- 删除使用 tombstone 或备份策略；
- 返回结构化结果，不返回模糊文本。

## 一个可重复的实验

不需要 LLM，按以下步骤验证笔记系统：

1. 创建 `task_state`、`blocker`、`action` 各一条；
2. 读取并检查 front matter；
3. 更新 blocker 为 resolved；
4. 人工修改 Markdown 正文；
5. 新进程重新打开同一 workspace；
6. 搜索 blocker，确认状态与正文一致；
7. 删除一条笔记，检查索引与文件；
8. 并发创建 20 条，检查 ID 碰撞。

记录：

- 成功/失败操作数；
- 索引不一致次数；
- 重复 ID；
- 恢复后遗漏；
- 人工编辑是否被覆盖。

## 本仓库映射

当前仓库没有 NoteTool。可复用的原料是：

- InsightMem 的 source ID 与证据 hits；
- email-agent 的运行 manifest 与失败案例；
- Markdown 教程与 Wiki。

但它们不是任务状态系统。新增 NoteTool 时，应把“证据引用”作为笔记来源，而不是复制全部检索内容。

## 本章小结与下一步

你已经知道：

- NoteTool 是项目外部状态，不是向量记忆；
- V0.2.8 使用 Markdown + YAML，但返回字符串且生命周期不完整；
- 集成可能因解析失败或 type 未展示而断链；
- 可靠实现需要版本、状态、路径安全和索引一致性。

下一章 [04 TerminalTool：安全的文件系统探索](04-terminal-tool.md) 会讨论 Agent 怎样按需读取文件，以及为什么“白名单 + cwd”不等于沙箱。
