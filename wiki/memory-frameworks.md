---
title: Agent Memory 框架机制对比
summary: 从记忆单元、写入、更新、检索和上下文管理比较 InsightMem 与六类框架。
status: source-reviewed
section: 框架
order: 30
updated: 2026-11-24
tags: [agent-memory, frameworks, comparison]
sources:
  - docs/papers-zh/01-foundations.md
  - docs/papers-zh/03-systems.md
  - docs/architecture.md
---

# Agent Memory 框架机制对比

## 对比表

| 系统 | 记忆单元 | 写入 | 更新 | 检索 | 上下文管理 |
|---|---|---|---|---|---|
| **InsightMem** | 原始消息、chunk、source view、向量 | 全量追加、同步 embedding | 无事实整合；查询期过滤与去重 | raw BM25 + code BM25 + dense + RRF | 无 |
| **Mem0** | 抽取记忆、实体、可选图关系 | LLM 抽取显著信息 | 论文版可整合；新版 ADD-only | 语义、BM25、实体、时间等信号 | 无 |
| **Zep / Graphiti** | episode、entity、fact、edge | 抽取进入时序图 | 双时间失效，保留历史 | 语义 + 关键词 + 图遍历 | 无 MemGPT 式分页 |
| **MemGPT / Letta V1** | memory blocks、recall、archival | agent 函数调用读写 | 队列驱逐、递归摘要、外部存储 | recall 与 archival search | Main/External Context、Queue Manager |
| **Letta Code / MemFS** | 版本化 Markdown 文件 | agent 编辑文件 | git 版本、后台 dreaming | 按需读文件，可选搜索 mod | 根目录常驻，子目录按需读取 |
| **MemOS** | MemCube | 调度器异步写入 | 组合、迁移、融合 | 按记忆类型调度 | 记忆资源与表示管理 |
| **MemoryOS** | 对话页、主题 segment、人格 | STM FIFO、MTM 按热度归档 | 分段分页、热度淘汰、人格更新 | STM + segment/page + LPM | 三层记忆层次 |
| **A-MEM** | 结构化笔记与链接 | LLM 生成笔记并连接 | 新记忆触发旧记忆演化 | 网络关联与语义检索 | 无专门上下文分页 |

## InsightMem 的位置

InsightMem 与 **Mem0 的检索侧**和 **Zep 的 episode 留存思想**有相似之处，但缺少两者核心的写入治理：

- 相比 Mem0，它不抽取、不整合、不维护事实和实体。
- 相比 Zep，它没有图遍历、关系推理和事实失效。
- 相比 MemGPT/Letta，它不管理当前上下文，没有队列驱逐和递归摘要。
- 相比 MemOS/MemoryOS，它没有记忆调度、分层迁移、热度或人格演化。
- 相比 A-MEM，它没有结构化笔记网络和旧记忆演化。

## 怎么读这张表

不要只比较“是否长期保存”，要比较**系统如何处理错误事实、冲突、过时和上下文预算**。InsightMem 选择保留原始证据，把综合与答案生成留给调用方；其他系统则把更多认知和维护责任放进记忆层。

详细入口：

- [[memgpt-letta]]
- [[memos-vs-memoryos]]
- [[insightmem]]
- [03-systems.md](../docs/papers-zh/03-systems.md)
- [01-foundations.md](../docs/papers-zh/01-foundations.md#memgpt)

<!-- generated:backlinks:start -->
## 反向链接

- [[insightmem|InsightMem 机制审计]] — InsightMem 是全量会话轨迹持久化与确定性混合证据检索，不是抽取式记忆 OS。
- [[insightmem-governance|InsightMem 隔离、幂等与数据治理]] — 正常运行采用 append-only，user_id 隔离检索，删除依赖离线运维流程。
- [[agent-memory|Agent Memory 概念地图]] — 用五个动作、四种记忆类型和四层知识结构理解 Agent Memory。
- [[learning-path|用 InsightMem 学习 Agent Memory]] — 把 InsightMem 当作外部情景记忆与混合检索的可运行参考，再补齐抽取、更新和遗忘。
- [[memgpt-letta|MemGPT、Letta 与 MemFS]] — MemGPT 用主外上下文和队列管理模拟 OS，Letta 将其产品化，MemFS 是新的文件式记忆形态。
- [[memos-vs-memoryos|MemOS 与 MemoryOS 不要混淆]] — MemOS 管理记忆资源与表示，MemoryOS 管理短中长期对话记忆、分页与人格。
<!-- generated:backlinks:end -->
