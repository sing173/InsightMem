# 04 召回（第 4 周）

> 上一章：[03 存储与索引](03-storage.md) · 下一章：[05 融合与选择](05-fusion.md)
> 预计：6–8 小时
> 本章目标：能解释每条召回腿的假设、盲区和停止条件；能区分检索与重排；能把“没召回、排太后、被截断”分开诊断。

---

## 1. 本周要解决的问题

召回的目标不是返回最终答案，而是让正确证据进入候选集。一个候选一旦没有进入后续阶段，再好的融合和生成也救不回来。

因此本章关注：

- 哪些腿能互补；
- 每条腿需要多深；
- 查询分类是否可靠；
- 图检索何时停止；
- 重排为什么不能替代召回；
- 如何定位失败发生在哪一步。

---

## 2. 召回流水线

```text
query
  │
  ├─ query understanding / scope
  ├─ lexical recall
  ├─ dense recall
  ├─ graph / structured recall
  ├─ metadata & time filter
  └─ candidate union → dedup → optional rerank → downstream fusion
```

每一步都要记录：

```text
query → leg → raw candidate count → filtered count → returned ids → latency
```

没有 trace，就无法判断是召回失败还是选择失败。

---

## 3. 四条常见召回腿

| 腿 | 假设 | 擅长 | 盲区 |
|---|---|---|---|
| Raw lexical | 共享词面 | 错误码、函数名、路径、CJK 字符 | 同义改写、跨措辞 |
| Code-expanded lexical | 标识符可拆分 | snake_case、camelCase、路径组件 | 自然语言关系 |
| Dense | 语义相似可由向量近似 | 改写、意图、概念 | 精确串、罕见 ID、数字 |
| Graph / structured | 关系需要沿边遍历 | 多跳、实体、时间 | 抽取错误、hub 扩散 |

多路召回的价值不是“更多”，而是**错误方式不同**。如果两条腿都偏向同一类表面相似文档，增加腿数并不会提升覆盖。

---

## 4. 词法召回

### 4.1 Raw lexical

InsightMem 的 raw leg 对每个 source chunk 的原文计算 BM25。tokenizer 将英文/数字/下划线、CJK 字符和标点作为 token，再做 case-fold； punctuation 最终不参与 BM25。

适合：

```text
KeyError: 'user_id'
parse_user_id
src/insightmem/coding/service.py
```

不适合：

```text
“为什么反斜杠会消失”
```

### 4.2 代码展开

代码展开不是简单 lowercase。InsightMem 的 `code_tokens` 会：

- 统一路径分隔符；
- 保留完整标识符；
- 按 `/ . : _ -` 拆分；
- 将 camelCase / PascalCase 拆成词；
- 保留数字片段。

例如：

```text
parseHTTPResponse_v2
→ parsehttpresponse_v2
→ parsehttpresponse
→ v2
→ parse
→ http
→ response
→ 2
```

这让 `HTTP response parser` 有机会匹配 `parseHTTPResponse`，但也会增加噪声和重复 token。

### 4.3 词法失败诊断

| 现象 | 原因 | 改进 |
|---|---|---|
| 查询词完全不匹配 | 改写、缩写、语言差异 | dense / query expansion |
| 长模板霸榜 | 重复词、长度归一化不足 | 调 b、去重模板 |
| 精确 ID 排名靠后 | 语料噪声、候选截断 | 提升 raw 权重、扩大 depth |
| CJK 查询漏召回 | tokenizer 粒度过细 | 增加词级或子词索引 |

---

## 5. Dense 召回

### 5.1  bi-encoder

Query 和 document 分别编码，再算 cosine：

```text
q = E_query(query)
d = E_document(document)
score = cos(q,d)
```

优点是 document embedding 可预计算；缺点是 query 与 document 的交互有限，对精确 token 和否定不敏感。

### 5.2 精确与 ANN

- 精确 kNN：扫描全部向量，结果可复现；
- ANN：用 HNSW 等图索引减少扫描，换取近似误差；
- ANN recall 必须用 exact top-k 作为参照。

不要把 ANN recall 当成问答准确率。语义最近不等于证据正确。

### 5.3 Dense 失败诊断

