# 05 高级检索与本仓库实现

> 上一章：[04 RAG 系统与最小知识库](04-rag-system.md) · 下一章：[06 项目：智能文档问答助手](06-document-qa-assistant.md)
> 对应 Hello Agents 第 8 章的 8.3.5：高级检索策略。

## 本章你会得到什么

- 一张常见检索策略地图；
- InsightMem 三路召回的准确定位；
- 一个可执行的消融实验设计；
- 一份“已实现 / 教学骨架 / 未实现”清单。

## 先问：为什么要高级检索

单一检索器很难覆盖所有问题：

- 精确 ID 可能需要词法匹配；
- 同义改写可能需要 dense；
- 多跳关系可能需要图遍历；
- 时间问题需要时间过滤；
- 候选已经很多时，可能需要重排。

高级检索不是“算法越多越好”，而是让不同错误方式的检索器互补，并把候选控制到可解释、可预算的范围内。

## 检索策略地图

| 策略 | 核心做法 | 适合问题 | 主要成本/风险 |
|---|---|---|---|
| 词法检索 | BM25、TF-IDF | ID、路径、错误码、精确短语 | 同义改写弱 |
| Dense | embedding + cosine/kNN | 语义相近表达 | 精确 token 弱、模型成本 |
| 混合检索 | 词法 + dense + 融合 | 通用问答 | 融合参数与候选深度 |
| Late interaction | token 级匹配，如 ColBERT | 细粒度语义匹配 | 存储与计算更大 |
| Cross-encoder | query-doc 联合打分 | 候选重排 | 延迟高，不能替代召回 |
| 图检索 | entity/edge 遍历 | 多跳关系 | 抽取错误会沿边传播 |
| 时间检索 | valid/recorded interval | as-of、更新、过期 | 时间语义必须严格 |
| Agentic retrieval | Agent 自主改写 query、翻页 | 多轮探索 | 成本与停止条件难控制 |

Hello Agents 第 8 章讨论了多种高级策略。本仓库当前实现的是**词法 + dense + 确定性融合与选择**，没有图检索、cross-encoder 或 Agentic retrieval。

## InsightMem 的三路召回

### Raw BM25

直接对 source chunk 原文做 BM25：

```python
raw = bm25_scores([chunk["raw_content"] for chunk in chunks], query)
```

适合精确标识符和原文短语。

### Code-expanded BM25

对代码符号做拆词和扩展，再对 view 文本检索。例如：

```text
parseHTTPResponse_v2
  → parse HTTP Response v2
```

适合代码场景中的大小写、下划线和组合词变化。

### Exact dense

对 query 和 view embedding 做精确点积：

```python
dense = document_vectors @ query_vector
```

它不是 ANN。语料规模增大时，需要重新测量扫描成本。

### Grouped-rank fusion

InsightMem 使用分组名次融合，不是逐文档标准 RRF。同组 chunk 共享名次，融合后再做候选准备、bundle 和 span 抑制。

因此不能把 InsightMem 的分数直接与标准 RRF 实现横比。

## 做一次三路消融

目标：验证三条腿是否互补，而不是只看 full system 的 Recall。

### 实验矩阵

| 配置 | raw BM25 | code BM25 | dense |
|---|---|---|---|
| all | 开 | 开 | 开 |
| raw only | 开 | 关 | 关 |
| view only | 关 | 开 | 关 |
| dense only | 关 | 关 | 开 |
| no raw | 关 | 开 | 开 |
| no view | 开 | 关 | 开 |
| no dense | 开 | 开 | 关 |

固定：

- 同一 snapshot；
- 同一 query 集合；
- 同一 embedding identity；
- 同一 `top_k`、候选深度和融合参数；
- 同一最终 selector。

### 当前实现边界

公开 Add/Search **没有逐腿开关**。不能写成：

```python
service.search(..., disable_dense=True)  # 当前接口不存在
```

可行方式：

1. 在独立实验分支暴露内部候选阶段；
2. 或对同一快照离线调用 `bm25_scores`、向量矩阵和融合逻辑；
3. 保持生产接口和数据库不变，记录实验 commit。

### 记录哪些结果

每题至少保存：

```text
query_id
gold_chunk_ids
每条腿的 rank / score
fused rank
final selected ids
```

指标：

- Recall@5 / Recall@10；
- MRR；
- all-recall：任一腿是否包含 gold；
- 失败类型：gold 未进候选、候选内排后、最终被去重/预算挤掉。

**核心思想：** 如果 gold 进入某条腿但没进入 fused top_k，问题在候选深度或融合；如果三腿都没有 gold，问题在表示、chunk 或 query。

