# Agent 记忆系统学习路线（2026）

> **旧版备份**：本目录保留 2026-11-25 前的教程内容，供历史参考和论文精读导航使用。新教程见 [Agent Memory 实战教程](../agent-memory-course/README.md)。

> 面向：有 Python 基础、用过 LLM API、想系统掌握 agent memory 的开发者。
> 主线：先学 **LangGraph 长时记忆工程**，再学 **LLM as Operating Systems / MemGPT–Letta**。
> 时长：8 周；通常每周 6–8 小时，Capstone 10–14 小时。4 周可速通，12 周可加读论文。
> 最终产出：一个带长期记忆的邮件 Agent + 一个可评测的 memory OS mini service + 架构/实验报告。
> 配套实验：`experiments/email-agent` 运行阶段一邮件 Agent，`experiments/insightmem` 运行确定性证据实验；阶段二 memory OS 尚未建立 Notebook 项目。
> 版本：2026-11-24。所有分数都标口径，不同 benchmark 的数字不要横比。

本教程不把“记忆”等同于向量库，也不把 MemGPT 的 OS 类比当成唯一架构。学习路线刻意分成两个阶段：

1. **阶段一：LangGraph 长时记忆工程**——先掌握语义、情景、程序三类记忆，以及 Store、namespace、检索、上下文装配、更新和评测。
2. **阶段二：LLM as Operating Systems**——再理解 core / archival / recall memory、memory pressure、paging、self-editing、dreaming 和多 Agent 共享记忆。

两个阶段共享同一套五个动作：**写入 → 组织 → 检索 → 使用 → 治理**。先能把记忆作为数据系统做对，再让 Agent 自主管理上下文。

---

## 本教程的写法

两门主课程都采用“先做出来，再解释为什么”的项目式教学。本教程保留这套节奏，同时补上论文机制、失败模式和工程边界：

1. **场景**：从一个真实任务出发，例如邮件 Agent 或研究 Agent；
2. **基线**：先写没有记忆的版本，观察失败；
3. **加机制**：每次只增加一种记忆或一个管理动作；
4. **看轨迹**：检查工具调用、检索结果、prompt 与状态变化；
5. **做检查**：用固定问题判断机制是否生效；
6. **再深化**：阅读论文与官方文档，解释收益、代价和边界。

因此，每章前面的“本章实战”是学习主线，后面的公式、源码分析和框架对比是参考资料。代码块分两类：**教学骨架**用于说明控制流和课程 API；**可运行 Notebook**用于在仓库里复现实验。稳定实现和回归测试放在各实验项目的 `src/` 与 `tests/`，Notebook 只负责设置、调用、展示和保存结果。

---

<a id="notebook-map"></a>

## 教程与 Notebook 对照

本教程、Notebook 和源码各承担一层职责：

- **教程**：解释概念、接口契约、失败模式和检查点；
- **Notebook**：提供可运行实验入口，适合 baseline、消融和报告；
- **`src/` + `tests/`**：保存稳定实现与回归验证，是代码事实来源。

项目入口：

- [email-agent](../../experiments/email-agent/README.md)：阶段一邮件 Agent，当前为离线 `LocalStore` + 确定性策略；
- [insightmem](../../experiments/insightmem/README.md)：Add/Search、三路召回与确定性选择实验；
- memory OS mini：阶段二计划项目，目前没有 Notebook。

| 教程内容 | Notebook | 稳定实现 | 当前覆盖与边界 |
|---|---|---|---|
| 01 无记忆基线 | [01-baseline](../../experiments/email-agent/notebooks/01-baseline.ipynb) | [agent.py](../../experiments/email-agent/src/email_memory_lab/agent.py) | 覆盖离线路由与失败记录；不含 LangGraph 图和真实工具 |
| 02 三类记忆 | [02-semantic](../../experiments/email-agent/notebooks/02-semantic-memory.ipynb)、[03-episodic/procedural](../../experiments/email-agent/notebooks/03-episodic-and-procedural.ipynb) | [memory.py](../../experiments/email-agent/src/email_memory_lab/memory.py)、[store.py](../../experiments/email-agent/src/email_memory_lab/store.py) | 覆盖三类记忆的离线行为；不含 LangMem 工具与 LLM prompt 更新 |
| 03 namespace 与存储 | 02/03 Notebook | [store.py](../../experiments/email-agent/src/email_memory_lab/store.py) | 覆盖 namespace 与 `put/get/search` 形态；不含 BM25、dense、ANN、Recall/Archival |
| 04 Agentic 检索 | 未实现 | 未实现 | 保留课程工具骨架，不能用现有 Notebook 替代 |
| 05 装配与 memory pressure | 未实现 | 未实现 | 保留 context builder 与 paging 机制说明 |
| 06 自编辑、dreaming、共享 | 未实现 | 未实现 | 属于阶段二治理能力 |
| 07 邮件 Agent 评测 | [04-evaluation](../../experiments/email-agent/notebooks/04-evaluation.ipynb) | [evaluation.py](../../experiments/email-agent/src/email_memory_lab/evaluation.py) | 覆盖 10 题离线对照；不含 LLM 成本、judge 与 paired bootstrap |
| 08 阶段一 M0–M4 | 01–04 Notebook | 上述实验包 | 部分覆盖；阶段二 memory OS 尚未实现 |

