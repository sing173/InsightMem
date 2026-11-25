# 05 融合与选择（第 5 周）

> 上一章：[04 召回](04-retrieval.md) · 下一章：[06 更新与治理](06-governance.md)
> 阶段：阶段一做上下文装配，阶段二加入 memory pressure 与 paging。
> 预计：6–8 小时
> 本章目标：能把多路候选融合成稳定排名；能在融合前做规范化去重；能设计去重、bundle、多样性和全局预算，并理解每一步的代价。

---

## 1. 本周要解决的问题

召回产生候选，融合产生统一排名，选择产生最终注入列表。三者常被混为一谈：

```text
Recall → canonicalize → fuse → filter → bundle/dedup → budget → order
```

本章回答：

1. 为什么不能直接把不同分数相加？
2. RRF 的 rank 到底是什么？
3. 重复内容应在融合前还是融合后处理？
4. bundle 与成员为什么必须共存？
5. 如何在固定预算下保留互补证据？

## 本章实战：装配上下文与处理 memory pressure

> 当前未实现 context builder 或 memory-pressure Notebook。`04-evaluation.ipynb` 只比较记忆配置，不覆盖 token 预算、paging 和上下文驱逐；本节应保留为机制与实现骨架。

阶段一的 context builder 是确定性流水线：

```python
def build_context(query: str, user_id: str, budget: int) -> str:
    facts = store.search(("memories", user_id, "collection"), query=query, limit=5)
    examples = store.search(("examples", user_id), query=query, limit=2)
    instructions = store.get(("instructions", user_id), key="email-style")

    blocks = [
        ("instructions", instructions.value if instructions else DEFAULT_INSTRUCTIONS),
        ("relevant facts", format_memories(facts)),
        ("few-shot examples", format_examples(examples)),
        ("current task", query),
    ]
    return pack_with_budget(blocks, budget)
```

先固定顺序，再调节参；不要同时改召回、排序和 prompt，否则无法归因。

阶段二的 memory manager 还要决定“现在该把什么换出去”：

```text
build_context(state, query, budget)
  → retrieve candidates
  → select evidence
  → if context_pressure > threshold:
       summarize low-priority history
       page out cold blocks
       page in relevant archival items
  → validate budget
```

最小 memory-pressure 策略：

1. 先删除重复、过期和低价值内容；
2. 再摘要仍有必要保留的对话历史；
3. 然后把冷 core block 移到外部存储；
4. 最后按当前任务检索 archival memory；
5. 记录每一次 page-in/page-out 的原因与 token 变化。

```python
def manage_pressure(state, budget):
    if count_tokens(state.context) < state.warning_threshold:
        return state

    summary = summarize(state.old_messages + state.previous_summary)
    cold_blocks = choose_cold_blocks(state.core_memory)
    archival_items = state.archival.search(state.current_query, limit=3)

    return state.with_context(
        summary=summary,
        core_memory=remove(cold_blocks),
        recalled=archival_items,
        events=[
            {"action": "summarize", "input_tokens": ..., "output_tokens": ...},
            {"action": "page_out", "block_ids": [...]},
            {"action": "page_in", "item_ids": [...]},
        ],
    )
```

**eviction 不等于 deletion**：换出上下文的内容仍应可检索；只有明确治理操作才删除。

### 检查点

- context builder 与 memory manager 的职责分别是什么？
- 为什么三类记忆需要固定注入顺序？
- 什么情况下应该摘要，什么情况下应该 page-out？
- 如何证明 page-in 的内容真的被 reader 使用？
- 如果上下文已经超过预算，第一条消息应该保留什么？

### 练习

实现一个 2K token 的 context builder。逐步加入 facts、examples、instructions，记录每步的命中率与 token；再实现 warning/refresh 两档 memory pressure，验证 eviction 后仍能检索旧消息。

---

## 2. 候选协议：先约定再融合

融合前必须记录：

