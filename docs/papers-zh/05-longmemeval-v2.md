# LongMemEval-V2：长期 Agent 记忆的中文翻译与精读

> 论文：**LongMemEval-V2: Evaluating Long-Term Agent Memory Toward Experienced Colleagues**
> 论文版本：arXiv v1，2026-05-12。仓库核对版本：`main @ 2cc8c540bdb87fe6761629b585e727e1c4704520`，提交日期 2026-08-09；核对日期 2026-11-24。
> 配套：[论文精读索引](README.md) · [第 7 周评测](../../learning/agent-memory-tutorial/07-evaluation.md) · [评测手册](../../learning/agent-memory-tutorial/evaluation.md)

## 阅读约定

本文严格区分证据来源：

- **【论文自报】**：论文正文、附录或论文中的实验表。所有成绩、延迟和比例在未另注明时都属于这一类别，不代表独立复现。
- **【HF 数据核对】**：对官方 Hugging Face 数据集公共 schema、questions 文件及固定 revision 的直接统计。
- **【当前仓库】**：指定 commit 的 README、脚本或代码行为，可能与论文不同。
- **【官方更新页自报】**：论文发表后的 AgentRunbook-C V2 研究更新，不能混入论文 v1 主表。
- **【公开 issue 报告】**：issue 作者或维护者的陈述，未在本项目中复现。
- **【工程解读】**：本文对论文方法、评测协议和 InsightMem 的分析与建议，不是作者结论。

## 1. 元数据与链接