## MQE 与 HyDE：扩展候选，不是重排

Hello Agents 第 8 章还展示了两种查询侧扩展策略。

### MQE：生成多个查询

MQE（Multi-Query Expansion）用 LLM 把一个问题改写成多个查询，再合并候选：

```text
原始 query
  → 生成 query 1 / query 2 / query 3
  → 分别检索
  → 按文档 ID 去重
  → 保留每个文档的最高分
  → 排序取 top_k
```

它解决的是“原始 query 表述单一”，但会增加 LLM 调用与候选扫描成本。

### HyDE：用假设答案做检索

HyDE 先生成一段假设性答案，再用这段文字的 embedding 去检索：

```text
query → hypothetical answer → embed(answer) → retrieve
```

假设答案不是最终回答，只是把 query 映射到更接近文档分布的表示空间。生成错误可能把检索带偏。

### Hello Agents 示例配置

研究报告核对的示例配置是：

```text
top_k = 8
only_rag_data = True
enable_mqe = False
mqe_expansions = 2
enable_hyde = False
candidate_pool_multiplier = 4
```

候选池为：

```text
max(top_k × candidate_pool_multiplier, 20)
```

候选按 ID 去重并保留最大分数。**这是候选扩展与去重，不是 LLM reranking，也不自动证明效果提升。**

### 本仓库状态

InsightMem 当前没有 MQE/HyDE。要用它做实验，需要：

1. 固定原始 query 与 gold evidence；
2. 固定 expansion 模型、prompt、seed；
3. 分别跑 baseline 与 expansion；
4. 报告 Recall@k、MRR、候选数、token 与 p95；
5. 保存生成的 query 与候选归因。

## 重排：什么时候需要 cross-encoder

Cross-encoder 同时读取 query 和 document，通常比双编码器更精细，但成本更高。它适合在较小候选集上重排：

```python
candidates = hybrid_search(query, top_n=100)
reranked = cross_encoder.predict([(query, doc.text) for doc in candidates])
final = top_k(reranked, k=10)
```

本仓库尚未实现 cross-encoder。当前 `selection.py` 使用确定性规则处理相关性、query coverage、重复和 span，而不是模型重排。

## 图检索：什么时候值得引入

如果问题需要多跳：

```text
Alice → 负责项目 X → 项目 X 使用服务 Y → Y 的负责人是谁？
```

单次向量相似度通常不够，需要 entity/edge 遍历。最小流程：

```text
query → 识别实体 → 获取邻居 → 扩展路径 → 聚合证据 → 排序
```

本仓库没有图腿。引入前先验证：

- 实体和边抽取是否可靠；
- 边是否保留来源；
- 错误边会不会被放大；
- 图维护成本是否超过收益。

## 时间检索：为什么不能只按 timestamp 排序

用户问“我上周住在哪里”，系统需要区分：

- **事件时间**：事实什么时候为真；
- **写入时间**：系统什么时候知道；
- **查询时间**：这次查询发生在什么时候。

一个最小 as-of 条件：

```sql
valid_from <= :event_time
  AND (valid_to IS NULL OR :event_time < valid_to)
```

InsightMem 保存 message timestamp，但没有事实失效、双时间查询或时间过滤 API。时间治理属于扩展设计，不能把 message timestamp 当成完整双时间。

## Agentic retrieval：让 Agent 自己决定怎么搜

Hello Agents 第 8 章之外，阶段二还会进一步强调 Agent 自主管理上下文。Agentic retrieval 的典型循环是：

```text
初始 query
  → 搜索
  → 检查证据是否足够
  → 改写 query 或扩大范围
  → 再搜索
  → 停止并回答
```

优点是能处理模糊问题和多轮探索；风险是过度检索、延迟不稳定和成本失控。必须记录：

- 为什么触发搜索；
- 每次 query 是什么；
- 返回哪些 ID；
- 为什么继续或停止；
- 最终注入了哪些证据。

本仓库当前由应用显式调用 Search，没有实现 Agentic retrieval。

## 本章小结与下一步

你已经知道：

- 高级检索的目标是互补和归因，不是堆算法；
- InsightMem 已有 raw BM25、code BM25、exact dense 和确定性选择；
- 当前没有逐腿开关、cross-encoder、图腿、双时间或 Agentic retrieval；
- 消融实验必须固定 snapshot、embedding、候选深度和 selector。

下一章 [06 项目：智能文档问答助手](06-document-qa-assistant.md) 会把记忆、检索和固定 reader 组装成一个可评测的最小系统。
