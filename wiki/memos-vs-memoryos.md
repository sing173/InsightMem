---
title: MemOS 与 MemoryOS 不要混淆
summary: MemOS 管理记忆资源与表示，MemoryOS 管理短中长期对话记忆、分页与人格。
status: source-reviewed
section: 框架
order: 32
updated: 2026-11-24
tags: [memos, memoryos, comparison, memory-os]
sources:
  - docs/papers-zh/03-systems.md
  - learning/agent-memory-tutorial/03-storage.md
---

# MemOS 与 MemoryOS 不要混淆

两者都使用“Memory OS”命名，但来自不同团队，解决不同问题。

## 对比

| 维度 | MemOS | MemoryOS |
|---|---|---|
| 论文 | *MemOS: A Memory OS for AI System* | *Memory OS of AI Agent* |
| 团队 | MemTensor | BAI-LAB / 北邮、腾讯 AI Lab 等作者 |
| 核心单元 | MemCube | dialogue page、topic segment、persona |
| 记忆层次 | 明文、激活、参数三类记忆 | STM、MTM、LPM 三层 |
| 写入 | MemScheduler 异步调度 | STM FIFO；MTM 按热度归档 |
| 更新 | 组合、迁移、融合 | 分段分页、热度淘汰、人格更新 |
| 检索 | 与记忆类型和调度关联 | STM + segment/page + LPM |
| 目标 | 记忆资源、表示与参数学习 | 长对话连贯性和用户个性化 |

## MemOS 的关键问题

MemOS 把记忆当作可管理系统资源，用 MemCube 封装内容和元数据，并在明文记忆、激活记忆、参数记忆之间转换。阅读重点是**表示、调度和演化**，见 [03-systems.md#memos](../docs/papers-zh/03-systems.md#memos)。

## MemoryOS 的关键问题

MemoryOS 借用操作系统的分段分页思想：

1. STM 保存近期对话页，队列满时按 FIFO 迁移到 MTM。
2. MTM 将同主题对话页组织成 segment。
3. segment 热度由检索次数、交互长度和时间衰减决定。
4. 低热度 segment 被淘汰，高热度 segment 归档到 LPM。
5. LPM 更新 User Profile、User KB、User Traits、Agent Profile 和 Agent Traits。
6. 检索先选 segment，再选 page，最后与人格信息一起生成回答。

阅读重点是**三层迁移、热度和人格维护**，见 [03-systems.md#memoryos](../docs/papers-zh/03-systems.md#memoryos)。

## 与 InsightMem 的关系

InsightMem 的 chunk、span 和 bundle 只是检索表示，不是 MemoryOS 的 STM/MTM/LPM，也不是 MemOS 的 MemCube。它没有热度、人格或调度机制。相关定位见 [[insightmem]] 和 [[memory-frameworks]]。

<!-- generated:backlinks:start -->
## 反向链接

- [[memory-frameworks|Agent Memory 框架机制对比]] — 从记忆单元、写入、更新、检索和上下文管理比较 InsightMem 与六类框架。
<!-- generated:backlinks:end -->
