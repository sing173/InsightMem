# 02 MemoryTool 与记忆操作

> 上一章：[01 记忆系统的工作流程](01-memory-workflow.md) · 下一章：[03 MemoryManager 与四种记忆](03-memory-manager-and-types.md)
> 对应 Hello Agents 第 8 章的 8.2.2–8.2.3：快速体验与 MemoryTool 详解。

## 本章你会得到什么

- 一张记忆操作清单：add、search、update、forget、consolidate；
- 每个操作的输入、输出、失败模式；
- 本仓库当前实现与 Hello Agents MemoryTool 的对应关系；
- 一个不会把“设计能力”误写成“已有 API”的实现状态表。

## MemoryTool 为什么存在

没有 MemoryTool 时，应用可以直接操作数据库。但当 Agent 需要自主记忆时，工具提供了统一接口：

```text
Agent
  → 选择工具与参数
  → MemoryTool 校验 scope/schema
  → MemoryManager 选择类型与生命周期
  → Store 读写
  → 返回可解释结果
```

工具的价值不是“把函数包一层”，而是把调用方必须知道的契约集中起来：

- 参数是什么；
- 哪个用户/命名空间；
- 成功返回什么；
- 冲突、越权、容量超限时怎样报错；
- 操作是否可重试、可审计。

Hello Agents 第 8 章的 MemoryTool 操作面比本仓库更完整：

| 操作 | 作用 |
|---|---|
| `add` | 写入记忆，可指定类型、重要性、文件路径和模态 |
| `search` | 按 query、类型、limit、最低重要性检索 |
| `summary` | 汇总当前记忆状态 |
| `stats` | 返回数量与统计 |
| `update` | 更新已有记忆 |
| `remove` | 删除指定记忆 |
| `forget` | 按策略清理低价值记忆 |
| `consolidate` | 整合或迁移记忆 |
| `clear_all` | 清空当前 scope 的记忆 |

下面重点拆解 add/search/update/forget/consolidate；summary/stats/clear_all 属于管理与运维操作。

## 操作 1：add——把经验写入记忆

### 输入

一条经验至少需要：

```text
content
type / kind
scope / user_id
source
metadata
```

Hello Agents 的 `MemoryTool.add` 还支持 `importance`、`file_path`、`modality` 等参数；本仓库的离线示例只使用前四项。

例如：

```python
semantic.add("signature", {
    "kind": "signature",
    "value": "John Doe",
    "content": "Always sign email replies as John Doe.",
})
```

### 输出

当前 `SemanticMemory.add()` 返回 `None`，实际写入发生在 `LocalStore.put()`。Hello Agents 的 MemoryTool 通常会返回工具可读的成功信息，例如记忆 ID 或数量。

### 失败模式

- scope 缺失；
- content 为空；
- key 冲突但 payload 不同；
- 敏感信息未分类；
- 同一经验重复写入。

本仓库的 email-agent 是离线实验，不包含完整工具 schema、鉴权和审计；这些属于生产 MemoryTool 扩展。

## 操作 2：search——按问题找回记忆

### 输入

```text
query
scope
memory_type（可选）
limit
min_importance（可选）
```

### 本仓库实现

```python
facts = semantic.recall("signature tone", limit=3)
examples = episodic.similar(current_email, limit=2)
```

`LocalStore.search()` 返回：

```python
MemoryItem(key=..., value=..., score=...)
```

### 输出必须包含什么

- 记忆 ID/key；
- 原始 value；
- 分数或排序依据；
- 来源与 scope；
- 是否被过滤。

没有来源和 scope，调用方无法判断能否注入，也无法排查串扰。

### 失败模式

- query 太宽泛；
- namespace 写错；
- 只搜 semantic，却需要 episodic；
- 候选深度不足；
- 过期记忆未失效。

## 操作 3：update——纠正或替换旧记忆

更新不是简单覆盖。至少区分：