| 现象 | 原因 | 改进 |
|---|---|---|
| 语义相近但事实错误 | embedding 不编码事实细节 | lexical / rerank |
| 罕见 ID 漏召回 | 训练分布中缺少该 token | code lexical |
| 否定或数字错配 | 向量压缩细节 | structured filter / exact match |
| 旧向量仍被召回 | 索引版本陈旧 | 失效与重建 |
| 查询向量维度变化 | 模型或 provider 改变 | identity 校验 |

---

## 6. Late interaction 与 cross-encoder

### 6.1 ColBERT：token 级 late interaction

ColBERT 为 query 和 document 产生 token embedding，再做 MaxSim：

```text
Score(q,D) = Σᵢ maxⱼ (qᵢ · dⱼ)
```

它比单一 document vector 保留更多细粒度匹配信息，代价是索引体积和计算量增加。

### 6.2 Cross-encoder：候选重排

Cross-encoder 把 query 和 document 拼在一起输入模型，联合判断相关性：

```text
top-N recall
  → dedup
  → cross-encoder score each (query, doc)
  → top-K
```

优点：判断更精细。缺点：

- 无法提前为 document 独立编码；
- 只能处理候选集；
- 延迟和 token 成本高；
- 不能修复正确文档未进入 top-N 的问题。

### 6.3 检索与重排的边界

```text
Recall 决定“能不能找到”
Rerank 决定“找到的里面谁更相关”
Selection 决定“最终注入哪些”
```

实验应比较 dense、BM25、RRF、+ColBERT、+cross-encoder 的 MRR、P95 延迟和 token。不能只报重排后的最终答案准确率。

---

## 7. 图与结构化召回

### 7.1 图遍历

典型流程：

```text
识别 query entities
  → 找 seed nodes
  → 沿关系扩展
  → 时间/scope 过滤
  → 按路径或相关性排序
  → 停止并返回 evidence
```

停止条件必须显式定义：

- 最大跳数；
- 最大节点数；
- 分数阈值；
- 时间窗口；
- 证据预算。

否则 hub 节点会让图遍历失控。

### 7.2 HippoRAG

HippoRAG 用实体图上的个性化 PageRank 从 query entity 传播相关性，目标是一次图传播找到多跳邻居，替代部分迭代检索。

适用：显式关系、多跳 bridge、需要路径证据。

失败：实体误合并、hub 扩散、错误边传播、图更新成本。

### 7.3 GraphRAG

GraphRAG 的全局查询使用社区摘要 map-reduce，更适合“整个语料的主要主题是什么”，不是普通局部事实检索的最佳替代。

### 7.4 时间召回

时间查询需要先确定范围：

```text
“上周” → 时间窗口过滤
“当前” → active version
“当时” → as-of valid time
```

没有时间索引和有效期字段，只在 query 里出现“上周”无法可靠检索。

---

## 8. 查询分类与自适应路由

### 8.1 规则版

| 信号 | 可能类型 | 路由 |
|---|---|---|
| 错误码、引号内 ID、路径 | 精确匹配 | raw + code lexical |
| 自然语言意图、无稀有词 | 语义改写 | dense + raw |
| 实体关系词 | 多跳 | graph + lexical |
| “当前、之前、上周” | 时间 | metadata + lexical |

### 8.2 学习版

用标注 query 训练分类器，输出类型概率，再决定腿和权重。必须有 dev/test 划分，并报告误路由率。

风险：分类器一旦把精确 ID 路由到 dense，会直接漏召回。工程上常采用：

```text
高置信度分类 → 自适应路由
低置信度 → hybrid fallback
```

InsightMem 当前没有查询分类器，三路全开；因此“按查询类型调权”是待实现设计，不是现有行为。

---

## 9. 多查询与 query expansion

常见方法：

- 同义词扩展；
- 代码标识符拆分；
- HyDE：先生成假设答案，再用它检索；
- multi-query：生成多个子查询。

收益：提高改写覆盖。风险：

- 扩展引入新主题；
- 假设答案放大模型偏见；
- 多次调用增加成本；
- 原始查询与扩展查询的权重难解释。

至少保留原始 query 腿，并对 expansion 做独立消融。

---

## 10. InsightMem 的三条腿

