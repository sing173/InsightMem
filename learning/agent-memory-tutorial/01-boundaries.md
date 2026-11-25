# 01 边界与地图（第 1 周）

> 上一章：[00 定位与概念](00-orientation.md) · 下一章：[02 写入](02-writing.md)
> 阶段：阶段一建立 LangGraph 边界，阶段二复用同一张地图理解 MemGPT/Letta。
> 预计：5–6 小时；Notebook walkthrough 约 60–90 分钟，L0 审计约 2 小时。

## 本章你会得到什么

学完本章，你会拿到三份具体产出：

1. 一份无记忆邮件 Agent 的 baseline 结果；
2. 一张能区分 prompt、checkpoint、短期记忆和长期记忆的状态地图；
3. 一份真实工具的记忆审计表，能指出“记忆在哪一层丢失”。

本章不急着写向量数据库。先回答一个更基础的问题：**Agent 已经看到的信息、任务执行状态和跨会话记忆，到底有什么区别？**

## 开始前准备

- 按 [附录 C](appendix.md#c-vs-code-notebook-实验环境) 配置 VS Code Notebook 环境；
- 打开 [email-agent 项目说明](../../experiments/email-agent/README.md)；
- 本章只需要运行 [01-baseline.ipynb](../../experiments/email-agent/notebooks/01-baseline.ipynb)，不需要 API Key 或模型下载；
- 准备一个你常用的 AI 工具，用于后面的 L0 审计。

Notebook 使用离线的 `LocalStore` 和确定性策略。它的作用是让你看清“没有记忆时系统会怎样失败”，不是模拟真实 LLM 的全部能力。

---

## 先从一个真实问题开始

假设你有一个邮件 Agent。你说：

> “用我平时的语气回复 Alice。”

没有记忆的 Agent 也能生成一封语法正确的邮件，但它不知道：

- 你希望简洁还是正式；
- 你的签名是什么；
- Alice 上次问过什么；
- 哪些邮件应该直接忽略。

这不一定是模型“不够聪明”。更常见的原因是：**系统根本没有保存，或者没有把这些信息放进本次上下文。**

所以本章的任务不是先加一个向量库，而是先搞清楚：

1. 哪些信息只对当前任务有用？
2. 哪些信息需要跨会话保留？
3. 哪些状态只是用来恢复执行？
4. 记忆丢失后，错误会从哪里开始？

## 本章的核心思想

> **判断一个系统有没有记忆，不是只看它保存了什么，而是看它能否在合适的时间、scope 和预算下，把合适的历史信息重新放进上下文。**

由此得到三个贯穿全章的判断：

- **保存不等于使用**：写入成功，但如果没有被检索并注入，本次回答仍不会受益；
- **持久化不等于长期记忆**：checkpoint 也会落盘，但它的主要目的可能是恢复执行，而不是复用知识；
- **记忆类型由内容和用途决定**：同一段信息可能成为 fact、example 或 rule，存储介质不是分类依据。

本章不会证明“加了记忆一定更好”。它要建立的是**失败归因的方法和后续单变量实验的标尺**：先知道没有记忆时错在哪里，后面加 semantic、episodic 或 procedural memory 时，才能判断收益来自哪一种机制。

### 一条贯穿全章的推理链

```text
观察 baseline 失败
  → 定位每个失败缺少的信息
  → 判断信息属于哪种状态与生命周期
  → 决定它应该放在哪里
  → 验证它下一次是否真正进入上下文
```

| 操作 | 你会得到的结果 | 印证的核心思想 | 自然引出的下一步 |
|---|---|---|---|
| 运行无记忆 baseline | 路由、写作、记忆召回三组数字 | 先把“模型本身能力”和“记忆贡献”分开 | 打开具体失败，而不是只看总分 |
| 分析三个失败案例 | 签名缺失、示例缺失、规则缺失 | 不同失败需要不同记忆类型 | 给每种状态判断生命周期 |
| 绘制状态地图 | prompt / checkpoint / memory 的边界 | 边界由用途决定，不由数据库决定 | 专门区分最易混淆的 checkpoint |
| 分析 checkpoint 例子 | 能恢复执行，但不自动跨会话复用 | 持久化不是长期记忆的充分条件 | 用四层结构审计真实工具 |
| 完成 L0 审计 | 原始记录、派生表示、注入路径与缺口 | 保存层存在，不代表注入层存在 | 下一章决定“到底要写什么” |

带着这条链往下做，你就不会把 Notebook 当成一个孤立 Demo。

---

## 实战：做一份邮件 Agent 的记忆地图

### 第 1 步：先运行一个没有记忆的 baseline

**你要验证的核心思想：** baseline 是控制组，不是最终产品。它把“模型与固定策略本身能做什么”和“记忆额外贡献了什么”分开，后面每加一种记忆才有可比较的起点。

打开 [01-baseline.ipynb](../../experiments/email-agent/notebooks/01-baseline.ipynb)，选择 `.venv` 内核，执行 **Run All**。

Notebook 会依次完成：

1. 读取 10 封标注邮件；
2. 创建一次独立实验运行；
3. 在关闭三类记忆的配置下逐封处理；
4. 保存失败案例、统计信息和 manifest。

运行结束后，你会看到类似结果：

| 指标 | 结果 | 它在说什么 |
|---|---:|---|
| Routing accuracy | 8/10 | 两封邮件被分错动作 |
| Writing compliance | 0/4 | 四封应回复邮件都没有满足签名要求 |
| Required-memory recall | 0/6 | baseline 没有读取任何必需记忆 |

结果保存在：

```text
experiments/email-agent/runs/<run_id>/baseline-results.json
```

**结果说明什么：** 8/10 说明基础路由已经能处理大部分邮件；0/4 说明个性化写作是独立短板；0/6 说明当前配置完全没有使用必需记忆。三个指标必须分开看，因为“路由正确”不代表“回答已经符合用户要求”。

这也说明 baseline 不是“坏了”，而是提供了一个可归因的对照。后面即使只提高两封邮件的路由准确率，也要能说清是 episodic 还是 procedural memory 起了作用。

**所以下一步：** 不要继续调总分，打开具体失败案例，看每一次失败到底缺少哪一类信息。

### 第 2 步：不要只看总分，打开三个失败案例

**你要验证的核心思想：** 记忆类型不是按“用了哪个数据库”划分，而是按“失败缺少哪类信息”划分。先归因，再决定写什么。

#### 案例 A：动作正确，但回复不像你

`docs-question` 的期望动作是 `respond`，baseline 也判断对了。但回复里没有 `John Doe` 签名。

这说明：

- 路由没有问题；
- 写作个性化失败；
- 缺少的是一条 semantic memory：用户签名与写作偏好。

#### 案例 B：过去遇到过，但没有利用经验

`vendor-pricing` 是一封 vendor 询价邮件，期望被忽略。baseline 把它判成了 `respond`。

如果系统保存过类似邮件及其处理结果，就可以检索一条历史示例。这属于 **episodic memory**：过去发生过什么、当时怎么处理。

#### 案例 C：规则已经知道，但没有进入决策

`event-invite` 来自 `noreply@events.example`，期望被忽略。baseline 仍选择回复。

如果你已经告诉 Agent“忽略这类活动邀请”，这条规则应作为 **procedural memory** 参与后续决策，而不是每次重新猜测。

把三个案例放在一起：

| 失败案例 | 缺少的信息 | 记忆类型 | 后续章节 |
|---|---|---|---|
| `docs-question` | 用户签名、语气偏好 | Semantic | [02 写入](02-writing.md)、[03 存储](03-storage.md) |
| `vendor-pricing` | 过去相似邮件的处理示例 | Episodic | [02 写入](02-writing.md)、[05 融合与选择](05-fusion.md) |
| `event-invite` | 从反馈得到的长期路由规则 | Procedural | [02 写入](02-writing.md)、[06 更新与治理](06-governance.md) |

到这里，baseline 的价值已经体现出来了：**它不是“失败的代码”，而是一把尺子。** 后面每加一种记忆，都要回答“哪一类失败减少了”。

**结果说明什么：** 三个案例看起来都是“回答不对”，根因却分别是事实缺失、经验缺失和规则缺失。它们分别对应 semantic、episodic、procedural memory，不能用同一个“向量库”笼统解决。

这也解释了为什么第 2 章要按内容类型分别写入，而不是先把所有历史消息一股塞进数据库。

**所以下一步：** 已经知道“缺什么”，还要判断“该在哪里、活多久、谁能读”，否则可能把临时草稿误当长期偏好，或把 checkpoint 误当用户事实。

### 第 3 步：给每种状态找到位置

**你要验证的核心思想：** 状态边界由用途和生命周期决定，不由存储介质决定。先判断“它为什么存在”，再决定“放在哪里”。

看到同一个变量时，先问四个问题：

1. 它只在本次请求里可见吗？
2. 它需要跨会话保留吗？
3. 它的主要作用是恢复任务执行吗？
4. 它会不会被更新、失效或删除？

用邮件 Agent 举例：

| 状态 | 项目中的具体例子 | 应该放在哪里 | 为什么 |
|---|---|---|---|
| Prompt context | 当前邮件正文、系统指令 | 本次推理的 token | 请求结束就不再作为上下文 |
| Working memory | 当前草稿、刚拿到的日历结果 | Agent state | 只服务当前决策周期 |
| Checkpoint | 图已经执行到 triage，还没执行 response | thread checkpointer | 用于暂停后继续执行 |
| Semantic memory | “回复署名为 John Doe” | Store | 跨会话复用的事实与偏好 |
| Episodic memory | 上次如何处理 vendor pricing 邮件 | Store examples | 回溯发生过什么 |
| Procedural memory | “忽略活动邀请邮件” | Store instructions | 复用做事规则 |
| Compaction summary | 长邮件的简短历史 | 当前窗口或派生记忆 | 释放当前上下文空间 |

一个简单判断口诀：

> **本次要看的是上下文；下次还要用的是记忆；暂停后要继续的是 checkpoint。**

**结果说明什么：** 同一份邮件草稿，在生成时是 working memory，被持久化后用于恢复执行可能变成 checkpoint，只有当你主动提炼“用户偏好简短回复”并供新会话使用时，它才成为 semantic memory。数据没变，边界随用途改变。

这也说明“用了 SQLite”或“用了向量库”不能直接判断是不是记忆系统。

**所以下一步：** 这张表里最容易混淆的是 checkpoint。它和长期记忆都会持久化，但回答的是不同问题，需要单独用一个崩溃恢复例子验证。

### 第 4 步：用一个具体例子区分 checkpoint 和长期记忆

**你要验证的核心思想：** “会话结束后还在”只证明持久化，不证明长期记忆。关键看它是否被用于跨会话知识复用，而不是只用于恢复原任务。

假设 Agent 已经完成 triage，正准备调用日历工具，此时进程崩溃。

如果系统保存了 thread state，恢复同一个 thread 后可以继续。这时 checkpoint 在做它最擅长的事：**恢复执行。**

但如果用户第二天新开一个 thread，问“以后回复都用简短语气”，仅恢复旧 thread 不够。系统需要把“简短语气”写入长期 Store，并在新 thread 中检索。

所以：

- checkpoint 持久化，不等于长期语义记忆；
- checkpoint 的首要目标是恢复工作流；
- 从历史 thread 抽取偏好并供新 thread 使用，才构成跨会话语义记忆。

**结果说明什么：** checkpoint 回答“刚才做到哪了”，长期记忆回答“下次应该知道什么”。两者可以共用数据库，甚至可以引用同一份原始消息，但不能因此混为一谈。

这也解释了为什么有些工具看起来“记得很多”，新会话却仍然重复问同样的问题：它保存了历史，却没有把历史转化成可复用的知识并注入。

**所以下一步：** 带着“保存路径”和“注入路径要分别检查”的观点，去审计一个真实工具。

如果你想把同一流程写成 LangGraph，可以使用下面的课程骨架。它省略了模型初始化和完整编译，重点是展示状态与记忆的分工：

```python
class TriageDecision(BaseModel):
    reasoning: str
    classification: Literal["ignore", "notify", "respond"]


def triage_email(email: dict) -> TriageDecision:
    prompt = TRIAGE_PROMPT.format(
        user_profile=STATIC_PROFILE,
        triage_rules=DEFAULT_TRIAGE_RULES,
        email=format_email(email),
    )
    return router.with_structured_output(TriageDecision).invoke(prompt)


def build_response_agent():
    return create_react_agent(
        model=RESPONSE_MODEL,
        tools=[check_calendar, schedule_meeting, write_email],
        prompt=build_response_prompt,
    )
```

这段代码仍然没有长期记忆。第 2 章才会分别加入 semantic、episodic 和 procedural memory。

### 第 5 步：审计一个真实工具，验证你的地图

**你要验证的核心思想：** 写入路径和注入路径必须分别检查。只有“保存了”还不足以证明记忆有效，必须找到它下一次进入上下文的证据。

选一个你常用的 AI 工具，追一条具体记忆，例如“用户喜欢简短回答”。

按顺序记录：

1. 原始来源在哪里？
2. 保存位置在哪里？
3. 是否建立索引或派生表示？
4. 下一次会话如何注入？
5. 用户纠正后如何更新？
6. 删除后会影响哪些副本和缓存？
7. 切换用户后是否还能看到？

使用下面的模板：

| 层 | 该工具的实现 | 证据 | 缺口 |
|---|---|---|---|
| Transcripts |  |  |  |
| Memory notes |  |  |  |
| Representations |  |  |  |
| Injected context |  |  |  |

看不到内部实现时，写“未观察到”，不要猜。审计证据按强度分级：

| 等级 | 证据 | 能支持的结论 |
|---|---|---|
| A | 官方文档、API 合同、源码 | 声明的行为和实现约束 |
| B | 用户导出、数据库快照、日志 | 本机实际保存的状态 |
| C | 行为探针 | 特定输入下观察到的读写行为 |
| D | UI 印象、推测 | 只能作为待验证假设 |

**结果说明什么：** 你得到的不只是“这个工具有没有记忆”的结论，而是一条可检查的传播链：

```text
原始来源 → 保存 → 派生表示 → 检索/选择 → 注入上下文 → 影响回答
```

任何一层缺失，都可能让前面已经保存的信息失效。例如界面显示了一条偏好，但模型生成时没有看到它，这属于注入层失败，不是存储层失败。

这也解释了为什么第 7 章要同时报告检索、注入和回答指标，而不是只报一个 accuracy。

**所以下一步：** 边界和失败层已经清楚，下一章才能决定“哪些信息值得写、写成什么单元、什么时候写”。

完整步骤见 [实验手册 L0](labs.md#l0)。

### 实战结束：检查你是否真的完成

你应该能提交以下内容：

- `baseline-results.json` 和对应 `manifest.json`；
- 三个失败案例的原因表；
- 一张状态地图，能区分 prompt、working memory、checkpoint 和三类长期记忆；
- 一份真实工具的四层审计表；
- 一句话结论：这个工具最薄弱的记忆层是什么，它会造成什么具体失败。

如果只能说出“它有记忆”，还没有完成本章。你要能指出**信息从哪里进入、在哪里丢失、下一次为什么没有被使用**。

最后用一句话把五个步骤串起来：

> baseline 先建立控制组，三个失败案例告诉你缺哪类信息，状态地图决定信息该放在哪里，checkpoint 例子排除“持久化就是记忆”的误解，L0 审计再验证保存的信息是否真正进入下一次上下文。

这就是本章的核心成果：你不是只跑了一个 Notebook，而是建立了一套从失败到记忆边界的判断方法。

---

## 参考：把记忆地图补充完整

前面的实战先建立直觉。下面各节用于回答更细的工程问题。

### 1.1 状态按生命周期分类

| 状态 | 存在哪里 | 典型寿命 | 主要用途 | 是否属于本文记忆 |
|---|---|---|---|---|
| Prompt context | 当前请求的 token | 单次推理 | 给模型提供立即可见信息 | 否，除非被持久化并跨会话读取 |
| Working memory | 当前任务变量、窗口、草稿 | 当前会话或任务 | 维护短期状态 | 是，短期/工作记忆 |
| Checkpoint | 图状态、消息、任务位置 | 线程生命周期，可恢复 | 暂停/恢复工作流 | 可以是短期记忆，但不等于语义记忆 |
| Episodic memory | 原始消息、episode、工具轨迹 | 跨会话，按策略保留 | 回溯发生过什么 | 是 |
| Semantic memory | fact、profile、entity、relation | 跨会话，可更新/失效 | 保存事实、偏好、关系 | 是 |
| Procedural memory | rule、skill、playbook | 跨会话，可版本化 | 复用做事方法 | 是 |
| Compaction summary | 对旧上下文的摘要 | 通常跟随当前窗口 | 释放当前上下文空间 | 否；写入长期存储后才可能成为记忆 |
| Model weights | 微调后的参数 | 模型版本生命周期 | 改变通用能力 | 否，属于训练 |

### 1.2 LangGraph 视角与 OS 视角

阶段一先用 LangGraph 的工程边界，阶段二再用 MemGPT/Letta 的 OS 类比理解同一张图：

| 概念 | LangGraph 工程视角 | MemGPT / Letta OS 视角 |
|---|---|---|
| 当前工作区 | thread state + 当前消息 | main context / core memory |
| 可恢复执行 | checkpointer | 状态恢复，但不自动等于长期知识 |
| 跨会话事实 | Store 中的 semantic memory | archival memory 或可编辑 memory block |
| 最近对话 | thread-scoped short-term memory | recall memory / 当前上下文历史 |
| 外部档案 | Store、向量库或数据库 | archival memory |
| 上下文溢出 | 截断、摘要、检查点 | memory pressure → paging / 递归摘要 |
| 规则与技能 | procedural memory / prompt | core memory block / skill / MemFS 文件 |

两种视角可以组合：**LangGraph Store 提供持久化与语义检索，memory manager 决定何时把哪些内容换入上下文。** OS 类比不意味着硬件级隔离，也不意味着所有系统都必须实现页表或虚拟内存。

[LangGraph 的 checkpoint 中文说明](../../docs/langchain-memory-zh.md#短期记忆)指出，它会持久化 thread state，因此“会话结束后还在”。但它的首要目的仍是恢复执行状态，例如图走到哪一步、工具是否完成、消息队列是什么。

判断它是不是长期记忆，要看使用方式：

- 恢复同一个 thread 的工作流：主要是短期/工作记忆；
- 从历史 thread 抽取用户偏好供新 thread 使用：才构成跨会话语义记忆；
- 把所有 checkpoint 无差别注入新会话：通常是噪声和预算问题，不是好的记忆设计。

### 1.3 一条状态生命周期

```text
原始事件
  │
  ├─► 当前上下文 ──► 推理 ──► 丢弃
  │
  ├─► 工作记忆 / checkpoint ──► 恢复任务 ──► 归档或清理
  │
  └─► 长期记忆
          ├─► 原文 episode
          ├─► 提炼 fact / note
          └─► 规则 / skill
                    │
                    ▼
              更新 / 失效 / 删除 / 审计
```

设计时至少标注三个时间：

- **事件时间**：事情什么时候发生；
- **写入时间**：系统什么时候知道；
- **读取时间**：这次查询发生在什么时候。

例如用户今天说“我搬到上海”，事件时间可能是今天，但系统昨天还保存着“住在北京”。只按写入时间排序，无法可靠处理现实世界的变化。双时间的完整讨论见 [06 更新与治理](06-governance.md)。

### 1.4 短期记忆与长期记忆不是“窗口 vs 向量库”

| 维度 | 短期记忆 | 长期记忆 |
|---|---|---|
| 目标 | 维持当前任务连续性 | 支持跨会话复用 |
| 单元 | 消息、工具状态、草稿、checkpoint | episode、fact、note、rule |
| 更新 | 高频、覆盖或追加 | 抽取、合并、失效、版本化 |
| 读取 | 通常直接注入或按需取回 | 检索、过滤、排序、预算控制 |
| 删除 | 会话结束或任务完成 | 用户请求、TTL、合规策略 |

一个系统可以两者都有，也可以只有其中之一。[MemGPT 本地精读](../../docs/papers-zh/01-foundations.md#memgpt) 中的主上下文和外部上下文是典型分层；InsightMem 更偏向长期原文证据存储，不负责当前窗口管理。

### 1.5 Compaction、RAG 与 Memory

#### Compaction 解决当前上下文预算

Compaction 把旧消息压缩成较短表示，让当前对话继续。如果摘要只存在于当前 prompt 中，它不是长期记忆；如果把摘要写入外部存储，并保留来源和版本，它才进入记忆生命周期。

一个可实现的压缩协议是：

```python
while token_count(context) > budget:
    turn = evict_oldest_complete_turn()
    summary = summarize(summary, turn)
    anchors.extend(extract_source_anchors(turn))
```

“完整轮次”不仅是 user/assistant 两条消息，还应包括 tool call 与对应 tool result。只截断其中一半，模型会看到无法解释的 ID 或缺失参数。

至少保留两类锚点：

- 原始消息 ID 与角色；
- 关键约束、数值、路径、错误码的原文位置。

实验时扫描预算 `B`，同时测关键约束保留率、工具配对完整率和摘要忠实度。只报 token 缩减比例不够。

#### RAG 与 Memory 的工程重叠

RAG 通常检索相对静态的文档库；agent memory 更强调从交互经验中持续获得、更新和治理知识。两者都要 chunk、embed、检索、重排和注入上下文，区别主要在数据来源与生命周期，而不是“有没有向量数据库”。

真正的记忆系统还要回答：

- 谁写入，写什么？
- 新事实与旧事实冲突怎么办？
- 用户能否查看、纠正和删除？
- 检索结果如何证明来源？
- 跨用户是否隔离？

### 1.6 四层结构审计法

Anthropic 的四层结构适合审计真实工具：

| 层 | 要找的东西 | 审计问题 |
|---|---|---|
| Transcripts | 原始对话、工具调用、执行结果 | 是否逐字保存？能否定位到具体消息？ |
| Memory notes | 自动或人工写下的偏好、经验、规则 | 谁生成？谁能改？是否保留来源？ |
| Representations | 索引、wiki、标签、交叉链接 | 如何更新？会不会产生重复或陈旧链接？ |
| Injected context | 每次会话主动加载的内容 | 注入多少？按什么顺序？是否可关闭？ |

每一层都应能回答：

```text
谁写入 → 谁读取 → 对谁可见 → 来自哪里 → 何时失效
```

对应字段至少包含 `writer`、`reader`、`visibility`、`source_span`、`valid_until`。存储层存在不代表注入层存在；界面展示过某条记忆，也不代表模型生成时用过它。

### 1.7 三个真实形态

#### InsightMem：长期原文证据层

[InsightMem](../../wiki/insightmem.md) 保存全部消息、chunk、view 和 embedding，Search 返回有限证据。它有 Transcripts 和检索表示，但没有当前窗口管理、事实抽取、时间失效和自动遗忘。`user_id` 是唯一检索隔离边界，`session_id` 只是来源标识。

因此它适合回答“过去发生过什么、证据在哪里”，不适合直接回答“用户现在真正喜欢什么”。

#### MemGPT：主上下文 + 外部上下文

[MemGPT 精读](../../docs/papers-zh/01-foundations.md#memgpt) 把有限上下文当主内存，外部存储当磁盘：

- 主上下文包含系统指令、working context 和 FIFO 队列；
- 外部包含 recall storage 与 archival storage；
- 内存压力触发写入、驱逐和递归摘要；
- 被驱逐消息仍可检索，**驱逐不等于删除**。

它展示的是上下文管理与外部记忆的协作，不是单纯“向量库”。

#### Letta Code / MemFS：文件式长期记忆

[Letta 官方文档](https://docs.letta.com/letta-code/memory) 与 [MemFS 机制笔记](../../wiki/memgpt-letta.md) 用 Markdown 文件保存记忆：

- 根目录文件进入系统提示；
- 子目录按需读取；
- 文件可编辑、可版本化；
- 后台 dreaming 整理记忆。

优势是透明、可审计、易人工纠正；风险是上下文注入预算、链接陈旧和写入冲突。

### 1.8 Hot path 与 background

| 路径 | 何时发生 | 优点 | 风险 | 典型操作 |
|---|---|---|---|---|
| Hot path | 用户请求期间同步执行 | 立即可用、延迟可预测 | 阻塞主流程、失败影响请求 | 原文写入、幂等检查、即时事实抽取 |
| Background | 会话后或定时执行 | 可批量总结、成本可控 | 滞后、需要任务状态和重试 | dreaming、批量 embedding、图整合 |

[LangGraph Memory 中文译文](../../docs/langchain-memory-zh.md) 明确区分这两种写入时机。设计原则：

- 不能把“以后整理”当成“现在不记”；
- 不能把所有 LLM 抽取都放在关键路径；
- 后台任务必须可重试、可观测、幂等；
- 原文应先在事务中落库，派生表示可以后续补齐。

### 1.9 最小记忆契约

| 字段/能力 | 为什么需要 |
|---|---|
| `memory_id` | 稳定标识，支持更新和删除 |
| `user_id` / `tenant_id` | 读取隔离边界 |
| `session_id` / `source_id` | 溯源，不一定是检索过滤条件 |
| `source_span` | 指向原文位置，支持核验 |
| `ingested_at` | 写入时间 |
| `valid_from` / `valid_to` | 事实生效区间 |
| `status` | active / invalidated / deleted / archived |
| `version` | 追踪覆盖与回滚 |
| `confidence` / `method` | 标识规则、LLM 或人工来源 |

不是所有系统都要同时实现全部字段，但必须明确哪些缺失会带来风险。

一种实用 namespace 是：

```text
(tenant_id, user_id, project_id, thread_id)
```

每一层按授权策略过滤：

- 写入时确定 owner 和 visibility；
- 检索时先过滤，再排序；
- 注入时再次校验；
- 后台任务也使用同一 scope；
- 缓存键包含 scope 和索引版本。

测试不能只检查代码里有 `user_id`。给两个用户投放不同唯一哨兵，再交换查询：

1. 用户 A 写入只有 A 知道的短语；
2. 用户 B 用该短语检索；
3. 断言零结果；
4. 清空缓存、重建索引后重复；
5. 检查导出、备份恢复和后台任务路径。

删除是一条状态链，不是一次 `DELETE`：

```text
请求删除
  → 主记录 tombstone
  → 派生 notes 失效
  → 索引/缓存失效
  → prompt 缓存失效
  → 搜索验证
  → 按保留策略处理备份
```

分别定义业务删除、索引删除、备份保留期和合规例外。恢复备份可能重新引入已删除记录，因此需要重放 tombstone 或删除日志。

验证至少覆盖删除后立即检索、重建索引后检索、恢复备份后检索、同一用户另一会话，以及其他用户的越权检索。

### 1.10 本章验收

- 能解释为什么无关、过时、重复记忆进入上下文或维护路径可能降效并增本；
- 能区分 checkpoint、compaction 和长期语义记忆；
- 能解释 compaction 与长期记忆的边界；
- 能指出一个工具的错误记忆会从哪一层进入；
- 能设计一次跨用户隔离测试，而不是只检查代码里有没有 `user_id`；
- 能用 baseline 结果说明：动作错误、写作错误和记忆未使用分别是什么问题。

---

## 机制依据与延伸阅读

### 一手依据

- [Anthropic: The components of agent memory](https://www.anthropic.com/research/components-of-agent-memory)：四层结构与注入层。
- [LangGraph Memory overview](https://docs.langchain.com/oss/python/langgraph/memory)：short-term / long-term、hot path / background。[中文参考译文](../../docs/langchain-memory-zh.md)
- [CoALA, arXiv:2309.02427](https://arxiv.org/abs/2309.02427)：working memory、episodic/semantic/procedural memory。[中文译文](../../docs/coala-zh.md)
- [MemGPT, arXiv:2310.08560](https://arxiv.org/abs/2310.08560)：主/外部上下文与虚拟上下文管理。[中文精读](../../docs/papers-zh/01-foundations.md#memgpt)
- [Letta memory & dreaming](https://docs.letta.com/letta-code/memory)：文件式记忆的官方工程说明。

### 课程与资源

- [LangChain Academy](https://academy.langchain.com/)：用 thread state、checkpoint 和 store 做对照实验。
- [Awesome-AI-Memory](https://github.com/IAAR-Shanghai/Awesome-AI-Memory)：按 memory type 和 framework 找后续阅读。
- 更多资源见 [社区资源](community.md)。

---

## 本章小结与下一步

本章最重要的不是记住所有术语，而是建立一个判断顺序：

1. 先看信息是否进入本次上下文；
2. 再看它是否需要跨会话保存；
3. 区分恢复执行的 checkpoint 与可复用知识；
4. 最后检查更新、隔离、删除和审计是否完整。

下一章 [02 写入](02-writing.md) 会回答：**如果决定要记住一条信息，应该写成 fact、example，还是 prompt？**
