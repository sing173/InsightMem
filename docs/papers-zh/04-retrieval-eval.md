# 04 检索与评测：HippoRAG、GraphRAG、LongMemEval、LoCoMo

> 配套：[论文精读索引](README.md) · [学习路线](../../learning/agent-memory-tutorial/README.md)
> 这一卷看两类问题：多跳检索怎么做，长期记忆怎么评。

---

<a id="hipporag"></a>
## HippoRAG: Neurobiologically Inspired Long-Term Memory for Large Language Models

**作者**：Bernal Jiménez Gutiérrez, Yiheng Shu, Yu Gu, Michihiro Yasunaga, Yu Su
**时间**：2024（arXiv:2405.14831v3）
**一句话**：借海马索引理论，把 LLM、知识图谱和个性化 PageRank 组合起来，做便宜又快的多跳检索。

### 摘要（译文）

为了在恶劣、多变的环境中生存，哺乳动物大脑进化出存储大量世界知识、持续整合新信息并避免灾难性遗忘的能力。尽管 LLM 取得了 impressive 的成就，即使有 RAG，它们仍难以在预训练后高效、有效地整合大量新经验。本文提出 **HippoRAG**：一种受人类长期记忆的海马索引理论启发的检索框架，用于在新经验上实现更深、更高效的知识整合。HippoRAG 协同编排 LLM、知识图谱和个性化 PageRank 算法，模拟人类记忆中皮层和海马的不同角色。作者在多跳问答上与现有 RAG 方法比较，结果显示最高提升 20%；HippoRAG 的单步检索达到与 IRCoT 等迭代检索相当或更好的性能，同时便宜 10–30 倍、快 6–13 倍；把 HippoRAG 集成到 IRCoT 还能带来进一步提升。最后，作者展示了该方法能处理现有方法无法触及的新场景。

### 核心设计

- **知识图谱**：从文档抽取实体和关系，构建图；
- **个性化 PageRank（PPR）**：从查询实体出发，在图上传播相关性，找到多跳邻居；
- **海马/皮层类比**：LLM 负责语义处理，图 + PPR 负责索引和关联召回；
- **单步检索**：一次图传播替代多轮迭代检索。

### 实验与结论

多跳 QA 上最高提升 20%；相比 IRCoT 便宜 10–30 倍、快 6–13 倍；与 IRCoT 结合还能进一步提升（论文自报）。

### 局限

- 图构建依赖实体/关系抽取，抽取错误会传播；
- 图更新和维护有成本；
- 主要在静态文档语料上验证，动态对话记忆的适用性需进一步研究。

### 为什么读

如果你的查询需要“A 通过 B 关联到 C”，单靠向量和词法不够，HippoRAG 展示了图 + PPR 的性价比。读它重点看：图怎么建、PPR 怎么用、为什么能替代多轮检索。

### 与教程对应

[04 召回](../../learning/agent-memory-tutorial/04-retrieval.md) · [05 融合](../../learning/agent-memory-tutorial/05-fusion.md)

---

<a id="graphrag"></a>
## From Local to Global: A Graph RAG Approach to Query-Focused Summarization

**作者**：Darren Edge, Ha Trinh, Newman Cheng, Joshua Bradley, Alex Chao, Apurva Mody, Steven Truitt, Dasha Metropolitansky, Robert Osazuwa Ness, Jonathan Larson
**时间**：2024（arXiv:2404.16130v2，CC BY）
**一句话**：用实体知识图谱 + 社区摘要回答“整个语料的主题是什么”这类全局问题。

### 摘要（译文）

用 RAG 从外部知识源检索相关信息，可以让 LLM 回答私有或未见文档集合上的问题。但 RAG 在面向整个文本语料的全局问题上会失败，例如“这个数据集的主要主题是什么？”——这本质上是查询聚焦摘要（QFS）任务，而不是显式检索任务。此前的 QFS 方法又无法扩展到典型 RAG 系统索引的文本量。为结合两类方法的优势，作者提出 **GraphRAG**：一种基于图的私有文本语料问答方法，能随用户问题的通用性和源文本数量扩展。该方法用 LLM 分两阶段构建图索引：先从源文档派生实体知识图谱，再为紧密相关实体组预生成社区摘要。给定问题时，每个社区摘要生成部分回答，再把所有部分回答汇总成最终回答。在 100 万 token 规模数据集的全局 sensemaking 问题上，GraphRAG 在答案的全面性和多样性上显著优于传统 RAG 基线。