| 更新语义 | 含义 | 风险 |
|---|---|---|
| Append | 新增一条事实 | 冲突与重复 |
| Overwrite | 替换当前值 | 丢失历史 |
| Invalidate | 旧值失效，保留审计 | 需要时间与来源 |
| Version | 新版本指向旧版本 | 需要 CAS 与回滚 |

教学骨架：

```python
def update_memory(store, namespace, key, expected_version, new_value):
    current = store.get(namespace, key)
    if current and current.value.get("version") != expected_version:
        raise ConflictError("memory changed")
    store.put(namespace, key, {**new_value, "version": expected_version + 1})
```

**当前仓库没有实现这个版本化更新接口。** email-agent 的种子记忆是预置数据，`LocalStore.put()` 可以直接覆盖，但没有 CAS、审计或冲突语义。

## 操作 4：forget——删除低价值或不应保留的记忆

遗忘不等于“从列表里消失”。Hello Agents 第 8 章讨论三类策略：

- 基于重要性：删除重要性低于阈值的记忆；
- 基于时间：删除超过指定天数的记忆；
- 基于容量：超限时删除最不重要的记忆。

教学骨架：

```python
def forget_by_capacity(memories, max_items):
    ranked = sorted(memories, key=lambda item: item.importance, reverse=True)
    removed = ranked[max_items:]
    for item in removed:
        tombstone(item.id, reason="capacity")
    return removed
```

生产实现还必须处理：

- 派生索引和缓存；
- 备份与恢复；
- 删除日志/tombstone；
- 共享 block 的权限；
- 恢复后不复活。

**当前仓库没有自动遗忘 API。** InsightMem 的用户删除依赖离线运维流程，不是 MemoryTool 的在线 forget。

## 操作 5：consolidate——把零散经验整理成稳定记忆

Consolidation 常见方向：

- working memory → episodic memory；
- episodic memory → semantic memory；
- 多条相似 fact 合并；
- 生成规则或 prompt；
- 清理重复与低价值内容。

教学骨架：

```python
def consolidate(snapshot):
    proposals = propose_merges(snapshot)
    current = reload_current_state()
    accepted = []
    for proposal in proposals:
        if still_applicable(proposal, current):
            accepted.append(proposal)
    return commit_with_cas(accepted)
```

关键约束：

- 不读取 gold label；
- 不覆盖新人工纠正；
- 可重试、可观测；
- 保留来源和版本。

**当前仓库没有后台 consolidation。** 第 03 章会进一步讨论 MemoryManager 怎样协调这些操作。

## 用现有 Notebook 验证 add/search

打开 [02-semantic-memory.ipynb](../../../experiments/email-agent/notebooks/02-semantic-memory.ipynb)，重点看三件事：

1. `seed_memories()` 如何写入；
2. `semantic.recall()` 如何检索；
3. `used_memory` 如何证明检索结果进入行为。

这个 Notebook 不需要调用 LLM，也不会自主决定何时搜索；它验证的是工具背后的数据契约。

## 当前实现状态

| 操作 | email-agent | InsightMem | 说明 |
|---|---|---|---|
| add | `SemanticMemory.add` 等 | `CodingMemoryService.add` | 可运行 |
| search | `recall` / `similar` / `search` | `CodingMemoryService.search` | 可运行 |
| update | 直接 `put` 覆盖 | append-only source | 无版本化更新工具 |
| forget | 未实现 | 离线 purge 流程 | 不是统一 MemoryTool |
| consolidate | 未实现 | 未实现 | 教学骨架 |

## 本章小结与下一步

你已经知道 MemoryTool 的五个核心操作，以及每个操作的契约和风险。当前仓库可运行 add/search，但 update、forget、consolidate 仍是设计能力。

下一章 [03 MemoryManager 与四种记忆](03-memory-manager-and-types.md) 会回答：这些操作应该由谁协调，记忆为什么分成不同类型，容量和遗忘策略怎样工作。