[service.search](../../src/insightmem/coding/service.py#L163) 的实际流程：

1. 读取一个 committed snapshot；
2. raw BM25 over source chunks；
3. view BM25 over code-expanded views；
4. dense cosine over view embeddings；
5. RRF 融合；
6. candidate order；
7. 过滤低信息 assistant/thinking chunk；
8. prepare sources 与 select。

关键限制：

- 没有图腿；
- 没有查询分类器；
- 没有时间/metadata filter；
- 没有 cross-encoder；
- 过滤发生在融合后；
- view 通过 span overlap 映射回 chunk；
- 当前 dense 是精确 kNN。

因此它能验证词法、代码展开与 dense 的互补，但不能直接验证图召回、ANN 或自适应路由。

---

## 11. 召回指标

| 指标 | 定义 | 用途 |
|---|---|---|
| Recall@k | 命中的 gold 证据数 / 应召回证据数 | 证据覆盖 |
| MRR | 第一条相关结果的倒数名次 | 排名质量 |
| nDCG@k | 按相关性等级加权的折扣增益 | 多级相关 |
| all-recall | 所有 gold 证据是否都进入候选 | 多证据题 |
| abstention precision | 无答案时是否正确不返回证据 | 防止硬召回 |

如果一条查询需要 3 段证据，top-5 命中 1 段的 Recall@5 只有 `1/3`；只报 hit@5 会高估覆盖。

### 配对比较

对同一组 query 计算：

```text
Δ = score_A - score_B
```

用 paired bootstrap 给出 95% CI，并报告单跳、多跳、时间、更新、弃答切片。30 题的偶然波动不应直接称为提升。

---

## 12. 动手：L3 三路召回消融

完整步骤见 [实验手册 L3](labs.md#l3)。

### 实验矩阵

| 配置 | raw | view | dense |
|---|---:|---:|---:|
| all | ✓ | ✓ | ✓ |
| no raw | — | ✓ | ✓ |
| no view | ✓ | — | ✓ |
| no dense | ✓ | ✓ | — |
| raw only | ✓ | — | — |
| view only | — | ✓ | — |
| dense only | — | — | ✓ |

固定 query、chunk、top_k、embedding identity 和 snapshot。

### 记录

- 每腿 raw candidate count；
- 融合前 union size；
- Recall@5 / @10；
- MRR、nDCG、all-recall；
- P50/P95 延迟；
- 失败阶段：未召回 / 排太后 / 被截断。

再做 chunk 大小消融（160/320/640 token），但不要同时改变 overlap 和检索器。

---

## 13. 验收

- 能说出每条腿在什么查询上赢、什么查询上输；
- 能解释代码展开不是简单 lowercase；
- 能区分 bi-encoder、ColBERT 和 cross-encoder；
- 能解释为什么 rerank 不能修复召回遗漏；
- 能设计图遍历的停止条件；
- 能把失败分成未召回、排太后和被截断。

---

## 14. 机制依据与延伸阅读

### 一手依据

- [BM25 and Beyond](https://doi.org/10.1561/1500000019)：词法检索的参数与模型。
- [ColBERT](https://arxiv.org/html/2004.12832v2)：late interaction 与 token-level retrieval。
- [Passage Re-ranking with BERT](https://arxiv.org/abs/1901.04085)：cross-encoder 重排。
- [Sentence Transformers: Retrieve & Re-Rank](https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html)：官方实践。
- [HippoRAG](https://arxiv.org/html/2405.14831v3)：实体图与 PPR。[中文精读](../../docs/papers-zh/04-retrieval-eval.md#hipporag)
- [HippoRAG 2](https://arxiv.org/html/2502.14802v1)：后续记忆检索框架，注意与第一代区分。
- [GraphRAG](https://arxiv.org/html/2404.16130v2)：社区摘要与全局查询。[中文精读](../../docs/papers-zh/04-retrieval-eval.md#graphrag)
- [GraphRAG Query Overview](https://microsoft.github.io/graphrag/query/overview/)：官方查询模式。
- [Qdrant Late Interaction](https://qdrant.tech/documentation/tutorials-search-engineering/using-multivector-representations/)：多向量检索工程说明。

---

## 本章产出

1. 一张“查询类型 × 召回腿”矩阵；
2. L3 消融表与失败 trace；
3. 一个 cross-encoder 候选重排对照；
4. 至少 3 条未召回查询的根因分析。

下一章：[05 融合与选择](05-fusion.md)。
