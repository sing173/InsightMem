# 03 现代系统：Mem0、Zep、MemOS、MemoryOS、A-MEM

> 配套：[论文精读索引](README.md) · [学习路线](../../learning/agent-memory-tutorial/README.md)
> 这一卷看五种不同的“记忆组织方式”：抽取、时序图、两种记忆 OS、链接网络。

---

<a id="mem0"></a>
## Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory

**作者**：Prateek Chhikara, Dev Khant, Saket Aryan, Taranjeet Singh, Deshraj Yadav
**时间**：2025（arXiv:2504.19413v1）
**一句话**：把对话中的显著信息抽取、整合、检索成可扩展的长期记忆，并给出图记忆变体。

### 摘要（译文）

LLM 能生成连贯回复，但固定上下文窗口使多会话对话的一致性成为根本挑战。作者提出 **Mem0**：一种以记忆为中心的可扩展架构，通过动态抽取、整合和检索对话中的显著信息来解决该问题。在此基础上，作者进一步提出增强变体，利用**基于图的记忆表示**捕捉对话元素之间的复杂关系结构。作者在 LOCOMO benchmark 上与六类基线系统比较：现有记忆增强系统、不同 chunk 大小和 k 值的 RAG、处理完整对话历史的全上下文方法、开源记忆方案、专有模型系统、专用记忆管理平台。结果显示，Mem0 在单跳、时间、多跳、开放域四类问题上一致优于现有记忆系统；在 LLM-as-a-Judge 指标上相对 OpenAI 提升 26%，图记忆版本比基础配置总体高约 2%。除准确率外，Mem0 还显著降低计算开销：相比全上下文方法，p95 延迟低 91%，token 成本节省超过 90%。

### 核心设计

- **抽取（extraction）**：用 LLM 从对话中抽取值得长期保留的事实/偏好；
- **整合（consolidation）**：把新信息与已有记忆合并。论文版包含更新/删除逻辑；2026 年 README 的新算法改为**单次 ADD-only 抽取**，不覆盖旧记忆；
- **检索（retrieval）**：语义 + BM25 + 实体匹配多信号融合，并支持时间推理；
- **图记忆变体**：把实体和关系存成图，用于多跳和关系型问题。

### 实验与结论

LOCOMO 四类问题；论文自报：相对 OpenAI 的 LLM-as-a-Judge 提升 26%，图版本总体再高约 2%，p95 延迟降低 91%，token 节省 >90%（对比全上下文）。

### 局限

- 抽取质量依赖 LLM；抽取错误会固化进记忆；
- 论文数字来自作者自己的 harness，且云版与开源版可能不是同一算法；
- 图变体增加抽取和存储成本；
- 2026 年算法已变化，读论文时要对照当前 README。

### 为什么读

它是“LLM 抽取 + 多信号检索”的生产级代表。读它重点看：抽取什么、怎么整合、检索怎么融合，以及它如何用 token/延迟论证比全上下文更划算。

### 与教程对应

[02 写入](../../learning/agent-memory-tutorial/02-writing.md) · [04 召回](../../learning/agent-memory-tutorial/04-retrieval.md) · [05 融合](../../learning/agent-memory-tutorial/05-fusion.md)

---

<a id="zep"></a>
## Zep: A Temporal Knowledge Graph Architecture for Agent Memory

**作者**：Preston Rasmussen, Pavlo Paliychuk, Travis Beauvais, Jack Ryan, Daniel Chalef
**时间**：2025（arXiv:2501.13956v1，CC BY-NC-SA）
**一句话**：用带时间维度的知识图谱（Graphiti）组织对话和业务数据，事实会失效但历史保留。

### 摘要（译文）

作者提出 **Zep**：一种新的 AI agent 记忆层服务，在 Deep Memory Retrieval（DMR）benchmark 上优于当前最先进的 MemGPT；并在比 DMR 更全面、更接近真实企业用例的评测中表现优异。现有面向 LLM agent 的 RAG 框架局限于静态文档检索，而企业应用需要动态整合来自持续对话和业务数据等多种来源的知识。Zep 通过核心组件 **Graphiti** 解决这一限制：一个时序感知的知识图谱引擎，能动态综合非结构化对话数据和结构化业务数据，同时维护历史关系。在 MemGPT 团队建立的主要评测指标 DMR 上，Zep 达到 94.8%，MemGPT 为 93.4%。在更具挑战性的 LongMemEval 上，Zep 取得最高 18.5% 的准确率提升，同时相比基线实现降低 90% 的响应延迟。

