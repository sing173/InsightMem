<!-- generated:index:start -->
# Agent Memory Wiki

共 11 个页面。索引导航与状态从页面 frontmatter 生成。

维护入口：[Wiki 维护约定](wiki/schema.md) · [演进日志](log.md)

## 维护

| 页面 | 摘要 | 状态 |
|---|---|---|
| [Wiki 维护约定](wiki/schema.md) | 说明源文档、Wiki 页面、frontmatter、生成索引与反向链接的维护方式。 | maintained |

## 基础

| 页面 | 摘要 | 状态 |
|---|---|---|
| [Agent Memory 概念地图](wiki/agent-memory.md) | 用五个动作、四种记忆类型和四层知识结构理解 Agent Memory。 | source-reviewed |

## InsightMem

| 页面 | 摘要 | 状态 |
|---|---|---|
| [InsightMem 机制审计](wiki/insightmem.md) | InsightMem 是全量会话轨迹持久化与确定性混合证据检索，不是抽取式记忆 OS。 | verified |
| [InsightMem 三路检索与证据选择](wiki/insightmem-retrieval.md) | 原始 BM25、代码展开 BM25 与稠密向量经 RRF 融合，再过滤、合并和去重。 | verified |
| [InsightMem 隔离、幂等与数据治理](wiki/insightmem-governance.md) | 正常运行采用 append-only，user_id 隔离检索，删除依赖离线运维流程。 | verified |

## 框架

| 页面 | 摘要 | 状态 |
|---|---|---|
| [Agent Memory 框架机制对比](wiki/memory-frameworks.md) | 从记忆单元、写入、更新、检索和上下文管理比较 InsightMem 与六类框架。 | source-reviewed |
| [MemGPT、Letta 与 MemFS](wiki/memgpt-letta.md) | MemGPT 用主外上下文和队列管理模拟 OS，Letta 将其产品化，MemFS 是新的文件式记忆形态。 | source-reviewed |
| [MemOS 与 MemoryOS 不要混淆](wiki/memos-vs-memoryos.md) | MemOS 管理记忆资源与表示，MemoryOS 管理短中长期对话记忆、分页与人格。 | source-reviewed |

## 机制

| 页面 | 摘要 | 状态 |
|---|---|---|
| [混合检索与 RRF](wiki/hybrid-retrieval.md) | 用词法、代码词法、稠密向量等不同召回腿互补，再以 RRF 融合名次。 | source-reviewed |

## 评测

| 页面 | 摘要 | 状态 |
|---|---|---|
| [AML Coding Track 与 InsightMem 定位](wiki/aml-coding-harness.md) | InsightMem 是 AML 兼容的同步 Add/Search 记忆服务，平台负责固定答案生成与评分。 | verified |

## 学习

| 页面 | 摘要 | 状态 |
|---|---|---|
| [用 InsightMem 学习 Agent Memory](wiki/learning-path.md) | 把 InsightMem 当作外部情景记忆与混合检索的可运行参考，再补齐抽取、更新和遗忘。 | maintained |

## 来源覆盖