### 核心设计

- **实体知识图谱**：LLM 抽取实体和关系；
- **社区检测与摘要**：把紧密相关实体分组，预生成社区摘要；
- **查询时 map-reduce**：每个社区摘要生成部分回答，最后汇总；
- **面向全局问题**：不是找某一段，而是覆盖整个语料的主题和关系。

### 实验与结论

100 万 token 规模；在全面性和多样性上优于传统 RAG（论文自报）。具体评分口径见原文。

### 局限

- 索引阶段 LLM 成本高，构建慢；
- 面向静态语料，不处理时间失效和对话更新；
- 对局部事实问题不一定优于普通 RAG；
- 社区摘要可能丢失细节或引入概括错误。

### 为什么读

它和 Zep/Graphiti 形成对照：GraphRAG 是“静态语料的全局理解”，Graphiti 是“动态对话的时序事实”。读它重点看社区摘要和 map-reduce 查询，而不是把它当通用记忆系统。

### 与教程对应

[03 存储](../../learning/agent-memory-tutorial/03-storage.md) · [04 召回](../../learning/agent-memory-tutorial/04-retrieval.md)

---

<a id="longmemeval"></a>
## LongMemEval: Benchmarking Chat Assistants on Long-Term Interactive Memory

**作者**：Di Wu, Hongwei Wang, Wenhao Yu, Yuwei Zhang, Kai-Wei Chang, Dong Yu
**时间**：2024（arXiv:2410.10813v2，CC BY）
**一句话**：用 500 道题系统评测聊天助手的五种长期记忆能力，并把记忆设计拆成索引、检索、阅读三段。

### 摘要（译文）

近期 LLM 驱动的聊天助手集成了记忆组件来跟踪用户-助手聊天历史，从而提供更准确、个性化的回复。但它们在持续交互中的长期记忆能力仍未充分探索。作者提出 **LongMemEval**：一个综合 benchmark，评测聊天助手的五种核心长期记忆能力：**信息抽取、多会话推理、时间推理、知识更新、弃答（abstention）**。500 道精心策划的问题嵌入可自由扩展的用户-助手聊天历史中，对现有长期记忆系统构成重大挑战：商业聊天助手和长上下文 LLM 在跨持续交互记忆信息时准确率下降 30%。作者提出一个统一框架，把长期记忆设计拆成三个阶段：**索引、检索、阅读**；基于关键实验洞见提出若干记忆设计优化，包括会话分解以提升价值粒度、事实增强的键扩展用于索引、时间感知的查询扩展用于细化搜索范围。大量实验表明，这些优化显著提升 LongMemEval 上的记忆召回和下游问答。作者公开了 benchmark 和代码。

### 五种能力

| 能力 | 考什么 |
|---|---|
| 信息抽取 | 从长历史中找到具体事实 |
| 多会话推理 | 跨多个会话组合信息 |
| 时间推理 | 事件顺序、时间点、时间跨度 |
| 知识更新 | 用户信息变化后取新值 |
| 弃答 | 没有答案时不要编 |

### 核心设计

- **可扩展历史**：问题嵌入不同长度的聊天历史；
- **三阶段框架**：索引 → 检索 → 阅读；
- **优化**：会话分解、事实增强键扩展、时间感知查询扩展。

### 实验与结论

500 题；商业助手和长上下文 LLM 在持续交互中准确率下降 30%（论文自报）。优化同时提升召回和下游 QA。

### 局限

- 是 benchmark，不是记忆系统；
- 题目和 answerer/prompt 会影响分数，跨论文比较要谨慎；
- 主要面向聊天助手，编码/多模态场景覆盖有限。

