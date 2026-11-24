# 记忆概览（Memory overview）

> **非官方中文翻译，仅供个人学习参考。**
> 原文：<https://docs.langchain.com/oss/python/concepts/memory>
> 原文标题：Memory overview
> 原文仓库：[langchain-ai/docs](https://github.com/langchain-ai/docs)，MIT License
> 翻译日期：2026-11-23
> 说明：LangChain 文档会持续更新；如译文与原文有出入，以英文原文为准。

**译者说明**

- 代码中的标识符、类名和 API 名称保持英文，只翻译注释。
- `thread` 译为“线程/会话线程”，`namespace` 译为“命名空间”，`Store` 保留为 Store，`hot path` 译为“热路径”，`profile` 译为“画像”，`collection` 译为“集合”。
- 原文中的图片未转载，位置以“原文配图”注明；可点击文首原文链接查看。

---

## 引言

[记忆（Memory）](https://docs.langchain.com/oss/python/langgraph/add-memory.md)是一个能够记住此前交互信息的系统。对 AI agent 来说，记忆至关重要，因为它让 agent 记住之前的交互、从反馈中学习，并适应用户偏好。随着 agent 处理越来越复杂的任务、与用户进行大量交互，这种能力对效率和用户满意度都变得不可或缺。

本概念指南按**回忆范围（recall scope）**区分两类记忆：

- [**短期记忆**](#短期记忆)，或称[线程作用域记忆](https://docs.langchain.com/oss/python/langgraph/checkpointers.md#threads)：通过在单个会话内维护消息历史来跟踪当前对话。LangGraph 把短期记忆作为 agent [状态](https://docs.langchain.com/oss/python/langgraph/graph-api.md#state)的一部分来管理。状态通过 [checkpointer](https://docs.langchain.com/oss/python/langgraph/checkpointers.md#checkpoints) 持久化到数据库，因此线程可以随时恢复。短期记忆在图被调用或某一步完成时更新，并在每一步开始时读取状态。
- [**长期记忆**](#长期记忆)：跨会话保存用户特定或应用级数据，并在不同对话线程之间共享。它可以在任意时间、任意线程中被回忆。记忆的作用域可以是任意自定义命名空间，而不只是单个 thread ID。LangGraph 提供 [store](https://docs.langchain.com/oss/python/langgraph/stores.md)（[参考文档](https://reference.langchain.com/python/langgraph.store/base/BaseStore)）来保存和回忆长期记忆。

> 原文配图：短期记忆与长期记忆的对比。

---

## 短期记忆

[短期记忆](https://docs.langchain.com/oss/python/langgraph/add-memory.md#add-short-term-memory)让应用在单个[线程](https://docs.langchain.com/oss/python/langgraph/checkpointers.md#threads)或对话内记住之前的交互。[线程](https://docs.langchain.com/oss/python/langgraph/checkpointers.md#threads)把一次会话中的多次交互组织起来，类似电子邮件把消息归入同一段对话。

LangGraph 把短期记忆作为 agent 状态的一部分管理，并通过线程作用域的 checkpoint 持久化。这个状态通常包括对话历史，也可以包括其他有状态数据，例如上传的文件、检索到的文档或生成的产物。把这些内容存进图的状态后，bot 既能访问某次对话的完整上下文，又能保持不同线程之间的隔离。

### 管理短期记忆

对话历史是最常见的短期记忆形式，而长对话对当今的 LLM 构成了挑战。完整历史可能放不进 LLM 的上下文窗口，导致不可恢复的错误。即使 LLM 支持完整的上下文长度，多数 LLM 在长上下文上的表现仍然不佳：它们会被过时或跑题的内容“分散注意力”，同时响应更慢、成本更高。

聊天模型通过消息接收上下文，包括开发者提供的指令（system message）和用户输入（human message）。在聊天应用中，消息在人类输入和模型回复之间交替，消息列表会越来越长。由于上下文窗口有限，而且消息列表 token 多、成本高，许多应用会受益于手动移除或遗忘过时信息的技术。

> 原文配图：对消息列表进行过滤。

关于管理消息的常见技术，参见[添加和管理记忆](https://docs.langchain.com/oss/python/langgraph/add-memory.md#manage-short-term-memory)指南。

---

## 长期记忆

LangGraph 的[长期记忆](https://docs.langchain.com/oss/python/langgraph/add-memory.md#add-long-term-memory)让系统跨不同对话或会话保留信息。与**线程作用域**的短期记忆不同，长期记忆保存在自定义的“命名空间”中。

长期记忆是一个复杂的挑战，没有放之四海而皆准的解决方案。不过，以下问题提供了一个帮助你选择技术的框架：

- **记忆类型是什么？** 人类用记忆记住事实（[语义记忆](#语义记忆)）、经历（[情景记忆](#情景记忆)）和规则（[程序记忆](#程序记忆)）。AI agent 也可以用同样的方式使用记忆。例如，agent 可以用记忆记住关于用户的特定事实，从而完成任务。
- [**何时更新记忆？**](#写入记忆) 记忆可以作为 agent 应用逻辑的一部分更新（例如“在热路径上”）。此时 agent 通常在回复用户之前决定要记住哪些事实。另一种做法是把记忆更新作为后台任务（在后台/异步运行、生成记忆的逻辑）。下文会解释这两种方法的取舍。

不同应用需要不同类型的记忆。这个类比并不完美，但考察[人类的记忆类型](https://www.psychologytoday.com/us/basics/memory/types-of-memory?ref=blog.langchain.dev)会很有启发。一些研究（例如 [CoALA 论文中文译文](coala-zh.md)）甚至把人类的记忆类型映射到了 AI agent 使用的类型上。

| 记忆类型 | 存储内容 | 人类例子 | Agent 例子 |
|---|---|---|---|
| [语义](#语义记忆) | 事实 | 在学校学到的东西 | 关于用户的事实 |
| [情景](#情景记忆) | 经历 | 我做过的事 | agent 过去的动作 |
| [程序](#程序记忆) | 指令 | 本能或运动技能 | agent 的 system prompt |

### 语义记忆

[语义记忆](https://en.wikipedia.org/wiki/Semantic_memory)在人类和 AI agent 中都涉及对具体事实和概念的保留。对人类来说，它可以包括在学校学到的信息，以及对概念及其关系的理解。对 AI agent 来说，语义记忆常用于个性化应用：记住过去交互中的事实或概念。

> **注意**
>
> 语义记忆不同于“语义搜索”。语义搜索是一种用“含义”（通常是 embedding）寻找相似内容的技术。语义记忆是心理学词汇，指存储事实和知识；语义搜索是一种基于含义而非精确匹配来检索信息的方法。

语义记忆可以用不同方式管理：

#### 画像（Profile）

记忆可以是一份持续更新的“画像”，包含关于用户、组织或其他实体（包括 agent 自身）的范围明确、具体的信息。画像通常就是一个 JSON 文档，包含你为领域选择的键值对。

维护画像时，每次都需要**更新**它。因此，你会希望传入旧画像，[让模型生成新画像](https://github.com/langchain-ai/memory-template)（或生成一个 [JSON patch](https://github.com/hinthornw/trustcall) 应用到旧画像上）。画像变大后容易出错，可以考虑把画像拆成多个文档，或在生成文档时使用**严格**解码，确保记忆 schema 始终合法。

> 原文配图：更新画像。

#### 集合（Collection）

另一种做法是把记忆做成一个持续更新和扩展的文档集合。每条记忆的作用域可以更窄、更容易生成，因此随着时间推移更不容易**丢失**信息。对 LLM 来说，为新信息生成**新对象**，比把新信息与已有画像调和更容易。因此，文档集合通常能带来更高的下游[召回率](https://en.wikipedia.org/wiki/Precision_and_recall)。

但这会把一部分复杂度转移到记忆更新上。模型现在必须**删除**或**更新**列表中的已有条目，这并不容易。此外，有些模型倾向于过度插入，有些则倾向于过度更新。可以参考 [Trustcall](https://github.com/hinthornw/trustcall) 包来管理这一点，并考虑用评估（例如 [LangSmith](https://docs.langchain.com/langsmith/evaluation.md)）来调优行为。

使用文档集合还会把复杂度转移到对列表的**搜索**上。Store 目前同时支持[语义搜索](https://reference.langchain.com/python/langgraph.store/base/SearchOp/query)和[按内容过滤](https://reference.langchain.com/python/langgraph.store/base/SearchOp/filter)。

最后，使用记忆集合可能难以为模型提供全面的上下文。虽然单条记忆可能遵循特定 schema，但这种结构可能无法捕捉记忆之间的完整上下文或关系。因此，用这些记忆生成回复时，模型可能缺少统一画像方法中更容易获得的重要上下文信息。

> 原文配图：更新列表。

无论采用哪种记忆管理方式，核心都是：agent 会用语义记忆为其回复提供依据（ground its responses），这通常会带来更个性化、更相关的交互。

### 情景记忆

[情景记忆](https://en.wikipedia.org/wiki/Episodic_memory)在人类和 AI agent 中都涉及回忆过去的事件或动作。[CoALA 论文中文译文](coala-zh.md)对此说得很清楚：事实可以写入语义记忆，而**经历**可以写入情景记忆。对 AI agent 来说，情景记忆常用于帮助 agent 记住如何完成一项任务。

在实践中，情景记忆常通过 few-shot 示例提示来实现：agent 从过去的序列中学习，从而正确执行任务。有时“展示”比“告诉”更容易，LLM 也很擅长从示例中学习。Few-shot 学习让你通过把输入-输出示例加入提示词来[“编程”](https://x.com/karpathy/status/1627366413840322562) LLM，以说明期望的行为。虽然生成 few-shot 示例有很多最佳实践，但真正的挑战往往是根据用户输入选择最相关的示例。

注意，记忆 [store](https://docs.langchain.com/oss/python/langgraph/stores.md) 只是把数据存为 few-shot 示例的一种方式。如果你希望开发者更多参与，或让 few-shot 与评估 harness 结合得更紧，也可以用 [LangSmith Dataset](https://docs.langchain.com/langsmith/manage-datasets.md) 存储数据，并实现自己的检索逻辑，根据用户输入选择最相关示例。

参见这两篇博客：[用 few-shot prompting 改进工具调用性能](https://blog.langchain.dev/few-shot-prompting-to-improve-tool-calling-performance/)；[用 few-shot 示例让 LLM 与人类偏好对齐](https://blog.langchain.dev/aligning-llm-as-a-judge-with-human-preferences/)。

### 程序记忆

[程序记忆](https://en.wikipedia.org/wiki/Procedural_memory)在人类和 AI agent 中都涉及记住执行任务所用的规则。对人类来说，程序记忆像通过基本运动技能和平衡内化的骑自行车知识；情景记忆则是回忆具体经历，比如第一次不用辅助轮骑车成功，或一次难忘的骑行。对 AI agent 来说，程序记忆是模型权重、agent 代码和 agent 提示词的组合，共同决定 agent 的功能。

在实践中，agent 修改模型权重或重写代码并不常见；更常见的是 agent 修改自己的提示词。

一种有效的改进指令的方法是[“反思”（Reflection）](https://blog.langchain.dev/reflection-agents/)或元提示（meta-prompting）：把当前指令（如 system prompt）连同最近的对话或明确的用户反馈一起提示 agent，agent 根据这些输入改进自己的指令。这种方法特别适合那些难以预先写清指令的任务，因为它让 agent 从交互中学习和适应。

例如，我们做了一个 [Tweet 生成器](https://www.youtube.com/watch?v=Vn8A3BxfplE)，用外部反馈和提示词重写来生成高质量的论文摘要推文。这个案例中，具体的摘要提示词很难先验地写清楚，但让用户批评生成的推文并给出改进反馈却很容易。

下面的伪代码展示了如何用 LangGraph memory [store](https://docs.langchain.com/oss/python/langgraph/stores.md) 实现：用 store 保存提示词，`update_instructions` 节点获取当前提示词以及 `state["messages"]` 中捕获的用户反馈，更新提示词并写回 store；`call_model` 节点从 store 读取更新后的提示词来生成回复。

```python
# 使用指令的节点
def call_model(state: State, store: BaseStore):
    namespace = ("agent_instructions", )
    instructions = store.get(namespace, key="agent_a")[0]
    # 应用逻辑
    prompt = prompt_template.format(instructions=instructions.value["instructions"])
    ...

# 更新指令的节点
def update_instructions(state: State, store: BaseStore):
    namespace = ("instructions",)
    instructions = store.search(namespace)[0]
    # 记忆逻辑
    prompt = prompt_template.format(instructions=instructions.value["instructions"], conversation=state["messages"])
    output = llm.invoke(prompt)
    new_instructions = output['new_instructions']
    store.put(("agent_instructions",), "agent_a", {"instructions": new_instructions})
    ...
```

> 原文配图：更新指令。

### 写入记忆

agent 写入记忆主要有两种方式：[“在热路径上”（in the hot path）](#在热路径上)和[“在后台”（in the background）](#在后台)。

> 原文配图：热路径与后台的对比。

#### 在热路径上

运行时创建记忆既有优点也有挑战。优点是实时更新，新记忆可以立即用于后续交互；它还带来透明度，用户可以在记忆创建和存储时收到通知。

但这种方法也有挑战：如果 agent 需要新工具来决定提交什么记忆，复杂度会增加；思考“要保存什么”会影响 agent 延迟；agent 还必须在记忆创建和其他职责之间多任务切换，可能影响记忆的数量和质量。

例如，ChatGPT 使用 [`save_memories`](https://openai.com/index/memory-and-new-controls-for-chatgpt/) 工具把记忆作为内容字符串 upsert，并决定每条用户消息是否以及如何使用该工具。参考实现见 [memory-agent](https://github.com/langchain-ai/memory-agent) 模板。

#### 在后台

把记忆创建作为独立的后台任务有几个优点：消除主应用的延迟；把应用逻辑与记忆管理解耦；让 agent 更专注地完成任务；还可以灵活安排创建时机，避免重复工作。

但这种方法也有自己的挑战。确定记忆写入频率很关键，更新太少会让其他线程缺少新上下文；决定何时触发记忆形成也很重要。常见策略包括：固定时间后调度（有新事件时重新调度）、cron 调度，或允许用户/应用逻辑手动触发。

参考实现见 [memory-service](https://github.com/langchain-ai/memory-template) 模板。

### 记忆存储

LangGraph 把长期记忆作为 JSON 文档存储在 [store](https://docs.langchain.com/oss/python/langgraph/stores.md) 中。每条记忆组织在自定义的 `namespace`（类似文件夹）和唯一的 `key`（类似文件名）下。命名空间常包含用户或组织 ID 等标签，便于组织信息；这种结构支持记忆的层级组织。跨命名空间搜索则通过内容过滤器支持。

```python
from langgraph.store.memory import InMemoryStore


def embed(texts: list[str]) -> list[list[float]]:
    # 替换为实际的 embedding 函数或 LangChain embeddings 对象
    return [[1.0, 2.0] * len(texts)]


# InMemoryStore 把数据保存在内存字典中。生产环境请使用数据库支持的 store。
store = InMemoryStore(index={"embed": embed, "dims": 2})
user_id = "my-user"
application_context = "chitchat"
namespace = (user_id, application_context)
store.put(
    namespace,
    "a-memory",
    {
        "rules": [
            "User likes short, direct language",
            "User only speaks English & python",
        ],
        "my-key": "my-value",
    },
)
# 按 ID 获取这条“记忆”
item = store.get(namespace, "a-memory")
# 在该命名空间内搜索“记忆”，按内容等价性过滤，并按向量相似度排序
items = store.search(
    namespace, filter={"my-key": "my-value"}, query="language preferences"
)
```

关于记忆 store 的更多信息，参见[持久化](https://docs.langchain.com/oss/python/langgraph/stores.md)指南。

---

## 了解更多

- [上下文概念概览](https://docs.langchain.com/oss/python/concepts/context.md)
- [LangChain 中的短期记忆](https://docs.langchain.com/oss/python/langchain/short-term-memory.md)
- [LangGraph 中的记忆](https://docs.langchain.com/oss/python/langgraph/add-memory.md)

---

## 术语对照

| 英文 | 中文 | 说明 |
|---|---|---|
| memory | 记忆 | 跨交互保留的信息 |
| short-term memory | 短期记忆 | 线程级，随会话状态保存 |
| long-term memory | 长期记忆 | 跨会话，按命名空间组织 |
| thread-scoped | 线程作用域 | 只在单个会话线程内有效 |
| checkpointer | 检查点保存器 | 持久化图状态的机制 |
| namespace | 命名空间 | 类似文件夹的作用域 |
| store | 存储 / Store | LangGraph 的长期记忆接口 |
| semantic memory | 语义记忆 | 事实、概念 |
| episodic memory | 情景记忆 | 经历、动作 |
| procedural memory | 程序记忆 | 规则、指令、技能 |
| profile | 画像 | 单个持续更新的 JSON 文档 |
| collection | 集合 | 多条独立记忆文档 |
| hot path | 热路径 | 在主请求处理过程中写入 |
| background | 后台 | 异步或离线写入 |
| reflection | 反思 | 根据反馈改写自身指令 |
| meta-prompting | 元提示 | 用提示词改进提示词 |
| few-shot prompting | few-shot 示例提示 | 用输入-输出示例引导模型 |
| grounding | 依据 / 落地 | 让回复基于检索到的记忆 |

---

## 原文与许可

- 原文：<https://docs.langchain.com/oss/python/concepts/memory>
- 原文标题：Memory overview
- 原文仓库：[langchain-ai/docs](https://github.com/langchain-ai/docs)
- 许可：MIT License
- 翻译日期：2026-11-23

本文为非官方翻译，仅用于个人学习参考，不代表 LangChain 官方。原文可能随时更新；如需引用或用于生产，请以英文原文为准。