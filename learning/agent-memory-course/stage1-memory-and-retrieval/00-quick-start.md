# 00 快速开始：记忆与 RAG 是什么

> 上一章：[教程入口](../README.md) · 下一章：[01 记忆系统的工作流程](01-memory-workflow.md)
> 对应 Hello Agents 第 8 章的 8.1：从认知科学到智能体记忆、系统架构与快速体验。

## 本章你会得到什么

- 一个能亲眼观察的“失忆”baseline；
- 一次 InsightMem Add/Search 体验；
- 一张区分 Memory 与 RAG 的架构图；
- 后续所有实验都要回答的三个问题：**记什么、怎么取、怎样证明用上。**

## 先看一个具体问题

第一次对话：

```text
用户：以后回复邮件简短一点，签名写 John Doe。
Agent：好的，我记住了。
```

第二次对话，程序重启后：

```text
用户：回复 Alice 刚才的邮件。
Agent：生成一封通用邮件，没有 John Doe 签名。
```

Agent 并不是“忘了模型参数”，而是第二次请求没有拿到那条外部状态。人类记忆给我们的启发是：经验需要被编码、保存，并在合适的时候重新激活；智能体也要完成同样的闭环。

```text
经验/事件 → 编码 → 保存 → 检索 → 注入上下文 → 影响行动
```

如果只完成“保存”，没有完成“检索与注入”，记忆对本次回答仍然没有贡献。

## Memory 和 RAG 的关系

两者经常一起出现，但回答的问题不同：

| 维度 | Agent Memory | RAG |
|---|---|---|
| 主要问题 | Agent 过去学到了什么？ | 外部知识库中哪些内容能回答当前问题？ |
| 数据来源 | 对话、反馈、工具轨迹、用户偏好 | 文档、手册、网页、知识库 |
| 典型操作 | add/search/update/forget/consolidate | load/chunk/embed/index/retrieve/generate |
| 关键风险 | 错误固化、过时、串扰、遗忘不完整 | 检索不到、噪声、上下文过长、无依据回答 |
| 共同工程基础 | scope、索引、检索、排序、预算、可观测 | 同左 |

记忆系统可以把 RAG 当作检索基础设施，RAG 也可以检索记忆笔记。区别主要在**数据来源与生命周期**，不是“有没有向量数据库”。

## 一张系统架构图

```text
                         ┌──────────────────────┐
用户输入 ───────────────► │ Agent / Reader       │
                         │ 决策、工具调用、回答  │
                         └──────────┬───────────┘
                                    │
                 ┌──────────────────┴──────────────────┐
                 │                                     │
          ┌──────▼───────┐                     ┌──────▼───────┐
          │ Memory Tool  │                     │ RAG Tool      │
          │ 经验与偏好    │                     │ 外部知识       │
          └──────┬───────┘                     └──────┬───────┘
                 │                                     │
          ┌──────▼───────┐                     ┌──────▼───────┐
          │ MemoryManager│                     │ 文档处理/索引  │
          │ 类型/整合/遗忘│                     │ chunk/vector  │
          └──────┬───────┘                     └──────┬───────┘
                 │                                     │
          ┌──────▼───────┐                     ┌──────▼───────┐
          │ 记忆存储      │                     │ 知识存储       │
          └──────────────┘                     └──────────────┘
```

本仓库目前提供了两条可运行路径：

- `experiments/email-agent`：验证 Memory 的写入、类型和效果；
- `experiments/insightmem`：验证 RAG 式 Add/Search、混合召回与证据选择。

Hello Agents 第 8 章还包含 MemoryManager、Qdrant、Neo4j 和更完整的 RAG Tool；这些内容会在后续章节讲解，并明确标注本仓库的实现缺口。

## 快速体验 A：先看没有记忆的 Agent

打开 [01-baseline.ipynb](../../../experiments/email-agent/notebooks/01-baseline.ipynb)，运行全部单元格。

你会看到：

```text
Routing accuracy:          8/10
Writing compliance:        0/4
Required-memory recall:    0/6
```

不要只记分数，打开三个失败案例：

| 案例 | 现象 | 说明什么 |
|---|---|---|
| `docs-question` | 路由正确，但没有 John Doe 签名 | 动作正确不等于个性化正确 |
| `vendor-pricing` | 应忽略，却回复 | 没有利用过去相似经验 |
| `event-invite` | 应忽略，却回复 | 已知规则没有进入决策 |

**这次操作印证的核心思想：** baseline 是控制组。它把“固定策略本身的能力”和“记忆的贡献”分开；后面每加一种记忆，都要回答哪一类失败减少了。

结果保存在 `experiments/email-agent/runs/<run_id>/baseline-results.json`。

## 快速体验 B：再跑一次 Add/Search

打开 [InsightMem Quickstart](../../../experiments/insightmem/notebooks/00-quickstart.ipynb)。

Notebook 会完成：

1. 创建独立 SQLite 运行目录；
2. 写入样本消息；
3. 用相同 request 重放，验证幂等；
4. 搜索 parser 相关证据；
5. 用双用户哨兵验证隔离；
6. 保存 manifest 与原始 hits。

预期观察：

- Add 返回后，Search 立即可检索；
- 同一请求重放不会产生重复 source；
- 返回内容带 source 标签与稳定 ID；
- 用户 A 看不到用户 B 的独有哨兵。

**这次操作印证的核心思想：** RAG 式检索服务首先要保证写入原子、scope 隔离和证据可追溯，然后才谈检索质量。没有这些契约，Recall 再高也不可信。

## 把两次体验放在一起

| 观察 | Memory 路径 | RAG 路径 | 共同结论 |
|---|---|---|---|
| 输入 | 邮件处理经验、用户反馈 | 文档、消息、知识片段 | 都要明确 source 与 scope |
| 保存 | fact / example / rule | chunk / view / vector | 保存只是开始 |
| 检索 | 按用户与问题找记忆 | 按 query 找证据 | 都要控制候选与预算 |
| 使用 | 改变路由或回复 | 进入 reader 上下文 | 必须验证是否真正注入 |
| 失败 | 过时、错误固化、串扰 | 噪声、漏召回、无依据 | 都要保留失败轨迹 |

## 本章小结与下一步

你已经完成两个最小闭环：

- Memory：看到“没有记忆时哪里失败”；
- RAG：看到“Add 之后如何 Search，并验证隔离与溯源”。

下一章 [01 记忆系统的工作流程](01-memory-workflow.md) 会拆开 Memory 路径，回答一条信息从输入到再次使用，中间到底经过哪些步骤。
