# 08 架构对比与 Capstone（第 8 周）

> 上一章：[07 评测](07-evaluation.md) · 返回：[路线入口](README.md)
> 阶段：阶段二 memory OS + 两阶段综合验收。
> 预计：10–14 小时
> 本章目标：把前 7 周的能力收束成一个可运行、可评测的系统；能按任务约束解释 LangGraph 与 MemGPT/Letta 为什么这样设计，而不是按品牌或榜单选型。

详细机制见 [现代系统精读](../../docs/papers-zh/03-systems.md)、[MemGPT 精读](../../docs/papers-zh/01-foundations.md#memgpt) 与 [项目架构](../../docs/architecture.md)。

---

## 1. 先统一比较维度

“谁的记忆更强”不是可回答的问题。应先固定：

```text
任务类型 · 时间跨度 · 更新频率 · 隔离范围
答案形式 · 证据要求 · 延迟预算 · 运维约束
```

然后比较五个动作：

| 维度 | 要问的问题 |
|---|---|
| 写入 | 保存原文、抽取事实，还是两者都做？同步还是异步？ |
| 组织 | 线性日志、上下文页、事实集合、时序图、笔记网络，还是 MemCube？ |
| 检索 | 词法、dense、图、时间过滤如何组合？候选深度多少？ |
| 使用 | 谁把记忆变成上下文？如何限制预算、去重和处理冲突？ |
| 治理 | 追加、覆盖、失效、遗忘、删除、隔离和审计分别由谁负责？ |

一张只在“向量数据库 / 图数据库”层面打勾的表，无法解释真实差异。例如同样是“保存原文”，有的系统只用于审计，有的系统同时作为检索 source of truth；同样是“长期记忆”，有的只存偏好，有的保存可执行经验。

---

## 2. 六种架构形态

### 2.1 MemGPT / Letta：上下文管理与外部存储

[MemGPT 本地精读](../../docs/papers-zh/01-foundations.md#memgpt) 把有限上下文看成需要主动管理的工作区：

```text
Main Context
  ↔ memory tools
External Context
  - recall memory
  - archival memory
```

关键机制：

- 通过函数调用在上下文与外部存储之间换入、换出；
- 用 FIFO、递归摘要等方式缓解 memory pressure；
- 将 eviction 与 deletion 分开：离开上下文不等于从存储删除；
- [Letta 官方文档](https://docs.letta.com/letta-code/memory) 将这套思想产品化为 agent runtime，并引入持久 memory blocks、文件式记忆等工程形态。

**Leverage**：调用方获得“像管理内存一样管理上下文”的统一抽象，不必自己处理每次溢出。
**代价**：上下文管理策略会改变 agent 可见信息，需要可观测的换入/换出日志；系统提示与工具设计对效果影响很大。

适合：需要 agent 自主查阅档案、维护工作区，且能接受上下文策略参与决策的项目。
不适合：只需要确定性 Add/Search 证据接口的竞赛或批处理场景。

### 2.2 Mem0：显著事实抽取与多信号检索

[Mem0 本地精读](../../docs/papers-zh/03-systems.md#mem0) 将对话压缩为值得长期保留的记忆，再通过语义、关键词与实体信号检索；图变体把实体关系组织成图。

必须分版：

- **论文版**：抽取后存在整合、更新、删除逻辑；
- **2026 README 的新算法**：单次 ADD-only 抽取，不覆盖旧记忆；
- 云版与开源版不能默认视为同一实现。

**Leverage**：调用方用较小的事实集合获得长期个性化，而不必暴露全部原文。
**代价**：抽取和整合成为主要误差源；错误事实、过时事实或错误合并会被后续检索反复使用。没有原文与 source span 时，审计和纠错更困难。

适合：用户偏好、助手个性化、需要低读取成本的生产 API。
不适合：要求逐字证据、强溯源、同步确定性写入的编码评测。

### 2.3 Zep / Graphiti：双时间知识图谱

[Zep / Graphiti 本地精读](../../docs/papers-zh/03-systems.md#zep) 以 Graphiti 为核心组织 episode、entity、fact 与 edge：

```text
episode
  → entity / fact / edge
  → valid interval + recorded interval
  → semantic + keyword + graph retrieval
```

关键机制：

- episode 保存原始输入，事实与边保留来源关系；
- 新事实使旧事实失效，历史仍可查询；
- valid time 与 recorded time 区分“世界何时为真”和“系统何时知道”；
- 图遍历补充多跳关系，时间过滤支持 as-of 查询。

**Leverage**：把冲突、时序与关系推理集中到时序图模块，而不是散落在每个 caller。
**代价**：LLM 抽取、图构建与图维护增加成本和故障面；图结构错误会沿边传播，时间语义也要求 schema 与查询严格一致。

适合：企业知识、动态用户画像、时间推理、关系型多跳。
不适合：只需要关键词/dense 两路召回、希望单 SQLite 文件部署的最小服务。

### 2.4 MemOS：记忆资源与调度

[MemOS 本地精读](../../docs/papers-zh/03-systems.md#memos) 的基本单元是 MemCube，统一封装内容与来源、版本等元数据，并连接明文、激活、参数三类记忆。

```text
MemCube
  - plaintext memory
  - activation memory
  - parametric memory
  - metadata / provenance / version

MemScheduler
  - lifecycle
  - migration
  - combination / fusion
```

**Leverage**：在更高抽象层讨论记忆的表示、调度、迁移与演化，而不把记忆限定为 RAG 文本。
**代价**：概念覆盖范围大，落地依赖多种基础设施；参数级记忆还涉及训练成本、遗忘与可审计性问题。

适合：持续学习、跨表示迁移、记忆系统研究。
不适合：仅需稳定证据召回、要求快速复现的入门 Capstone。

**不要与 [MemoryOS 本地精读](../../docs/papers-zh/03-systems.md#memoryos) 混淆**：MemOS 研究记忆资源与三类表示；MemoryOS 研究对话记忆的分层存储。

### 2.5 MemoryOS：STM / MTM / LPM 分层对话记忆

MemoryOS 将长对话组织为：

```text
STM：近期对话页，按对话链维护
  → FIFO 迁移
MTM：同主题 segment → dialogue page
  → 热度驱动的检索、淘汰与归档
LPM：User/Agent Profile、KB、Traits
  → 人格与稳定知识
```

检索同时取近期上下文、相关主题页和人格信息，再统一构造回答提示。

**Leverage**：把“当前聊什么、过去相关细节、稳定偏好”分开管理，适合长对话连续性。
**代价**：主题分段、对话链和人格更新依赖 LLM 判断；热度由访问次数、页数与时间衰减构成，可能偏好热门内容而忽略罕见关键信息。

适合：长期聊天、陪伴、用户画像与个性化。
不适合：跨仓库编码证据、严格 namespace 与可撤销写入优先的系统。

### 2.6 InsightMem：不可变证据层与确定性选择

InsightMem 保存 source message 及其 chunk span，以 source slice 作为当前主要检索表示；Add/Search 同步完成，没有生成与后台 worker。

```text
immutable source messages
  → source chunks / index views
  → raw BM25 + code-expanded BM25 + exact dense
  → grouped RRF
  → bundle / member evidence
  → deterministic selection
```

关键特征：

- SQLite 单库，所有用户数据表按 `user_id` 隔离；`coding_meta` 只保存全局 schema/fingerprint；
- request 幂等与 payload 冲突检查；
- Add 的单事务保证 Search 不观察半提交；
- raw BM25 与 dense 都是精确扫描，不是倒排 postings 或 ANN；
- 融合采用分组名次，同组 chunk 共享名次，不是逐文档标准 RRF；
- bundle 与成员共存，按 span 抑制冗余；
- 相关性优先，query-term novelty 只作 tie-break；
- 当前没有双时间、冲突仲裁、TTL、删除 API、图腿或全局 token 预算。

**Leverage**：调用方得到有序、可逐字追溯、写入后可立即检索的证据，且选择路径不依赖 LLM 采样。
**代价**：它更接近“原文证据层”，不是完整的个人记忆治理系统；精确扫描的维护与查询成本需要随语料规模测量。

适合：编码 agent 查历史证据、相关/噪声对照、可复现检索实验。
不适合：直接替代人格记忆、动态关系图或完整合规删除系统。

---

## 3. 横向对比表

| 维度 | MemGPT / Letta | Mem0 | Zep / Graphiti | MemOS | MemoryOS | InsightMem |
|---|---|---|---|---|---|---|
| 核心记忆单元 | 上下文块 + 档案 | 抽取事实 / 图实体 | episode + fact + edge | MemCube | 对话页 / segment / persona | source message / chunk / view |
| 保留原文 | 外部存储可保留 | 取决于实现，需核对 | episode 保留来源 | cube 元数据可溯源 | 对话页保留 | 不可变原文 |
| 写入 LLM | 摘要/管理可能使用 | 抽取核心 | 抽取入图核心 | 调度与转换相关 | 分段、人格更新相关 | 否；规则切块 |
| 更新语义 | 换入/换出、摘要、编辑 | 论文版整合；新版 ADD-only | 双时间失效 | 组合/迁移/融合 | FIFO + 热度归档 | append-only source |
| 检索 | recall/archival 工具 | 多信号融合 | semantic + keyword + graph | 跨表示调度 | STM + MTM + LPM | BM25 + BM25 view + dense |
| 时间语义 | 取决于存储设计 | 论文支持时间推理 | 显式双时间 | 元数据层 | 对话时间与衰减 | message timestamp，无失效 |
| 隔离 | 部署与产品层 | 产品/存储层 | 产品/图数据层 | 部署相关 | 实现相关 | 每表 `user_id` |
| 同步可检索 | 取决于调用方式 | 取决于 API | 取决于 API | 调度相关 | 迁移相关 | 是，单事务后 |
| 主要故障 | 上下文策略错误 | 抽取/合并污染 | 图与失效误判 | 调度与转换错误 | 热度/主题误判 | 证据噪声、精确扫描成本 |
| 最适任务 | 自主上下文管理 | 个性化事实记忆 | 时序企业知识 | 记忆 OS 研究 | 长对话人格 | 确定性证据检索 |

> 表中“取决于实现/产品层”表示不能仅凭论文名断言。选型时必须 pin 到具体版本、部署形态与接口。

---

## 4. 如何按约束选型

### 任务 A：编码 agent 查历史实现

优先级：

1. 原文保真与 span 溯源；
2. 精确标识符召回；
3. 同步写入后可检索；
4. 低方差选择与统一 answerer 实验；
5. relevant/noisy 对照。

优先组合：不可变证据层 + 词法/dense 融合 + 确定性选择。InsightMem 更接近这一层；若要时间更新或图关系，再单独增加事实层，不要让事实抽取替代原文。

### 任务 B：长期个性化助手

优先级：

1. 用户偏好抽取；
2. 低读取成本；
3. 更新与冲突处理；
4. 隐私删除与审计。

优先组合：Mem0 式事实层或 Zep 式时序事实层，并保留 episode/source。纯 persona 更新不够时，需要显式处理旧值失效与来源。

### 任务 C：关系密集企业知识

优先级：

1. 多跳关系；
2. 动态事实失效；
3. as-of 查询；
4. 来源追踪与权限。

优先组合：Zep / Graphiti 式 episode-fact-edge 模型。先验证抽取准确率与图维护成本，再扩展社区摘要或大规模图遍历。

### 任务 D：持续学习研究

优先级：

1. 跨任务经验复用；
2. 程序性记忆；
3. 生命周期与迁移；
4. 参数级表示评估。

优先组合：MemOS 式调度视角，或独立实现“经验—验证—提升”的闭环。不要把微调默认当成必要组件；先用明文经验验证任务效用。

### 任务 E：长对话与人格

优先级：

1. 近期上下文连续性；
2. 主题分段；
3. 稳定偏好与动态特征分离；
4. 延迟与 token 预算。

优先组合：MemoryOS 式分层结构，或 MemGPT 式主动上下文管理。两者可以组合，但要明确哪一层负责淘汰、哪一层负责摘要、哪一层负责可恢复原文。

---

## 5. 跨框架的五个共同失败模式

| 失败 | 表面现象 | 根因位置 | 必要观测 |
|---|---|---|---|
| 错误固化 | 同一错误事实反复出现 | 写入抽取/整合 | source、method、version、confidence |
| 过时误用 | 当前问题返回旧答案 | 更新/时间语义 | valid/recorded interval |
| 关系污染 | 多跳答案越来越偏 | 图边或笔记链接 | edge provenance、遍历路径 |
| 预算挤占 | 相关证据被重复内容挤掉 | 选择与上下文装配 | selected spans、duplicate key、budget |
| 删除复活 | 重放/恢复后 PII 再出现 | 派生索引与 tombstone | 删除链验证、恢复测试 |

框架差异主要是把这些故障放在不同 Module 里。真正可靠的系统需要让每个故障都有明确归属，而不是让 caller 分别猜测。

---

## 6. 两阶段 Capstone 路线

### 6.1 阶段一：带长期记忆的邮件 Agent

对应 [Long-Term Agentic Memory With LangGraph](https://www.deeplearning.ai/short-courses/long-term-agentic-memory-with-langgraph/)。

最低要求：

1. **Semantic memory**：保存用户事实、偏好与约束，支持按 `user_id + namespace` 检索；
2. **Episodic memory**：保存历史邮件处理示例，并检索相关 few-shot；
3. **Procedural memory**：根据反馈更新写作、路由或工具使用指令；
4. **Hot path / background**：至少一条记忆同步写入，一条后台整理；
5. **Context builder**：对检索结果去重、排序并限制 token；
6. **Evaluation**：对比 no memory、single memory type、full memory，报告准确率、token、p95 与失败案例。

推荐实现：LangGraph + Store + 一个固定 reader；InsightMem 可作为外部证据检索 Adapter，但不必承担全部记忆逻辑。

### 6.2 阶段二：memory OS mini service

对应 [LLMs as Operating Systems: Agent Memory](https://www.deeplearning.ai/short-courses/llms-as-operating-systems-agent-memory/)。

最低要求：

1. **Core memory**：少量当前可见事实与指令，支持 Agent 自编辑并保留版本；
2. **Recall memory**：最近对话与当前任务状态；
3. **Archival memory**：可搜索的外部档案；
4. **Memory pressure**：超过阈值时触发摘要、page-out 或 page-in；
5. **Self-editing**：记录修改前后 diff、理由与回滚点；
6. **Dreaming / consolidation**：后台整理，不覆盖新人工纠正；
7. **Shared memory**：至少两个 Agent 共享一个只读或受控 memory block；
8. **Evaluation**：报告换入换出准确率、摘要保真、回滚成功率、隔离与完整成本。

推荐实现：一个显式 `MemoryManager` + Store/文件后端。不要一开始就调用通用 coding agent；先实现可观察、可测试的确定性策略。实验步骤见 [L8](labs.md#l8)。

### 6.2.1 阶段一的里程碑

> 可运行入口是 `experiments/email-agent/notebooks/01-baseline.ipynb` 到 `04-evaluation.ipynb`。当前实现是离线 `LocalStore` + 确定性策略，尚未包含 LangGraph Store 工具、真实 LLM、hot path/background 或 context builder。

| 里程碑 | 交付物 | 验收问题 | 可运行入口 |
|---|---|---|---|
| M0 基线 | triage + response Agent | 没有记忆时哪些任务失败？ | [01-baseline](../../experiments/email-agent/notebooks/01-baseline.ipynb) |
| M1 Semantic | Store + manage/search tools | 能否记住并纠正用户事实？ | [02-semantic-memory](../../experiments/email-agent/notebooks/02-semantic-memory.ipynb) |
| M2 Episodic | examples namespace + few-shot | 新示例是否只影响目标用户？ | [03-episodic-and-procedural](../../experiments/email-agent/notebooks/03-episodic-and-procedural.ipynb) |
| M3 Procedural | prompt 版本与反馈更新 | 反馈是否改变后续行为？ | [03-episodic-and-procedural](../../experiments/email-agent/notebooks/03-episodic-and-procedural.ipynb) |
| M4 Evaluation | 四组对照与轨迹 | 收益是否来自单一机制？ | [04-evaluation](../../experiments/email-agent/notebooks/04-evaluation.ipynb) |

Notebook 验证的是离线机制版本：M1 没有 LangMem 的 manage/search 工具，M2/M3 没有 LLM few-shot 或 prompt optimizer，M4 没有 token/p95 与统计置信区间。完成课程项目时仍需补齐这些能力。

### 6.2.2 阶段二的里程碑

> 阶段二目前没有可运行 Notebook；下表是设计与实现清单，不能由阶段一 01–04 Notebook 替代。

| 里程碑 | 交付物 | 验收问题 |
|---|---|---|
| M0 自编辑 | dictionary + tool loop | 用户纠正后能否立即生效？ |
| M1 外部记忆 | recall + archival Adapter | Agent 是否按需检索？ |
| M2 上下文管理 | warning/refresh + summary | eviction 后能否找回旧消息？ |
| M3 治理 | 版本、审计、后台 consolidation | 后台任务是否覆盖新纠正？ |
| M4 多 Agent | shared block + 权限 | 共享是否造成越权？ |
| M5 Evaluation | pressure/rollback/isolation 报告 | 是否报告完整成本？ |

### 6.2.3 MemoryManager 最小接口

```python
class MemoryManager:
    def compile_context(self, state, query, budget) -> Context:
        """把 core、recall、archival 与当前任务装配成有限上下文。"""

    def edit_core(self, block_id, old_value, new_value, reason) -> Version:
        """校验版本、写入 diff 与审计，返回可回滚版本。"""

    def search_recall(self, query, limit) -> list[Message]:
        """搜索完整消息历史，不把 eviction 当 deletion。"""

    def search_archival(self, query, limit) -> list[Passage]:
        """搜索外部知识，保持来源与 scope。"""

    def consolidate(self, snapshot) -> ConsolidationResult:
        """后台整理；提交前重新读取并做 CAS。"""
```

接口验收比内部实现更重要：调用者必须知道预算、顺序、错误模式与回滚语义，而不只是看到函数签名。

### 6.2.4 Capstone 检查点

- 能否用一条轨迹证明 semantic memory 被检索并使用？
- 能否用一条轨迹证明 procedural memory 被更新？
- 能否证明 page-out 不等于 delete？
- 能否证明 consolidation 不覆盖新版本？
- 能否证明两个 Agent 共享 block 时仍有权限边界？

### 6.3 共同验收

- 写入原子、幂等、可追溯；
- 检索与上下文装配有明确预算；
- 自编辑与后台整理可回滚；
- 多用户、多 Agent、多项目隔离；
- 固定 reader、prompt、数据与 seed；
- 至少两个消融、三个失败案例和完整成本表。

---

## 7. 通用证据服务：mini memory service

### 7.1 目标与边界

实现一个同步、可复现的记忆证据服务：

```text
Add(event)     → committed source + chunks + vectors
Search(query)  → ordered evidence items with provenance
```

第一版不生成答案、不做后台 dreaming、不做图遍历。先证明写入、隔离、召回、融合和评测正确，再增加治理能力。

### 7.2 接口合同

```http
POST /add
Idempotency-Key: <request_id>

{
  "user_id": "u1",
  "session_id": "s1",
  "messages": [
    {"role": "tool", "content": "...", "timestamp_ms": 1763942400000}
  ]
}
```

```http
POST /search

{
  "user_id": "u1",
  "query": "...",
  "top_k": 10
}
```

Add：

- 同 `(user_id, request_id)` 同 payload 返回旧结果；
- 同 key 不同 payload 返回 409；
- 成功返回前，原文、chunk、vector 已可在同一快照中检索；
- 不允许把异步 embedding 伪装成“写入完成”。

Search：

- 只返回该 `user_id` 的证据；
- 结果有序，带 `id`、`content`、`score`、`source`、`spans`；
- content 是原文 slice，不由检索器改写；
- `top_k` 是数量上限，不保证凑满；
- 不返回其他用户的 id、score 或存在性信息。

### 7.3 最小数据模型

```text
request
  user_id, request_id, payload_hash, created_at

source_message
  user_id, message_id, session_id, role, kind, timestamp_ms, raw_content

source_chunk
  user_id, chunk_id, message_id, start_char, end_char, raw_content

view
  user_id, view_id, text, representation

view_embedding
  user_id, view_id, model_id, dim, vector

view_source
  view_id, message_id, start_char, end_char
```

约束：

- `UNIQUE(user_id, request_id)`；
- 外键与 scope 同时存在，不能只靠 caller 自觉过滤；
- chunk span 必须落在对应 message 范围内；
- vector 的模型与维度必须和 fingerprint 一致；
- source 不可变；纠错产生新版本或新事实，不静默改原文。

### 7.4 最小检索流水线

```text
snapshot
  → raw lexical
  → expanded lexical
  → dense
  → deduplicate candidate identity
  → RRF
  → build source-slice candidates
  → remove exact/covered/overlapping evidence
  → order by relevance, novelty, cost, id
  → top_k
```

第一版使用标准 RRF 即可：

```text
RRF(d) = Σᵣ wᵣ / (k + rankᵣ(d))
```

在融合前按 canonical chunk ID 去重。证据 bundle 是优化，不是正确性前提；如果实现不稳定，先返回成员，再增加 bundle。

### 7.5 不可妥协的不变量

1. **原子性**：Search 永远看不到半个 Add；
2. **幂等性**：重放不产生重复 source；
3. **隔离性**：任何表、索引、缓存键都带 scope；
4. **保真性**：返回 content 与 source span 一致；
5. **可复现性**：固定模型、prompt、top_k、seed 后可重跑；
6. **预算性**：结果上限可解释，不仅是一个 top_k 数字。

### 7.6 测试面

| 层 | 必须测试 |
|---|---|
| 写入 | 重放、payload 冲突、部分失败回滚、span 合法 |
| 隔离 | 双用户哨兵、同 session 不同 user、缓存交叉 |
| 检索 | 精确 ID、语义改写、多跳、无答案 |
| 选择 | 完全重复、部分重叠、bundle 与成员、top_k |
| 时间 | 当前值、as-of、迟到证据 |
| 删除 | 原文、facts、postings、vectors、cache、备份恢复 |
| 并发 | 不同 request 同时写、版本冲突、重试 |
| 评测 | manifest、raw artifacts、paired CI、成本 |

接口就是测试面。只测试内部 helper，不测试 Add/Search 的组合行为，无法发现事务、scope 与融合顺序的 bug。

---

## 8. InsightMem 深化

InsightMem 已有不可变 source、三腿召回、bundle 与 span 去重。可选择一个方向做深，不要同时重构整条链路。

### 候选 B1：证据装配 Module

将分散在 `evidence.py`、`selection.py`、`service.py` 中的候选构造、bundle、去重与预算逻辑收成一个深 Module。

- **Problem**：理解“为什么最终没有返回某段原文”需要跨多个文件追踪；
- **Solution**：让一个接口接收候选与 scope/config，返回带 provenance 的有序证据及选择原因；
- **Benefits**：提高 locality，使选择规则集中测试；提高 leverage，Search 不再了解 bundle/span 细节；
- **Tests**：同一输入确定性输出、成员不被 bundle 错误替代、部分重叠不被误删、预算可解释。

删除测试：如果删掉这个 Module 后，复杂度只是重新散落到多个 caller，它就在赚取 depth；如果它只做一次透传，应合并回 caller。

### 候选 B2：显式全局预算

当前选择主要按 `top_k` 停止。可增加字符或 token 预算，并记录每条证据的 cost。

- **Problem**：10 条长证据与 10 条短证据的实际上下文成本不同；
- **Solution**：在选择时维护累计预算，优先高 utility，必要时用更短成员替代 bundle；
- **Benefits**：提高预算可控性与成本可预测性；
- **Tests**：预算边界、零预算、单条超限、bundle/成员替换、确定性 tie-break。

### 候选 B3：事实治理层

在不可变证据层之上增加 fact、version、valid/recorded interval 与 tombstone，不替换 source。

- **Problem**：原文层无法表达“旧值已失效”或“系统何时知道”；
- **Solution**：facts 引用 source span，更新产生新版本，检索可区分 current/as-of/as-of knowledge；
- **Benefits**：提高时间查询的 locality，避免每个 caller 自行解释时间戳；
- **Tests**：迟到证据、同时冲突、异域、CAS、删除传播、恢复后不复活。

这三个方向分别对应选择、预算、治理，必须分别评测，不能把提升混在一起。

---

## 9. 框架最小复现

只复现“能解释机制”的最小闭环，不追求功能齐全。

### Mem0 最小核心

```text
messages
  → fact extraction
  → ADD / UPDATE decision
  → semantic + keyword candidates
  → fused top_k facts
  → fixed reader
```

必须报告：抽取错误、合并错误、旧值处理与 source 可追溯性。

### Zep / Graphiti 最小核心

```text
episode
  → entities / facts / edges
  → valid + recorded intervals
  → keyword/semantic/graph candidates
  → as-of reader
```

必须报告：边来源、失效传播、时间边界与图抽取成本。

### MemOS 最小核心

```text
MemCube(plaintext, metadata)
  → scheduler policy
  → migrate / combine
  → retrieve
```

第一版不实现参数微调。用可观测的迁移策略验证“调度是否带来任务收益”，否则只是在复现包装。

### MemoryOS 最小核心

```text
STM queue
  → dialogue chain / segment
  → MTM page retrieval
  → LPM profile
  → context builder
```

必须报告：热门偏见、主题误分、人格更新错误，以及每层 token 成本。

---

## 10. 实验与评分

### 10.1 最小实验矩阵

| 配置 | 目的 |
|---|---|
| no memory | 模型本身基线 |
| full context | reader 与预算上界 |
| raw lexical | 单腿基线 |
| hybrid | 融合系统 |
| hybrid - dedup | 去重贡献 |
| hybrid - bundle | bundle 贡献 |
| hybrid - budget | 预算贡献 |
| hybrid + noise | 抗噪能力 |

固定 answerer、prompt、top_k、query 集合与证据预算。用 paired Δ 与 bootstrap CI，不用单次平均分宣称提升。

### 10.2 Rubric

| 维度 | 权重 | 满分标准 |
|---|---:|---|
| 正确性 | 20 | 原子、幂等、隔离、span 正确、无半提交 |
| 检索质量 | 25 | 有 baseline、逐项消融、按切片报告 |
| 评测严谨 | 20 | held-out、配对 CI、judge 校准、分子分母 |
| 工程质量 | 15 | 可运行、可测试、失败可诊断、配置可复现 |
| 架构表达 | 10 | Module 接口清楚，locality/leverage 有证据 |
| 成本与治理 | 10 | 完整成本、时间/删除/并发至少覆盖一项 |

### 10.3 必交产物

1. 一页数据流与状态图；
2. Add/Search 接口合同与不变量；
3. 干净环境启动命令；
4. manifest 与原始 predictions/retrievals/metrics；
5. baseline、消融、paired CI 与成本表；
6. 至少 3 个失败案例；
7. 一页设计结论：保留了哪些机制、删除了哪些机制、为什么。

---

## 11. 设计评审问题

提交前逐条回答：

- 删除哪个 Module 会让复杂度消失，还是让它重新散落到 caller？
- 哪个 Interface 包含了调用者必须知道的全部不变量？
- 哪条行为只有一个 Adapter，因而还不能算真正的 Seam？
- 哪项错误只有通过组合测试才能暴露？
- 哪部分成本没有计入 build、maintenance、retry 或存储？
- 哪项“记忆更新”实际上是覆盖、缓存淘汰或归档？
- 哪项能力只有厂商自报或单次实验支持？
- 如果换一个 answerer，结论是否仍成立？

---

## 12. 验收

- 系统能在干净环境跑起来，失败时不会静默半提交；
- 双用户隔离、幂等重放与 payload 冲突有自动测试；
- Search 返回有序、可溯源、未改写的证据；
- 评测固定变量，结果带样本数、分子分母、paired CI 与 manifest；
- 至少完成两个消融，并报告完整成本；
- 能解释三个关键设计选择及其代价；
- 能指出至少一个失败模式，并说明它属于写入、组织、检索、使用还是治理；
- 不把论文版、当前 OSS 版、云版或不同 benchmark 的数字混为一谈。

---

## 13. 机制依据与课程

### 一手论文与项目

- [MemGPT 精读](../../docs/papers-zh/01-foundations.md#memgpt)：上下文管理、外部存储与 eviction/deletion 边界。
- [现代系统精读](../../docs/papers-zh/03-systems.md)：Mem0、Zep、MemOS、MemoryOS、A-MEM。
- [InsightMem 架构](../../docs/architecture.md)：不可变日志、同步 Add/Search、三腿检索与确定性选择。
- [AML API Guide](https://agentmemories.ai/api-guide)：竞赛 Add/Search 与统一评测边界。

### 课程

- [Long-Term Agentic Memory With LangGraph](https://www.deeplearning.ai/short-courses/long-term-agentic-memory-with-langgraph/)：从可运行工作流理解记忆生命周期。
- [LLMs as Operating Systems: Agent Memory](https://www.deeplearning.ai/short-courses/llms-as-operating-systems-agent-memory/)：从 Letta 的系统视角理解上下文与外部记忆。

### 下一步

回到 [路线入口](README.md) 更新进度，然后：

- 把 Capstone 结果整理成可复现技术报告；
- 从 Capstone B 选择一个 Module 做接口深化；
- 按 [评测手册](evaluation.md) 参加公开 benchmark，并明确报告不可比项。
