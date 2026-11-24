# 02 写入（第 2 周）

> 上一章：[01 边界与地图](01-boundaries.md) · 下一章：[03 存储与索引](03-storage.md)
> 预计：6–8 小时
> 本章目标：能把“值得记”变成可校准规则；能设计带来源、时间和版本的写入协议；能区分幂等、去重与并发控制。

---

## 1. 本周要解决的问题

写入不是“把聊天塞进数据库”。它要同时决定：

1. **记不记**：这条信息未来还有用吗？
2. **记什么**：原文、笔记、事实，还是规则？
3. **何时记**：同步写入，还是后台整理？
4. **怎样提交**：重复、冲突、失败和并发时如何处理？
5. **怎样证明质量**：抽取准不准、约束丢没丢、成本是多少？

本章用一条写入流水线串联这些问题。

---

## 2. 写入流水线

```text
event
  │
  ├─ 1. 校验 scope、权限、schema
  ├─ 2. 幂等检查
  ├─ 3. 原文/事件事务落库
  ├─ 4. salience 判断：NOOP 或继续
  ├─ 5. 抽取候选 fact / note / rule
  ├─ 6. 检索相似记忆
  ├─ 7. 判定 ADD / UPDATE / DELETE / NOOP / TOMBSTONE
  ├─ 8. 提交新版本与来源关系
  └─ 9. 更新索引、缓存与审计日志
```

原则：**先保存可审计来源，再生成派生表示；失败时不能留下半条事实。**

---

## 2.1 显著性：未来任务效用，而不是情绪强度

Anthropic 的 memory notes 框架把 salience 作为写入筛选依据。工程上不要把它实现成“语气强就记”，而应估计未来效用。

一个可解释的打分起点：

```text
salience = task_utility
         + surprise
         + persistence
         + reuse_value
         - redundancy
         - ephemeral_detail
```

各因子需要校准，而不是凭感觉定权重：

| 因子 | 高值例子 | 低值例子 |
|---|---|---|
| task_utility | 影响后续步骤的约束 | 与当前任务无关的寒暄 |
| surprise | 与既有记忆矛盾的新信息 | 重复确认 |
| persistence | 长期偏好、项目决策 | 一次性情绪 |
| reuse_value | 可复用技能、稳定事实 | 某个按钮的临时位置 |
| redundancy | 已被更完整记录覆盖 | 新来源 |
| ephemeral_detail | 一次性的 token 数值 | 通用配置原则 |

### 校准方法

1. 从真实会话采样候选片段；
2. 人工标注“未来 30 天是否有用”及理由；
3. 在 dev set 上调阈值；
4. 在 test set 上测 precision / recall；
5. 按查询类型分别报告，不只看总体均值。

只记录失败可能丢掉成功路径中的稳定偏好；全量记录又会把噪声写进长期记忆。正确目标是**用较低写入误报保存高价值经验**。

---

## 2.2 三种写入表示

| 表示 | 保留什么 | 优点 | 缺点 | 适合 |
|---|---|---|---|---|
| 全量原文 | 消息、工具调用、结果、时间、角色 | 无损、可审计、可重处理 | 体积大、噪声多 | 编码、合规、证据问答 |
| Memory notes | 经验、规则、偏好、结论 | 紧凑、可读、易人工编辑 | 可能丢细节或产生摘要偏差 | 个人助手、长期协作 |
| Fact / graph | subject、predicate、object、关系、有效期 | 可查询、可更新、适合多跳 | 抽取错误会固化，schema 复杂 | 时间事实、企业知识 |

三者不必互斥。常见组合是：

```text
原文 episode 作为 ground truth
  → notes 用于可读摘要
  → facts 用于结构化查询
  → 所有派生记录指向原文
```

### 选型判断

问三个问题：

- 哪种信息丢了就找不回来？
- 哪种信息需要频繁更新或关系查询？
- 哪种信息必须逐字引用？

