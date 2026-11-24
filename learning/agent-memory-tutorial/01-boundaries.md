# 01 边界与地图（第 1 周）

> 上一章：[00 定位与概念](00-orientation.md) · 下一章：[02 写入](02-writing.md)
> 预计：5–6 小时
> 本章目标：能区分工作上下文、短期记忆、长期记忆、权重、压缩和 RAG；能审计一个真实工具的记忆层，并画出状态生命周期。

---

## 1. 本周要解决的问题

“这个工具有记忆吗”通常不是二元问题。更准确的问题是：

1. 它保存了哪些状态？
2. 状态活多久？
3. 谁能读取？
4. 状态如何更新和删除？
5. 保存的状态是否真的进入下一次推理？

本章用一张状态地图回答这些问题。先看边界，再学实现，避免把 checkpoint、summary、vector store 混为一谈。

---

## 1.1 状态按生命周期分类

| 状态 | 存在哪里 | 典型寿命 | 主要用途 | 是否属于本文记忆 |
|---|---|---|---|---|
| Prompt context | 当前请求的 token | 单次推理 | 给模型提供立即可见信息 | 否，除非被持久化并跨会话读取 |
| Working memory | 当前任务变量、窗口、草稿 | 当前会话或任务 | 维护短期状态 | 是，短期/工作记忆 |
| Checkpoint | 图状态、消息、任务位置 | 线程生命周期，可恢复 | 暂停/恢复工作流 | 可以是短期记忆，但不等于语义记忆 |
| Episodic memory | 原始消息、episode、工具轨迹 | 跨会话，按策略保留 | 回溯发生过什么 | 是 |
| Semantic memory | fact、profile、entity、relation | 跨会话，可更新/失效 | 保存事实、偏好、关系 | 是 |
| Procedural memory | rule、skill、playbook | 跨会话，可版本化 | 复用做事方法 | 是 |
| Compaction summary | 对旧上下文的摘要 | 通常跟随当前窗口 | 释放当前上下文空间 | 否；写入长期存储后才可能成为记忆 |
| Model weights | 微调后的参数 | 模型版本生命周期 | 改变通用能力 | 否，属于训练 |

### Checkpoint 为什么容易混淆

LangGraph 的 checkpoint 会持久化 thread state，因此“会话结束后还在”。但它的首要目的是**恢复执行状态**，例如图走到哪一步、工具是否完成、消息队列是什么。

判断它是不是长期记忆，要看使用方式：

- 恢复同一个 thread 的工作流：主要是短期/工作记忆；
- 从历史 thread 抽取用户偏好供新 thread 使用：才构成跨会话语义记忆；
- 把所有 checkpoint 无差别注入新会话：通常是噪声和预算问题，不是好的记忆设计。

---

## 1.2 一条状态生命周期

```text
原始事件
  │
  ├─► 当前上下文 ──► 推理 ──► 丢弃
  │
  ├─► 工作记忆 / checkpoint ──► 恢复任务 ──► 归档或清理
  │
  └─► 长期记忆
          ├─► 原文 episode
          ├─► 提炼 fact / note
          └─► 规则 / skill
                    │
                    ▼
              更新 / 失效 / 删除 / 审计
```

设计时至少标注三个时间：

- **事件时间**：事情什么时候发生；
- **写入时间**：系统什么时候知道；
- **读取时间**：这次查询发生在什么时候。

三者不同。例如用户今天说“我搬到上海”，事件时间可能是今天，但系统昨天还保存着“住在北京”。只按写入时间排序，无法可靠处理现实世界的变化。双时间的完整讨论见 [06 更新与治理](06-governance.md)。

---

## 1.3 短期记忆与长期记忆不是“窗口 vs 向量库”

常见误解是把短期记忆等同于滑动窗口，把长期记忆等同于向量库。实际上：

| 维度 | 短期记忆 | 长期记忆 |
|---|---|---|
| 目标 | 维持当前任务连续性 | 支持跨会话复用 |
| 单元 | 消息、工具状态、草稿、checkpoint | episode、fact、note、rule |
| 更新 | 高频、覆盖或追加 | 抽取、合并、失效、版本化 |
| 读取 | 通常直接注入或按需取回 | 检索、过滤、排序、预算控制 |
| 删除 | 会话结束或任务完成 | 用户请求、TTL、合规策略 |

一个系统可以两者都有，也可以只有其中之一。MemGPT 的主上下文和外部上下文是典型分层；InsightMem 更偏向长期原文证据存储，不负责当前窗口管理。

---

## 1.4 Compaction、RAG 与 Memory

### Compaction

Compaction 把旧消息压缩成较短表示，让当前对话能继续。它解决的是**本次上下文预算**。

如果摘要只存在于当前 prompt 中，它不是长期记忆；如果把摘要作为派生记忆写入外部存储，并保留来源和版本，它才进入记忆生命周期。

风险：

- 压缩比例过高会丢失约束；
- 递归摘要会累积误差；
- 摘要看起来流畅，但不一定忠实；
- 只存摘要会导致无法审计。

### Compaction 协议：按完整轮次驱逐