| 来源 | 引用页面 |
|---|---|
| `README.md` | [InsightMem 机制审计](wiki/insightmem.md)、[AML Coding Track 与 InsightMem 定位](wiki/aml-coding-harness.md) |
| `configs/coding/default.json` | [InsightMem 机制审计](wiki/insightmem.md)、[InsightMem 三路检索与证据选择](wiki/insightmem-retrieval.md) |
| `docs/api-contract.md` | [InsightMem 机制审计](wiki/insightmem.md)、[InsightMem 隔离、幂等与数据治理](wiki/insightmem-governance.md)、[AML Coding Track 与 InsightMem 定位](wiki/aml-coding-harness.md) |
| `docs/architecture.md` | [InsightMem 机制审计](wiki/insightmem.md)、[Agent Memory 框架机制对比](wiki/memory-frameworks.md) |
| `docs/karpathy_llm_wiki.zh.md` | [Wiki 维护约定](wiki/schema.md) |
| `docs/langchain-memory-zh.md` | [Agent Memory 概念地图](wiki/agent-memory.md) |
| `docs/operations.md` | [InsightMem 隔离、幂等与数据治理](wiki/insightmem-governance.md) |
| `docs/papers-zh/01-foundations.md` | [Agent Memory 框架机制对比](wiki/memory-frameworks.md)、[MemGPT、Letta 与 MemFS](wiki/memgpt-letta.md) |
| `docs/papers-zh/02-surveys.md` | [Agent Memory 概念地图](wiki/agent-memory.md) |
| `docs/papers-zh/03-systems.md` | [Agent Memory 框架机制对比](wiki/memory-frameworks.md)、[MemOS 与 MemoryOS 不要混淆](wiki/memos-vs-memoryos.md) |
| `docs/papers-zh/04-retrieval-eval.md` | [AML Coding Track 与 InsightMem 定位](wiki/aml-coding-harness.md) |
| `learning/agent-memory-tutorial/00-orientation.md` | [Agent Memory 概念地图](wiki/agent-memory.md) |
| `learning/agent-memory-tutorial/01-boundaries.md` | [Agent Memory 概念地图](wiki/agent-memory.md) |
| `learning/agent-memory-tutorial/02-writing.md` | [Agent Memory 概念地图](wiki/agent-memory.md)、[用 InsightMem 学习 Agent Memory](wiki/learning-path.md) |
| `learning/agent-memory-tutorial/03-storage.md` | [MemOS 与 MemoryOS 不要混淆](wiki/memos-vs-memoryos.md) |
| `learning/agent-memory-tutorial/04-retrieval.md` | [InsightMem 三路检索与证据选择](wiki/insightmem-retrieval.md)、[混合检索与 RRF](wiki/hybrid-retrieval.md)、[用 InsightMem 学习 Agent Memory](wiki/learning-path.md) |
| `learning/agent-memory-tutorial/05-fusion.md` | [InsightMem 三路检索与证据选择](wiki/insightmem-retrieval.md)、[混合检索与 RRF](wiki/hybrid-retrieval.md)、[用 InsightMem 学习 Agent Memory](wiki/learning-path.md) |
| `learning/agent-memory-tutorial/06-governance.md` | [Agent Memory 概念地图](wiki/agent-memory.md)、[InsightMem 隔离、幂等与数据治理](wiki/insightmem-governance.md)、[用 InsightMem 学习 Agent Memory](wiki/learning-path.md) |
| `learning/agent-memory-tutorial/07-evaluation.md` | [AML Coding Track 与 InsightMem 定位](wiki/aml-coding-harness.md) |
| `learning/agent-memory-tutorial/08-capstone.md` | [用 InsightMem 学习 Agent Memory](wiki/learning-path.md) |
| `learning/agent-memory-tutorial/README.md` | [用 InsightMem 学习 Agent Memory](wiki/learning-path.md) |
| `learning/agent-memory-tutorial/evaluation.md` | [AML Coding Track 与 InsightMem 定位](wiki/aml-coding-harness.md) |
| `learning/agent-memory-tutorial/labs.md` | [用 InsightMem 学习 Agent Memory](wiki/learning-path.md) |
| `learning/agent-memory-tutorial/reading-list.md` | [MemGPT、Letta 与 MemFS](wiki/memgpt-letta.md) |
| `scripts/purge_user.py` | [InsightMem 隔离、幂等与数据治理](wiki/insightmem-governance.md) |
| `scripts/wiki.py` | [Wiki 维护约定](wiki/schema.md) |
| `src/insightmem/coding/content.py` | [InsightMem 三路检索与证据选择](wiki/insightmem-retrieval.md) |
| `src/insightmem/coding/evidence.py` | [InsightMem 三路检索与证据选择](wiki/insightmem-retrieval.md) |
| `src/insightmem/coding/filter.py` | [InsightMem 三路检索与证据选择](wiki/insightmem-retrieval.md) |
| `src/insightmem/coding/parse.py` | [InsightMem 机制审计](wiki/insightmem.md)、[InsightMem 三路检索与证据选择](wiki/insightmem-retrieval.md) |
| `src/insightmem/coding/selection.py` | [InsightMem 三路检索与证据选择](wiki/insightmem-retrieval.md) |
| `src/insightmem/coding/service.py` | [InsightMem 机制审计](wiki/insightmem.md)、[InsightMem 三路检索与证据选择](wiki/insightmem-retrieval.md)、[InsightMem 隔离、幂等与数据治理](wiki/insightmem-governance.md)、[混合检索与 RRF](wiki/hybrid-retrieval.md) |
| `src/insightmem/store.py` | [混合检索与 RRF](wiki/hybrid-retrieval.md) |

状态说明：`verified` 为代码或契约核对；`source-reviewed` 为资料综合；`conceptual` 为概念整理；`maintained` 为持续维护入口。
<!-- generated:index:end -->
