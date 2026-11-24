# 精读清单

> 配套：[八周路线](README.md)
> 原则：一手文档 > 论文 > 二手解读。每篇只精读方法、实验和失败案例。
> 论文已整理为中文精读版：[docs/papers-zh/README.md](../../docs/papers-zh/README.md)；CoALA 为全文翻译。

---

<a id="概念与综述"></a>
## 概念与综述

- **Anthropic, The components of agent memory（2026-11）**：目前最好的工程概念框架；四层结构 + dreaming。注意是厂商研究，数字不可外推。[原文](https://www.anthropic.com/research/components-of-agent-memory)
- **LangGraph Memory overview**：短期/长期、语义/情景/程序、hot path/background，工程视角最清晰。[文档](https://docs.langchain.com/oss/python/langgraph/memory) · [中文参考译文](../../docs/langchain-memory-zh.md)
- **CoALA（arXiv:2309.02427）**：认知架构视角的经典分类，适合建立术语。[中文译文](../../docs/coala-zh.md)
- **A Survey on the Memory Mechanism of LLM Based Agents（arXiv:2404.13501）**：2024 年的系统综述，适合补全早期工作。[中文精读](../../docs/papers-zh/02-surveys.md#survey-2404-13501)
- **From Storage to Experience（arXiv:2605.06716，ACL 2026）**：从“存储”到“经验”的演进视角。[中文精读](../../docs/papers-zh/02-surveys.md#survey-2605-06716)
- **Agent Memory Research in 2026: A Data-Driven Survey and Extended Taxonomy**：2026 年的数据驱动综述和扩展分类。[中文条目](../../docs/papers-zh/02-surveys.md#zenodo-2026)

---

## 经典架构

- **MemGPT（arXiv:2310.08560）**：OS 类比，主上下文/外部上下文，自编辑记忆；Letta 的前身。[中文精读](../../docs/papers-zh/01-foundations.md#memgpt)
- **Generative Agents（arXiv:2304.03442）**：memory stream + recency/importance/relevance 检索，经典中的经典。[中文精读](../../docs/papers-zh/01-foundations.md#generative-agents)
- **MemoryBank（arXiv:2305.10250）**：长期记忆 + 遗忘曲线，适合理解“时间衰减”。[中文精读](../../docs/papers-zh/01-foundations.md#memorybank)
- **A-MEM（arXiv:2502.12110）**：agentic memory，笔记之间的链接与重组。[中文精读](../../docs/papers-zh/03-systems.md#a-mem)

---

<a id="现代系统"></a>
## 现代系统

- **Mem0（arXiv:2504.19413 + README）**：生产级抽取管线、多信号检索；注意 2026 版算法已改为 ADD-only。[中文精读](../../docs/papers-zh/03-systems.md#mem0) · [仓库](https://github.com/mem0ai/mem0)
- **Zep（arXiv:2501.13956）+ Graphiti README**：时序知识图谱、双时间、episode 溯源、混合检索。[中文精读](../../docs/papers-zh/03-systems.md#zep) · [Graphiti](https://github.com/getzep/graphiti)
- **MemOS（arXiv:2507.03724 + README）**：MemCube、调度器、图 + 向量、技能演进。[中文精读](../../docs/papers-zh/03-systems.md#memos) · [仓库](https://github.com/MemTensor/MemOS)
- **MemoryOS（arXiv:2506.06326）**：STM/MTM/LPM、分段分页与人格更新；不要与 MemOS 混淆。[中文精读](../../docs/papers-zh/03-systems.md#memoryos) · [官方仓库](https://github.com/BAI-LAB/MemoryOS)
- **Letta 文档**：MemFS、记忆块、dreaming、`/remember`。[文档](https://docs.letta.com/letta-code/memory)
- **HippoRAG（arXiv:2405.14831）**：图 + 个性化 PageRank，多跳检索的代表。[中文精读](../../docs/papers-zh/04-retrieval-eval.md#hipporag)
- **GraphRAG（arXiv:2404.16130）**：社区摘要式图检索，和 Graphiti 的时序图形成对照。[中文精读](../../docs/papers-zh/04-retrieval-eval.md#graphrag)

---

<a id="评测"></a>
## 评测

- **LongMemEval（arXiv:2410.10813）**：多类长期记忆能力；原版 S/M/oracle 与 V2 分开。[中文精读](../../docs/papers-zh/04-retrieval-eval.md#longmemeval) · [官方仓库](https://github.com/xiaowu0162/LongMemEval)
- **LoCoMo（arXiv:2402.17753）**：超长对话记忆评测；当前公开 locomo10 是原 50 conversations 的子集。[中文精读](../../docs/papers-zh/04-retrieval-eval.md#locomo) · [官方仓库](https://github.com/snap-research/locomo)
- **BEAM**：百万到千万 token 规模，适合压力测试。
- **CAMBench Coding / AML**：编码证据复用，relevant/noisy 双条件。[AML 指南](https://agentmemories.ai/api-guide) · [开源榜](https://agentmemories.ai/leaderboard/academic/coding)
- **CL-Bench**：持续学习闭环，适合验证 dreaming 类机制。[说明](https://continual-learning-bench.com/news/cl-bench-1-0/)
- **VibeMemBench**：仓库级编码记忆评测；本教程尚未核验一手规模与当前版本，不把“111 仓库”等数字作为既定事实。
- **OmniMemEval**：多数据集统一评测框架。[仓库](https://github.com/MemTensor/OmniMemEval)

---

<a id="读论文检查表"></a>
## 读论文检查表

读任何记忆论文，按顺序问：

1. 记忆单元是什么：消息、chunk、episode、fact、note、wiki、还是权重？
2. 写入用不用 LLM？一次写多少？失败会不会固化？
3. 存储是什么：文件、关系库、向量、图、混合？
4. 检索有几路？怎么融合？怎么去重？怎么截断？
5. 更新语义是什么：追加、覆盖、失效、还是离线整理？
6. 作用域是什么：user、session、agent、tenant？
7. 评测数据集、answerer、top_k、baseline 是什么？
8. 有没有消融？有没有噪声/矛盾场景？
9. 失败模式是什么？作者自己写了哪些？
10. 这套设计在什么任务上会输？