编码任务里，错误串、文件路径、失败尝试和改动原因通常不能丢；个人助手里的称呼和偏好适合 notes；企业知识里的组织关系和时间事实更适合 graph。

---

## 2.3 Fact schema

最小结构化事实可以写成：

```text
Fact {
  fact_id,
  user_id,
  project_id,
  subject,
  predicate,
  object,
  source_episode_id,
  source_span,
  speaker,
  event_time,
  ingested_at,
  valid_from,
  valid_to,
  confidence,
  extraction_method,
  version,
  status
}
```

关键约束：

- **speaker** 决定“谁说的”。用户说“她喜欢茶”不等于“用户喜欢茶”；
- **source_span** 必须可回到原文；
- **confidence** 表示证据强度，不是抽取模型的自评概率；
- **extraction_method** 区分规则、LLM、人工和导入；
- **status** 至少区分 active、invalidated、deleted、archived。

### 抽取质量指标

不要只数抽取了多少条。分别报告：

| 指标 | 定义 |
|---|---|
| Fact precision | 抽取出的事实中，有证据支持的比例 |
| Fact recall | 应抽取事实中，被正确抽取的比例 |
| Slot accuracy | subject / predicate / object / time 各字段准确率 |
| Faithfulness | 派生记录是否引入原文没有的信息 |
| Provenance coverage | 有有效 source span 的记录比例 |

LLM 抽取失败常表现为“看起来更完整”：自动补全时间、把代词归错人、把否定丢掉。因此需要保留原句，而不是只存模型输出。

---

## 2.4 提交决策：ADD / UPDATE / DELETE / NOOP / TOMBSTONE

拿到候选后，先检索相似记忆，再决定操作：

| 操作 | 条件 | 结果 |
|---|---|---|
| `ADD` | 没有足够相似或冲突记录 | 新增版本 |
| `UPDATE` | 同一主题的新事实取代旧事实 | 旧版本失效，新版本活跃 |
| `DELETE` | 用户明确要求删除，或数据不应保留 | 删除业务可见记录 |
| `NOOP` | 重复、低价值、证据不足 | 不产生新记忆 |
| `TOMBSTONE` | 防止备份恢复或重放把旧记录带回来 | 保留删除标记而非内容 |

伪代码：

```python
candidate = extract(event)
if not is_salient(candidate):
    return NOOP

similar = find_similar(scope, candidate)
decision = compare(candidate, similar)

if decision == NOOP:
    return

with transaction():
    assert_expected_version(similar)
    write_version(candidate, decision)
    write_provenance(candidate, event)
    write_audit(decision)
```

### 冲突不等于覆盖

以下情况不应自动覆盖：

- 不同说话人；
- 不同项目或时间范围；
- 证据不足的推断；
- 同一用户在不同场景的偏好；
- 用户明确要求保留历史。

更安全的策略是保留两个版本，并标注适用范围与有效期。完整讨论见 [06 更新与治理](06-governance.md)。

---

## 2.5 幂等、去重与并发是三个问题

### 幂等

同一个请求重试多少次，结果相同。常见键：

```text
(user_id, request_id) + payload_hash
```

- 同键同 payload：返回旧结果；
- 同键不同 payload：报冲突；
- 不同 request_id 但相同内容：可能仍是两条合法事件。

### 去重

相同或相似内容是否合并。原文去重可能破坏“发生过几次”的信息，因此常保留每次 occurrence，只合并检索表示。

### 并发

两个写入同时更新同一主题时，幂等键无法防止覆盖。需要：

```sql
UPDATE memory
SET version = version + 1, ...
WHERE memory_id = ? AND version = ?;
```

或使用事务、串行化队列、版本号 / CAS。重试必须重新读取最新版本，而不是盲目重放旧 payload。

### 最小故障注入实验