“未实现”表示当前仓库没有对应可运行项目，不表示该机制不重要。教程中的公式、双时间 SQL、删除链和 API 合同也不能用现有 Notebook 替代。

---

## 从哪开始

| 你的情况 | 建议路径 |
|---|---|
| 第一次系统学 | [00 定位与概念](00-orientation.md) → [01 边界](01-boundaries.md) → [阶段一](#阶段一langgraph-长时记忆工程) |
| 已做过 RAG/记忆项目 | 从 [02 写入](02-writing.md) 开始，再补 [01 边界](01-boundaries.md) |
| 想先跟着课程做项目 | [Long-Term Agentic Memory With LangGraph](https://www.deeplearning.ai/short-courses/long-term-agentic-memory-with-langgraph/) → 本教程阶段一 |
| 对 MemGPT/Letta 更感兴趣 | 先快速过阶段一，再进入 [阶段二](#阶段二llm-as-operating-systems) 与 [08 Capstone](08-capstone.md) |
| 只想做评测 | [07 评测](07-evaluation.md) + [评测手册](evaluation.md) + [实验 L7](labs.md#l7) |
| 只有四周 | 按下面的“4 周速通”合并章节 |

---

## 两阶段课程地图

### 阶段一：LangGraph 长时记忆工程

对应课程：[Long-Term Agentic Memory With LangGraph](https://www.deeplearning.ai/short-courses/long-term-agentic-memory-with-langgraph/)。

| 课程模块 | 本教程章节 | 学完能做什么 |
|---|---|---|
| Introduction to Agent Memory | [00 定位](00-orientation.md) · [01 边界](01-boundaries.md) | 区分工作上下文、checkpoint、短期与长期记忆 |
| Baseline Email Assistant | [01 边界](01-boundaries.md) · [04 召回](04-retrieval.md) | 画出无记忆邮件 Agent 的状态流 |
| Semantic Memory | [02 写入](02-writing.md) · [03 存储](03-storage.md) · [04 召回](04-retrieval.md) | 保存用户事实、偏好并跨 thread 检索 |
| Episodic Memory | [02 写入](02-writing.md) · [05 融合与选择](05-fusion.md) | 用历史交互 few-shot 改善分类与工具调用 |
| Procedural Memory | [02 写入](02-writing.md) · [05 融合与选择](05-fusion.md) · [06 治理](06-governance.md) | 把经验反馈变成可版本化指令 |
| Hot path / Background | [02 写入](02-writing.md) · [06 治理](06-governance.md) | 选择同步写入或后台整理，并处理失败恢复 |
| Evaluation | [07 评测](07-evaluation.md) | 固定数据、reader、prompt、预算并报告成本 |

阶段一的主项目是**带语义/情景/程序记忆的邮件 Agent**：能记住用户偏好、从历史邮件处理示例学习，并更新自己的写作与路由指令。

### 阶段二：LLM as Operating Systems

对应课程：[LLMs as Operating Systems: Agent Memory](https://www.deeplearning.ai/short-courses/llms-as-operating-systems-agent-memory/)。

| 课程模块 | 本教程章节 | 学完能做什么 |
|---|---|---|
| Editable Memory | [02 写入](02-writing.md) · [06 治理](06-governance.md) | 设计 Agent 可自编辑的 core memory |
| Understanding MemGPT | [01 边界](01-boundaries.md) · [03 存储](03-storage.md) | 解释主上下文、外部上下文与 OS 类比的边界 |
| Building Agents with Memory | [03 存储](03-storage.md) · [05 融合与选择](05-fusion.md) | 实现 recall / archival 存取与 memory pressure |
| Programming Agent Memory | [05 融合与选择](05-fusion.md) · [06 治理](06-governance.md) | 实现换入换出、递归摘要和自编辑策略 |
| Agentic RAG / External Memory | [03 存储](03-storage.md) · [04 召回](04-retrieval.md) | 把外部检索作为 Agent 可调用工具 |
| Multi-agent Orchestration | [06 治理](06-governance.md) · [08 Capstone](08-capstone.md) | 共享 memory blocks，并验证隔离与权限 |

阶段二的主项目是**memory OS mini service**：有限上下文作为工作区，外部存储作为档案，Agent 根据 memory pressure 主动换入换出，并能编辑、整理和共享记忆。

---

## 八周总表

| 周 | 阶段 | 主题 | 核心问题 | 产出 |
|---|---|---|---|---|
| 1 | 准备 + 阶段一 | 边界与地图 | 什么算记忆，checkpoint 与长期记忆差在哪 | 一页记忆地图 |
| 2 | 阶段一 | 写入 | 语义/情景/程序记忆分别写什么，何时写 | 三类记忆写入策略对比 |
| 3 | 阶段一 | 存储与索引 | Store、namespace、profile/collection 如何选 | 选型矩阵 |
| 4 | 阶段一 | 召回与使用 | 如何检索并装配进邮件 Agent 上下文 | 召回失败分析 + context builder |
| 5 | 阶段一 | 更新与治理 | hot path/background、冲突、删除与隔离 | 治理策略 |
| 6 | 阶段一 | 评测 | 如何证明记忆机制有效且成本可接受 | 邮件 Agent 评测报告 |
| 7 | 阶段二 | OS 记忆管理 | core/archival/recall、memory pressure、paging、self-editing | memory OS 设计图 |
| 8 | 阶段二 | dreaming、共享记忆与 Capstone | 如何整理、共享并评测自主记忆 | 可评测 memory OS mini service |

**4 周速通**：第 1+2 周合并，3+4 周合并，5+6 周合并，7+8 周合并。
**12 周深入**：前 8 周保持主线，每周加读 1 篇论文；后 4 周分别复现 LangGraph、MemGPT/Letta、一个图记忆系统和一个公开 benchmark。

---

## 章节索引

| # | 章节 | 阶段 | 核心问题 | 一周产出 |
|---|---|---|---|---|
| 00 | [定位与概念](00-orientation.md) | 准备 | 什么算记忆，什么不算 | 两阶段学习地图 |
| 01 | [边界与地图](01-boundaries.md) | 阶段一 + 二 | 上下文、短期、长期、权重、OS 类比怎么分 | 记忆审计 |
| 02 | [写入](02-writing.md) | 阶段一 + 二 | 语义/情景/程序记忆写什么，Agent 如何自编辑 | 三类写入策略对比 |
| 03 | [存储与索引](03-storage.md) | 阶段一 + 二 | Store、外部存储、MemFS、向量和图怎么选 | 选型矩阵 |
| 04 | [召回](04-retrieval.md) | 阶段一 + 二 | 词法、dense、recall、archival 各管什么 | 召回失败分析 |
| 05 | [融合与选择](05-fusion.md) | 阶段一 + 二 | 如何装配上下文，memory pressure 下换什么 | 选择与 paging 策略 |
| 06 | [更新与治理](06-governance.md) | 阶段一 + 二 | 冲突、 dreaming、共享、删除、隔离 | 治理策略 |
| 07 | [评测](07-evaluation.md) | 阶段一 | 数据集、baseline、成本、复现 | 评测报告 |
| 08 | [架构对比与 Capstone](08-capstone.md) | 阶段二 + 综合 | 为什么各家这样设计，如何做 memory OS | 可评测 mini memory |

配套文档：

- [实验项目总入口](../../experiments/README.md)：各实验项目的目录约定与 VS Code Notebook 用法；
- [八种记忆策略导读](strategy-overview.md)：用全量、窗口、过滤、摘要、向量、图谱、分层和类 OS 建立策略地图；
- [实验手册](labs.md)：L0–L8 的完整步骤、依赖、验收；
- [评测手册](evaluation.md)：数据集、指标、协议、陷阱；
- [精读清单](reading-list.md)：按主题分组的论文与文档；
- [社区资源](community.md)：两门主课程、Awesome 列表、官方教程；
- [常见误区](pitfalls.md)：高频错误；
- [附录](appendix.md)：结业自测、VS Code Notebook 环境、InsightMem 实验命令、参考资料。

---

## 每周节奏

每周固定四件事：

- **学课程**：完成对应模块的一个视频或代码示例；
- **读一手**：读 1 篇官方文档或论文的相关小节，不逐字硬啃；
- **画**：把该系统的写入/读取/更新/上下文装配画成一页图；
- **做**：跑一个对照实验，必须有 baseline、失败案例和成本数字；
- **写**：一页结论，包含数字、口径、失败案例。

阶段一切记：**先证明记忆作为数据系统能工作，再讨论 Agent 是否聪明。**
阶段二切记：**OS 类比是设计工具，不是声称 Agent 真的拥有虚拟内存、页表或硬件级隔离。**

---

## 目录结构

```text
agent-memory-tutorial/
├── README.md               # 两阶段入口与总表
├── 00-orientation.md       # 概念、地图、学习路线
├── 01-boundaries.md        # 边界：LangGraph + OS 两种视角
├── strategy-overview.md    # 八种策略导读
├── 02-writing.md           # 语义/情景/程序写入 + 自编辑
├── 03-storage.md           # Store/外部存储/MemFS/索引
├── 04-retrieval.md         # 召回：dense/lexical/recall/archival
├── 05-fusion.md            # 上下文装配 + memory pressure/paging
├── 06-governance.md        # 更新/dreaming/共享/删除
├── 07-evaluation.md        # 阶段一评测
├── 08-capstone.md          # 阶段二 + 综合项目
├── labs.md                 # L0–L8 实验手册
├── evaluation.md           # 评测手册
├── reading-list.md         # 精读清单
├── community.md            # 课程与社区资源
├── pitfalls.md             # 常见误区
└── appendix.md             # 自测、Notebook 环境、命令、参考资料
```

---

## 进度清单

### 阶段一：LangGraph 长时记忆工程

- [ ] 00 读完，能区分上下文、记忆、压缩、权重
- [ ] 01 完成记忆审计，能解释 checkpoint 与长期 Store 的边界
- [ ] 02 完成语义/情景/程序三类记忆写入对比
- [ ] 03 完成 Store namespace 与双索引对照
- [ ] 04 完成邮件 Agent 的召回失败分析
- [ ] 05 完成上下文装配、去重与预算实验
- [ ] 06 完成 hot path/background、矛盾序列与删除验证
- [ ] 07 完成带 baseline、成本和失败案例的评测报告

### 阶段二：LLM as Operating Systems

- [ ] 能画出 main context / external context 与 core / archival / recall 的映射
- [ ] 能实现一次 memory pressure 触发、换入换出或递归摘要
- [ ] 能实现 Agent 自编辑 core memory，并记录版本与审计
- [ ] 能实现后台 dreaming/consolidation，并验证不覆盖新人工纠正
- [ ] 能实现多 Agent 共享 memory block，并验证权限与隔离
- [ ] 08 完成可评测的 memory OS mini service

### 综合

- [ ] 读完精读清单里的至少 8 篇一手材料
- [ ] 能解释 LangGraph 路线与 MemGPT/Letta 路线的取舍
- [ ] 能报告至少一个失败模式和完整成本

---

## 来源标注约定

- 具名论文、课程、社区教程和文章首次出现时添加来源链接；同一资源重复出现时不必重复列条目。
- 有本地精读或全文翻译时优先链接本地文档，并标注“本地精读”或“中文译文”；没有时链接外部原文。
- 论文统一入口见 [精读清单](reading-list.md)，两门主课程与其他资源见 [社区资源](community.md)。
- 外部链接可能变化；引用分数、版本或商业限制时，仍须核对原文和访问日期。

---

## 约定

- 一手文档 > 论文 > 二手解读 > 短视频；二手材料只用来建立直觉，不引用其数字。
- 看到“某系统提升 X%”先问：baseline 是什么、answerer 是谁、数据集多大、是不是厂商自报。
- 每读一个框架，画一张“写入/读取/更新/上下文装配”图，比读十篇测评更有用。