### 核心设计

- **Episode**：原始输入（消息、文档、事件）作为可追溯的来源；
- **Entity / Fact / Edge**：从 episode 抽取实体、关系和事实；
- **双时间（bi-temporal）**：事实有生效时间（valid time）和写入时间（ingest time）；新事实使旧事实失效，但不删除历史；
- **混合检索**：语义 + 关键词 + 图遍历，支持时间过滤；
- **Graphiti**：开源图引擎；Zep 在其上提供企业级治理和服务。

### 实验与结论

DMR：Zep 94.8% vs MemGPT 93.4%；LongMemEval：最高 18.5% 准确率提升，90% 延迟降低（论文自报）。

### 局限

- 依赖图数据库、LLM 抽取和 embedding，运维复杂；
- 抽取和失效判断可能出错，错误会进入图；
- 论文许可是 CC BY-NC-SA，复用需注意非商业和相同方式共享；
- 与静态 RAG 的对比公平性依赖具体实现。

### 为什么读

如果你要处理“事实会变”的记忆，Zep 的双时间失效是目前最完整的工程答案。读它重点看：episode 如何溯源、事实如何失效、混合检索如何组合。

### 与教程对应

[03 存储](../../learning/agent-memory-tutorial/03-storage.md) · [06 更新与治理](../../learning/agent-memory-tutorial/06-governance.md)

---

<a id="memos"></a>
## MemOS: A Memory OS for AI System

**作者**：Zhiyu Li 等（MemTensor 团队，作者列表较长）
**时间**：2025（arXiv:2507.03724v4，CC BY）
**一句话**：把记忆当成操作系统资源，用 MemCube 统一明文、激活和参数三种记忆的表示、调度与演化。

### 摘要（译文）

LLM 已成为通用人工智能的重要基础设施，但缺乏明确的记忆管理系统，阻碍了长上下文推理、持续个性化和知识一致性。现有模型主要依赖静态参数和短命上下文状态，难以长期跟踪用户偏好或更新知识。RAG 用明文引入外部知识，但仍是无状态的权宜之计，没有生命周期控制，也没有与持久表示集成。近期工作从记忆层次视角建模 LLM 的训练和推理成本，表明在参数记忆和外部检索之间引入显式记忆层，可以通过外化特定知识显著降低成本。除计算效率外，LLM 还面临信息在时间和上下文上分布方式带来的更广泛挑战，需要能管理跨不同时间尺度和来源的异构知识的系统。为此，作者提出 **MemOS**：一个把记忆视为可管理系统资源的记忆操作系统，统一明文、基于激活和参数级记忆的表示、调度与演化，实现高性价比的存储和检索。基本单元 **MemCube** 封装记忆内容以及来源、版本等元数据；MemCube 可以随时间组合、迁移和融合，支持记忆类型之间的灵活转换，并连接检索与基于参数的学习。MemOS 建立了以记忆为中心的系统框架，为 LLM 带来可控性、可塑性和可演化性。

### 核心设计

- **MemCube**：记忆的基本封装，包含内容 + 元数据（来源、版本等）；
- **三种记忆**：明文记忆、激活记忆、参数记忆；可以在类型之间转换；
- **调度与演化**：MemScheduler 管理异步写入、生命周期和更新；
- **组合/迁移/融合**：不同 cube 可以组合成更大记忆，也可以跨用户/任务迁移；
- **目标**：把检索和参数学习连接起来，支持持续学习。

### 实验与结论

论文提出系统框架和能力主张；具体 benchmark 数字见原文和 MemOS 仓库的后续报告。不要把仓库 README 的自报分数当作论文结论。

### 局限

- 系统复杂：自托管需要 Neo4j + Qdrant 等基础设施；
- 参数级记忆涉及微调，成本和风险高；
- 概念先进，但工程落地和长期稳定性仍需验证。

### 为什么读

它提供了“记忆不只是检索，还包括调度、生命周期和参数化”的更大视角。读它重点看 MemCube 的抽象和三类记忆的转换，而不是具体部署细节。

