---
title: MemGPT、Letta 与 MemFS
summary: MemGPT 用主外上下文和队列管理模拟 OS，Letta 将其产品化，MemFS 是新的文件式记忆形态。
status: source-reviewed
section: 框架
order: 31
updated: 2026-11-24
tags: [memgpt, letta, memfs, context-management]
sources:
  - docs/papers-zh/01-foundations.md
  - learning/agent-memory-tutorial/reading-list.md
---

# MemGPT、Letta 与 MemFS

## MemGPT 论文机制

MemGPT 把 LLM 当作一台由操作系统管理的虚拟机：

- **Main Context**：System Instructions、Working Context、FIFO Queue。
- **External Context**：Recall Storage、Archival Storage。
- **Queue Manager**：在上下文压力下警告、驱逐旧消息并递归摘要。
- **Function Executor**：执行记忆读写、检索和 function chaining。
- **事件与中断**：通过 yield/request control 管理执行节奏。

它的关键不是“有一个向量库”，而是**agent 主动管理自己的上下文与外部记忆**。详见 [01-foundations.md:21–130](../docs/papers-zh/01-foundations.md#L21)。

## Letta 的产品化

Letta 是 MemGPT 的直接产品化。旧 V1/archive 形态最接近论文：

- memory blocks；
- recall memory；
- archival memory；
- queue manager；
- agent 可调用的记忆函数。

## Letta Code 与 MemFS

当前 Letta Code 使用 **MemFS**：

- 记忆是 git 版本化的 Markdown 文件系统；
- 根目录中的文件常驻 system prompt；
- 子目录按需读取；
- 默认没有向量索引，可选 MemFS Search mod；
- 对话搜索是另一条路径；
- dreaming 可由后台 subagent 整理记忆。

MemFS 更接近 MemGPT 的 OS 哲学，但不是论文机制的完整复刻。

## 与 InsightMem 的区别

| 维度 | MemGPT / Letta | InsightMem |
|---|---|---|
| 当前上下文 | 系统主动分页、驱逐、摘要 | 不管理 |
| 外部记忆 | recall、archival 或 MemFS | 原始消息、chunk、向量 |
| 谁发起读写 | agent 的记忆函数 | 外部 harness 调用 Add/Search |
| 更新方式 | 可编辑记忆、摘要、版本化 | 正常路径只追加 |
| 输出 | agent 回复 | 证据列表 |

因此，InsightMem 可以借鉴 MemGPT 的“外部记忆”概念，但不能称为 MemGPT 式记忆操作系统。进一步对照见 [[memory-frameworks]]。

<!-- generated:backlinks:start -->
## 反向链接

- [[learning-path|用 InsightMem 学习 Agent Memory]] — 把 InsightMem 当作外部情景记忆与混合检索的可运行参考，再补齐抽取、更新和遗忘。
- [[memory-frameworks|Agent Memory 框架机制对比]] — 从记忆单元、写入、更新、检索和上下文管理比较 InsightMem 与六类框架。
<!-- generated:backlinks:end -->
