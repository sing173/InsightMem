# 03 存储与索引（第 3 周）

> 上一章：[02 写入](02-writing.md) · 下一章：[04 召回](04-retrieval.md)
> 阶段：阶段一选 Store/namespace 与索引，阶段二设计外部上下文与 MemFS。
> 预计：6–8 小时
> 本章目标：能先选记忆单元，再选存储与索引；能解释 BM25、精确 kNN、ANN 和图的适用边界；能把更新、隔离、重建与成本纳入设计。

---

## 1. 本周要解决的问题

“用什么数据库”不是第一个问题。先问：

1. 一条记忆的原子单元是什么？
2. 哪些查询必须在毫秒级完成？
3. 哪些索引是源数据，哪些是可重建的派生表示？
4. 新事实到来后，哪些索引必须同步更新？
5. 用户、项目、时间如何影响候选范围？

本章按“单元 → 源存储 → 索引 → 生命周期 → 成本”展开。

---

## 2. 先选记忆单元

| 单元 | 存什么 | 适合 | 主要风险 |
|---|---|---|---|
| Message | 一条原始消息 | 证据、审计、对话回溯 | 长消息难检索 |
| Chunk | 字符/token 跨度 | 长文检索、证据定位 | 切分破坏语义 |
| Episode | 一次输入及其来源 | 图与事实溯源 | 与 message 边界重叠 |
| Fact | subject-predicate-object + 时间 | 结构化查询、时间与多跳 | 抽取错误固化 |
| Note | 经验、规则、偏好 | 人工可读、跨会话复用 | 摘要漂移 |
| View | 为检索构造的表示 | 代码展开、摘要索引 | 与源不同步 |

原则：**源记录与检索表示分离。** 同一事实可以存在于原文、fact、view 和 embedding 中，但必须能互相追溯。

### LangGraph Store、外部上下文与 MemFS

| 形态 | 适合存什么 | 典型接口 | 阶段一用途 | 阶段二用途 |
|---|---|---|---|---|
| LangGraph Store | JSON 文档、用户偏好、few-shot 示例 | `namespace + key + value`，支持语义搜索与过滤 | 跨 thread 长期记忆 | memory manager 的外部记忆后端 |
| Checkpointer | 当前 thread 的图状态 | `thread_id + checkpoint` | 暂停/恢复邮件 Agent | 恢复执行，不替代 archival memory |
| 向量库 / 文档库 | 可语义检索的原始片段 | search / filter | semantic/episodic retrieval | archival memory |
| Core memory block | 当前必须可见的少量事实与指令 | read / edit | 可作为显式 prompt 的一部分 | Agent 自编辑工作区 |
| MemFS | Git-backed Markdown 记忆与技能 | 文件读写、版本、diff | 可审计的程序记忆 | 文件式 core/archival memory |

关键区别：**Store 解决“跨会话保存与检索”，memory manager 解决“当前上下文放什么”。** 二者可以共用同一数据库，也可以分别实现。

---

## 本章实战：给三类记忆设计 namespace