| 字段 | 含义 |
|---|---|
| `canonical_id` | 跨腿稳定身份 |
| `content_hash` | 完全重复内容 |
| `provenance` | 原文 message/span |
| `leg_rank` | 该腿中的名次 |
| `raw_score` | 原始分数，可用于诊断 |
| `scope/status` | 租户、权限、有效期 |
| `cost` | token/字符、延迟贡献 |

没有 canonical identity，同一文档在两个腿里会被当成两个候选；没有 provenance，去重和引用无法验证。

---

## 3. RRF：倒数排名融合

标准形式：

```text
RRF(d) = Σᵣ wᵣ / (k + rankᵣ(d))
```

其中：

- `rankᵣ(d)` 通常从 1 开始；
- `k` 控制头部与长尾的平滑程度；
- `wᵣ` 可以表达腿的可信度；
- 同一文档在同一腿只出现一次。

### 3.1 为什么用名次

不同腿的分数分布不可比：

- BM25 可能从 0 到几十；
- cosine 固定在 `[-1,1]`；
- graph score 可能是路径概率；
- cross-encoder 是另一个模型的 logit。

RRF 不依赖分数量纲，对单腿异常高分更稳健。

### 3.2 失效场景

- 某腿返回大量近似重复，挤占名次；
- 候选深度不同，长尾文档吃亏；
- `k` 太小会过度奖励 top-1；
- 腿的可信度不同却没有权重；
- 权限、时间过滤放在融合后，浪费名次；
- 同一内容在融合前没有 collapse，重复计分。

### 3.3 参数实验

固定 query 集，扫描：

```text
depth ∈ {50, 100, 200}
k     ∈ {2, 20, 60}
weight ∈ {equal, raw-heavy, view-heavy, dense-heavy}
```

报告 Recall@k、MRR、all-recall、P95 延迟和失败样本。不要只选一个总体最优 `k`。

---

## 4. InsightMem 的 RRF 不是逐文档标准 RRF

