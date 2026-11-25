# 02 GSSC 流水线

> 上一章：[01 ContextBuilder](01-context-builder.md) · 下一章：[03 NoteTool：结构化任务笔记](03-note-tool.md)
> 对应 Hello Agents 第 9 章的 9.3.3–9.3.5：GSSC 详解、完整示例与最佳实践。

## 本章你会得到什么

- Gather、Select、Structure、Compress 的准确行为；
- 一个固定时间戳、可重复的 GSSC 示例；
- 三个真实缺口：分数覆盖、note 不展示、前缀截断；
- 一组可执行的对照实验设计。

## 先看四个阶段分别解决什么

| 阶段 | 输入 | 输出 | 核心问题 |
|---|---|---|---|
| Gather | query、history、instructions、memory/RAG | 候选 packet 列表 | 信息从哪里来？ |
| Select | 候选 packet、query、config | 选中 packet 列表 | 这次带哪些？ |
| Structure | 选中 packet | 固定分区文本 | 怎样组织？ |
| Compress | 结构化文本、预算 | 最终上下文 | 超预算怎么办？ |

```text
Gather → Select → Structure → Compress
```

每个阶段都可能丢失信息，因此要分别记录输入、输出和原因。

## Gather：收集候选

V0.2.8 的实际顺序：

1. **系统指令**：类型 `instructions`，内容原样封装；
2. **任务状态记忆**：固定查询“任务状态 OR 子目标 OR 结论 OR 阻塞”，`min_importance=0.7, limit=5`；
3. **相关记忆**：按用户 query 检索，`limit=5`；
4. **RAG**：按用户 query 检索，`limit=5`；
5. **对话历史**：最后 10 条消息合并成一个 `history` 包；
6. **额外包**：原样追加，顺序不变。

外部检索异常会打印警告并继续。这是容错，但不是“无影响”：证据可能静默丢失。

### Gather 的教学骨架

```python
def gather(user_query, history, memory_hits, rag_hits, extra_packets):
    packets = [
        ContextPacket("Role & Policies", metadata={"type": "instructions"}),
        ContextPacket(user_query, metadata={"type": "task"}),
    ]
    packets += memory_hits
    packets += rag_hits
    if history:
        packets.append(ContextPacket(
            "\n".join(f"[{m.role}] {m.content}" for m in history[-10:]),
            metadata={"type": "history", "count": len(history[-10:])},
        ))
    packets += extra_packets
    return packets
```

真实实现把用户 query 放在 Structure 的 Task 分区，而不是作为普通候选参与相关度过滤。

## Select：按相关性与新近性选择

V0.2.8 的相关性：

```text
relevance = |query_tokens ∩ content_tokens| / |query_tokens|
```

新近性：

```text
recency = exp(-age_seconds / 3600)
```

综合分：

```text
score = 0.7 × relevance + 0.3 × recency
```

非系统包必须满足 `min_relevance`。系统包先放入，其余按综合分降序，贪心填充预算；放不下的包会跳过，并继续尝试更小的包。

### 一个固定例子

假设：

```text
query_tokens = {parser, backslashes}
```

候选 A：

```text
content = "parser backslashes"
age = 2 hours
relevance = 1.0
recency = exp(-2) ≈ 0.1353
score = 0.7 × 1.0 + 0.3 × 0.1353 ≈ 0.7406
```

候选 B：

```text
content = "parser release notes"
age = 0 hours
relevance = 0.5
recency = 1.0
score = 0.7 × 0.5 + 0.3 × 1.0 = 0.65
```

A 虽然更旧，但因为更相关，仍可能排在 B 前面。

### 三个容易忽略的行为

1. **覆盖原始分数**：Select 会重新计算所有包的 `relevance_score`。维护助手给 blocker 设置 0.9，并不保证它最终排第一。
2. **系统包不保证保留**：如果系统包自身超过预算，也可能放不进去。
3. **没有真正 MMR**：V0.2.8 配置了 `enable_mmr`，但实际没有多样性重排。

## Structure：把选中内容组织成固定分区

V0.2.8 的实际分区顺序：

```text
[Role & Policies]
  系统指令

[Task]
  用户问题

[State]
  task_state

[Evidence]
  related_memory / knowledge_base / retrieval / tool_result

[Context]
  history

[Output]
  结论、依据、风险与假设、下一步行动建议
```

固定结构有两个好处：

- reader 知道去哪里找任务、状态和证据；
- 评测可以按分区检查预算与遗漏。

### 一个真实集成缺口

NoteTool 集成示例把笔记标为：

```python
metadata={"type": "note"}
```

但 Structure 没有 `note` 分类。结果是：**笔记可能被 Gather 和 Select 选中，却没有显示在任何分区。**

这正好说明“检索到了不等于注入了”。修复方式不是继续调分数，而是明确 note 的展示归属，例如映射到 `[State]` 或 `[Evidence]`。

## Compress：超预算时怎样处理

V0.2.8 的实际压缩不是 LLM 摘要，而是**按行前缀截断**：

```text
可用预算 = max_tokens × (1 - reserve_ratio)
未超预算：原样返回
超预算：逐行保留，下一行放不下就停止
```

例如：

```text
max_tokens=4000, reserve=0.15 → 3400 tokens
```

风险：

- 可能优先丢掉 Evidence 后半段或 Output；
- Task、Output、分区标题和空行没有完整计入 packet 预算；
- `enable_compression=False` 时直接返回，可能超预算；
- 截断看起来像摘要，但没有保证语义完整。

### 教学骨架

```python
def compress_by_lines(text: str, budget: int, count_tokens) -> str:
    kept = []
    used = 0
    for line in text.splitlines():
        cost = count_tokens(line + "\n")
        if used + cost > budget:
            break
        kept.append(line)
        used += cost
    return "\n".join(kept)
```

生产实现应优先按分区压缩，而不是机械截断全文。

## 三个对照实验

### 实验 1：高相关旧包 vs 低相关新包

固定两个 timestamp，只改变内容相关性，观察 Select 排序。记录综合分和是否进入最终上下文。

### 实验 2：note 包能否显示

创建 `metadata.type="note"` 的包，运行 Structure，检查输出是否包含笔记内容。预期在 V0.2.8 中不显示。

### 实验 3：预算边界

逐步降低 `max_tokens`，记录：

- 第一个被过滤的包；
- 第一个被截断的分区；
- 最终 token 估算；
- 关键证据是否丢失。

不要只报“压缩成功”，要报“丢了什么”。

## 本仓库怎样复用这套思路

InsightMem 已经提供：

- 有序 hits；
- source ID；
- score；
- 去重与 span 信息。

ContextBuilder 需要新增：

- packet 元数据；
- token 估算；
- 相关性与新近性选择；
- 固定分区；
- 预算诊断；
- 压缩策略。

最小映射：

```text
InsightMem hits
  → ContextPacket(type=knowledge_base, source_id=hit.id)
  → Select
  → [Evidence]
  → Fixed Reader
```

当前仓库没有这条产品实现，本章代码是教学骨架。

## 本章小结与下一步

你已经知道 GSSC 的每一层，以及三个真实失败：

- 原始相关分数可能被覆盖；
- note 可能被选中但不展示；
- 前缀截断可能丢失关键分区。

下一章 [03 NoteTool：结构化任务笔记](03-note-tool.md) 会解决“跨请求状态怎样持久化”，并说明 Markdown 笔记的 schema、操作和与 ContextBuilder 的集成。