- 同一 Add 连续重放 5 次；
- 两个并发请求使用同一 request_id；
- 两个并发 UPDATE 使用同一 expected_version；
- 原文落库后让 LLM 抽取失败；
- 原文和派生索引提交到一半时终止进程。

预期：原文不重复、冲突可识别、旧版本不被静默覆盖、失败可恢复。

---

## 2.6 双时间：事件时间与写入时间

```text
valid time:    [2026-10-01, 2026-11-20)
ingested_at:   2026-11-21
```

它表示“用户从 10 月 1 日起住在上海，11 月 20 日结束；系统在 11 月 21 日才知道”。

只用 `ingested_at` 会把迟报事实放到错误的历史位置。Zep 的 bi-temporal 设计将 valid time 与 ingest time 分开，使“当时知道什么”和“现在有效什么”都可查询。

实验：

1. 写入旧事实；
2. 迟报一个覆盖旧时间段的新事实；
3. 查询“当时有效”和“当前有效”；
4. 比较旧事实误用率与历史回溯准确率。

---

## 2.7 写入时机：hot path 与 background

| 路径 | 何时发生 | 优点 | 风险 | 适合 |
|---|---|---|---|---|
| Hot path | 用户请求期间同步执行 | 立即可用、一致性直观 | 增加延迟，失败影响请求 | 原文、幂等、明确用户指令 |
| Background | 会话后或定时执行 | 批量总结、成本可控、可重试 | 滞后、任务状态复杂 | dreaming、批量抽取、图整合 |

