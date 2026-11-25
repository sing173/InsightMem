# Agent Memory 实战教程

> 新教程入口。旧版内容保留在 [agent-memory-tutorial（备份）](../agent-memory-tutorial/README.md)，用于论文精读、历史实验和参考资料。
> 阶段一结构参考 [Hello Agents 第八章：记忆与检索](https://hello-agents.datawhale.cc/#/./chapter8/%E7%AC%AC%E5%85%AB%E7%AB%A0%20%E8%AE%B0%E5%BF%86%E4%B8%8E%E6%A3%80%E7%B4%A2)，讲解、代码和实验均结合本仓库重写。

## 这门教程怎么学

本教程不先堆框架名词，而是按两个问题推进：

1. **Agent 怎样记住经验？**——对应阶段一“记忆与检索”；
2. **Agent 怎样在有限上下文里主动管理信息？**——对应阶段二“上下文工程”。

每个章节都遵循同一条学习路径：

```text
场景与目标
  → 运行最小示例
  → 观察输出
  → 解释机制
  → 查看本仓库实现
  → 做对照实验
  → 明确当前缺口与下一步
```

## 阶段一：记忆与检索

阶段一对应 Hello Agents 第 8 章，目标是让你不仅能调用“记忆”和“RAG”，还能解释它们内部发生了什么。

| 顺序 | 章节 | 核心问题 | 可运行入口 |
|---|---|---|---|
| 00 | [快速开始：记忆与 RAG 是什么](stage1-memory-and-retrieval/00-quick-start.md) | 为什么需要记忆？记忆和 RAG 有什么关系？ | email-agent baseline、InsightMem Quickstart |
| 01 | [记忆系统的工作流程](stage1-memory-and-retrieval/01-memory-workflow.md) | 一条信息怎样从输入变成可复用记忆？ | semantic/episodic/procedural Notebook |
| 02 | [MemoryTool 与记忆操作](stage1-memory-and-retrieval/02-memory-tool.md) | add、search、forget、consolidate 各自解决什么？ | `email_memory_lab.memory` |
| 03 | [MemoryManager 与四种记忆](stage1-memory-and-retrieval/03-memory-manager-and-types.md) | 工作、情景、语义、感知记忆怎样协作？ | 离线实现 + 教学骨架 |
| 04 | [RAG 系统与最小知识库](stage1-memory-and-retrieval/04-rag-system.md) | 文档怎样经过处理、检索进入回答？ | InsightMem Quickstart |
| 05 | [高级检索与本仓库实现](stage1-memory-and-retrieval/05-advanced-retrieval.md) | 词法、dense、混合、重排、图检索各自适合什么？ | InsightMem 三路召回 |
| 06 | [项目：智能文档问答助手](stage1-memory-and-retrieval/06-document-qa-assistant.md) | 如何把记忆、检索和固定 reader 组装成可评测系统？ | InsightMem + 评测 Notebook |
| 07 | [总结、练习与实现缺口](stage1-memory-and-retrieval/07-review.md) | 哪些能力已经可运行，哪些仍是设计骨架？ | 全部实验产物 |

## 开始前准备

### 只做离线实验

不需要 API Key 或模型下载：

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e "experiments/email-agent[notebooks]"
```

InsightMem 实验需要额外安装根包依赖，命令见 [InsightMem 实验项目](../../experiments/insightmem/README.md#安装)。

Windows PowerShell 使用 `.\.venv\Scripts\Activate.ps1`。VS Code 的完整操作见旧版备份附录 [C：VS Code Notebook 实验环境](../agent-memory-tutorial/appendix.md#c-vs-code-notebook-实验环境)。

### 实验项目

- [email-agent](../../experiments/email-agent/README.md)：离线验证 baseline、semantic、episodic、procedural memory；
- [insightmem](../../experiments/insightmem/README.md)：验证 Add/Search、BM25 + dense + RRF、隔离与证据选择。

## 实现状态标记

新教程会明确区分三种内容，避免把设计当成已有能力：

- **可运行**：本仓库已有代码、Notebook 和测试；
- **教学骨架**：用于解释机制，尚未接入真实模型或持久化服务；
- **扩展设计**：Hello Agents 第 8、9 章覆盖、但本仓库尚未实现的能力，例如 MemoryManager 的容量遗忘、Qdrant/Neo4j、图检索、多模态感知记忆、ContextBuilder、NoteTool 和 TerminalTool。

## 阶段二：上下文工程

阶段二对应 [Hello Agents 第九章：上下文工程](https://github.com/datawhalechina/hello-agents/tree/main/docs/chapter9)，目标是让 Agent 在有限上下文中主动收集、选择、组织和压缩信息，并通过结构化笔记与文件系统工具维持长程任务。

| 顺序 | 章节 | 核心问题 | 实现状态 |
|---|---|---|---|
| 00 | [什么是上下文工程](stage2-context-engineering/00-context-engineering.md) | 为什么上下文需要被主动构建？ | 概念讲解 |
| 01 | [ContextBuilder：把候选信息变成上下文](stage2-context-engineering/01-context-builder.md) | ContextPacket 与 ContextConfig 分别负责什么？ | 教学骨架 |
| 02 | [GSSC 流水线](stage2-context-engineering/02-gssc-pipeline.md) | Gather、Select、Structure、Compress 怎样协作？ | 教学骨架 |
| 03 | [NoteTool：结构化任务笔记](stage2-context-engineering/03-note-tool.md) | 任务状态、blocker、action 怎样跨请求保存？ | 教学骨架 |
| 04 | [TerminalTool：安全的文件系统探索](stage2-context-engineering/04-terminal-tool.md) | Agent 怎样按需读文件而不越权？ | 教学骨架 |
| 05 | [项目：长程代码库维护助手](stage2-context-engineering/05-codebase-maintainer.md) | 三天工作流怎样保持连续？ | 综合设计 |
| 06 | [总结、练习与实现缺口](stage2-context-engineering/06-review.md) | 进入实现前还必须补齐什么？ | 验收清单 |

当前仓库没有 ContextBuilder、NoteTool、TerminalTool 或 memory OS 运行项目。阶段二代码用于解释机制与设计实验，不代表这些 API 已经存在。
