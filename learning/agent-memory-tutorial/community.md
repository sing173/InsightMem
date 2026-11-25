# 社区资源（已核对，2026-11-24）

> 配套：[八周路线](README.md) · [精读清单](reading-list.md)

---

## 最值得先看的

| 资源 | 类型 | 适合 | 备注 |
|---|---|---|---|
| [Anthropic: The components of agent memory](https://www.anthropic.com/research/components-of-agent-memory) | 工程研究 | 建立四层框架 | 2026-11-06，厂商自述 |
| [LangGraph Memory overview](https://docs.langchain.com/oss/python/langgraph/memory) | 官方文档 | 工程 baseline | 短期/长期、写入时机讲得最清楚 |
| [Awesome-AI-Memory](https://github.com/IAAR-Shanghai/Awesome-AI-Memory) | 知识库 | 系统索引 | 1.3k stars，含论文/框架/评测 |
| [Awesome-Memory-for-Agents](https://github.com/TsinghuaC3I/Awesome-Memory-for-Agents) | 论文列表 | 找论文 | 669 stars，更新到 2026-11 |
| [Evolving-LLM-Agent-Memory-Survey](https://github.com/FeishuLuo/Evolving-LLM-Agent-Memory-Survey) | 论文列表 | 看演进脉络 | ACL 2026 survey 配套 |

---

## 框架官方文档

- [Letta memory & dreaming](https://docs.letta.com/letta-code/memory)
- [Mem0 Quickstart](https://docs.mem0.ai/quickstart)
- [Mem0](https://github.com/mem0ai/mem0)
- [Graphiti](https://github.com/getzep/graphiti)
- [MemOS](https://github.com/MemTensor/MemOS)
- [MemoryOS 官方仓库](https://github.com/BAI-LAB/MemoryOS) · [文档](https://bai-lab.github.io/MemoryOS/docs)
- [LongMemEval](https://github.com/xiaowu0162/LongMemEval) · [LongMemEval-V2](https://github.com/xiaowu0162/LongMemEval-V2) · [LoCoMo](https://github.com/snap-research/locomo)
- [AML Add/Search 指南](https://agentmemories.ai/api-guide) · [规则](https://agentmemories.ai/rules) · [文档](https://agentmemories.ai/docs)

---

## 课程与教程

| 资源 | 类型 | 说明 |
|---|---|---|
| [LangChain Academy](https://academy.langchain.com/) | 免费课程 | LangGraph 基础，官方维护 |
| [Long-Term Agentic Memory With LangGraph](https://www.deeplearning.ai/short-courses/long-term-agentic-memory-with-langgraph/) | 阶段一主课程 | 免费；1h24m；语义/情景/程序记忆与邮件 Agent 实战 |
| [LLMs as Operating Systems: Agent Memory](https://www.deeplearning.ai/short-courses/llms-as-operating-systems-agent-memory/) | 阶段二主课程 | 免费；1h32m；MemGPT/Letta、自编辑记忆、上下文换入换出与多 Agent 共享 |
| [Redis AI docs](https://redis.io/docs/latest/develop/ai/) | 教程 | LangGraph/ADK + 记忆服务的动手教程 |
| [MongoDB Atlas × LangGraph.js](https://www.mongodb.com/docs/atlas/ai-integrations/langgraph-js/long-term-memory-store/) | 教程 | Store 持久化、长期记忆接线 |
| [Bilibili：Agent Memory 教程（2026）](https://www.bilibili.com/video/BV1SwtP6vE9G) | 视频 | 中文入门，LangChain 实战；课程营销，选看 |
| [CSDN：7 篇综述](https://blog.csdn.net/2401_85373898/article/details/163924899) | 中文索引 | 快速概览；二手材料，回到原文核对；2026-11-24 本机 TLS 复核失败 |

---

## 本教程推荐顺序

1. [Long-Term Agentic Memory With LangGraph](https://www.deeplearning.ai/short-courses/long-term-agentic-memory-with-langgraph/)：先完成语义、情景、程序记忆的工程实践；
2. [LLMs as Operating Systems: Agent Memory](https://www.deeplearning.ai/short-courses/llms-as-operating-systems-agent-memory/)：再学习 Agent 自主管理上下文与内外部记忆；
3. 用 [LangGraph Memory Overview](https://docs.langchain.com/oss/python/langgraph/memory) 和 [Letta Memory & Dreaming](https://docs.letta.com/letta-code/memory) 作为实现时的官方参考；
4. 用 Awesome 列表持续跟踪论文与项目，不把课程分数当 benchmark 结论。

---

## 使用建议

- 一手文档 > 论文 > 二手解读 > 短视频。二手材料只用来建立直觉，不引用其数字。
- 看到“某系统提升 X%”先问：baseline 是什么、answerer 是谁、数据集多大、是不是厂商自报。
- 每读一个框架，画一张“写入/读取/更新”三列图，比读十篇测评更有用。
- 社区资源会过时；版本号和日期比标题更重要。