一个可实现的压缩协议是：

```python
while token_count(context) > budget:
    turn = evict_oldest_complete_turn()
    summary = summarize(summary, turn)
    anchors.extend(extract_source_anchors(turn))
```

“完整轮次”不仅是 user/assistant 两条消息，还应包括 tool call 与对应 tool result。只截断其中一半，模型会看到无法解释的 ID 或缺失的参数。

至少保留两类锚点：

- 原始消息 ID 与角色；
- 关键约束、数值、路径、错误码的原文位置。

实验时扫描预算 `B`，同时测关键约束保留率、工具配对完整率和摘要忠实度。只报 token 缩减比例是不够的。

### RAG

RAG 通常检索相对静态的文档库；agent memory 更强调从交互经验中持续获得、更新和治理知识。

但两者工程上高度重叠：都要 chunk、embed、检索、重排和注入上下文。区别主要在数据来源与生命周期，而不是“有没有向量数据库”。

### Memory

真正的记忆系统还要回答：

- 谁写入，写什么？
- 新事实与旧事实冲突怎么办？
- 用户能否查看、纠正和删除？
- 检索结果如何证明来源？
- 跨用户是否隔离？

---

## 1.5 四层结构审计法

Anthropic 的四层结构适合审计真实工具：

| 层 | 要找的东西 | 审计问题 |
|---|---|---|
| Transcripts | 原始对话、工具调用、执行结果 | 是否逐字保存？能否定位到具体消息？ |
| Memory notes | 自动或人工写下的偏好、经验、规则 | 谁生成？谁能改？是否保留来源？ |
| Representations | 索引、wiki、标签、交叉链接 | 如何更新？会不会产生重复或陈旧链接？ |
| Injected context | 每次会话主动加载的内容 | 注入多少？按什么顺序？是否可关闭？ |

### 审计步骤

1. **列存储**：文件、SQLite、向量库、图、云端档案分别在哪里？
2. **追一条事实**：从原始消息追到注入上下文，记录每次转换。
3. **追一次更新**：旧事实如何被新事实取代？
4. **追一次删除**：用户要求删除时，哪些副本、索引和缓存会受影响？
5. **测作用域**：换一个 user/tenant，是否还能读到原文？
6. **记录缺口**：缺来源、缺失效、缺删除、缺预算中的哪一项？

### 四层的可观测契约

每一层都应能回答：

```text
谁写入 → 谁读取 → 对谁可见 → 来自哪里 → 何时失效
```

对应字段至少包含 `writer`、`reader`、`visibility`、`source_span`、`valid_until`。存储层存在不代表注入层存在：界面展示过某条记忆，也不代表模型在生成时用过它。

### 审计证据分级

把事实与推测分开记录：

| 等级 | 证据 | 能支持的结论 |
|---|---|---|
| A | 官方文档、API 合同、源码 | 声明的行为和实现约束 |
| B | 用户导出、数据库快照、日志 | 本机实际保存的状态 |
| C | 行为探针 | 在特定输入下观察到的读写行为 |
| D | UI 印象、推测 | 只能作为待验证假设 |

例如看到界面有“记忆”开关，不能据此推断它用了向量库。对闭源产品，导出后清空再导入可以验证恢复路径，但无法验证云端内部索引。未知项写“未知”，不要补成确定结论。

---

## 1.6 三个真实形态

### InsightMem：长期原文证据层

[InsightMem](../../wiki/insightmem.md) 保存全部消息、chunk、view 和 embedding，Search 返回有限证据。它：

- 有 Transcripts 和检索表示；
- 没有当前窗口管理、事实抽取、时间失效和自动遗忘；
- `user_id` 是唯一检索隔离边界，`session_id` 只是来源标识。

因此它适合回答“过去发生过什么、证据在哪里”，不适合回答“用户现在真正喜欢什么”。

### MemGPT：主上下文 + 外部上下文

