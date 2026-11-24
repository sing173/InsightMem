---
title: Agent Memory 概念地图
summary: 用五个动作、四种记忆类型和四层知识结构理解 Agent Memory。
status: source-reviewed
section: 基础
order: 10
updated: 2026-11-24
tags: [agent-memory, concepts, taxonomy]
sources:
  - learning/agent-memory-tutorial/00-orientation.md
  - learning/agent-memory-tutorial/01-boundaries.md
  - learning/agent-memory-tutorial/02-writing.md
  - learning/agent-memory-tutorial/06-governance.md
  - docs/langchain-memory-zh.md
  - docs/papers-zh/02-surveys.md
---

# Agent Memory 概念地图

Agent Memory 是**跨会话保留、之后可以作为上下文重新读取的外部知识**。它不等于当前上下文，不等于压缩当前对话，也不等于训练模型权重。

## 五个动作

| 动作 | 要回答的问题 |
|---|---|
| 写入 | 记什么、何时记、保存原文还是提炼 |
| 组织 | 用什么记忆单元、索引和元数据 |
| 检索 | 如何召回、融合、去重并控制预算 |
| 使用 | 注入多少内容、以什么顺序、是否带来源 |
| 治理 | 如何隔离、纠错、过期、删除和审计 |

详细学习入口见 [00-orientation.md](../learning/agent-memory-tutorial/00-orientation.md)。

## 四种记忆类型

| 类型 | 内容 | 常见实现 |
|---|---|---|
| 工作记忆 / 短期记忆 | 当前会话状态 | checkpoint、当前上下文 |
| 情景记忆 | 发生过什么、原始事件和轨迹 | transcript、episode、执行日志 |
| 语义记忆 | 事实、偏好、关系 | 抽取事实、用户画像、知识图谱 |
| 程序记忆 | 怎么做 | 技能、规则、playbook、提示词 |

**semantic memory** 与 **semantic search** 不是一回事：前者指事实知识，后者只是用向量寻找相似内容。

## 四层外部知识结构

1. **Transcripts**：原始对话、工具调用和执行结果。
2. **Memory notes**：从经验中提炼的结论、经验和规则。
3. **Memory representations**：索引、wiki、交叉链接等导航结构。
4. **Injected context**：每次会话主动加载的少量高价值内容。

[[insightmem]] 目前主要实现第一层和第三层的检索部分；[[memory-frameworks]] 中的不同框架则覆盖不同层。

## 常见误区

- 有向量检索不代表有语义记忆。
- 保存全部历史不代表知道哪些事实已经过时。
- 返回很多片段不代表有效上下文。
- 能检索不代表能纠错、遗忘或维护跨页面一致性。

下一步可读 [[learning-path]]，或从 [[hybrid-retrieval]] 理解最常见的工程机制。

<!-- generated:backlinks:start -->
## 反向链接

- [[learning-path|用 InsightMem 学习 Agent Memory]] — 把 InsightMem 当作外部情景记忆与混合检索的可运行参考，再补齐抽取、更新和遗忘。
- [[schema|Wiki 维护约定]] — 说明源文档、Wiki 页面、frontmatter、生成索引与反向链接的维护方式。
<!-- generated:backlinks:end -->
