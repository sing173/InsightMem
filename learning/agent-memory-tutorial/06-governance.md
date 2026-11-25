# 06 更新与治理（第 6 周）

> 上一章：[05 融合与选择](05-fusion.md) · 下一章：[07 评测](07-evaluation.md)
> 阶段：阶段一做 hot path/background 与治理，阶段二加入 self-editing、dreaming 和共享记忆。
> 预计：6–8 小时
> 本章目标：能处理冲突、迟到证据、并发和撤回；能区分失效、归档、遗忘与法律擦除；能设计删除全链传播和隔离验证。

---

## 1. 本周要解决的问题

记忆不是只读档案。用户会改口，事实会过期，系统会迟到，后台任务会并发，用户会要求删除。治理要回答：

1. 新事实与旧事实是什么关系？
2. 查询“当前”与“当时”分别返回什么？
3. 迟到证据能否改写历史视图？
4. 删除如何传播到 notes、索引、缓存和备份？
5. 自动遗忘如何避免误删？
6. 多用户、多项目如何隔离？

---

## 2. 四种更新语义

| 语义 | 做法 | 代表 | 优点 | 风险 |
|---|---|---|---|---|
| 追加 | 只写不改 | InsightMem；[Mem0 本地精读](../../docs/papers-zh/03-systems.md#mem0) 的 2026 ADD-only | 保真、可审计 | 旧事实仍可能误用 |
| 覆盖 | 直接替换 | 简单 profile | 当前状态简单 | 历史丢失、难回滚 |
| 失效 | 旧版本标记失效，历史保留 | [Zep / Graphiti 本地精读](../../docs/papers-zh/03-systems.md#zep) | 支持 as-of 与审计 | 查询和时间逻辑复杂 |
| 离线整理 | dreaming 重写、合并、纠错 | [Anthropic](https://www.anthropic.com/research/components-of-agent-memory) / [Letta](https://docs.letta.com/letta-code/memory) | 降低噪声、形成高层知识 | 成本高、可能引入新错 |

选择标准不是“哪种更先进”，而是：

- 是否需要“当时为真”的历史？
- 是否需要逐条撤销和回滚？
- 当前状态是否必须唯一？
- 后台整理失败时能否回退？

---

## 3. 完整双时间

### 3.1 两套区间

不要把世界侧失效和系统侧失效都塞进一个 `valid_to`：

```text
valid interval:     [valid_from, valid_to)
recorded interval:  [recorded_from, recorded_to)
```

| 时间 | 含义 |
|---|---|
| `valid_from` | 事实在世界中开始为真 |
| `valid_to` | 事实在世界中不再为真 |
| `recorded_from` | 系统开始相信/记录该事实 |
| `recorded_to` | 系统停止将该版本视为当前记录 |

统一使用半开区间，避免边界重复：

```sql
valid_from <= t AND t < valid_to
recorded_from <= s AND s < recorded_to
```

NULL 可表示“未知”或“仍有效”，但必须在 schema 中明确语义，不能混用。

### 3.2 当前与 as-of 查询

当前有效：

```sql
WHERE valid_from <= :now
  AND (valid_to IS NULL OR :now < valid_to)
  AND (recorded_to IS NULL)
```

历史事实：

```sql
WHERE valid_from <= :event_time
  AND (valid_to IS NULL OR :event_time < valid_to)
```

系统当时知道什么：

```sql
WHERE recorded_from <= :knowledge_time
  AND (recorded_to IS NULL OR :knowledge_time < recorded_to)
```

### 3.3 迟到证据

例：

```text
2026-10-01  用户搬到上海
2026-11-20  用户搬离上海
2026-11-21  系统才收到第二条消息
```

“当前”应无此 active fact；“2026-11-10 的历史状态”应仍返回上海；“系统在 2026-11-21 之前知道什么”不应假装早就知道搬离。

[Zep 的 facts 文档](https://help.getzep.com/facts)列出四个 fact timestamps；具体字段名和 API 可能随版本变化，但 valid 与 recorded 的区分是核心。

---

## 4. 冲突仲裁

### 4.1 先分类，再决定

| 关系 | 例子 | 处理 |
|---|---|---|
| 相同 | 同一事实的重复说法 | NOOP 或合并来源 |
| 互补 | “住上海” + “在 X 公司工作” | 都保留 |
| 冲突 | “住北京” vs “住上海”，同时间同 scope | disputed / resolved |
| 异域 | 项目 A 用 Python，项目 B 用 Go | 按 scope 分别保留 |

冲突判断必须考虑：

- subject 与 speaker；
- project / tenant / session；
- 事件时间；
- 证据可信度；
- 是否只是不同语境。

### 4.2 状态机

```text
seen → disputed → resolved → superseded
  │        │          │
  │        │          └─ 新版本成为当前
  │        └─ 证据不足，保留双方并标注
  └─ 低价值或重复，NOOP
```

不要无条件“后来者覆盖”。新信息可能更晚写入，但事实更早发生；也可能来自不可靠 speaker。

### 4.3 冲突记录

```text
conflict_id
fact_ids[]
relation
evidence[]
decision
decision_method
resolved_by
resolved_at
```

 unresolved 冲突应允许 `retain_both`，并在生成时提示模型存在矛盾，而不是随机选一条。

---

## 5. 并发与离线合并

### 5.1 请求级幂等

```text
UNIQUE(user_id, request_id)
```

同 request 重放返回旧结果；不同 payload 报冲突。它防重复提交，不防两个不同 request 同时更新同一 fact。

### 5.2 版本控制

```sql
UPDATE fact
SET object = ?, version = version + 1, ...
WHERE fact_id = ? AND version = ? AND recorded_to IS NULL;
```

失败说明版本已变化，需要重新读取并重新仲裁。

### 5.3 离线 dreaming 合并

后台任务必须：

- 读取最新版本，而不是任务启动时的旧快照；
- 使用 compare-and-swap；
- 不覆盖任务运行期间的新人工纠正；
- 可重试、幂等、可回滚；
- 记录输入版本与输出版本。

推荐流程：

```text
snapshot → propose changes → re-read current → CAS commit → audit
```

## 本章实战：自编辑、dreaming 与共享记忆

> 当前未实现阶段二治理 Notebook。现有 `email-agent` 不含 core memory 自编辑、版本/CAS、共享 block 或删除传播；本节代码属于后续 memory OS 项目。

阶段二把治理从“应用更新数据”扩展为“Agent 维护自己的记忆”：

| 操作 | 谁触发 | 必须满足 |
|---|---|---|
| Edit core memory | Agent 或用户显式指令 | 保留旧版本、diff、理由与可回滚点 |
| Append archival memory | Agent 工具或 background task | 带来源、scope、去重与置信度 |
| Dreaming / consolidation | 后台任务 | 不读取 gold label；不覆盖新人工纠正；可重试 |
| Share memory block | 多 Agent 协作 | 明确 read/write 权限、租户边界与审计 |
| Forget / delete | 用户或治理策略 | 全链传播，恢复后不复活 |

#### 项目步骤一：从 Python dictionary 开始自编辑

课程先从一个最小 core memory 开始：

```python
core_memory = {"human": "", "persona": ""}


def core_memory_save(section: str, memory: str) -> str:
    core_memory[section] += memory
    return f"Updated {section} memory"
```

随后把函数暴露为 tool，并把 memory 渲染进 system prompt。用户说“我的名字其实是 Charles”，Agent 应调用工具，再基于新 memory 回复。

生产版本不能只保存一个可变 dictionary，至少需要：

```text
block_id · old_value · new_value · reason · actor · version · timestamp
```

#### 项目步骤二：从反馈更新程序记忆

```python
def consolidate_feedback(trajectory, feedback, current_prompt):
    proposal = optimizer.invoke({
        "trajectory": trajectory,
        "feedback": feedback,
        "current_prompt": current_prompt,
    })
    validate_prompt_schema(proposal)
    return write_new_version(proposal, reason="user-feedback")
```

后台任务必须使用与在线写入相同的版本检查，否则可能覆盖用户刚做的人工纠正。

#### 项目步骤三：多 Agent 共享 memory block

```python
shared_company = memory_store.create_block(
    label="company",
    value="Agent OS builds deployment tools.",
    limit_chars=10_000,
)

evaluator.attach_block(shared_company.id, permission="read")
outreach.attach_block(shared_company.id, permission="read_write")
```

共享同一 block ID 会让修改在两个 Agent 的上下文中同步出现；但生产系统还要限制写权限、记录审计，并避免把用户隐私放入共享块。

多 Agent 通信有两种常见形态：

- **独立 thread + message tool**：按需发送结构化消息；
- **group chat**：共享消息历史，适合 round-robin 协作。

### 检查点

- 自编辑与普通文本生成有什么区别？
- 为什么 core memory 需要字符上限？
- 后台 consolidation 为什么不读取 gold label？
- 共享 block 与共享 thread 有什么区别？
- 如何验证一个 Agent 的修改没有污染另一个租户？

### 练习

实现一个带版本的 core memory block，注入一次“Agent 修改 → 用户纠正 → 后台整理”序列，验证后台任务不会覆盖最新版本；再创建两个 Agent 共享只读 block，测试越权写入被拒绝。

[Letta Memory & Dreaming](https://docs.letta.com/letta-code/memory) 提供了 `/remember`、MemFS 与后台整理的工程参考；实现时可以借鉴，但不应把产品行为当作唯一标准。

---

## 6. 生命周期与遗忘

```text
active → cold → archived → forgotten
```

| 状态 | 可检索 | 可注入 | 说明 |
|---|---|---|---|
| active | 是 | 是 | 当前可用 |
| cold | 可降权 | 通常否 | 低价值但保留 |
| archived | 按策略 | 通常否 | 历史审计 |
| forgotten | 否 | 否 | 内容已删除或匿名化 |

[MemoryBank 本地精读](../../docs/papers-zh/01-foundations.md#memorybank) 的时间衰减是启发式：时间和重要性影响保留/强化。工程上还要防止：

- 一次命中就永久强化；
- 长期未访问误删高价值规则；
- 归档摘要仍引用已删除原文；
- 缓存淘汰被误称为记忆遗忘。

**缓存淘汰、记忆降级、业务删除和法律擦除是不同操作。**

---

## 7. 隐私删除与撤回

### 7.1 删除状态链

```text
delete request
  → tombstone
  → source records
  → derived facts / notes
  → graph edges / community summaries
  → lexical postings
  → dense vectors
  → caches / prompt cache
  → verify
  → backup retention policy
```

### 7.2 Tombstone

删除后保留最小标记：

```text
memory_id, deleted_at, deletion_request_id
```

用途：

- 防止 backup restore 复活；
- 防止重放任务重新抽取；
- 支持删除审计；
- 避免长期保存被删内容。

### 7.3 验证面

至少覆盖：

1. 直接 ID 查询；
2. lexical 查询；
3. dense 查询；
4. graph traversal；
5. cache 命中；
6. 导出；
7. 备份恢复后重放 tombstone；
8. 后台任务重跑。

### 7.4 删除与 machine unlearning

数据库删除不等于消除模型训练影响。若数据已用于微调，需要单独评估 [machine unlearning](https://arxiv.org/abs/2405.07406)、重训或模型替换策略。

[GDPR Article 17](https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng) 规定删除权及例外；工程实现应结合法务要求，不能把“数据库 DELETE”直接等同于满足所有合规义务。

---

## 8. 隔离、权限与审计

### 8.1 Namespace

```text
(tenant_id, user_id, project_id, thread_id)
```

每张表、每个索引、每个缓存键和后台任务都必须遵守同一 scope。

### 8.2 读写权限

- 写入者是否有权创建该 scope 的记忆？
- 读取者是否能访问所有候选来源？
- 共享记忆是否允许项目内跨用户？
- 后台任务是否使用最小权限？
- 导出是否经过单独授权？

### 8.3 审计日志

至少记录：

```text
actor, action, memory_id, old_version, new_version,
source, reason, timestamp, request_id
```

审计日志本身也要隔离、限权、设保留期。

---

## 9. InsightMem 的治理边界

InsightMem 提供：

- `user_id` 级检索隔离；
- immutable source messages/chunks；
- request 幂等与 payload 冲突；
- 单事务 Add；
- embedding identity / build fingerprint 校验。

它没有提供：

- fact valid time / recorded time；
- 冲突仲裁；
- TTL 或自动遗忘；
- 用户主动纠错/删除 API；
- 后台 dreaming；
- tombstone 与备份恢复策略。

因此它适合作为“原文证据层”，不能直接承担完整的个人记忆治理。

---

## 10. 常见失败模式

| 失败 | 后果 | 防护 |
|---|---|---|
| 后来者无条件覆盖 | 旧但真实的事实被替换 | 冲突分类 + 双时间 |
| 只用 ingested_at | 历史视图错误 | valid/recorded 双区间 |
| 删除主库不删向量 | PII 仍被召回 | 全链 tombstone |
| 后台任务覆盖新人工纠正 | 用户修正失效 | CAS + 版本检查 |
| 归档摘要引用已删原文 | 删除后信息泄漏 | 派生图传播删除 |
| 只按访问频率遗忘 | 罕见但关键规则被删 | 价值/重要性联合评估 |
| scope 只在 SQL 层 | 共享缓存泄漏 | 每个索引与缓存独立测试 |

---

## 11. 动手：L6 矛盾序列

完整步骤见 [实验手册 L6](labs.md#l6)。

### 扩展测试集

| 测试族 | 规模建议 | 测什么 |
|---|---:|---|
| 顺序 old → new | 20+ | 当前值、历史值 |
| 同时冲突 | 50+ | retain_both 与消解 |
| 迟到证据 | 50+ | as-of 快照一致性 |
| scope 交叉 | 50 用户 × 项目 | 项目偏好不污染全局 |
| 撤回/删除 | 20+ | 派生记录复活 |
| 并发/崩溃 | 1000 请求 | 幂等、CAS、恢复 |

### 指标

- 旧事实误用率；
- 新事实命中率；
- as-of 准确率；
- 冲突误判率；
- 删除后泄漏率；
- 重复写入率；
- 恢复后版本一致率。

删除测试的泄漏率目标应为零；不要用“平均分还行”掩盖单条 PII 泄漏。

---

## 12. 验收

- 能区分 `valid_to` 与 `recorded_to`，并写出半开区间查询；
- 能把冲突分成相同、互补、冲突和异域；
- 能设计 unresolved 状态，而不是强迫自动覆盖；
- 能解释幂等与 CAS 的分工；
- 能区分缓存淘汰、归档、遗忘和法律擦除；
- 能设计删除后的全检索面验证。

---

## 13. 机制依据与延伸阅读

### 一手依据

- [Zep, arXiv:2501.13956](https://arxiv.org/html/2501.13956v1)：episode、fact、edge 与双时间。[中文精读](../../docs/papers-zh/03-systems.md#zep)
- [Zep v4 Facts](https://help.getzep.com/facts)：四个 fact timestamps 与更新语义。
- [Mem0 论文](https://arxiv.org/html/2504.19413v1)：ADD/UPDATE/DELETE/NOOP 与矛盾处理。[中文精读](../../docs/papers-zh/03-systems.md#mem0)
- [Mem0 当前实现](https://github.com/mem0ai/mem0#new-memory-algorithm-april-2026)：2026 single-pass ADD-only，不能与论文版混写。
- [MemoryBank, arXiv:2305.10250](https://arxiv.org/abs/2305.10250)：时间衰减与强化。[中文精读](../../docs/papers-zh/01-foundations.md#memorybank)
- [MemGPT, arXiv:2310.08560](https://arxiv.org/abs/2310.08560)：eviction 不等于 deletion。[中文精读](../../docs/papers-zh/01-foundations.md#memgpt)
- [Letta Memory](https://docs.letta.com/letta-code/memory)：文件编辑、版本与 dreaming。
- [Machine Unlearning Survey](https://arxiv.org/html/2405.07406v3)：训练影响消除与数据库删除的区别。
- [GDPR Article 17](https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng)：删除权与例外。

### 术语提醒

- **[MemOS 本地精读](../../docs/papers-zh/03-systems.md#memos)**：MemCube 与明文/激活/参数记忆调度；
- **[MemoryOS 本地精读](../../docs/papers-zh/03-systems.md#memoryos)**：STM/MTM/LPM 三层对话记忆。

两者都借用 OS 概念，但机制不同，不能混用。

---

## 本章产出

1. 一张双时间 schema；
2. 一张冲突状态机；
3. 一份删除传播清单；
4. L6 的 scope、迟到、撤回、并发测试结果。

下一章：[07 评测](07-evaluation.md)。