### 与教程对应

[03 存储](../../learning/agent-memory-tutorial/03-storage.md) · [06 更新与治理](../../learning/agent-memory-tutorial/06-governance.md)

---

<a id="memoryos"></a>
## MemoryOS: Memory OS of AI Agent

**作者**：Jiazheng Kang, Mingming Ji, Zhe Zhao, Ting Bai
**时间**：2025（arXiv:2506.06326v1）
**一句话**：借鉴操作系统的存储管理，用“短期—中期—长期人格”三层记忆和分段分页机制管理长对话。

### 摘要（译文）

LLM 的固定上下文窗口使其难以维持长期对话的一致性和用户个性化。作者提出 **MemoryOS**，将记忆管理建模为一套包含 **Memory Storage、Memory Updating、Memory Retrieval、Response Generation** 四个模块的系统。存储层分为短期记忆（STM）、中期记忆（MTM）和长期人格记忆（LPM）：STM 保存近期对话，MTM 按主题分段保存对话页，LPM 保存用户与 agent 的稳定属性和动态特征。短期到中期的迁移采用基于对话链的 FIFO；中期到长期的迁移采用分段分页和基于热度的替换策略。检索时分别获取近期上下文、相关主题中的对话页以及人格信息，再统一构造提示词。论文在 LoCoMo 和 GVD 数据集上验证了其长对话问答与个性化能力。

### 核心设计

- **三层存储**：
  - **STM（Short-Term Memory）**：以对话页保存用户问题、模型回复和时间戳，并用 LLM 判断相邻对话页是否属于同一对话链；实验配置中队列长度为 7；
  - **MTM（Mid-Term Memory）**：把同主题对话页组织成 segment，segment 再细分为 dialogue page，形成“分段 + 分页”结构；主题匹配结合语义相似度和关键词 Jaccard 相似度；
  - **LPM（Long-term Persona Memory）**：保存 User Profile、User KB、User Traits，以及 Agent Profile、Agent Traits；既保留固定属性，也动态更新事实、兴趣、习惯和交互中形成的特征。
- **热度驱动的更新**：MTM 的 segment 热度由检索次数、对话页数量和时间衰减共同决定。容量超限时淘汰低热度 segment；热度超过阈值的 segment 被归档到 LPM，并用于更新用户知识、用户特征和 agent 特征。
- **分层迁移**：STM 队列满时，最旧对话页按 FIFO 进入 MTM；MTM 与 LPM 之间则不是简单先进先出，而是按热度归档，并重置已迁移 segment 的交互计数。
- **两阶段检索**：STM 返回近期对话；MTM 先选相关 segment，再从选中 segment 内检索相关 dialogue page；LPM 检索 User KB 和 Agent Traits，并注入完整的 profile 与 traits。
- **统一生成**：把 STM、MTM、LPM 的检索结果与当前问题组合成最终提示词，同时利用近期上下文、历史细节和人格信息。

### 实验与结论

实验使用 LoCoMo 与 GVD 两个长对话数据集。论文报告，在 LoCoMo 上使用 GPT-4o-mini 时，MemoryOS 相对基线的 F1 平均提升 **49.11%**，BLEU-1 平均提升 **46.18%**。效率实验中，MemoryOS 的检索 token 消耗为 **3,874**，低于 MemGPT 的 **16,977**；平均 LLM 调用次数为 **4.9**，低于同环境复现的 A-Mem 的 **13.0**。消融实验显示，MTM 对结果影响最大，其次是 LPM，对话链的贡献相对较小。以上均为论文自报结果。

### 局限

- 热度依赖检索次数、交互长度和衰减参数，需要可靠的访问记录；阈值与容量也需要按场景调优。
- 对话链、主题分段和人格更新都依赖 LLM 判断，错误可能在归档和更新过程中累积。
- 固定长度的 STM、MTM 和人格队列意味着容量与记忆完整性之间需要权衡。
- 实验主要集中在长对话问答；跨任务知识、程序性记忆和长期运行稳定性仍缺少充分验证。

### 为什么读

它把“记忆如何存、如何迁移、如何检索、如何进入回答”串成了一套完整流程，适合研究长对话中的分层记忆。阅读时重点看：对话链如何维持上下文，segment/page 如何避免主题混杂，以及热度如何决定保留、淘汰和归档。

