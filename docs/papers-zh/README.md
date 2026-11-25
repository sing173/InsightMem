# 论文中文精读（Agent Memory）

> 配套：[Agent 记忆系统学习路线](../../learning/agent-memory-tutorial/README.md) · [精读清单](../../learning/agent-memory-tutorial/reading-list.md)
> 版本：2026-11-24

---

## 这是什么

阅读清单里推荐的论文已逐篇做中文精读。逐篇做全文翻译的体量很大，而且部分论文的许可不允许全文翻译或衍生。本目录采用**中文精读**的方式覆盖全部论文：

- **摘要**：逐段翻译或紧密意译；
- **方法与架构**：按论文结构整理，保留关键术语；
- **实验与结论**：只写论文明确给出的数字，并标注“论文自报”；
- **局限**：从工程视角补充论文没有强调的边界；
- **为什么读 / 与教程对应**：说明它在学习路线里的位置。

CoALA 已经完成全文翻译，单独放在 [docs/coala-zh.md](../coala-zh.md)；LangChain 的《Memory overview》译文在 [docs/langchain-memory-zh.md](../langchain-memory-zh.md)。

> **不是逐字全文翻译。** 如果你需要某一篇的全文翻译，先确认该论文的许可；对 CC BY 的篇目可以逐篇补全文。

---

## 许可状态

| 论文 | 论文页许可 | 全文翻译可行性 |
|---|---|---|
| CoALA（2309.02427） | CC BY 4.0 | 已完成全文翻译 |
| MemGPT（2310.08560） | CC BY | 可做，需署名 |
| MemOS（2507.03724） | CC BY | 可做，需署名 |
| GraphRAG（2404.16130） | CC BY | 可做，需署名 |
| LongMemEval（2410.10813） | CC BY | 可做，需署名 |
| LongMemEval-V2（2605.12493） | CC BY | 可做，需署名 |
| 2024 记忆综述（2404.13501） | CC BY | 可做，需署名 |
| Zep（2501.13956） | CC BY-NC-SA | 仅非商业、相同方式共享 |
| LoCoMo（2402.17753） | CC BY-NC-SA | 仅非商业、相同方式共享 |
| Mem0（2504.19413） | 未显示开放许可 | 仅导读 |
| Generative Agents（2304.03442） | 未显示开放许可 | 仅导读 |
| MemoryBank（2305.10250） | 未显示开放许可 | 仅导读 |
| A-MEM（2502.12110） | 未显示开放许可 | 仅导读 |
| HippoRAG（2405.14831） | 未显示开放许可 | 仅导读 |
| From Storage to Experience（2605.06716） | 未显示开放许可 | 仅导读 |

许可可能变化；正式复用前请以论文页为准。

---

## 分卷索引

| 分卷 | 论文 | 适合 |
|---|---|---|
| [01 基础架构](01-foundations.md) | MemGPT、Generative Agents、MemoryBank、CoALA | 建立记忆分层、检索打分、反思与遗忘的直觉 |
| [02 综述](02-surveys.md) | 2024 记忆综述、2026 演化综述、2026 数据驱动综述 | 建立全局地图和术语 |
| [03 现代系统](03-systems.md) | Mem0、Zep、MemOS、A-MEM | 看生产系统如何做抽取、图、调度和链接 |
| [04 检索与评测](04-retrieval-eval.md) | HippoRAG、GraphRAG、LongMemEval、LoCoMo | 看多跳检索和长期记忆评测 |
| [05 LongMemEval-V2](05-longmemeval-v2.md) | LongMemEval-V2、AgentRunbook-R/C、LAFS | 看环境经验记忆、多模态轨迹与准确率—延迟折中 |

---

## 建议阅读顺序

1. **先读 [01 基础架构](01-foundations.md)**：MemGPT 给你“记忆分层”，Generative Agents 给你“检索打分 + 反思”，MemoryBank 给你“遗忘”，CoALA 给你统一术语。
2. **再读 [02 综述](02-surveys.md)**：把术语放进一张地图，注意每篇综述的截止时间。
3. **然后读 [03 现代系统](03-systems.md)**：看 Mem0 的抽取、Zep 的双时间图、MemOS 的 MemCube、A-MEM 的链接演化。
4. **最后读 [04 检索与评测](04-retrieval-eval.md)**：HippoRAG / GraphRAG 解决多跳，LongMemEval / LoCoMo 解决“怎么证明有效”。
5. **进阶读 [05 LongMemEval-V2](05-longmemeval-v2.md)**：理解环境经验、轨迹状态、文件式记忆控制器和 LAFS。

每篇读完后，用 [阅读清单的 10 个问题](../../learning/agent-memory-tutorial/reading-list.md#读论文检查表) 做一次自查。

---

## 约定

- **数字口径**：只写论文摘要或正文明确给出的数字，标注“论文自报”；不把不同 benchmark 的分数横比。
- **术语**：`memory` = 记忆，`working memory` = 工作记忆，`episodic/semantic/procedural` = 情景/语义/程序，`grounding` = 落地，`retrieval` = 检索，`consolidation` = 整合/巩固。
- **链接**：本地精读优先；论文原文、官方仓库、项目页与数据集作为补充链接，便于核对版本。