---
title: InsightMem 三路检索与证据选择
summary: 原始 BM25、代码展开 BM25 与稠密向量经 RRF 融合，再过滤、合并和去重。
status: verified
section: InsightMem
order: 21
updated: 2026-11-24
tags: [insightmem, retrieval, bm25, rrf, evidence]
sources:
  - src/insightmem/coding/service.py
  - src/insightmem/coding/parse.py
  - src/insightmem/coding/content.py
  - src/insightmem/coding/filter.py
  - src/insightmem/coding/evidence.py
  - src/insightmem/coding/selection.py
  - configs/coding/default.json
  - learning/agent-memory-tutorial/04-retrieval.md
  - learning/agent-memory-tutorial/05-fusion.md
---

# InsightMem 三路检索与证据选择

## 检索流水线

```text
user_id 快照
  → raw BM25
  → code-expanded BM25
  → dense cosine
  → RRF
  → 过程叙述过滤
  → 相邻片段合并
  → 精确与跨度去重
  → top_k 证据
```

核心流程见 [service.py:163–284](../src/insightmem/coding/service.py#L163)。

## 三路召回

| 召回腿 | 实现 | 擅长 | 盲区 |
|---|---|---|---|
| raw BM25 | 对原始 chunk 文本做 BM25 | 精确词、错误串、罕见标识符 | 同义改写 |
| code-expanded BM25 | 拆分路径、snake_case、camelCase 和标识符 | 代码词汇、函数名、文件路径 | 自然语言语义 |
| dense cosine | query 向量与归一化 view 向量做点积 | 语义相似、改写 | 精确串、数字、罕见词 |

代码展开规则见 [parse.py:74–84](../src/insightmem/coding/parse.py#L74)。三路设计的目的不是简单增加召回量，而是让错误方式彼此不同。

## RRF 融合

RRF 按名次而不是原始分数累加：

```text
score(candidate) = Σ 1 / (k + rank_leg(candidate))
```

默认 `k=60`。这样避免把 BM25 分数与余弦相似度直接相加。每个候选在每路只保留最好名次，重复命中不会重复累加。

## 过程叙述过滤

只包含“准备查看”“任务完成”等过程信息的 assistant 消息会在查询时失去候选资格，但仍然：

- 保留在 BM25 语料中；
- 继续影响 BM25 统计；
- 占用 RRF 名次。

因此过滤不会改变其他证据原本的得分。相关规则见 [filter.py](../src/insightmem/coding/filter.py) 和 [service.py:194–205](../src/insightmem/coding/service.py#L194)。

## 证据合并与去重

- 同一消息中重叠或相邻的 chunk 可以合并为 evidence bundle。
- bundle 只是便利视图，不替换原始成员。
- 完全重复的正文排在唯一内容之后。
- 已选择跨度覆盖的候选会被抑制。
- 裸工具调用和过渡语句的类型因子为 `0.15`，其他内容为 `1.0`。
- 最终 utility 以相关性为主，查询覆盖和新颖性作为有界 tie-break。

实现见 [evidence.py:70–139](../src/insightmem/coding/evidence.py#L70) 和 [selection.py:8–42](../src/insightmem/coding/selection.py#L8)。

## 默认参数

| 参数 | 值 |
|---|---:|
| `chunk_units` | 320 |
| `overlap_units` | 40 |
| `max_chunk_chars` | 6000 |
| `rrf_k` | 60 |
| `leg_max` | 200 |
| `evidence_bundle_chars` | 4000 |
| `evidence_max_chars` | 12000 |

参数来源：[default.json](../configs/coding/default.json)。更改参数或 embedding 身份需要新数据库，因为数据库启动时会核对指纹。

## 学习价值

这个页面适合做三路消融：分别关闭 raw BM25、code BM25 和 dense，再比较不同查询类型的 Recall@5、MRR 和噪声稳定性。实验步骤见 [[learning-path]] 及 [04-retrieval.md](../learning/agent-memory-tutorial/04-retrieval.md)。

<!-- generated:backlinks:start -->
## 反向链接

- [[insightmem|InsightMem 机制审计]] — InsightMem 是全量会话轨迹持久化与确定性混合证据检索，不是抽取式记忆 OS。
- [[hybrid-retrieval|混合检索与 RRF]] — 用词法、代码词法、稠密向量等不同召回腿互补，再以 RRF 融合名次。
<!-- generated:backlinks:end -->