**注意不要与 MemOS 混淆**：MemoryOS 的核心是 STM/MTM/LPM 三层对话记忆、分段分页和人格更新；MemOS 的核心是 MemCube 与明文、激活、参数三类记忆。两者都借用“OS”概念，但记忆单元、管理目标和实现机制不同。

### 与教程对应

[03 存储](../../learning/agent-memory-tutorial/03-storage.md) · [04 召回](../../learning/agent-memory-tutorial/04-retrieval.md) · [06 更新与治理](../../learning/agent-memory-tutorial/06-governance.md)

---

<a id="a-mem"></a>
## A-MEM: Agentic Memory for LLM Agents

**作者**：Wujiang Xu, Zujie Liang, Kai Mei, Hang Gao, Juntao Tan, Yongfeng Zhang
**时间**：2025（arXiv:2502.12110v11）
**一句话**：用 Zettelkasten 卡片盒方法，把记忆做成会互相链接、会随新记忆演化的笔记网络。

### 摘要（译文）

LLM agent 可以用外部工具完成复杂任务，但需要记忆系统来利用历史经验。现有记忆系统能基本存储和检索，却缺乏复杂的记忆组织；尽管近期尝试引入图数据库，其固定操作和结构仍限制了跨任务适应性。为此，本文提出一种新的 agentic memory 系统，能够以 agent 的方式动态组织记忆。遵循 Zettelkasten 方法的基本原则，系统通过动态索引和链接创建互联的知识网络。添加新记忆时，系统生成一条包含多个结构化属性的综合笔记，包括上下文描述、关键词和标签；然后分析历史记忆，识别相关连接，在有意义的相似性处建立链接。这个过程还支持**记忆演化**：新记忆整合时，可以触发对已有历史记忆的上下文表示和属性的更新，使记忆网络不断细化理解。该方法结合了 Zettelkasten 的结构化组织原则和 agent 驱动决策的灵活性，实现更自适应、上下文感知的记忆管理。作者在六个基础模型上做了实验，相比现有 SOTA 基线有显著提升。

### 核心设计

- **结构化笔记**：每条记忆不是裸文本，而是带上下文描述、关键词、标签的笔记；
- **动态链接**：新笔记与历史笔记做相似性分析，建立有意义的连接；
- **记忆演化**：新记忆可以更新旧记忆的上下文和属性，而不是只追加；
- **Zettelkasten**：用卡片盒式网络组织知识，支持遍历和关联检索。

### 实验与结论

六个基础模型上的实证实验，论文自报优于现有 SOTA 基线；具体数字见原文。

### 局限

- 链接和演化依赖 LLM 判断，可能引入错误连接；
- 记忆网络增长后，遍历和维护成本上升；
- 评测范围和任务类型有限，通用性需验证。

### 为什么读

它代表“记忆不是列表，而是网络”的思路。读它重点看：一条记忆包含哪些属性、链接怎么建立、演化如何避免污染旧记忆。

### 与教程对应

[02 写入](../../learning/agent-memory-tutorial/02-writing.md) · [05 融合](../../learning/agent-memory-tutorial/05-fusion.md) · [06 更新与治理](../../learning/agent-memory-tutorial/06-governance.md)

---

## 五种系统怎么选

| 系统 | 记忆单元 | 写入 | 更新 | 适合 |
|---|---|---|---|---|
| Mem0 | 抽取后的记忆 + 实体 | LLM 抽取 | 论文版可更新；新版 ADD-only | 个性化助手、生产 API |
| Zep / Graphiti | episode + 实体/事实 | LLM 抽取入图 | 双时间失效，保留历史 | 企业知识、时间推理 |
| MemOS | MemCube（明文/激活/参数） | 调度器异步 | 组合/迁移/融合 | 记忆 OS、持续学习研究 |
| MemoryOS | 对话页 + 主题 segment + 人格 | STM FIFO；按热度归档 | 分段分页、热度淘汰与归档 | 长对话、用户画像与个性化 |
| A-MEM | 结构化笔记 + 链接 | LLM 生成笔记 | 记忆演化 | 知识网络、关联检索 |

下一步：[04 检索与评测](04-retrieval-eval.md)。