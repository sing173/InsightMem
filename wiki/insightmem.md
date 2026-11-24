---
title: InsightMem 机制审计
summary: InsightMem 是全量会话轨迹持久化与确定性混合证据检索，不是抽取式记忆 OS。
status: verified
section: InsightMem
order: 20
updated: 2026-11-24
tags: [insightmem, architecture, episodic-memory, evidence]
sources:
  - README.md
  - docs/architecture.md
  - docs/api-contract.md
  - src/insightmem/coding/service.py
  - src/insightmem/coding/parse.py
  - configs/coding/default.json
---

# InsightMem 机制审计

## 一句话定位

InsightMem 采用 **全量会话轨迹持久化 + chunk 级多路混合检索 + 查询时证据装配**。按记忆类型划分，它的核心是**外部情景记忆**；按工程形态划分，它更接近 **Transcript/Episode 存储 + Hybrid RAG**。

它不生成答案，不抽取长期事实，也不管理 LLM 当前上下文。调用方把返回的证据交给 answerer 或 agent 使用。

## 数据模型

SQLite 中保存以下相互关联的记录：

| 表 | 作用 |
|---|---|
| `coding_requests` | 请求幂等、载荷哈希、用户内写入序号 |
| `source_messages` | 原始消息、角色、类型、时间戳 |
| `source_chunks` | 消息的字符跨度与重叠切片 |
| `index_views` | 检索表示；当前主要是 source view |
| `view_sources` | view 到原始消息跨度的映射 |
| `view_embeddings` | 归一化向量、维度和模型身份 |

Schema 见 [service.py:24–34](../src/insightmem/coding/service.py#L24)。

## Add 做了什么

1. 对 `session_id + messages` 计算载荷哈希，检查 `request_id` 幂等。
2. 将消息分类为 issue prompt、assistant text、thinking、tool call、tool result 等。
3. 把每条消息切成默认 320 token、重叠 40 token、最多 6000 字符的 chunk。
4. 为 chunk 建立 source view，并对非空文本生成归一化 embedding。
5. 在一个事务内写入消息、chunk、view、来源映射和向量。

Add 是同步的：HTTP 成功返回时，数据已经可检索。实现见 [service.py:98–161](../src/insightmem/coding/service.py#L98)。

## Search 做了什么

1. 读取一个 `user_id` 下的已提交快照。
2. 运行 raw BM25、代码展开 BM25、dense cosine 三路召回。
3. 使用 RRF 融合，标记纯过程叙述，合并相邻片段并去重。
4. 按相关性、类型权重和查询覆盖选择最多 `top_k` 条证据。
5. 返回带来源角色和类型的原文证据，不重写内容。

详见 [[insightmem-retrieval]]。

## 能力边界

| 能力 | 状态 |
|---|---|
| 全量保存提交的消息 | 有 |
| 同步、立即可检索 | 有 |
| 用户级隔离 | 有 |
| 多路混合检索 | 有 |
| 原文证据去重与合并 | 有 |
| 事实抽取与整合 | 无 |
| 摘要、笔记、dreaming | 无 |
| 知识图谱与多跳遍历 | 无 |
| 双时间与事实失效 | 无 |
| 时间衰减、热度淘汰、自动遗忘 | 无 |
| 工作上下文分页与递归摘要 | 无 |
| 在线覆盖或删除 | 无 |

治理细节见 [[insightmem-governance]]，竞赛定位见 [[aml-coding-harness]]，框架对比见 [[memory-frameworks]]。

<!-- generated:backlinks:start -->
## 反向链接

- [[agent-memory|Agent Memory 概念地图]] — 用五个动作、四种记忆类型和四层知识结构理解 Agent Memory。
- [[learning-path|用 InsightMem 学习 Agent Memory]] — 把 InsightMem 当作外部情景记忆与混合检索的可运行参考，再补齐抽取、更新和遗忘。
- [[memory-frameworks|Agent Memory 框架机制对比]] — 从记忆单元、写入、更新、检索和上下文管理比较 InsightMem 与六类框架。
- [[memos-vs-memoryos|MemOS 与 MemoryOS 不要混淆]] — MemOS 管理记忆资源与表示，MemoryOS 管理短中长期对话记忆、分页与人格。
- [[schema|Wiki 维护约定]] — 说明源文档、Wiki 页面、frontmatter、生成索引与反向链接的维护方式。
- [[aml-coding-harness|AML Coding Track 与 InsightMem 定位]] — InsightMem 是 AML 兼容的同步 Add/Search 记忆服务，平台负责固定答案生成与评分。
<!-- generated:backlinks:end -->
