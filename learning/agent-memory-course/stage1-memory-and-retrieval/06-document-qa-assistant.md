# 06 项目：智能文档问答助手

> 上一章：[05 高级检索与本仓库实现](05-advanced-retrieval.md) · 下一章：[07 总结、练习与实现缺口](07-review.md)
> 对应 Hello Agents 第 8 章的 8.4：构建智能文档问答助手。

## 项目目标

做一个能回答文档问题、保留证据来源、在信息不足时拒答的最小助手：

```text
Add(documents) → committed evidence index
Search(question) → ordered evidence with provenance
Reader(question, evidence) → answer + citations / abstention
```

第一阶段不追求功能齐全，先验证三件事：

1. 写入的数据能否立即检索；
2. 检索结果能否追溯原文；
3. 回答质量能否与检索质量分开评测。

## 当前仓库能运行到哪一步

| 组件 | 状态 | 说明 |
|---|---|---|
| 文档/消息写入 | 可运行 | InsightMem Add |
| 分块、索引、三路召回 | 可运行 | InsightMem Search |
| 用户隔离、幂等、来源 span | 可运行 | Quickstart 与测试覆盖 |
| 上下文装配 | 教学骨架 | 需要固定顺序与预算 |
| 固定 reader | 教学骨架 | 可接 LLM 或确定性提取器 |
| 自动评测报告 | 部分可运行 | email-agent 有离线评测，文档 QA 需补数据 |

因此本章不是“已经有一个完整问答产品”，而是教你如何把现有证据层组装成可评测系统。

## 系统架构

```text
文档/消息
  │
  ▼
InsightMem Add
  │
  ▼
source_messages / source_chunks / index_views / view_embeddings
  │
  ▼
InsightMem Search
  │
  ├─ raw BM25
  ├─ code-expanded BM25
  └─ exact dense
  │
  ▼
fused candidates → bundle/dedup → deterministic top_k
  │
  ▼
Context Builder
  │
  ▼
Fixed Reader
  │
  ▼
Answer + citations / abstention
```

## Hello Agents 的综合案例

第 8 章的 `PDFLearningAssistant` 将 MemoryTool 与 RAGTool 组合起来，提供：

- PDF 加载；
- 文档问答；
- 学习笔记；
- 记忆回忆；
- 统计信息；
- JSON 报告；
- Gradio 界面。

它展示的是完整应用闭环，而不只是一个检索函数。但完整运行依赖模型服务、向量/图存储和文件读取；任何外部服务失败都可能阻断流程。

本教程借用它的案例结构，但把底座换成本仓库可离线验证的 InsightMem 证据层，并把 reader 保留为教学骨架，避免伪造 LLM 输出。

## 第 1 步：准备一个小型文档集

准备 10–20 篇短文档或消息，覆盖：

- 精确事实：版本号、路径、错误码；
- 语义问题：同义改写；
- 多跳问题：需要两篇文档；
- 更新问题：新值取代旧值；
- 无答案问题：必须拒答。

每篇文档记录：

```text
doc_id
source_path
content
```

每个问题记录：

```text
query_id
question
gold_doc_ids
gold_spans
expected_behavior: answer / abstain
```

不要只标 gold answer。没有 gold evidence，就无法区分检索失败和 reader 失败。

## 第 2 步：写入文档

使用 [InsightMem Quickstart](../../../experiments/insightmem/notebooks/00-quickstart.ipynb) 的运行接口：

```python
from insightmem_lab import HashEmbedder, start_experiment
from insightmem.store import MemoryMessage

run = start_experiment(
    "experiments/insightmem",
    "document-qa",
    embedder=HashEmbedder(),
)

messages = [
    MemoryMessage(role="user", content=doc["content"])
    for doc in documents
]

stored = run.add("docs-v1", "user-a", "docs", messages)
```

真实项目应使用配置好的 embedding backend。Quickstart 的 `HashEmbedder` 只用于离线验证数据流，不代表语义检索质量。

检查：

- `stored > 0`；
- 同一 request 重放结果不变；
- 数据库只属于当前 run；
- manifest 记录 embedding identity。

## 第 3 步：检索证据

```python
hits = run.search("user-a", question, top_k=5)
```

保存完整 hits，不只保存最终答案：