| 项目 | 信息 |
|---|---|
| 标题 | LongMemEval-V2: Evaluating Long-Term Agent Memory Toward Experienced Colleagues |
| 作者 | Di Wu、Zixiang Ji、Asmi Kawatkar、Bryan Kwan、Jia-Chen Gu、Nanyun Peng、Kai-Wei Chang |
| 机构 | UCLA |
| arXiv | [2605.12493](https://arxiv.org/abs/2605.12493) |
| HTML | [arXiv HTML v1](https://arxiv.org/html/2605.12493v1) |
| 项目页 | [LongMemEval-V2](https://xiaowu0162.github.io/longmemeval-v2/) |
| 官方仓库 | [xiaowu0162/LongMemEval-V2](https://github.com/xiaowu0162/LongMemEval-V2) |
| 数据集 | [xiaowu0162/longmemeval-v2](https://huggingface.co/datasets/xiaowu0162/longmemeval-v2) |
| 数据 schema | [HF SCHEMA.md](https://huggingface.co/datasets/xiaowu0162/longmemeval-v2/blob/main/SCHEMA.md) |
| 数据卡 | [HF DATA_CARD.md](https://huggingface.co/datasets/xiaowu0162/longmemeval-v2/blob/main/DATA_CARD.md) |
| V2 更新页 | [AgentRunbook-C V2: A Self-Improving Lightweight Memory Controller](https://xiaowu0162.github.io/longmemeval-v2/agentrunbook-c-v2/) |
| 论文许可 | CC BY 4.0 |
| 代码与公共数据许可 | Apache-2.0 |

【HF 数据核对】本次核对的 HF revision 为 `f152293e235517d504809563c833d7190b8c713b`，`lastModified` 为 2026-05-17。Dataset Viewer 显示的“29 rows”是自动 Parquet 展示分片相关的行数，不是题目数或轨迹数；直接读取 `questions.jsonl` 得到 **451 题**。

本次翻译底稿是提供的 arXiv HTML 全文转换件，并与官方仓库、项目页、HF schema 和更新页交叉核对。后文出现“当前”时，指上述 commit 或 revision，而不是未来最新状态。

## 2. 摘要译文

【论文自报；译文为保留信息密度的中文转述，不是逐字翻译】

长期记忆评测大多来自与聊天助手的对话，主要考察记住用户或从公开世界获得的信息；已有 Agent 记忆基准也常聚焦于用户历史、短轨迹或下游任务成功。但对于需要操作专属环境的 Agent，真正有用的记忆还包括：这个环境有哪些页面和控件、状态如何变化、重复任务怎样完成、哪些操作会反复失败，以及在其他部署中成立的步骤是否适用于当前部署。

LongMemEval-V2 将这一目标概括为：让 Agent 更像一位熟悉定制环境的资深同事，而不是只记住聊天记录。基准包含 451 道人工问题，覆盖五类能力：静态状态回忆、动态状态追踪、工作流知识、环境陷阱和前提意识。问题来自 WebArena、WorkArena 与 WorkArena++ 的定制 Web、ServiceNow 环境。每道题最多需要从约 500 条相关轨迹构成的记忆干草堆中找证据，最大规模达到约 115M tokens。

论文提出两个轻量级记忆控制器。AgentRunbook-R 将轨迹整理为原始状态切片、状态转移事件、过程与提示笔记三个池，再由查询规划器进行多路检索。AgentRunbook-C 不先压缩成向量库条目，而是在查询时把轨迹文件和截图交给增强 sandbox 中的 coding agent，让它借助清单、辅助脚本和有限的状态跨度输出支持材料。两种方法都只生成证据，最终回答由固定 reader 根据证据完成。

按 Small 与 Medium 两档等权平均，论文自报 AgentRunbook-C 的准确率为 **72.5%**，最强的 slice+notes RAG 为 **48.5%**，Codex 为 **69.3%**。采用 coding agent 的控制器明显更慢，因此论文进一步讨论如何在准确率、延迟和预算约束下比较这些方法。

摘要中的三个平均数需要在读表时澄清：

- AgentRunbook-C：`(74.9 + 70.1) / 2 = 72.5`。
- slice+notes RAG：`(51.0 + 45.9) / 2 = 48.45`，四舍五入为 48.5。
- Codex：`(69.9 + 68.7) / 2 = 69.3`。

它们不是 Small 或 Medium 任一单档成绩。

## 3. 研究动机：从 V1 到 V2，究竟改变了什么

【论文自报】传统长期记忆任务经常要求记住用户告诉模型的内容，或利用预训练时见过的公共知识。WebArena、WorkArena 等任务环境则不同：导航路径、字段位置、缺失功能、操作顺序和错误恢复往往只存在于该部署的经验中，无法仅凭公共知识可靠回答。

因此，论文把“有长期记忆”定义为：**过去大量交互中保留的信息，能帮助 Agent 在当前定制环境中正确判断和行动**。这里的变化不是简单增加聊天长度，而是把记忆对象从“用户事实和对话”转向“环境、状态、过程与反复出现的失败”。

| 维度 | LongMemEval V1 式问题 | LongMemEval-V2 |
|---|---|---|
| 主要对象 | 用户聊天、个人事实、公共信息 | 定制 Web、ServiceNow 环境中的经验 |
| 时间性 | 跨会话保留信息 | 从大量历史轨迹中形成可迁移经验 |
| 正确性来源 | 用户陈述或公共知识 | 当前环境的状态、动作和截图证据 |
| 推理形态 | 回忆、综合、时间推理 | 状态回忆、转移追踪、流程导航、陷阱与前提判断 |
| 记忆单元 | 消息或会话 | 状态、动作、截图、转移、过程、提示 |
| 输出协议 | 往往直接生成答案 | 先收集证据，再由固定 reader 回答 |

【工程解读】V2 不应被理解为 V1 数据集的简单“加长版”，也不应与 V1 分数直接排名。两者测试的分布、记忆结构和证据形态都不同。对 InsightMem 而言，V2 更接近“代码工作记忆”或“环境操作记忆”，而不是只增加聊天记录检索量。

## 4. 五种能力

【论文自报】论文将能力划分为以下五类。前四类在 Table 2 中按列报告；第五类通过 abstention 题目混入总体成绩，没有独立列。

| 能力 | 要记住什么 | 典型错误 |
|---|---|---|
| Static state recall，静态状态回忆 | 地标、页面布局、模块功能、控件名称、两个相似状态的细微差异 | 找到相近页面，但认错位置、模块或字段 |
| Dynamic state tracking，动态状态追踪 | 某个动作如何改变页面、状态和后续可用操作 | 只复述动作，不理解转移后的状态 |
| Workflow knowledge，工作流知识 | 重复任务的步骤、顺序、入口与导航路径 | 知道目标，但不知道在这个部署里如何完成 |
| Environment gotchas，环境陷阱 | 反复出现的失败、缺失功能、误导控件、特殊限制 | 套用一般经验，忽略该环境的坑 |
| Premise awareness，前提意识 | 识别“在别处成立、在当前部署不成立”的问题前提 | 接受错误前提并生成看似合理的答案 |

前提意识的关键不是回答“不知道”，而是确认当前环境中的证据**反驳了问题前提**。例如，问题假设存在某个按钮、字段或路径，但历史状态明确显示它不存在，正确行为应指出这一矛盾。

【HF 数据核对】公共 `questions.jsonl` 的 `question_type` 分布如下：

| 问题类型 | 数量 |
|---|---:|
| `static-environment` | 134 |
| `static-environment-abs` | 55 |
| `dynamic-environment` | 86 |
| `dynamic-environment-abs` | 41 |
| `procedure` | 74 |
| `procedure-abs` | 32 |
| `errors-gotchas` | 29 |
| **合计** | **451** |

其中 abstention 题合计 128，非 abstention 题 323。web 域 240 题，enterprise 域 211 题。按能力合并后，static 类 189 题、dynamic 类 127 题、workflow 类 106 题、gotchas 类 29 题。

题型采用真假判断、选择题或短答案；29 道含 `image` 字段的问题与 gotchas 题数量一致。截图题往往要求识别画面中的错误信息或误导提示。

## 5. 轨迹采集、标注与干草堆构建

### 5.1 轨迹采集

【论文自报】

- 共采集 **1,540 条**任务轨迹：WebArena 599 条，WorkArena/WorkArena++ 941 条。
- 采集成功率 **52.0%**，平均每条 **28.1 states**。
- 采集模型以 GPT-5-mini 为主，占 **73.1%**；GPT-5.2 占 **22.9%**；Codex + GPT-5.2 xhigh 占 **4.0%**。
- 主流程使用 AgentLab ReAct agent；Codex manual-action agent 补充 Level-3 WorkArena++ 轨迹。
- 论文没有直接使用公开 WebArena leaderboard 轨迹作为主来源，理由包括缺少截图、轨迹过短以及采集 Agent 过于专门化。

一条轨迹由目标 `goal` 和有序 state-action pair 构成。每个状态同时包含截图与 accessibility tree（AXTree）。WorkArena L2/L3 的目标会移除显式导航提示，只保留任务意图和参数，避免答案或流程直接从 `goal` 泄露。

【HF 数据核对】HF 数据卡称公共版本包含 **1,870 条 task trajectories**，与论文的 1,540 条采集池不一致。公开材料没有解释这一差异；可能是版本、筛选或打包范围不同，但不能未经说明就合并两个数字。

### 5.2 人工标注与答案构造

【论文自报】

1. 1 名研究生与 3 名本科生参与，每题至少由另一名标注者复核。
2. 使用无上下文的强模型测试，过滤仅靠公共平台常识就能回答的问题。
3. 证据必须在截图中可见；AXTree 可以帮助定位和筛选，但不能作为唯一可见证据。
4. Codex 根据问题与 answer-trajectory 生成初始答案提议，人工处理 ambiguous cases，并验证最终答案核心。
5. coverage map 可以包含多跳；每一跳都必须对应有证据的轨迹。
6. 失败轨迹与成功轨迹同样重要，因为许多 gotchas 和动态状态问题恰恰来自失败过程。

【工程解读】“证据必须截图可见”使问题更接近真实操作者看到的环境，但也提高了存储、检索和阅读成本。AXTree 可以作为索引特征，却不能替代最终视觉证据，这一点对多模态实现尤其重要。

### 5.3 干草堆构建

【论文自报】

- 全局最小答案核心：WebArena 44 条，ServiceNow 49 条；目标是让每个非零支持问题的每个证据跳至少有一条共享答案轨迹。
- **Small**：每个域共享一套 100 条轨迹的 haystack；同域所有题复用，成功与失败轨迹大致 1:1，并确定性打乱。
- **Medium**：每题单独构建，复用 Small 的答案种子，扩展到每题约 500 条；其他填充轨迹会排除可能提供额外答案的任务家族。
- abstention 题没有直接答案轨迹，复用人工验证的 anchor question haystack，再确认其中没有支持错误前提的证据。
- 规模约为 Small 25M tokens、Medium 115M tokens。
- Table 1 的实际会话长度范围是 **100–498**；“500”是目标规模，不是每条 Medium haystack 都恰好有 500 条。

【工程解读】Small 与 Medium 不只是“数量更多”：Small 有跨题共享记忆，Medium 更强调单题在大量近邻轨迹中的精确查找。共享干草堆也可能允许记忆中的内容帮助回答另一题，因此不应把每题都看成完全独立的单文档 QA。

## 6. Small、Medium 与多模态结构

| 设置 | 目标轨迹数 | 组织方式 | token 规模 | 主要难点 |
|---|---:|---|---:|---|
| Small | 每域 100 | 同域共享 haystack | 约 25M | 已能形成共同背景，仍需区分相关与近邻轨迹 |
| Medium | 每题约 500 | 每题独立，复用答案种子 | 约 115M | 更多干扰、更长上下文、更细粒度定位 |

【论文自报】多模态至少有三层：

1. 历史轨迹状态中有截图。
2. 同一状态中有 AXTree 文本。
3. 部分问题本身带截图，尤其是错误信息或界面 gotchas。

【HF 数据核对】公共 schema 的关键结构为：

| 文件/对象 | 主要字段 |
|---|---|
| `questions.jsonl` | `id`、`domain`、`environment`、`question_type`、`question`、可选 `image`、`answer`、`eval_function` |
| `trajectories.jsonl` | `id`、`domain`、`environment`、`goal`、`outcome`、`start_url`、`states` |
| state | `state_index`、`step`、`url`、`action`、`thought`、`accessibility_tree`、`screenshot` |
| Small haystack | `question_id` 映射到有序的 100 个 `trajectory_id` |
| Medium haystack | `question_id` 映射到各自的有序轨迹列表；多数约 500，部分 web 题更少 |

截图位置可能写作 `screenshots/<trajectory_id>/<step>.png`；实现读取时应以 schema 和实际文件布局为准。`state_index` 是零基序号，action 在初始状态可以为 null。

公共版本删除了 construction provenance、本地路径、原 task id、answer-bearing trajectory/span 标签、URL pattern 标签和标注流程标记，以避免构造细节直接泄露答案。因此，公共数据能支持协议复现，但不能自动复现论文中的全部 oracle 研究。

## 7. Insert、Query、固定 reader 与 200K 预算

【论文自报】对第 `i` 题，将 haystack 中的 `m[i]` 条轨迹顺序插入：

```text
M[i,j] = Insert(M[i,j-1], h[i,j])
c[i]   = Query(M[i,m[i]], q[i])
y_hat[i] = R(q[i], Trunc(c[i]))
```

- `Insert(h)` 接收历史轨迹。
- `Query(q)` 返回紧凑证据 `c`。
- `Trunc(c)` 将证据截断到 **200K Qwen3.5-9B tokens**。
- `R` 是固定 reader，只根据问题和证据生成最终答案。

200K 是经验设定的上下文预算，不是模型宣称的绝对上限。论文主要报告 answer accuracy 与 query latency。固定 reader 使不同记忆控制器可以共用同一个最终答题模型，从而把记忆质量与答题模型能力部分解耦；但检索、压缩和证据呈现仍然会通过 reader grounding 影响结果。

【当前仓库】

- 记忆后端实现 `insert(trajectory)` 与 `query(question, query_image)`；官方仓库不是 AML 的 HTTP `/add`、`/search` 服务，最终回答由固定 reader 完成。
- 截断按 reader 的 tokenizer 计算，而不是按字符数简单截断。
- 结构化答案使用确定性 evaluator；自由文本使用 LLM judge。
- reader 输出取最后一个 `\boxed{}`；没有 boxed 内容时取完整响应。
- `UNKNOWN` 在 abstention 评测中始终计错，必须明确反驳前提才可能得分。

【工程解读】200K 预算比较的是“交付给 reader 的证据”，不是原始干草堆总长度。一个控制器即使扫描了 115M tokens，只要最后交付少量高相关状态，也可以满足该预算；代价体现在查询时间。因而，低准确率的 RAG 与高准确率的 coding agent 并非只差检索算法，还使用了不同的内部计算预算。

## 8. 先导研究：无上下文、Oracle 与证据压缩

### 8.1 无上下文 frontier

【论文自报】只测非 abstention 题，单位为 %。该表用于说明公共世界知识不足以替代定制环境经验。

| 模型 | Overall | Static | Dynamic | Workflow | Gotchas |
|---|---:|---:|---:|---:|---:|
| GPT-5.2 | 4.7 | 0.0 | 0.0 | 3.2 | 21.0 |
| Gemini-3.1-Pro-Preview | 11.0 | 10.4 | 9.6 | 14.7 | 24.1 |
| Claude Opus 4.6 | 11.8 | 9.6 | 12.1 | 13.4 | 37.9 |
| GLM-5V-Turbo | 10.1 | 12.6 | 10.7 | 9.1 | 20.5 |
| Grok-4.20 | 2.4 | 0.0 | 2.9 | 15.1 | 10.2 |
| Kimi-K2.5 | 14.1 | 18.3 | 19.7 | 11.5 | 17.1 |
| Qwen3.6-Plus | 11.0 | 11.8 | 7.8 | 9.1 | 31.0 |

### 8.2 Oracle 设置

【论文自报】Oracle 只测非 abstention 题，单位为 %。

| 设置 | Overall | Static | Dynamic | Workflow | Gotchas |
|---|---:|---:|---:|---:|---:|
| Qwen3.5-9B thinking，无上下文 | 1.6 | 0.0 | 1.5 | 15.5 | 13.6 |
| Qwen3.5-9B，oracle trajectories | 59.6 | 56.6 | 66.8 | 71.8 | 31.0 |
| Qwen3.5-9B，oracle slices + notes | 82.5 | 90.8 | 87.9 | 75.0 | 48.4 |
| GPT-5.4-mini medium，无上下文 | 4.5 | 2.5 | 1.0 | 7.5 | 17.1 |
| GPT-5.4-mini medium，oracle trajectories | 65.3 | 66.0 | 69.6 | 69.7 | 48.4 |
| GPT-5.4-mini medium，oracle slices + notes | 86.3 | 95.0 | 84.3 | 90.5 | 46.7 |
| Codex + GPT-5.4-mini xhigh，oracle files | 89.7 | 98.6 | 94.7 | 81.5 | 51.7 |

【工程解读】

- 无上下文最佳总体只有 14.1%，支持论文的核心动机：问题确实依赖环境经验。
- 即使给对完整轨迹，Qwen3.5-9B 也只有 59.6%；找到答案与读懂答案不是同一个问题。
- radius-1 证据切片加笔记把 oracle 表现提高到 82.5%，说明压缩、局部窗口和可复用摘要非常重要。
- coding agent 直接读 oracle 文件达到 89.7%，是 AgentRunbook-C 的经验依据。
- Oracle 标签没有完整放入公共 HF 数据，外部复现 oracle 结果需要额外标注，不能声称与论文完全同设置。

## 9. AgentRunbook-R：三池与查询规划器

### 9.1 三池

【论文自报】

| 池 | 粒度 | 内容 |
|---|---|---|
| Raw state slice | 每个 state 一条 | radius-1 局部窗口、局部 UI、截图、动作、goal、局部及完整轨迹动作序列 |
| State transition event | 每对相邻 state 一条 | LLM 根据 pre-state、action、post-state 生成简洁转移标题与描述 |
| Procedure and hint notes | 每条轨迹两条 | procedure note 保存可复用流程；hint note 保存持久观察、陷阱、缺失功能和易混控件 |

三个池回答不同问题：状态切片提供“看到了什么”，转移事件提供“动作导致了什么”，笔记提供“以后应该怎么做、避免什么”。

### 9.2 查询规划与融合

【论文自报】查询规划器输出三路检索：

```json
{
  "raw_state_queries": ["..."],
  "event_query": "...",
  "note_query": "..."
}
```

- 最多 5 个 raw-state queries；可以跳过无关流。
- 使用 Qwen3-Embedding-8B dense retrieval，embedding 输入截断到 4,096 tokens。
- 主实验取 top-6 events、top-3 notes。
- 设 raw query 数为 `n`，每个 query 取 `m = min(2, 6 // n)`，合并后 raw-state budget 为 6。
- 最终渲染顺序为 notes、events、raw state slices。
- 控制器使用 Qwen3.5-9B；主表启用 thinking。

对照方法 slice+notes RAG 不使用查询规划器，直接把问题作为两池 query；取 radius-1 的 image+AXTree 状态切片和笔记，分别检索 top-6 states 与 top-3 notes。

【工程解读】R 的主要贡献不是单纯多建两个索引，而是让查询规划器把自然语言问题分解为“状态、转移、过程/陷阱”三种信息需求。它能绕开冗长叙述，但每次查询增加规划与多路检索成本，主表延迟约 26 秒。

## 10. AgentRunbook-C：文件工作区、清单、helper 与 20-state 预算

### 10.1 写入与查询工作区

【论文自报】`Insert` 将轨迹 JSON 与截图原样复制到工作区。`Query` 为 coding agent 建立一个查询目录，核心文件包括：

```text
question.json
INSTRUCTION.md
trajectories/
trajectories/<id>/trajectory.json
trajectories/<id>/screenshots/
trajectories/TRAJECTORY_SUMMARY_CONCISE.md
trajectories/TRAJECTORY_SUMMARY_FULL.md
scripts/inspect_trajectory.py
memory_module_output.json
```

- `question.json` 保存问题与查询相关信息。
- 两份 trajectory manifest 提供不同详细程度的入口，避免 agent 从大量文件中盲目开始。
- helper 支持读取整个轨迹、单个 state、连续 state span，以及在轨迹内做文本匹配。
- coding agent 自行列目录、搜索 manifest、调用 helper、查看截图并验证输出。

### 10.2 证据输出与 20-state 上限

【论文自报】控制器输出两部分：

```json
{
  "memory_markdown": "## Support Analysis\n...\n\n## Relevant Procedure and Hint Notes\n...",
  "trajectory_spans": [
    {
      "trajectory_id": "...",
      "start_state_index": 0,
      "end_state_index": 0
    }
  ]
}
```

- 状态序号从 0 开始，区间为闭区间。
- 所有 span 合计最多交付 **20 states**；通常每个 span 不超过 3 states。
- harness 校验 JSON、过滤越界 span，再把状态文本与截图渲染给 reader。
- 指令明确要求拒绝 near-but-not-exact match。
- 如果证据反驳问题前提，必须在 `memory_markdown` 中明确写出矛盾，而不是悄悄返回相似材料。

【论文自报】论文实验使用 Codex v0.117.0、GPT-5.4-mini xhigh，最多 3 个并行 query 进程。

【工程解读】C 把“检索”改成“在受限文件集合中调查”：manifest 降低启动成本，helper 提供确定性读取原语，20-state 上限控制最终 reader 输入。它没有把原始轨迹永久压缩成 embedding，因此更接近可审计的程序记忆；代价是更多工具调用、文件 I/O 和 agent 延迟。

## 11. 实验设置与评分协议

【论文自报】

| 项目 | 设置 |
|---|---|
| 固定 reader | Qwen3.5-9B，主表启用 thinking |
| reader 服务 | vLLM，本地 NVIDIA A100 |
| 采样 | temperature 0.6，top_p 0.95，top_k 20 |
| reader prompt | 人工调优，使无记忆表现接近零，并使 oracle image+text slices 表现尽可能高 |
| 自由文本 judge | GPT-5.2 medium |
| 结构化 evaluator | normalized phrase set、ordered phrase、single-choice、multi-select |
| gotchas / abstention | LLM binary JSON judge |
| 显著性 | paired bootstrap，`p < 0.05`，比较非 ablation baseline |

评分细节：

- gotchas judge 只要答案至少包含一个正确 insight 且没有矛盾即可得 1，不要求覆盖所有参考点。
- abstention judge 必须识别 flawed premise；仅输出 `UNKNOWN` 或泛泛表示“信息不足”为 0。
- 同时反驳前提又给出具体断言的答案也为 0。

【工程解读】reader prompt 是专门为 benchmark 调优的，这意味着“无记忆接近零”不证明该 reader 在所有任务上都很弱，而是说明它被鼓励依赖提供的证据。跨论文比较时，不能只替换 reader 名称而忽略 prompt、thinking 和 judge。

## 12. 主结果：Small、Medium 与逐能力发现

### 12.1 Small

【论文自报】数值单位为准确率 %，延迟为 memory query 秒数。`†` 表示与相应非 ablation baseline 的配对 bootstrap 比较达到 `p < 0.05`。

| Method | Overall | Static | Dynamic | Workflow | Gotchas | Latency |
|---|---:|---:|---:|---:|---:|---:|
| No retrieval | 1.3 | 0.0 | 0.8 | 9.4 | 13.8 | 0 s |
| RAG: query → slice | 42.8 | 47.1 | 42.5 | 41.5 | 20.7 | 0.1 s |
| RAG: query → slice + notes | 51.0 | 52.4 | 49.6 | 52.8 | 41.4 | 0.2 s |
| AgentRunbook-R | 58.6 † | 66.1 † | 58.3 † | 52.8 | 31.0 | 26.9 s |
| R ablation: raw slice pool | 42.3 | 28.6 | 55.1 | 53.8 | 34.5 | 16.7 s |
| R ablation: event pool | 55.6 | 61.4 | 55.9 | 52.8 | 27.6 | 19.1 s |
| R ablation: note pool | 57.9 | 65.1 | 61.4 | 48.1 | 31.0 | 22.8 s |
| Codex | 69.9 | 80.4 | 67.0 | 57.5 | 58.6 | 177.2 s |
| AgentRunbook-C | 74.9 † | 82.0 † | 72.4 † | 72.6 † | 48.3 | 108.3 s |
| C ablation: workflow | 70.1 | 77.2 | 67.7 | 63.2 | 58.6 | 167.9 s |
| C ablation: manifest artifacts | 74.7 | 84.7 | 70.9 | 69.8 | 44.8 | 155.0 s |
| C ablation: helper functions | 71.4 | 78.3 | 72.4 | 66.0 | 41.4 | 145.9 s |

### 12.2 Medium

【论文自报】标记含义同上。

| Method | Overall | Static | Dynamic | Workflow | Gotchas | Latency |
|---|---:|---:|---:|---:|---:|---:|
| No retrieval | 1.3 | 0.0 | 0.8 | 9.4 | 13.8 | 0 s |
| RAG: query → slice | 38.1 | 43.4 | 40.5 | 29.3 | 24.2 | 0.1 s |
| RAG: query → slice + notes | 45.9 | 48.7 | 47.2 | 43.4 | 31.0 | 0.3 s |
| AgentRunbook-R | 57.0 † | 63.0 † | 61.4 † | 47.2 † | 34.5 | 25.8 s |
| R ablation: raw slice pool | 33.5 | 23.3 | 43.3 | 37.7 | 41.3 | 17.1 s |
| R ablation: event pool | 48.4 | 53.4 | 49.6 | 43.4 | 27.6 | 18.5 s |
| R ablation: note pool | 49.9 | 56.1 | 54.3 | 39.6 | 27.6 | 20.5 s |
| Codex | 68.7 | 78.3 | 64.6 | 61.3 | 51.7 | 185.8 s |
| AgentRunbook-C | 70.1 | 78.8 | 70.1 † | 61.3 | 44.9 | 139.9 s |
| C ablation: workflow | 64.1 | 70.9 | 64.6 | 57.5 | 41.4 | 231.9 s |
| C ablation: manifest artifacts | 68.1 | 76.7 | 68.5 | 57.6 | 48.3 | 211.6 s |
| C ablation: helper functions | 71.8 | 80.4 | 69.3 | 68.9 | 38.0 | 182.5 s |

### 12.3 如何正确解读主表

【论文自报】

- AgentRunbook-C 总体最高：Small 74.9，Medium 70.1。
- 按平均延迟计算，C 为 `(108.3 + 139.9) / 2 = 124.1 s`，Codex 为 `(177.2 + 185.8) / 2 = 181.5 s`，C 约快 **31.6%**，与摘要“快 32%”一致。
- AgentRunbook-R 平均延迟约 `(26.9 + 25.8) / 2 = 26.35 s`；Codex 平均延迟约是它的 6.9 倍，C 约是它的 4.7 倍。
- 论文引言自报 slice RAG 约 40.1%，但 Table 2 为 42.8 与 38.1，平均 40.45%；按同一精度应约 40.5%。这是论文内部数字不一致，应以表 2 原始值为准。

逐能力发现：

1. **C 不是每项都最好。** Small gotchas 为 48.3，低于 Codex 的 58.6；Medium 为 44.9，也低于 Codex 的 51.7。
2. **raw slice pool 对 static 至关重要。** 去掉后，Small static 从 66.1 降到 28.6，Medium 从 63.0 降到 23.3。
3. **event pool 有稳定贡献。** 去掉后，两档总体、static、dynamic 和 gotchas 都下降；Small dynamic 从 58.3 降到 55.9。
4. **note pool 主要支持 workflow。** 去掉后，Small workflow 从 52.8 降到 48.1，Medium 从 47.2 降到 39.6。
5. **manifest 的主要收益是延迟。** 去掉 manifest 后，Small 延迟从 108.3 增至 155.0 s，准确率仅从 74.9 变为 74.7；Medium 延迟从 139.9 增至 211.6 s，准确率从 70.1 变为 68.1。
6. **helper 的效果不是单调提升。** Small 去掉 helper 后从 74.9 降到 71.4；Medium 反而从 70.1 升到 71.8，但两档都更慢。
7. **workflow instructions 的效果因能力而异。** 去掉后 Small 总体下降 4.8 个点，但 gotchas 从 48.3 升到 58.6；Medium 总体下降 6.0 个点。不能简单说某个模块对所有能力都有正收益。
8. **Medium workflow 不是 C 独占优势。** C 与 Codex 都为 61.3；C 在 static 与 dynamic 更高。

Table 2 没有独立 premise-awareness 列，Overall 也不是四列简单平均。128 道 abstention 题混在总体成绩中；前提反驳能力会影响 Overall，但不能从该表拆出单独 premise 分数。

## 13. LAFS：准确率—延迟前沿的面积指标

【官方仓库定义】设某方法的前沿为 `F = {(accuracy, latency)}`，定义截至预算 `T` 可达的最佳准确率：

```text
A_F(T) = max({0} ∪ {a : (a, t) ∈ F, t ≤ T})
```

LAFS 在 log-latency 轴上积分：

```text
LAFS(F) =
  1 / log(T_max / T_min)
  × ∫[T_min, T_max] A_F(T) dT/T

T_min = 1 s
T_max = 200 s
```

相对固定参考前沿的增益为：

```text
ΔLAFS(S | F_ref) = LAFS(F_ref ∪ S) - LAFS(F_ref)
```

固定参考前沿 Small 为：

| 方法 | Accuracy | Latency |
|---|---:|---:|
| slice + notes | 51.0% | 0.2 s |
| AgentRunbook-R | 58.6% | 26.9 s |
| Codex | 69.9% | 177.2 s |
| AgentRunbook-C | 74.9% | 108.3 s |

Medium 为：

| 方法 | Accuracy | Latency |
|---|---:|---:|
| slice + notes | 45.9% | 0.3 s |
| AgentRunbook-R | 57.0% | 25.8 s |
| Codex | 68.7% | 185.8 s |
| AgentRunbook-C | 70.1% | 139.9 s |

解读：

- LAFS 奖励在较宽延迟区间内保持高准确率，不只看最高单点准确率。
- 延迟低于 1 s 的点从 1 s 起计；高于 200 s 的点不会提高该区间内的可达上限。
- 一个被参考点支配的提交，Gain 为 0。
- 同一方法可以提交多个 operating points，形成自己的 Pareto 前沿。
- 参考集合合并后，Small 与 Medium 的 Codex 点都被 AgentRunbook-C 支配，因此不会扩大前沿。
- 当前 leaderboard 使用 `overall_full_set * 100` 与 `memory_query_avg_seconds`。

【工程解读】LAFS 不是平均准确率，也不是端到端总成本。它不包含：

- 轨迹写入和索引构建成本；
- reader 答题、LLM judge 和 evaluator 成本；
- V2 在线策略巩固成本；
- 并发数、内存、网络或存储成本。

对于低延迟 RAG，LAFS 尤其有解释力；对于 100 秒以上的 coding agent，单点准确率与 LAFS 可能给出不同排序。若 transport failure 被当成空答案计 0，或不同提交的 reader 配置不同，LAFS 还会继承这些评测差异。

## 14. 错误与工具使用分析

### 14.1 错误分类

【论文自报】

| 类别 | 定义 |
|---|---|
| Major retrieval miss | 没有命中任何 answer-bearing task family |
| Minor retrieval miss | 命中 task family，但没有命中精确 answer-bearing trajectory |
| Reading error | 已命中精确答案轨迹、答案 URL 或 gold text，reader 仍答错 |
| Gotcha failure | 未识别环境陷阱或错误信息 |
| Premise / abstention failure | 接受错误前提，或没有明确反驳前提 |

作者特别提醒：reading error 仍可能由记忆模块选择、压缩或呈现证据不当造成，不能全部归因于固定 reader。

【工程解读】这套分类比单一总分更有诊断价值：major miss 指向召回，minor miss 指向近邻区分，reading error 指向 grounding。若缺少 answer-bearing labels，外部复现很难得到完全相同的错误分布，因为需要知道“命中了哪个任务家族”和“哪条轨迹才是精确答案”。

### 14.2 工具行为

【论文自报】论文将工具调用分为五类：setup/read、harness-guided retrieval、raw trajectory exploration、visual inspection、output validation/other。

Medium 上：

- Codex 平均每题 **21.8 次** raw trajectory-exploration commands。
- AgentRunbook-C 平均每题 **18.0 次** harness-guided retrieval commands。
- C 平均只有 **1.2 次** raw exploration。

C 更早转向 manifest/helper；Codex 在后续轮次中更容易退化为原始文件搜索。这支持“辅助结构不仅节省时间，也约束搜索行为”的解读，但工具次数本身不是效率证明：不同命令的 token、I/O 和执行时间差异很大。

## 15. AgentRunbook-C V2 与在线学习更新

本节内容来自【官方更新页自报】，不是论文 v1 的实验结果。

### 15.1 机制变化

V2 使用 OpenAI Agents SDK，核心工具为：

- `ShellTool`
- `ApplyPatchTool`

在线巩固由 Codex consolidation agent 在每次 query 后读取检索轨迹，更新共享的 `LEARNED_RETRIEVAL_STRATEGY.md`。它不使用下游 reader 的答案、evaluator score 或 aggregate metrics，因此不是根据 gold answer 直接训练。

默认不写新笔记；只有出现强可复用检索经验时才更新策略。检索结果被分为四种证据状态：

| 状态 | 含义 |
|---|---|
| `directly_supported` | 直接支持问题 |
| `contradicts_premise` | 证据反驳问题前提 |
| `near_match_only` | 只有近邻匹配，不足以支持 |
| `insufficient` | 证据不足 |

`near_match_only` 与 `insufficient` 不得作为 positive example 进入 `Past Queries`。这是防止把“查过但没查对”的经验误写成成功策略。

### 15.2 GPT-5.4-mini 更新页结果

【官方更新页自报】页面 headline 称 medium effort 下 V2 比 V1 提高 **1.76 个百分点**，相对提升 2.5%，并快 **33.8%**；相比 Codex 提高 **5.56 个百分点**，相对提升 8.4%，并快 **64.4%**。

页面第一张 operating-point 表的 V2 数值为：

| System | Effort | Accuracy | Latency |
|---|---|---:|---:|
| Codex | Low | 47.30% | 95.00 s |
| Codex | Medium | 66.50% | 130.00 s |
| Codex | Xhigh | 69.90% | 177.20 s |
| V1 | Low | 66.00% | 62.00 s |
| V1 | Medium | 70.30% | 70.00 s |
| V1 | Xhigh | 74.90% | 108.30 s |
| V2 | Low | 66.08% | 23.55 s |
| V2 | Medium | 72.06% | 46.31 s |
| V2 | Xhigh | 74.50% | 116.01 s |

72.06 − 70.30 = 1.76，且 46.31 s 相比 70.00 s 快 33.8%，与 headline 一致。

但同一更新页“combined system”表给出的 V2 数值不同：

| System | Effort | Accuracy | Latency |
|---|---|---:|---:|
| V2 | Low | 65.41% | 26.11 s |
| V2 | Medium | 72.73% | 56.68 s |
| V2 | Xhigh | 75.61% | 130.54 s |

【工程解读】更新页没有在表注中清楚解释两组 V2 数字的实验条件差异。它们可能对应不同在线学习或 harness 配置，但不能拼接成一条曲线，也不能用第二张表的 72.73% 去验证第一组 headline。复现时应固定配置并报告实际版本。

### 15.3 GPT-5.6 Luna 结果

【官方更新页自报】

| System | Effort | Accuracy | Latency |
|---|---|---:|---:|
| V1 | Medium | 68.29% | 62.71 s |
| V1 | Xhigh | 73.61% | 101.83 s |
| V2 | Medium | 66.52% | 24.72 s |
| V2 | Xhigh | 75.17% | 48.94 s |
| Codex | Medium | 64.97% | 98.88 s |
| Codex | Xhigh | 73.39% | 155.51 s |

Luna 上 V2 medium 比 V1 准确率低，但延迟显著下降；V2 xhigh 则同时提高准确率并降低延迟。这说明 effort 是 operating point 的一部分，不能只报告模型名称。

### 15.4 当前仓库中的 V2 与成本边界

【当前仓库】

- `run_eval.py`、脚本和代码已包含 `agentrunbook_c_v2`，但 README 的模块列表仍主要列出 V1 六种方法。
- 默认模型为 `gpt-5.4-mini`，reasoning 为 `medium`，max turns 为 30。
- tool timeout 为 30 s，最大工具输出为 1,048,576 chars。
- query timeout 在 low/medium/xhigh 下分别为 200/800/1200 s。
- Responses transport 默认 `websocket`，SDK API max retries 默认 0。
- 在线学习默认关闭；开启时要求 `prompt_build_max_workers == 1`，即顺序执行。
- 巩固发生在 `post_query_hook`，而 `memory_query_duration_seconds` 只包住 `memory.query()`。

因此，【工程解读】当前 LAFS 使用的 query latency 不包含 post-query 策略巩固成本。若比较在线学习总成本，应额外报告每轮 consolidation 时间、总轮次时间和跨题状态污染风险。无标签在线学习仍然可能学到错误策略，只是它不直接读取 gold label。

另一个重要差异是：当前 `run_agentrunbook_c_v2.sh` 明确不启用 `view_image`，原因是低使用率与高延迟。脚本提示 screenshot-grounded 题可能只能依赖文本或 AXTree。因此 V2 当前实现不应被描述为与论文 V1 等价的完整视觉控制器。

## 16. 局限、伦理与复现边界

### 16.1 论文自报局限

【论文自报】

- 只覆盖定制的 browser/Web 环境，包括 ServiceNow；不覆盖 coding、computer-use 或所有 enterprise Agent。
- 使用预采集轨迹，而不是真实在线学习，难以模拟 Agent 自身行为变化带来的 distribution shift。
- 主要测 context gathering，不直接测端到端任务成功；规划、行动和执行质量没有完整纳入。
- 方法依赖轨迹表示、retriever、prompt 和 coding agent，不是新的基础模型架构或训练方法。

【工程解读】还需要补充三点：预采集轨迹可能使环境相对静态；固定 reader 会把 grounding 错误混入记忆分数；小规模人工题目不足以代表真实企业任务的分布。V2 的在线策略更新缓解了部分静态假设，却又引入题目顺序与跨题迁移变量。

### 16.2 伦理与发布说明

【论文自报】

- 标注团队为 1 名研究生和 3 名本科生；研究生获得工资支持，本科生获得 research credit，均列入 authorship。
- 参与者知情同意；机构认定该研究 IRB exempt。
- 沙箱使用合成任务、名称、记录和 PII，不能据此证明真实用户记忆系统的安全性。
- 生产应用仍需隐私审查、访问控制、数据最小化、过期机制与人工监督。
- 代码和衍生数据采用 Apache-2.0；项目不重新分发原始 benchmark datasets/harness。
- 使用 API 而非商业 ChatGPT subscription。
- Codex 用于答案提议、实验代码和图表；ChatGPT 用于 Figure 5 插图与 GPT-5.5 润色；作者承担最终责任。

【当前仓库】代码与 HF 公共数据现均已发布 Apache-2.0。公共数据有意移除 construction provenance 和易泄露标签，但 AXTree、截图、URL 和操作轨迹仍可能含敏感信息，不能因为“合成沙箱”就免除租户隔离与数据治理。

## 17. 当前工程实现与论文漂移

以下均为【当前仓库】与【工程解读】的对照，不应反向解释为论文原始行为。

| 主题 | 论文 v1 | 当前仓库 |
|---|---|---|
| 查询隐私 | R planner prompt 和 C `question.json` 含 question id、type、image path、original goals 等元数据 | commit `ef67f10a` 后，backend 只收到随机 `query_invocation_id`；R 只用 question text，并忽略 `query_image`；C/Codex 只收到问题文本与可选复制的图片 |
| 隐私回归测试 | 论文未描述此专门测试 | `tests/test_query_privacy.py` 禁止 qid、type、original goals 注入 |
| 方法列表 | 论文主表比较 RAG、R、Codex、C | README 模块列表未完整列出 V2，但执行器和脚本已支持 |
| V2 | 不属于论文 v1 | 新增 OpenAI Agents SDK 后端与可选在线巩固 |
| 证据状态 | C 指令要求处理 near-match 和 contradiction | Codex 可选证据契约会计算、校验 `evidence_status` / `answer_policy`，但 context builder 不把它们送入 reader |
| 视觉 | V1 可检查截图 | V2 wrapper 默认没有 `view_image` |
| “sandbox” | 论文以查询工作区描述隔离 | Codex 命令使用 `--dangerously-bypass-approvals-and-sandbox`；V2 `ShellTool` 设置 `needs_approval=False`，使用本地 `/bin/bash` 并继承环境变量 |
| 路径保护 | 强调受限查询目录 | `ApplyPatch` 有工作区路径检查，但整体不是论文读者容易理解的硬 OS 安全沙箱 |
| 在线延迟 | 论文无在线巩固 | 巩固在 post-query 阶段执行，不计入当前 memory query latency |
| reader 托管 | 论文使用本地 A100 + vLLM | harness 可配置 OpenAI-compatible API；leaderboard 是否接受所有托管方式仍见 issue #15 |
| 公共轨迹数 | 采集池 1,540 | HF 数据卡称 1,870，差异未解释 |

【工程解读】查询隐私加固是正确方向，但它改变了 planner 可见信息，因此当前复现成绩不一定等于论文成绩。把 benchmark metadata 从记忆中移除，也减少了模型利用题号、题型或原始目标猜答案的捷径。

“sandbox”在这里更准确地说是**查询工作目录与工具约束**，不能当作生产级安全隔离。Codex 的 bypass 参数、继承环境变量、可读文件范围和 shell 能力都需要在生产部署中重新设计。

## 18. 影响分数可靠性的公开 issue

核对时以下六个 issue 均为 **open**。本节只复述公开报告与当前代码事实，不声称独立复现，也不把“维护者计划修复”写成“已经修复”。

### 18.1 #14：短语评分把错误金额或矛盾答案判为正确

链接：[Issue #14](https://github.com/xiaowu0162/LongMemEval-V2/issues/14)

【公开 issue 报告】`norm_phrase_set_match` 主要检查 reference phrase 是否出现，不拒绝否定、备选项和额外列表项。报告示例包括：

- gold 为 `100` 时，`$1.00` 因标点归一化为 `100` 而判正确。
- `$100.00` 被归一化为 `10000`，反而判错误。
- `Not Class` 或 `Price; Class; Delivery time` 对 gold `Class` 判正确。
- `true or false`、`It is not false` 对 gold `false` 判正确。
- 额外的 Computer Room 类别没有被排除。

【当前仓库】相关归一化和短语包含逻辑仍然存在。【工程解读】该问题会影响单个题目的 evaluator 可靠性，但 issue 作者没有测量对已发表 aggregate 的影响，不能擅自给出修正后的总分。

### 18.2 #11：reader prompt 中 `\boxed{}` 的反斜杠转义错误

链接：[Issue #11](https://github.com/xiaowu0162/LongMemEval-V2/issues/11)

【公开 issue 报告】两个域的 prompt 写成：

```python
"explanation in \boxed{} explaining why ..."
```

Python 将 `\b` 解析为 backspace（`0x08`），reader 实际收到 `\x08oxed{}`。`\boxed{UNKNOWN}` 使用双反斜杠，因而保持完整。

报告者在一个 240 题 Small 子集中观察到：36 个 abstention UNKNOWN 中，17 个已经正确反驳前提，最终却因格式要求输出 UNKNOWN。所有 128 道 abstention 的 generic UNKNOWN 都计错。

【当前仓库】对应 prompt 仍是单反斜杠。【工程解读】这是 harness bug 与评分规则叠加，不应简单归因为模型不会 abstain。修复后必须重新运行 reader prompt 与 evaluator 回归，而不是手工把这 17 题加分。

### 18.3 #7：传输失败被当作空答案计零

链接：[Issue #7](https://github.com/xiaowu0162/LongMemEval-V2/issues/7)

【公开 issue 报告】harness 捕获 `BadRequestError` 后将响应设为空字符串、usage 设为全零，再按普通答案评分；没有 `instrument_failed` 标记。一次完整 451 题运行中有 7 题因 HTTP 524 得到空响应，影响约 1.55 个百分点。

【当前仓库】client 已设置 `OPENAI_MAX_RETRIES = 10`，但最终仍可能失败；当前路径没有把 instrument failure 与模型真实空答案分开。评论建议优先增加 outcome classification，而不是简单继续加重试。

【工程解读】至少应区分 `ok`、`model_empty`、`instrument_failed`，报告有效分母，并把失败重试作为独立实验事件。否则，不同托管 API 的网络可靠性会直接改变模型排名。

### 18.4 #6：Codex 的证据状态契约处于休眠状态

链接：[Issue #6](https://github.com/xiaowu0162/LongMemEval-V2/issues/6)

【公开 issue 报告】`evidence_status` / `answer_policy` 被计算与校验，但没有进入 reader context。报告者称，在一个 enriched 192-question abstention slice 上，reader 对 115/128 道 gold-abstention 题仍给出断言。把状态接入 reader 的 paired control 没有达到显著门槛：McNemar `p = 0.585`，`n = 128`；报告者因此不声称这会改变 headline。

【当前仓库】`VALID_EVIDENCE_STATUSES`、`ANSWER_POLICY_BY_EVIDENCE_STATUS` 与 payload 校验存在，但 `_build_memory_context_from_output()` 只渲染 `memory_markdown` 和 valid spans。

【工程解读】这是“控制器认为证据不足，reader 却仍被要求回答”的协议断裂。即使接入状态没有显著改变该小样本总分，也不代表该字段可以长期省略；它首先应是证据契约的一部分。

### 18.5 #1：gold 与轨迹 DOM 存在矛盾

链接：[Issue #1](https://github.com/xiaowu0162/LongMemEval-V2/issues/1)

【公开 issue 报告】QID `01f6e679` 询问 body 与 forum 之间的 field。gold 是“不存在这样的 field，body 与 forum 相邻”；但轨迹 `08e662c8` 的 state 3 DOM 显示中间有 `Formatting help +` checkbox。

维护者回复：最初把 Formatting help 当作 link 而不是 field，但计划把问题中的 field 改为 text box，以消除歧义。issue 仍 open。

【HF 数据核对】当前 revision `f152293...` 的修改时间早于该回复；直接检查该 revision，问题仍写 “field name”，gold 未变。

【工程解读】这是题目与可见证据冲突，不只是模型答错。任何分数修正都应同时给出题目版本、数据 revision 和逐题变更记录。

### 18.6 #15：reader 托管与推理配置未明确

链接：[Issue #15](https://github.com/xiaowu0162/LongMemEval-V2/issues/15)

【公开 issue 报告】issue 询问 hosted OpenAI-compatible API 是否可接受、vLLM 是否必需、量化是否允许、采样/thinking/image 设置，以及 controller 是否可换成另一模型。核对时没有维护者回复。

【当前仓库】leaderboard 校验 reader model 字符串包含 `qwen3.5-9b`，judge 包含 `gpt-5.2`，但没有规定精度、硬件、推理引擎、托管方和完整采样配置。

【工程解读】模型名称相同不等于模型行为相同。跨提交至少应固定 tokenizer、量化、vLLM/SDK 版本、thinking、采样、图片预处理、reader prompt 和 judge 版本；否则 LAFS 比较混入了托管差异。

## 19. 对 InsightMem 的启示

本节全部为【工程解读】。InsightMem 当前实现见 [README](../../README.md)、[架构文档](../architecture.md)、[coding service](../../src/insightmem/coding/service.py) 与 [selection](../../src/insightmem/coding/selection.py)。

### 19.1 当前 InsightMem 与 V2 的对应关系

InsightMem 目前是同步、确定性的证据服务：只提供 `/add` 和 `/search`，不生成最终答案；SQLite 中保存不可变原文，按 `user_id` 隔离；检索融合 source-chunk BM25、code-expanded view BM25 与 dense cosine，使用分组 reciprocal-rank 信号，再合并相邻 slice、去重并按相关性与 novelty 选择证据。

默认配置为 chunk 320 units、overlap 40 units、单块最大 6000 字符、`rrf_k = 60`、每路 `leg_max = 200`、evidence bundle 4000 字符、总 evidence 最大 12000 字符。

这与 V2 的 context-gathering 定位相似，但单位、数据结构和能力不同：

- InsightMem 以消息、代码块和 source span 为主，没有 trajectory/state/screenshot 原生模型。
- InsightMem 不调用 LLM 生成 procedure note、transition event 或查询计划。
- InsightMem 没有 coding-agent 文件调查循环，也没有在线策略巩固。
- InsightMem 的同步 Add/Search 更接近低延迟、可审计的工程证据服务，而不是 V2 的生成式控制器。

### 19.2 可借鉴的设计

1. **保留 Add/Search 边界，不把 benchmark 逻辑硬塞进 AML API。**
   如需支持 Web/ServiceNow 轨迹，可增加独立 trajectory adapter，把 state、action、screenshot、URL 和 source span 映射到现有存储。固定 reader 应由调用方负责，InsightMem 继续只返回证据。

2. **原始轨迹与派生索引并存。**
   R 的三池说明摘要能提升召回，但 C 和 oracle 研究说明原始状态仍不可替代。InsightMem 可在现有不可变原文之上增加 event view、procedure/hint view，同时保留可回查的 source span 与 trajectory/state id。

3. **优先做确定性的 manifest/helper，而非默认引入 agent。**
   对长轨迹，先生成稳定清单、状态序号和确定性读取工具；只有当向量检索的 minor-miss 明显时，再评测 agent 调查是否值得延迟成本。

4. **多模态证据需要独立设计。**
   当前 dense 与 BM25 主要处理文本。截图应保存为受控资产，通过引用进入证据，而不是把 base64 塞进 embedding；应单独评测 AXTree、截图和二者融合的收益。

5. **前提矛盾必须是显式证据状态，并真正送达 reader。**
   可定义 `supported`、`contradicts_premise`、`near_match`、`insufficient`，但必须贯穿检索、选择、输出契约和调用方 prompt。不能重蹈 issue #6 中“算了但没传给 reader”的断链。

6. **建立三层评测，而不是只看最终答案分数。**
   - retrieval：answer-bearing trajectory/span recall、major/minor miss；
   - reader grounding：证据已命中时是否答对、是否接受错误前提；
   - end-to-end：最终答案、延迟和失败率。
   InsightMem 不控制 reader，但仍应报告证据命中与输出契约，避免把 reader 能力误算成记忆能力。

7. **完整记录成本。**
   除 search latency 外，还应记录 add/index、导出、consolidation、reader 与 evaluator 成本。可内部采用 LAFS 思想，但不能把只有 query latency 的数字当作端到端成本。

8. **把公开 issue 变成回归测试。**
   至少覆盖：金额与否定短语评分、prompt 中转义、API 失败分类、证据状态传递、gold 与轨迹冲突、reader 配置指纹。当前 profile/embedding identity 不一致时拒绝启动是良好基础，可进一步扩展到 reader、prompt、数据与 evaluator 版本。

9. **在线学习保持默认关闭，并限制作用域。**
   若未来加入策略巩固，应使用无标签、可审计的更新，限定在同一用户或租户内，记录策略版本，并支持回滚。评测时固定题目顺序与是否启用在线学习，分别报告巩固成本。

10. **安全不能沿用“sandbox”名称。**
    若未来提供文件调查工具，需要独立处理租户隔离、路径与 symlink 逃逸、shell 权限、环境变量泄露和 prompt injection。查询工作目录只是实现细节，不是安全边界。

### 19.3 不建议直接照搬的部分

- 不建议为了“像 V2”而给 InsightMem 的每次 Search 默认加入 LLM planner：主表显示 R 相比 slice+notes 增加约 26 秒延迟，是否值得取决于任务。
- 不建议默认让 coding agent 遍历全部用户记忆：这会改变当前同步、可审计和小预算的服务定位。
- 不建议把 V2 在线策略当成跨用户共享记忆：这可能造成租户间信息泄露，也会让评测结果依赖历史查询顺序。
- 不应声称 InsightMem 已实现 LongMemEval-V2、已达到其成绩，或可直接与其主表排名比较。

## 20. 结论

LongMemEval-V2 的核心贡献不是把上下文从几千 tokens 扩到 115M，而是把长期记忆重定义为**对定制环境的可迁移经验**：状态、状态转移、流程、陷阱和前提。451 道人工题、最多约 500 条轨迹和 200K 证据预算，使“检索并读懂”成为独立于最终答题模型的评测对象。

论文自报结果显示两条可行路线：AgentRunbook-R 用规划与多池检索换取较低延迟，AgentRunbook-C 用文件调查、manifest 和 helper 换取更高准确率。C 的 Small/Medium 平均准确率为 72.5%，但 gotchas 不如 Codex，且 coding-agent 延迟显著更高；LAFS 正是为这种准确率—延迟折中而设计，而不是单点排行榜。

V2 更新进一步尝试让控制器从检索经验中在线改进策略。它不再完全静态，但也带来顺序依赖、巩固成本和新的复现变量。当前仓库与论文之间已经出现查询隐私、视觉工具、证据状态传递、sandbox 安全和在线成本口径等漂移；六个 open issues 又提示评分、prompt、传输失败、gold 与 reader 配置仍可能影响分数。

对 InsightMem 最稳妥的启示是：保留低延迟、确定性、可回查的证据服务定位，在原始 span 之上逐步增加轨迹与状态结构，并把 retrieval、reader grounding、end-to-end 和完整成本分开评测。任何新能力都应有独立证据，而不是借用 LongMemEval-V2 的论文分数为自己背书。
