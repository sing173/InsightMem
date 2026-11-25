# 07 总结、练习与实现缺口

> 上一章：[06 项目：智能文档问答助手](06-document-qa-assistant.md) · 返回：[教程入口](../README.md)
> 对应 Hello Agents 第 8 章的 8.5：本章总结与展望、习题。

## 阶段一你已经完成什么

你现在应该能把 Agent Memory 当成一个可检查的系统，而不是一句“它有记忆”：

```text
输入/经验
  → 编码
  → 保存
  → 检索
  → 注入
  → 使用
  → 更新/遗忘/审计
```

同时应该能把 RAG 当成一条流水线：

```text
文档
  → 加载/切分
  → 索引
  → 召回
  → 融合/选择
  → 注入
  → reader
  → 评测
```

## 核心概念清单

| 概念 | 一句话解释 | 本仓库对应 |
|---|---|---|
| Memory | 从经验获得、跨会话保留、可重新读取的外部知识 | email-agent 三类记忆 |
| RAG | 检索外部知识并注入上下文以增强回答 | InsightMem Add/Search |
| Working memory | 当前决策周期中的活跃状态 | Agent state、当前草稿 |
| Episodic memory | 过去发生过什么 | examples namespace |
| Semantic memory | 知道什么事实、偏好、关系 | facts/signature |
| Perceptual memory | 文本、图像、音频等感知信息 | 尚未实现 |
| Procedural memory | 怎样做事的规则与指令，属于本仓库扩展类型 | instructions/rules |
| MemoryManager | 管理类型、重要性、容量、整合与遗忘 | 尚未实现 |
| Consolidation | 把零散经验整理成更稳定的记忆 | 教学骨架 |
| Forgetting | 按重要性、时间或容量移除低价值记忆 | 尚未实现 |
| Hybrid retrieval | 用不同召回腿互补 | BM25 + dense + RRF |
| Evidence selection | 从候选形成有限、可解释的上下文 | bundle/dedup/select |
| Scope | 谁可以读写哪些数据 | namespace + user_id |

## 本仓库实现状态

| 能力 | 状态 | 证据 |
|---|---|---|
| 无记忆 baseline | 可运行 | `01-baseline.ipynb` |
| Semantic / episodic / procedural memory | 可运行 | 02/03 Notebook、`memory.py` |
| 用户隔离 | 可运行 | `test_email_memory.py` |
| Add/Search 原子写入与幂等 | 可运行 | InsightMem Quickstart、`test_lab.py` |
| BM25 + code BM25 + exact dense | 可运行 | `CodingMemoryService.search` |
| RRF、bundle、span 去重、确定性选择 | 可运行 | `evidence.py`、`selection.py` |
| MemoryManager | 教学骨架 | 第 03 章 |
| 重要性/时间/容量遗忘 | 教学骨架 | 第 03 章 |
| 多模态感知记忆 | 未实现 | 第 03 章扩展设计 |
| Cross-encoder / 图检索 / 双时间 | 未实现 | 第 05 章扩展设计 |
| 文档 QA reader | 教学骨架 | 第 06 章 |
| 阶段二上下文工程 | 待写 | 后续对照 Hello Agents 第 9 章 |

## 练习

### 练习 1：证明一条记忆确实被使用

选择 `docs-question`，分别运行 baseline 与 semantic：

1. 保存两组 `used_memory`；
2. 对比最终回复；
3. 写一句结论：哪一组证据证明 semantic memory 被使用，而不是只被保存。

### 练习 2：设计一次遗忘实验

构造 20 条记忆，其中：

- 5 条重要；
- 5 条过期；
- 10 条低价值。

分别设计：

- 重要性遗忘；
- 时间遗忘；
- 容量遗忘。

记录每条策略删除什么、保留什么、可能误删什么。当前仓库没有实现 MemoryManager，这一步只提交设计，不声称已运行。

### 练习 3：解释三路召回互补

对同一 query 保存：

- raw BM25 排名；
- code BM25 排名；
- dense 排名；
- fused 排名；
- 最终 selected IDs。

找出一个“某腿单独失败、融合后成功”的案例，并说明原因。

### 练习 4：做一次 oracle reader 对照

给固定 reader 两种输入：

1. 系统 hits；
2. gold evidence。

如果 oracle 好而系统差，把问题归因到检索/选择；如果两者都差，检查 reader 或任务定义。

### 练习 5：审计一个真实工具

按四层结构记录：

- Transcripts；
- Memory notes；
- Representations；
- Injected context。

标出证据等级，并写一句“最薄弱层 → 具体失败”的结论。

## 进入阶段二前要补齐什么

阶段一主要解决“记忆与检索作为数据系统怎样做对”。阶段二会继续追问：

- 有限上下文里到底放什么；
- 谁决定检索、摘要和换入换出；
- 怎样记录任务状态与阻塞点；
- 怎样进行结构化笔记和文件系统探索；
- 长程任务如何跨天保持连续。

这些内容对应 Hello Agents 第 9 章的 ContextBuilder、GSSC、NoteTool、TerminalTool 和长程智能体实战，已在 [阶段二：什么是上下文工程](../stage2-context-engineering/00-context-engineering.md) 中展开。

## 参考文献与延伸阅读

- [Hello Agents 第 8 章：记忆与检索](https://hello-agents.datawhale.cc/#/./chapter8/%E7%AC%AC%E5%85%AB%E7%AB%A0%20%E8%AE%B0%E5%BF%86%E4%B8%8E%E6%A3%80%E7%B4%A2)
- [Hello Agents 仓库](https://github.com/datawhalechina/hello-agents)
- [InsightMem 机制审计](../../../wiki/insightmem.md)
- [InsightMem 三路检索与证据选择](../../../wiki/insightmem-retrieval.md)
- [Agent Memory 概念地图](../../../wiki/agent-memory.md)
- 论文与框架精读见 [旧版教程备份：精读清单](../../agent-memory-tutorial/reading-list.md)。

## 下一步

阶段一结束后，先整理你的实验产物：

```text
baseline + 三类记忆对照
Add/Search Quickstart
三路召回消融设计
文档 QA 架构与失败归因
真实工具审计表
```

然后进入 [阶段二：什么是上下文工程](../stage2-context-engineering/00-context-engineering.md)。不要把阶段一的高 Recall 直接当成最终答案质量，也不要把 TerminalTool 的白名单当成安全保证。