[MemGPT 精读](../../docs/papers-zh/01-foundations.md#memgpt) 把有限上下文当主内存，外部存储当磁盘：

- 主上下文包含系统指令、working context 和 FIFO 队列；
- 外部包含 recall storage 与 archival storage；
- 内存压力触发写入、驱逐和递归摘要；
- 被驱逐消息仍可检索，**驱逐不等于删除**。

它展示的是上下文管理与外部记忆的协作，不是单纯“向量库”。

### Letta Code / MemFS：文件式长期记忆

[Letta 与 MemFS](../../wiki/memgpt-letta.md) 用 Markdown 文件保存记忆：

- 根目录文件进入系统提示；
- 子目录按需读取；
- 文件可编辑、可版本化；
- 后台 dreaming 整理记忆。

文件式记忆的优势是透明、可审计、易人工纠正；风险是上下文注入预算、链接陈旧和写入冲突。

---

## 1.7 Hot path 与 background

| 路径 | 何时发生 | 优点 | 风险 | 典型操作 |
|---|---|---|---|---|
| Hot path | 用户请求期间同步执行 | 立即可用、延迟可预测 | 阻塞主流程、失败影响请求 | 原文写入、幂等检查、即时事实抽取 |
| Background | 会话后或定时执行 | 可批量总结、成本可控 | 滞后、需要任务状态和重试 | dreaming、批量 embedding、图整合 |

[LangGraph Memory overview](https://docs.langchain.com/oss/python/langgraph/memory) 明确区分这两种写入时机。设计原则：

- 不能把“以后整理”当成“现在不记”；
- 不能把所有 LLM 抽取都放在关键路径；
- 后台任务必须可重试、可观测、幂等；
- 原文应先在事务中落库，派生表示可以后续补齐。

---

## 1.8 最小记忆契约

审计任何实现，都检查以下字段和语义：

| 字段/能力 | 为什么需要 |
|---|---|
| `memory_id` | 稳定标识，支持更新和删除 |
| `user_id` / `tenant_id` | 读取隔离边界 |
| `session_id` / `source_id` | 溯源，不一定是检索过滤条件 |
| `source_span` | 指向原文位置，支持核验 |
| `ingested_at` | 写入时间 |
| `valid_from` / `valid_to` | 事实生效区间 |
| `status` | active / invalidated / deleted / archived |
| `version` | 追踪覆盖与回滚 |
| `confidence` / `method` | 标识规则、LLM 或人工来源 |

不是所有系统都要同时实现全部字段，但必须明确哪些缺失会带来风险。

### 隔离模型

一种实用 namespace 是：

```text
(tenant_id, user_id, project_id, thread_id)
```

每一层按授权策略过滤：

- 写入时确定 owner 和 visibility；
- 检索时先过滤，再排序；
- 注入时再次校验；
- 后台任务也使用同一 scope；
- 缓存键包含 scope 和索引版本。

测试不能只检查“代码里有 `user_id`”。给两个用户投放不同唯一哨兵，再交换查询：

1. 用户 A 写入只有 A 知道的短语；
2. 用户 B 用该短语检索；
3. 断言零结果；
4. 清空缓存、重建索引后重复；
5. 检查导出、备份恢复和后台任务路径。

### 删除与保留

删除是一条状态链，不是一次 `DELETE`：

```text
请求删除
  → 主记录 tombstone
  → 派生 notes 失效
  → 索引/缓存失效
  → prompt 缓存失效
  → 搜索验证
  → 按保留策略处理备份
```

分别定义业务删除、索引删除、备份保留期和合规例外。恢复备份可能重新引入已删除记录，因此需要重放 tombstone 或删除日志。

验证至少覆盖：

- 删除后立即检索；
- 重建索引后检索；
- 恢复备份后检索；
- 同一用户的另一会话；
- 其他用户的越权检索。

---

## 1.9 动手：L0 记忆审计

完整步骤见 [实验手册 L0](labs.md#l0)。

选一个你常用的工具，追一条具体记忆，例如“用户喜欢简短回答”：

1. 找到原始来源；
2. 找到保存位置；
3. 找到索引或表示；
4. 找到下一次注入路径；
5. 找到更新和删除路径；
6. 尝试切换用户或会话，验证隔离。

### 产出模板

| 层 | 该工具的实现 | 证据 | 缺口 |
|---|---|---|---|
| Transcripts | | | |
| Memory notes | | | |
| Representations | | | |
| Injected context | | | |

底部写一句结论：这个工具最薄弱的记忆层是哪一层，它会造成什么具体失败？

---

## 1.10 验收

- 能用一句话解释为什么“无关、过时、重复记忆进入上下文或维护路径”可能降效并增本；
- 能区分 checkpoint、compaction 和长期语义记忆；
- 能解释 compaction 与长期记忆的边界；
- 能指出一个工具的错误记忆会从哪一层进入；
- 能设计一次跨用户隔离测试，而不是只检查代码里有没有 `user_id`。

---

## 1.11 机制依据与延伸阅读

### 一手依据

- [Anthropic: The components of agent memory](https://www.anthropic.com/research/components-of-agent-memory)：四层结构与注入层。
- [LangGraph Memory overview](https://docs.langchain.com/oss/python/langgraph/memory)：short-term / long-term、hot path / background。[中文参考译文](../../docs/langchain-memory-zh.md)
- [CoALA, arXiv:2309.02427](https://arxiv.org/abs/2309.02427)：working memory、episodic/semantic/procedural memory。[中文译文](../../docs/coala-zh.md)
- [MemGPT, arXiv:2310.08560](https://arxiv.org/abs/2310.08560)：主/外部上下文与虚拟上下文管理。[中文精读](../../docs/papers-zh/01-foundations.md#memgpt)
- [Letta memory & dreaming](https://docs.letta.com/letta-code/memory)：文件式记忆的官方工程说明。

### 课程与资源

- [LangChain Academy](https://academy.langchain.com/)：用 thread state、checkpoint 和 store 做对照实验。
- [Awesome-AI-Memory](https://github.com/IAAR-Shanghai/Awesome-AI-Memory)：按 memory type 和 framework 找后续阅读。
- 更多资源见 [社区资源](community.md)。

---

## 下一章

[02 写入](02-writing.md)：决定记什么、记成什么单元，以及什么时候写。
