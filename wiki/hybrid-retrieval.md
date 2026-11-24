---
title: 混合检索与 RRF
summary: 用词法、代码词法、稠密向量等不同召回腿互补，再以 RRF 融合名次。
status: source-reviewed
section: 机制
order: 40
updated: 2026-11-24
tags: [retrieval, hybrid-search, bm25, rrf]
sources:
  - learning/agent-memory-tutorial/04-retrieval.md
  - learning/agent-memory-tutorial/05-fusion.md
  - src/insightmem/coding/service.py
  - src/insightmem/store.py
---

# 混合检索与 RRF

## 为什么需要多路召回

没有一种检索方法覆盖所有问题：

| 方法 | 擅长 | 盲区 |
|---|---|---|
| BM25 | 精确词、错误串、罕见标识符 | 同义改写 |
| 代码词展开 | 路径、函数名、snake_case、camelCase | 自然语言语义 |
| 稠密向量 | 语义相似、改写 | 精确串、数字、罕见词 |
| 图 / 实体 / 时间 | 多跳、关系、时效 | 抽取质量与基础设施成本 |

多路召回的价值是**错误方式不同**，而不是单纯增加候选数量。详见 [04-retrieval.md:14–39](../learning/agent-memory-tutorial/04-retrieval.md#L14)。

## RRF 的基本形式

```text
RRF(d) = Σ 1 / (k + rank_i(d))
```

其中 `rank_i(d)` 是文档 `d` 在第 `i` 路的排名，`k` 是平滑常数。InsightMem 默认 `k=60`。

### 为什么不用原始分数直接相加

- BM25 与余弦分数的量纲不同。
- 不同 query 的分数尺度会变化。
- 某些召回腿的分数分布更陡峭，直接相加会让某一腿主导。
- 名次融合更稳健，也更容易解释。

### RRF 不能解决什么

- 时间、权限、租户隔离必须在前置过滤或查询约束中完成。
- 错误或高度重复的召回腿仍可能污染结果。
- RRF 不理解“新事实是否替代旧事实”。
- 它只融合已有候选，不能补救所有召回缺口。

## InsightMem 的实现特点

- 三路：raw BM25、code-expanded BM25、dense cosine。
- 同一候选在一路只取最好名次。
- 过程叙述保留语料统计和排名贡献，但不可被最终选中。
- 融合之后还有 bundle、精确去重、跨度去重和类型降权。

详见 [[insightmem-retrieval]] 和 [05-fusion.md](../learning/agent-memory-tutorial/05-fusion.md)。

## 最小实验

准备 30 个 query，分别关闭一路召回，记录 Recall@5、MRR 和 top-10 命中率；再按精确标识符、语义改写、错误串分类比较。实验框架见 [labs.md:83–99](../learning/agent-memory-tutorial/labs.md#L83)。

<!-- generated:backlinks:start -->
## 反向链接

- [[agent-memory|Agent Memory 概念地图]] — 用五个动作、四种记忆类型和四层知识结构理解 Agent Memory。
<!-- generated:backlinks:end -->