[service.py 的 `fuse`](../../src/insightmem/coding/service.py#L227) 输入是“每条腿的分组序列”：

- raw leg：每个 chunk 一组；
- view leg：一个 view 对应一组 overlap chunks；
- dense leg：一个 view 对应一组 overlap chunks；
- `rank` 按**组**递增，不按每个 document 递增；
- 同组 chunk 共享该组名次；
- 已在前序组/腿出现的 chunk 被跳过，不再计分。

因此更准确的描述是：

> InsightMem 使用基于分组的 reciprocal-rank 信号，并记录每个 chunk 的最佳组名次；它不是对每条腿逐文档 rank 直接求和的标准 RRF。

### 4.1 候选深度

```text
depth = min(leg_max, max(50, 2 * top_k))
scan_limit = min(leg_max, depth * 4)
```

融合在满足以下任一条件时提前停止：

- 已见 chunk 数达到 `scan_limit`；
- 唯一 `(role, kind, raw_content)` 数达到 `depth`；
- 当前腿组数达到 `scan_limit`。

这会影响长尾召回。`top_k` 变大不一定线性增加有效候选覆盖。

### 4.2 重复内容何时处理

当前流程：

```text
融合时按 chunk_id 去重
  → 融合后 candidate_order 将完全重复正文移到唯一正文之后
  → prepare_sources 生成 bundle 与成员
  → select 再按正文和 span 抑制冗余
```

它**没有在融合前按 canonical content collapse**。因此不同 chunk 的相同正文可能在融合阶段分别计分，然后才被移动或抑制。

推荐的标准协议是：

```text
每腿输出文档排名
  → canonical collapse
  → RRF
  → bundle / span dedup
```

同时保留 occurrence 信息：“这段内容出现 3 次”本身可能是有价值的证据，不应简单丢弃。

---

## 5. 加权融合与校准

当腿的可信度不同，可使用：

```text
score(d) = Σᵣ wᵣ / (k + rankᵣ(d))
```

权重来源：

- dev set 上按查询类型校准；
- 已知质量较差的腿降权；
- 精确标识符提高 raw 权重；
- 多跳题提高 graph 权重；
- 低置信度时回退到 equal weights。

注意：在 test set 上调权重会造成泄漏。权重必须版本化并保存配置。

---

## 6. 去重、合并与多样性

### 6.1 去重不是删除

区分三种操作：

| 操作 | 保留什么 | 风险 |
|---|---|---|
| 删除 occurrence | 只留一条 | 丢失“发生多次”的信号 |
| 移动重复项 | 唯一项优先，重复项仍在候选 | 列表可能仍被重复占满 |
| 抑制注入 | 底层保留，结果列表不重复 | 需要可审计的 suppression 规则 |

InsightMem 选择“移到后面”和“最终抑制”而不是底层删除，原文 occurrence 仍保存在 `source_chunks`。

### 6.2 Bundle

bundle 将同一 message 中重叠或 touching 的 chunk 合并，受 `evidence_bundle_chars` 限制。

关键不变量：

- bundle 不替代成员；
- 长 bundle 可能排不到前面；
- 只有 bundle 实际返回时，成员才被 span 去重抑制；
- 部分重叠可能包含新约束，不能一律删除。

因此 bundle 是**可选的整体视图**，不是新的源数据。

### 6.3 MMR 多样性

最大边际相关性：

```text
MMR(d) = λ × sim(query,d)
       - (1-λ) × max sim(d, selected)
```

适合防止 top-k 全是近重复内容。代价是可能把真正最相关的第二条证据挤掉。

InsightMem 的 novelty 是 query-term coverage 的 tie-break，不是完整 MMR；相关性仍是主排序键。

### 6.4 全局预算

常见目标：

```text
maximize Σ utility(d)
subject to Σ cost(d) <= budget
```

可用边际增益贪心近似：

```python
while budget_remaining > 0:
    pick argmax(marginal_utility(d, selected) - λ * cost(d))
    if no candidate fits:
        break
```

不要只按 `top_k` 截断：一条长证据可能挤掉多条短而互补的证据。

### 6.5 InsightMem 的预算现状

当前实现包含：

- `evidence_max_chars`：单条证据上限；
- `evidence_bundle_chars`：bundle 上限；
- `top_k`：结果条数上限；
- 类型因子与 novelty tie-break。

它**没有全局字符/token 预算**。`select` 不会累计已选文本长度并在超预算时停止。因此教程中的“全局预算”属于设计练习，不是现有 API 行为。

---

## 7. 类型降权与过滤

低信息 assistant/thinking 消息在候选选择前被过滤：

- 底层 chunk 仍存在；
- 仍参与 BM25 语料统计；
- 仍占据 RRF 名次；
- 不会成为最终证据。

类型因子用于降低裸工具调用和过渡叙述的权重。设计时要防止：

- 把有用的错误处理当成过程叙述；
- 把工具参数中的关键约束过滤掉；
- 在融合后过滤导致候选浪费；
- 降权系数掩盖召回问题。

更清晰的协议是：能在检索前可靠过滤的就前置；必须保留语料统计的，明确记录过滤阶段。

---

## 8. 失败模式

| 失败 | 现象 | 根因 | 实验 |
|---|---|---|---|
| 重复霸榜 | top-k 都是同一正文 | 融合前未 canonical collapse | L5 |
| 单腿异常高分 | 结果被一条腿统治 | 直接相加、权重过高 | 逐腿消融 |
| 长文挤占 | 多条互补证据被截 | 无全局预算 | 字符预算扫描 |
| bundle 吞掉细节 | 返回长包但关键行被挤掉 | bundle 优先级过高 | bundle/成员对照 |
| 过滤浪费名次 | 过滤后候选不足 | 过滤发生在融合后 | 记录过滤前后数量 |
| novelty 误伤 | 相关但覆盖新词少的证据靠后 | tie-break 设计错误 | 固定 query 分析 |
| 类型降权误杀 | 工具结果关键信息丢失 | 规则过宽 | 对抗样本 |

---

## 9. 评估指标

| 指标 | 定义 | 用途 |
|---|---|---|
| Recall@k | gold 证据覆盖 | 是否找到 |
| MRR / nDCG | 排名质量 | 是否排前 |
| all-recall | 所有 gold 是否进入候选 | 多证据题 |
| Duplicate rate | 结果中重复/近重复比例 | 去重效果 |
| Coverage diversity | 不同 message/query-term 覆盖 | 互补性 |
| Token / char cost | 最终注入体积 | 预算 |
| Truncation rate | 被截断证据比例 | 预算失败 |
| Provenance precision | 引用跨度是否支持结论 | 可解释性 |

L4 噪声实验应报告：

```text
delta = relevant_score - noisy_score
```

如果 `delta > 0`，表示加入噪声后性能退化。不要写成含义相反的 `noisy - relevant`。

---

## 10. 动手：L4 噪声注入 + L5 去重

完整步骤见 [L4](labs.md#l4) 和 [L5](labs.md#l5)。

### L4：噪声注入

1. 固定相关语料与 query；
2. 记录无噪声结果；
3. 加入不同项目、语言、主题的无关会话；
4. 重跑同一 query；
5. 对每条 query 计算 paired delta；
6. 报告退化切片、被挤掉的证据和成本变化。

### L5：霸榜与修复

1. 同一正文写入 3 个 occurrence；
2. 观察融合前 canonical 数量；
3. 比较无去重、融合后移动、融合前 collapse；
4. 比较 bundle 开/关；
5. 检查底层 occurrence 是否仍存在；
6. 检查引用与 span 是否正确。

当前公开接口没有逐腿开关或 dedup 开关。实验需要在受控副本中修改代码或搭建独立 harness，不能写成“改配置即可”。

---

## 11. 设计练习：4000 字符预算

输出一份选择策略：

1. 候选来自哪些腿，候选深度多少？
2. canonical identity 是什么？
3. RRF 的 `k` 和腿权重是什么？
4. 去重发生在融合前还是融合后？
5. bundle 与成员如何共存？
6. 类型因子如何设置？
7. 全局预算如何计算？
8. 预算耗尽时保留来源标签还是截断正文？
9. 如何验证没有丢掉唯一证据？
10. 一个失败案例如何复现？

---

## 12. 验收

- 能写出加权 RRF，并说明 rank 的起点；
- 能解释 InsightMem 为什么不是逐文档标准 RRF；
- 能解释为什么 canonical collapse 应在融合前；
- 能说明 bundle 不替代成员，以及 span 去重条件；
- 能设计全局预算和多样性策略；
- 能区分底层保留、候选移动和最终抑制。

---

## 13. 机制依据与延伸阅读

### 一手依据

- [Cormack et al., Reciprocal Rank Fusion](http://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf)：RRF 原始论文。
- [Azure Hybrid Search Scoring](https://learn.microsoft.com/en-us/azure/search/hybrid-search-ranking)：RRF、weighted scores 与候选数量。
- [Qdrant Hybrid Queries](https://qdrant.tech/documentation/search/hybrid-queries/)：RRF、DBSF 与多阶段查询。
- [Qdrant Hybrid Search with Reranking](https://qdrant.tech/documentation/tutorials-basics/reranking-hybrid-search/)：混合召回与重排实践。
- [Anthropic: The components of agent memory](https://www.anthropic.com/research/components-of-agent-memory)：injected context 的预算与遵循度。
- 本项目实现：[evidence.py:94](../../src/insightmem/coding/evidence.py#L94)、[selection.py:8](../../src/insightmem/coding/selection.py#L8)、[service.py:227](../../src/insightmem/coding/service.py#L227)。

---

## 本章产出

1. 一张候选协议表；
2. RRF 的 depth/k/weight 扫描；
3. L4 paired delta 与 L5 去重对照；
4. 4000 字符预算设计及失败案例。

下一章：[06 更新与治理](06-governance.md)。