### 为什么读

如果你要搭自己的评测，LongMemEval 的五种能力和三阶段框架可以直接借用。读它重点看：问题怎么构造、哪些能力最容易掉分、三种优化为什么有效。

### 与教程对应

[07 评测](../../learning/agent-memory-tutorial/07-evaluation.md) · [评测手册](../../learning/agent-memory-tutorial/evaluation.md)

---

<a id="locomo"></a>
## Evaluating Very Long-Term Conversational Memory of LLM Agents（LoCoMo）

**作者**：Adyasha Maharana, Dong-Ho Lee, Sergey Tulyakov, Mohit Bansal, Francesco Barbieri, Yuwei Fang
**时间**：2024（arXiv:2402.17753v1，CC BY-NC-SA）
**一句话**：构造平均 300 轮、跨 35 个会话的超长期对话，评测 LLM 的长期记忆、时间因果和多模态理解。

### 摘要（译文）

现有长期开放域对话工作最多只评估 5 个会话内的回复。尽管长上下文 LLM 和 RAG 有进展，它们在超长期对话中的有效性仍未探索。为填补空白，作者提出一个机器-人类流水线：利用基于 LLM 的 agent 架构，把对话建立在人设和时间事件图上，生成高质量超长期对话；每个 agent 还能分享和回应图像。生成的对话经人工标注者验证和编辑，以保证长程一致性和对事件图的落地。用该流水线，作者收集了 **LoCoMo**：一个超长期对话数据集，每个平均 300 轮、9K token，跨最多 35 个会话。基于 LoCoMo，作者提出一个综合评测 benchmark，覆盖问答、事件摘要和多模态对话生成。实验表明，LLM 在理解长对话、长程时间和因果动态方面存在挑战；长上下文 LLM 或 RAG 能带来改进，但仍显著落后于人类。

### 数据与任务

- 平均 300 轮、9K token、最多 35 个会话；
- 人设 + 时间事件图 + 图像分享；
- 任务：问答、事件摘要、多模态对话生成；
- 人工验证长程一致性。

### 实验与结论

长上下文和 RAG 有提升，但仍低于人类；LLM 在长程时间/因果理解上明显吃力（论文自报）。

### 局限

- 对话是合成的，虽经人工验证，仍不等于真实用户分布；
- 主要是英文；
- 评测规模和任务类型有限；
- 论文许可是 CC BY-NC-SA。

### 为什么读

它是“超长期对话记忆”最常用的评测之一。读它重点看：数据怎么构造、问题类型、为什么长上下文仍然不够。

### 与教程对应

[07 评测](../../learning/agent-memory-tutorial/07-evaluation.md) · [评测手册](../../learning/agent-memory-tutorial/evaluation.md)

---

## 评测资源补充

| 资源 | 类型 | 看什么 | 注意 |
|---|---|---|---|
| BEAM | 超长上下文评测 | 百万到千万 token 规模 | 成本高，适合压力测试 |
| CAMBench Coding / AML | 编码记忆评测 | 150 个 SWE 任务 × relevant/noisy | 平台统一 answerer，单次 Full 有方差 |
| CL-Bench | 持续学习评测 | 记忆能否形成学习闭环 | 厂商研究环境 |
| VibeMemBench | 仓库级编码记忆 | 111 个仓库任务 | 2026 新基准，样本有限 |
| OmniMemEval | 多数据集统一评测 | 多指标横向比较 | 看 harness 细节和版本 |

---

## 本卷小结

| 论文 | 解决什么 | 关键机制 |
|---|---|---|
| HippoRAG | 多跳检索 | 知识图谱 + 个性化 PageRank |
| GraphRAG | 全局理解 | 实体图 + 社区摘要 |
| LongMemEval | 长期记忆评测 | 五种能力 + 索引/检索/阅读 |
| LoCoMo | 超长期对话评测 | 300 轮、35 会话、多模态 |

回到 [论文精读索引](README.md)，或继续 [学习路线](../../learning/agent-memory-tutorial/README.md)。