```python
run.save("retrievals.json", {
    "query_id": query_id,
    "question": question,
    "hits": hits,
})
```

检查：

- 每条 hit 是否有稳定 ID；
- content 是否带来源标签；
- gold doc 是否进入候选；
- 是否存在重复或重叠证据；
- top_k 是否超过预算。

## 第 4 步：装配上下文

一个最小 context builder：

```python
def build_context(hits: list[dict], budget_chars: int) -> str:
    blocks = []
    used = 0
    for hit in hits:
        block = hit["content"]
        cost = len(block) + 2
        if used + cost > budget_chars:
            continue
        blocks.append(block)
        used += cost
    return "\n\n".join(blocks)
```

固定顺序，例如按相关性从高到低。记录：

- 候选 ID；
- 最终注入 ID；
- 每条证据的字符成本；
- 因预算被挤掉的证据。

**核心思想：** “召回了”不等于“注入了”。预算和选择是独立失败层。

## 第 5 步：接入固定 reader

Reader 必须固定模型、prompt、温度和上下文预算。最小接口：

```python
class FixedReader:
    def answer(self, question: str, context: str) -> str:
        ...
```

Prompt 至少包含：

```text
只根据给定上下文回答。
每个结论标注来源 ID。
信息不足时明确说无法确认。
不要编造上下文之外的路径、版本或数字。
```

输出结构：

```json
{
  "answer": "...",
  "citations": ["c1-..."],
  "abstained": false
}
```

如果暂时不接 LLM，可以做一个确定性提取 reader：只有当 gold span 出现在 hits 中时返回该 span，否则 abstain。它适合验证评测链路，不适合评估真实生成能力。

## 第 6 步：分开评测检索与 reader

### 检索层

- Recall@k：gold evidence 是否进入候选；
- MRR：第一个 gold 的排名；
- Citation coverage：答案引用是否指向真实 hit；
- Duplicate occupancy：重复内容占用多少 top_k。

### Reader 层

- Answer accuracy；
- Abstention correctness；
- Citation correctness；
- Constraint retention：版本、路径、数字是否保持。

### Oracle reader

给同一个 reader 两种输入：

1. 系统检索结果；
2. gold evidence。

结论：

| 现象 | 归因 |
|---|---|
| oracle 好、检索差 | 召回/选择问题 |
| 两者都差 | reader/prompt 或任务问题 |
| 检索好、回答仍差 | 证据使用、冲突或推理问题 |

## 第 7 步：保存完整运行产物

```text
runs/<run_id>/
├── manifest.json
├── memory.sqlite3
├── retrievals.json
├── predictions.json
├── metrics.json
└── failures.json
```

manifest 至少记录：

- 数据版本与 hash；
- query IDs；
- code commit；
- embedding identity；
- top_k、候选深度、预算；
- reader/prompt 版本；
- 失败与重试。

## 常见失败与修复

| 失败 | 现象 | 修复方向 |
|---|---|---|
| 写入遗漏 |  gold 文档不在库中 | 检查 Add、过滤和切分 |
| 召回失败 | 库里有但 top_k 没有 | 改 query、词法/dense 融合、候选深度 |
| 选择失败 | 候选有但被去重/预算挤掉 | 检查 selector 与上下文预算 |
| Reader 失败 | 证据正确但回答错 | 固定 reader、prompt、oracle 对照 |
| 无依据回答 | 信息不足仍编造 | 强化 abstention 与引用校验 |
| 串扰 | 看到其他用户文档 | 检查 namespace、缓存和恢复路径 |

## 项目验收

- Add 幂等且立即可检索；
- Search 只返回当前用户证据；
- 每条证据可追溯到来源；
- 候选、注入和回答分别保存；
- 至少两类 query：精确匹配与语义改写；
- 至少一个无答案题验证 abstention；
- 至少一个失败案例能定位到具体层；
- 报告成本，不只报 accuracy。

## 本章小结与下一步

这个项目把前五章串成一条完整链路：

```text
文档 → 索引 → 检索 → 选择 → 注入 → reader → 评测
```

你现在应该能把“回答错了”拆成具体层，而不是统一归因于“模型不行”。下一章 [07 总结、练习与实现缺口](07-review.md) 会汇总阶段一，并列出进入阶段二前还需要补齐的能力。