> 可运行实验：02/03 邮件 Agent Notebook；稳定实现：[LocalStore](../../experiments/email-agent/src/email_memory_lab/store.py#L20) 与 [SemanticMemory / EpisodicMemory / ProceduralMemory](../../experiments/email-agent/src/email_memory_lab/memory.py#L6)。
> 当前 Notebook 覆盖 namespace 与 `put/get/search` 形态，不覆盖 BM25、dense、ANN 或 Recall/Archival Adapter。

课程项目把所有长期记忆放在同一个 Store，但用 namespace 分开：

```python
NAMESPACES = {
    "semantic": ("memories", user_id, "collection"),
    "episodic": ("examples", user_id),
    "procedural": ("instructions", user_id),
}
```

### Profile 还是 Collection

| 形态 | 适合 | 更新方式 | 风险 |
|---|---|---|---|
| Profile | 用户画像、稳定偏好 | patch 单个 JSON 文档 | 文档变大后容易丢字段 |
| Collection | 多条事实、事件、示例 | insert / update / delete | 重复、冲突与检索噪声 |
| Procedural document | 写作与路由指令 | 版本化替换 | 错误反馈固化 |

一个实际系统可以同时使用三种形态。不要把“所有记忆都放进一个 vector store”当成唯一设计。

### 从 Store 到外部记忆 Adapter

阶段二的 Recall/Archival 不需要重新发明存储接口。可以定义两个 Adapter：

```python
class RecallStorage(Protocol):
    def append(self, message: dict) -> None: ...
    def search(self, query: str, limit: int) -> list[dict]: ...


class ArchivalStorage(Protocol):
    def insert(self, text: str, metadata: dict) -> str: ...
    def search(self, query: str, limit: int) -> list[dict]: ...
```

它们可以分别由消息表、向量库或文件搜索实现。MemoryManager 只依赖接口，不依赖具体数据库。

### 检查点

- namespace 与 thread_id 的区别是什么？
- 为什么 semantic、episodic、procedural 应该分开？
- profile 更新为什么需要 schema 校验？
- Recall Storage 与 Archival Storage 的内容粒度有何不同？
- 如果 Store 换成 Postgres，哪些代码应该不变？

### 练习

为邮件 Agent 设计三层存储：原始邮件事件、语义事实、程序指令。画出 source of truth 与派生索引，并为每一层写一个重建测试。

---

## 3. 源存储与派生索引

```text
Source of truth
  ├─ raw message / episode
  ├─ fact versions
  └─ provenance
          │
          ├─ lexical postings
          ├─ dense vectors
          ├─ graph edges
          └─ caches / summaries
```

派生索引应满足：

- 可删除后重建；
- 带索引版本；
- 与源记录版本一致；
- 更新失败可检测；
- 不承载唯一一份用户数据。

如果删除向量后事实也消失，说明向量库承担了源存储职责，需要重新审视边界。

---

## 4. 五种常见载体

| 载体 | 擅长 | 不擅长 | 典型查询 |
|---|---|---|---|
| 文件 + git | 可读、版本化、agent 可直接编辑 | 大规模并发检索、复杂过滤 | 最近修改、按路径读取 |
| 关系库 + 倒排 | 精确词、标识符、结构化过滤 | 语义改写 | 错误码、函数名、时间范围 |
| 向量库 | 语义相似、跨措辞 | 精确串、罕见 ID、关系推理 | “修复依赖冲突的尝试” |
| 图数据库 | 实体关系、多跳、时间 | 抽取成本、hub 扩散 | “A 经哪个模块影响 B” |
| 混合 | 多路互补 | 融合、一致性和运维复杂 | 词法 + dense + metadata |

不要把“向量库”当成长期记忆的同义词。向量只是索引；记忆还需要来源、更新、删除和隔离。

---

## 5. 倒排索引与 BM25

### 5.1 倒排索引

```text
term → [(doc_id, tf), (doc_id, tf), ...]
```

构建流程：

```text
tokenize documents
  → count df / tf / length
  → build postings
  → merge segments
  → score postings for query terms
```

更新可以是 in-place、追加 segment 后 merge，或全量重建。选择取决于写入频率、可接受延迟和存储成本。

### 5.2 BM25 公式

对文档 `d` 和查询 `q`：

```text
idf(t) = ln(1 + (N - df(t) + 0.5) / (df(t) + 0.5))

score(d,q) = Σ idf(t) ×
             tf(t,d) × (k1 + 1)
             ─────────────────────────────
             tf(t,d) + k1 × (1 - b + b × |d| / avgdl)
```

- `tf` 经过 `k1` 饱和，避免重复词无限加分；
- `b` 控制文档长度归一化；
- IDF 来自整个语料快照，不是当前候选集；
- 罕见精确标识符通常得到更高权重。

### 5.3 失败与实验

模板重复会让长文霸榜；罕见词则可能成为关键信号。固定语料后扫描：

```text
k1 ∈ {0.8, 1.2, 1.5}
b  ∈ {0.0, 0.4, 0.75}
```

报告 Recall@5、MRR、索引体积和 P95 延迟。不要只看单一数据集的最优参数。

### 5.4 InsightMem 的实际情况

InsightMem **没有使用 SQLite FTS5 虚拟表**。它在读取快照后，用 Python 对 raw chunk 和 code-expanded view 计算全量 BM25，并用有界 lexical cache 复用统计。

因此更准确的描述是：

- 全量 BM25 教学实现；
- 非持久化倒排索引；
- 每个快照重新计算 corpus statistics；
- 适合小到中等规模，不应当作大规模 FTS 性能结论。

源码见 [store.py:32](../../src/insightmem/store.py#L32) 与 [lexical.py:52](../../src/insightmem/coding/lexical.py#L52)。

---

## 6. Dense 检索：精确 kNN 与 ANN

### 6.1 向量与余弦

对 query 和 document：

```text
cos(q,d) = q · d / (||q|| × ||d||)
```

若两边都已归一化，点积就是余弦。InsightMem 在写入和查询时都归一化向量，并检查维度、有限值和范数。

### 6.2 精确 kNN

```python
scores = query_vector @ document_matrix.T
top_k = argpartition(scores, -k)[-k:]
```

优点：结果稳定、无近似误差。缺点：每次查询要扫描全部向量，内存与延迟随语料线性增长。

### 6.3 ANN / HNSW

HNSW 构建分层近邻图：

```text
insert(point):
  choose entry point
  greedily search upper layers
  connect to neighbors within M
  add point to selected layers

search(query, ef):
  start at entry point
  maintain candidate/heap
  explore graph neighbors until stopping condition
```

关键参数：

| 参数 | 影响 |
|---|---|
| `M` | 每层邻居数，影响图大小与搜索路径 |
| `efConstruction` | 构建时搜索宽度，影响索引质量与构建成本 |
| `efSearch` / `hnsw_ef` | 查询时搜索宽度，影响召回与延迟 |

ANN 的检索召回定义为：

```text
ANN recall = |ANN top-k ∩ exact top-k| / k
```

它与问答准确率不是一回事：ANN 找回了“向量意义上最近”的文档，不代表文档能回答问题。

实验应同时报告 recall、P95 延迟、索引内存和构建时间。不要只报 QPS。

### 6.4 InsightMem 的实际情况

InsightMem 的 dense 查询会：

1. 从 SQLite 读取该用户的全部 view vectors；
2. `np.stack` 成矩阵；
3. 与 query vector 做精确点积；
4. 按分数排序后进入融合。

因此它是**精确 dense kNN**，不是 HNSW/ANN。随着用户历史增长，这是需要基准测试的成本点。

---

## 7. Metadata、时间与租户过滤

检索范围通常由 metadata 决定：

```text
tenant_id = ?
user_id = ?
project_id IN (...)
visibility IN (...)
valid_from <= query_time < valid_to
status = active
```

过滤时机很重要：

- **检索前过滤**：减少候选，但要求索引支持；
- **检索后过滤**：实现简单，但可能把 top-k 全部过滤掉；
- **融合后过滤**：浪费融合名次，也可能改变候选分布。

InsightMem 当前查询条件主要是 `user_id`，并在融合后过滤低信息 assistant/thinking chunk。它没有时间、项目或 metadata filter API。

### 隔离测试

用唯一哨兵验证每个索引：

```text
用户 A 写入 A-only-token
用户 B 用 A-only-token 查询
断言 lexical / dense / graph / cache 都零结果
```

只在 SQL 层过滤，不清空共享缓存或图缓存，仍可能泄漏。

---

## 8. 图存储：什么时候值得

图适合显式实体、关系、路径和时间冲突，而不是“所有记忆都放进图”。

一条时序边可表示为：

```text
(source, predicate, object,
 valid_from, valid_to,
 recorded_from, recorded_to,
 source_episode_id)
```

### GraphRAG 与 HippoRAG 的边界

- [GraphRAG](../../docs/papers-zh/04-retrieval-eval.md#graphrag) 先构建实体图和社区摘要，查询时 map-reduce 社区摘要，擅长全局 sensemaking；
- [HippoRAG](../../docs/papers-zh/04-retrieval-eval.md#hipporag) 从 query entity 出发，在实体图上做个性化 PageRank，擅长多跳证据召回。

失败模式：

- 实体误合并导致错误路径；
- hub 实体扩散出大量无关节点；
- 图边抽取错误被多跳放大；
- 社区摘要丢失局部事实；
- 更新需要同步节点、边和摘要。

实验用 2–4 跳 bridge 题，比较 dense、BM25、PPR 的证据召回、路径准确率与构建成本。不能把论文在特定数据集上的收益外推为“图总是更好”。

---

## 9. 索引生命周期

```text
build → active → update → stale → rebuild → retire
```

每次 Add 至少考虑：

| 数据变化 | 需要更新 |
|---|---|
| 新 message/chunk | postings、vector、view |
| 新 fact version | 旧索引失效、新版本激活 |
| 删除/tombstone | postings、vector、graph、cache |
| embedding 模型变化 | 全部向量与 identity 元数据 |
| profile 变化 | 相关索引与指纹 |
| backup restore | 重放删除日志并校验版本 |

InsightMem 在启动时检查 `coding_meta` 的 schema、build fingerprint 和 embedding identity；不匹配就拒绝启动，要求重建。这是“派生索引不可跨表示版本混用”的具体例子。

---

## 10. 成本模型

不要只测查询延迟：

```text
total cost = build
            + index maintenance
            + storage
            + retrieval
            + rerank
            + answer generation
            + failure/retry
```

至少记录：

| 指标 | 说明 |
|---|---|
| Build time | 首次索引耗时 |
| Update p95 | 新数据多久可检索 |
| Query p50/p95 | 在线延迟 |
| Memory / disk | 向量、postings、图、缓存 |
| Tokens | embedding、rerank、answer |
| Rebuild time | 模型或 schema 升级成本 |

全量 BM25 和精确 kNN 的简单性有工程价值；在证明规模成为瓶颈前，不必提前引入 ANN。

---

## 11. 动手：L2 双索引对照

完整步骤见 [实验手册 L2](labs.md#l2)。

### 修正查询集

- 精确标识符：函数名、错误码、路径；
- 语义改写：同一意图的不同措辞；
- 单跳事实：一个 chunk 可回答；
- 多跳关系：需要图或跨多个 chunk；
- 时间/版本：旧值与新值；
- 弃答：没有答案时不应硬召回。

“多跳题”不能只用 BM25 和向量就声称验证了图检索。至少增加一个图腿，或明确把该切片标为“无图基线”。

### 固定条件

- 同一语料与 chunk；
- 固定 tokenizer、embedding、top_k；
- 固定 seed；
- 记录索引构建时间和内存；
- 保存每条查询的 gold span 与失败原因。

### 产出

| 查询类型 | BM25 Recall@5 | Dense Recall@5 | Hybrid Recall@5 | 主要失败 |
|---|---:|---:|---:|---|
| 精确标识符 | | | | |
| 语义改写 | | | | |
| 单跳事实 | | | | |
| 多跳关系 | | | | |
| 时间/版本 | | | | |
| 弃答 | | | | |

---

## 12. 设计练习

| 场景 | 单元 | 源存储 | 索引 | 更新语义 | 隔离边界 | 主要风险 |
|---|---|---|---|---|---|---|
| 个人助手，跨会话记偏好 | | | | | | |
| 编码 agent，查历史改动和错误 | | | | | | |
| 企业多租户，需要权限和审计 | | | | | | |

要求每个选择都能回答：

1. 哪份数据是 source of truth？
2. 索引删掉后能否重建？
3. 新事实到来后哪些索引失效？
4. 换用户、换项目、换时间范围会怎样？
5. 构建、更新和查询各花多少成本？

---

## 13. 验收

- 能解释 message、chunk、episode、fact、view 的区别；
- 能写出 BM25 的 TF 饱和与长度归一化直觉；
- 能区分精确 kNN、ANN recall 与问答准确率；
- 能说明图检索适合什么任务，以及 hub/误抽取风险；
- 能指出 InsightMem 当前没有 FTS5，也没有 ANN；
- 能给出一个可重建、可隔离、可删除的索引生命周期。

---

## 14. 机制依据与延伸阅读

### 一手依据

- [Robertson & Zaragoza, BM25 and Beyond](https://doi.org/10.1561/1500000019)：BM25 的参数与概率检索框架。
- [Malkov & Yashunin, HNSW](https://arxiv.org/abs/1603.09320)：分层近邻图的构建与搜索。
- [Qdrant: Measuring ANN Recall](https://qdrant.tech/documentation/tutorials-search-engineering/ann-recall/)：ANN 召回的工程测量。
- [Zep, arXiv:2501.13956](https://arxiv.org/html/2501.13956v1)：episode、fact、edge 与时序图。[中文精读](../../docs/papers-zh/03-systems.md#zep)
- [GraphRAG, arXiv:2404.16130](https://arxiv.org/html/2404.16130v2)：社区摘要与全局问答。[中文精读](../../docs/papers-zh/04-retrieval-eval.md#graphrag)
- [HippoRAG, arXiv:2405.14831](https://arxiv.org/html/2405.14831v3)：实体图与个性化 PageRank。[中文精读](../../docs/papers-zh/04-retrieval-eval.md#hipporag)
- [HippoRAG repository](https://github.com/OSU-NLP-Group/HippoRAG)：注意当前 main 与第一代 legacy 的版本差异。

### 官方工程文档

- [Azure Hybrid Search Scoring](https://learn.microsoft.com/en-us/azure/search/hybrid-search-ranking)：RRF 与加权融合。
- [Qdrant Hybrid Queries](https://qdrant.tech/documentation/search/hybrid-queries/)：多路检索与融合。
- [Letta Memory](https://docs.letta.com/letta-code/memory)：MemFS 文件式存储。
- 本项目实现：[architecture.md](../../docs/architecture.md) 与 [service.py:24](../../src/insightmem/coding/service.py#L24)。

---

## 本章产出

1. 一张“单元—存储—索引—更新—隔离”选型表；
2. BM25 参数扫描结果；
3. 精确 kNN 与 ANN 的 recall/延迟/内存对照；
4. 一个索引删除后从源记录重建的验证。

下一章：[04 召回](04-retrieval.md)。