[LangGraph Memory overview](https://docs.langchain.com/oss/python/langgraph/memory) 将两者列为不同写入策略。选型依据：

- 是否需要下一条消息立即使用；
- 抽取失败是否允许稍后补；
- 用户能否等待索引完成；
- 数据量是否适合批处理。

推荐模式：

```text
hot path: 原文 + event metadata 原子提交
background: 派生 notes / facts / embeddings
promotion: 仅当质量检查通过后进入常驻注入层
```

后台任务需要任务 ID、状态、重试次数、幂等键和失败样本。不能让“ dreaming 还没跑完”成为静默丢记忆。

---

## 2.8 InsightMem 的 Add：一个原文优先参考实现

[InsightMem 架构](../../docs/architecture.md#add) 的 Add 流程是：

1. 对 `session_id + messages` 计算 payload hash；
2. 同 `request_id` 同 payload 返回旧 chunk count；
3. 不同 payload 抛冲突；
4. 解析消息类型并生成稳定 ID；
5. 切分 chunk，保存 source 与 view；
6. 批量 embedding 并归一化；
7. 在一个事务中写入 request、message、chunk、view、source、vector。

它提供了：

- 原文保真；
- 幂等与冲突检测；
- 单事务提交；
- 用户级隔离；
- 可审计来源。

它没有提供：

- salience 抽取；
- 事实整合与冲突解决；
- valid time / ingest time；
- 后台 dreaming；
- 自动遗忘。

因此它是一个“**原文写入 + 派生检索表示**”的工程样本，不是完整的 fact memory 写入器。

---

## 2.9 常见失败模式

| 失败 | 后果 | 防护 |
|---|---|---|
| 只记失败 | 稳定偏好与成功经验缺失 | 按未来效用采样正负经验 |
| 抽取过度 | 噪声和错误固化 | 阈值校准、保留来源、允许 NOOP |
| 幂等键当成并发锁 | 并发覆盖 | 版本号 / CAS / 事务 |
| 原文未落库就抽取 | 抽取失败导致完全丢记忆 | 先提交来源，再异步派生 |
| 用入库时间替代事件时间 | 历史查询错误 | 双时间字段 |
| 删除主库不删索引 | 已删内容仍被召回 | tombstone + 索引失效 + 验证 |
| 固定生成 10/30 条 | 人为截断或灌水 | 按数据决定数量并记录生成参数 |

---

## 2.10 动手：L1 三种写入策略

完整步骤见 [实验手册 L1](labs.md#l1)。

### 不要一次改变两个变量

“原文 + BM25”对“笔记 + 向量”同时改变了表示和检索器，无法归因。采用二维矩阵：

| 表示 \ 检索器 | BM25 | Dense |
|---|---|---|
| 全量原文 | A1 | A2 |
| LLM notes | B1 | B2 |
| 抽取 facts | C1 | C2 |

### 冻结条件

- 同一语料、同一 dev/test 划分；
- 同一 answerer、prompt、top_k；
- 固定 embedding 模型与版本；
- 固定随机 seed；
- 不把 gold 答案泄漏给写入器；
- 去掉固定 10 notes / 30 facts 限制，或将其作为单独消融。

### Gold 不只包含答案

每条 gold query 至少记录：

```text
query
answer
evidence turn/message ID
required constraints
expected abstention
query type: single-hop / multi-hop / temporal / update / adversarial
```

### 报告指标

| 指标 | A1 | A2 | B1 | B2 | C1 | C2 |
|---|---:|---:|---:|---:|---:|---:|
| Fact precision / recall | | | | | | |
| Evidence Recall@k | | | | | | |
| Answer accuracy | | | | | | |
| Constraint retention | | | | | | |
| Write bytes | | | | | | |
| LLM tokens | | | | | | |
| Write p50 / p95 | | | | | | |

同时给出至少 3 个失败样本和复现命令。`hit@5` 只能证明检索命中，不能证明写入策略更优。

---

## 2.11 验收

- 能把 salience 解释为未来任务效用，并说明如何校准；
- 能设计带 speaker、source span、valid time、version 的 Fact schema；
- 能区分 ADD、UPDATE、NOOP、DELETE 和 TOMBSTONE；
- 能解释幂等为什么不等于并发控制；
- 能设计一个“表示 × 检索器”的公平对比，而不是只比较两个混合方案。

---

## 2.12 机制依据与延伸阅读

### 一手依据

- [Anthropic: The components of agent memory](https://www.anthropic.com/research/components-of-agent-memory)：salience、memory notes、dreaming 与注入。
- [Mem0 论文, arXiv:2504.19413](https://arxiv.org/html/2504.19413v1)：抽取、整合与检索流程。[中文精读](../../docs/papers-zh/03-systems.md#mem0)
- [Mem0 当前实现说明](https://github.com/mem0ai/mem0#new-memory-algorithm-april-2026)：2026 README 的 single-pass ADD-only 算法。它与论文版 UPDATE/DELETE 语义不同，不能混用分数与实现。
- [Zep, arXiv:2501.13956](https://arxiv.org/html/2501.13956v1)：episode、fact、edge 与双时间。[中文精读](../../docs/papers-zh/03-systems.md#zep)
- [Generative Agents, arXiv:2304.03442](https://arxiv.org/html/2304.03442v2)：memory stream、importance 与 reflection。[中文精读](../../docs/papers-zh/01-foundations.md#generative-agents)
- [LangGraph Memory overview](https://docs.langchain.com/oss/python/langgraph/memory)：hot path / background 写入。[中文参考译文](../../docs/langchain-memory-zh.md)
- [Letta memory & dreaming](https://docs.letta.com/letta-code/memory)：文件式记忆与后台整理。

### 学习资源

- [LangChain Academy](https://academy.langchain.com/)：用 store 和 thread state 对照不同写入时机。
- [Awesome-AI-Memory](https://github.com/IAAR-Shanghai/Awesome-AI-Memory)：按 memory operation 与 framework 找论文。
- 后续写入评测参考 [LoCoMo, arXiv:2402.17753](https://arxiv.org/html/2402.17753v1)，但注意其合成对话不等于真实生产分布。

---

## 本章产出

1. 一张 Fact schema；
2. 一张写入决策表；
3. 一组幂等与并发测试；
4. L1 的六格对比表和失败样本。

下一章：[03 存储与索引](03-storage.md)。
