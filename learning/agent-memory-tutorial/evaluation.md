# 评测手册

> 配套：[第 7 周](07-evaluation.md) · [实验 L7](labs.md#l7)
>
> 本手册定义一次“可信比较”的最小合同。它不是排行榜汇总：不同数据、answerer、top_k 或评分器的数字，不因放在同一张表里就可比。

---

## 1. 先写实验合同

开跑前保存一份 manifest。每次变更都产生新的 `run_id`，不覆盖旧结果。

```yaml
run_id: 2026-11-24-hybrid-r1
code_commit: <full-sha>
dataset:
  name: longmemeval
  variant: s_cleaned
  version: <release-or-download-date>
  sha256: <hash>
split:
  name: grouped-by-user-v1
  query_count: 30
  query_ids_sha256: <hash>
retrieval:
  top_k: 10
  index_config_sha256: <hash>
  embedding_model: <name-and-version>
  candidate_depth: 50
answering:
  model: <name-and-version>
  prompt_sha256: <hash>
  temperature: 0
  seed: 42
judge:
  enabled: false
  model: null
  rubric_sha256: null
runtime:
  python: "3.12"
  package_lock_sha256: <hash>
  hardware: <cpu-ram-gpu>
  cold_or_warm_cache: cold
```

最低限度必须固定：

```text
数据版本 · 查询集合 · gold 证据 · code commit · embedding/reader/judge
prompt · top_k · 候选预算 · seed · 运行环境
```

### 禁止事项

- 测试集调参后仍称其为 test；
- 只保存汇总表，不保存 predictions/retrievals；
- 同一实验里同时更换 chunk、embedding 和 prompt，却归因给一个机制；
- 把 oracle、S、M 或不同版本数据混合成一个分数；
- 把一次运行的点估计称为稳定提升。

---

## 2. 数据集与版本合同

| 数据集 | 形态 | 主要指标 | 适合验证 | 当前口径与限制 |
|---|---|---|---|---|
| LongMemEval | 超长多会话对话，500 题 | QA accuracy；可派生 Recall@k | 抽取、多跳、时间、知识更新、弃答 | 必须注明 S/M/oracle 与版本；V2 不能与原版混报 |
| LoCoMo | 长对话 QA / event summary | QA accuracy；证据命中 | 长期对话与跨会话事件 | 当前公开 `locomo10.json` 为 10 个对话，是原 50 conversations 的子集 |
| BEAM | 1M / 10M token 级上下文 | accuracy、成本 | 超长上下文记忆 | 规模成本高；先小规模验证协议 |
| CAMBench Coding | SWE 任务 × relevant/noisy | Overall Resolved | 编码证据复用、抗噪 | AML 平台统一 answerer/evaluator；150 任务，共 300 次尝试；正式 Top K=100 |
| CL-Bench | 持续学习任务 | reward / 达标率 | 学习闭环与 dreaming | 厂商研究环境；跨环境比较需固定 harness |
| VibeMemBench | 仓库级编码任务，待一手核验 | resolution | 编码记忆注入 | 本教程不采用“111 仓库、2026 新基准”等未核验数字作为事实 |
| OmniMemEval | 多数据集统一评测 | 多指标 | 横向检查能力覆盖 | 必须核对 harness、数据版本与评分器 |

### LongMemEval 的三种文件

| 文件 | 证据形态 | 合理用途 |
|---|---|---|
| `longmemeval_s_cleaned.json` | 标准长历史，约 40 sessions | 主实验；成本较高 |
| `longmemeval_m_cleaned.json` | 每题约 500 sessions | 大规模压力测试 |
| `longmemeval_oracle.json` | 只包含 evidence sessions | 上界与 reader 归因，不是真实召回成绩 |

500 题的五类能力应单独报告：信息抽取、多会话推理、时间推理、知识更新、弃答。官方预测格式为 `question_id + hypothesis` JSONL，再用官方 evaluator。

### LoCoMo 的版本边界

论文早期版本含 50 conversations；当前公开仓库的 `data/locomo10.json` 含 10 conversations。引用成绩必须写清是哪一个。

QA 提供 evidence dialog IDs，可用于证据命中实验。多模态图片不随数据发布，只有 URL、caption、search query；部分多模态与 event-summary 工具仍标注 coming soon，不能假设现成脚本可直接复现全部任务。

### AML 的评测边界

AML 参赛方实现 Add/Search，平台统一 Answer、Eval、Top K 与汇总。Search 返回证据，不生成答案；正式 Top K=100，`user_id` 是唯一检索隔离范围，Search 不接受 filters、rerank 或 keyword_search。

CAMBench Coding 的 150 个任务分别在 relevant/noisy 条件下运行，共 300 attempts。300 次尝试不等于 300 个独立任务；小比例差异必须同时报告任务分子分母。

---

## 3. 指标分层

### 3.1 检索层

设 `G_q` 为 query `q` 的 gold 证据集合，`R_q@k` 为前 k 条结果。

```text
Hit@k(q) = 1[ G_q ∩ R_q@k ≠ ∅ ]
Recall@k(q) = |G_q ∩ R_q@k| / |G_q|
Precision@k(q) = |G_q ∩ R_q@k| / k
MRR(q) = 1 / rank(first relevant result)，无命中则为 0
all-recall@k = 是否召回了该题要求的全部证据
```

报告时同时给出 micro 与 macro 两种口径：

- **micro**：先汇总所有题的证据命中数，再除以总 gold 数；受多证据题影响更大；
- **macro**：先计算每题 Recall@k，再对题取平均；每题权重相同。

若某个 benchmark 的官方指标只按“至少一个 evidence session 命中”计分，应写 `session-hit`，不要与 span 级 Recall 混用。

### 3.2 回答层

- **Accuracy / F1 / Exact Match**：能用确定性评分时优先使用；
- **Resolved rate**：编码任务由官方 harness 判定，记录已解决/总数；
- **Abstention**：无答案时是否正确拒答；同时报告误拒答率；
- **Citation correctness**：答案正确但引错证据，仍应单独扣分或分报。

LLM judge 只负责 rubric 内可判断的维度。judge 分数不能替代执行测试、单元测试或人工复核。

### 3.3 系统层

| 指标 | 记录方式 |
|---|---|
| write / read tokens | 区分 extraction、embedding、rerank、reader、retry |
| latency | p50 / p95；分别记录 Add、Search、Answer |
| build cost | 索引构建时间、CPU/GPU 时间、token |
| index maintenance | 每次 Add 的增量成本与周期性 rebuild 成本 |
| storage | 原文、facts/notes、postings、vectors、图、缓存 |
| memory | 峰值 RSS / GPU memory |
| reliability | 失败、超时、重试、部分写入 |

不要只报“每次查询 token”。长期系统的真实成本通常是：

```text
总成本 = build + maintenance + retrieval + rerank + answer + retry
```

---

## 4. 最小评测协议

### 4.1 冻结与切分

1. 固定语料、query、gold evidence、answerer、prompt、top_k；
2. 按 user / conversation / repository 分组切分，防止同一主体跨 dev/test 泄漏；
3. 在 dev 选参数，test 只运行一次最终确认；
4. 保存 query IDs 与数据集 hash。

### 4.2 Baseline

至少包含：

| 配置 | 排除的因素 |
|---|---|
| no memory | 排除所有外部记忆收益 |
| full context | 给出同 reader 的上下文预算上界 |
| single retriever | 排除融合收益 |
| raw lexical | 排除 dense/view 的增益 |
| full system | 实际候选系统 |

full context 不是天然更优：超长上下文可能增加干扰、成本和延迟。它主要用于回答“收益来自证据还是更多 token”。

### 4.3 消融

每次只关闭一个机制：

```text
hybrid
hybrid - dense
hybrid - view expansion
hybrid - dedup
hybrid - bundle
hybrid - type filter
```

如果候选深度、token 预算和 top_k 同时变化，不能把差异归因于 dedup。应控制检索输入，只让目标机制变化。

### 4.4 样本量

- 探索性文本实验至少 30 题，只能作为方向信号；
- 编码任务至少 100 个任务；
- 正式榜单或研究结论遵循 benchmark 官方规模；
- 分层结论的每个能力切片也应报告实际 `n`。

“300 次运行”如果只是同一任务跑 3 次，有效样本量仍接近任务数，不能把运行次数当独立样本数。

---

## 5. 检索、阅读与回答归因

固定 reader 后，对同一题运行：

```text
A = reader(system retrieved evidence)
B = reader(gold evidence)
C = reader(no evidence)
```

| 结果 | 优先诊断 |
|---|---|
| A 差、B 好、C 差 | 召回或候选选择 |
| A、B 都差 | reader、prompt、任务本身或 gold 不完整 |
| A 好但引用差 | 证据使用、排序、引用约束 |
| B 不比 C 好 | reader 无法利用该证据，或答案不在证据内 |

gold evidence 是证据标注，不是 gold answer。直接把答案放入 reader 会泄漏；必须保留从证据到答案的过程。

同时保存：

```text
query_id
retrieved_ids
gold_ids
injected_spans
reader_input_hash
prediction
```

这样才能复现“检索到了但没用上”。

---

## 6. 配对统计与噪声差值

### 6.1 配对比较

A/B 必须跑在同一组 query 上。对第 `i` 题：

```text
Δᵢ = score_A(i) - score_B(i)
mean(Δ) = Σ Δᵢ / n
```

`Δ > 0` 表示 A 更好。噪声条件同理：

```text
improvement(q) = relevant_score(q) - noisy_score(q)
degradation(q)  = max(0, noisy_score(q) - relevant_score(q))
```

不要写“噪声差值 = noisy − relevant”却不解释方向。建议直接使用上表命名，避免歧义。

### 6.2 Paired bootstrap

1. 对 `n` 个 query 有放回抽样 `n` 次；
2. 每次计算抽样集合的平均 Δ；
3. 重复 1000–10000 次；
4. 取 2.5% 与 97.5% 分位数作为 95% CI；
5. 报告 `n`、mean Δ、CI，以及原始分数分子/分母。

伪代码：

```python
deltas = np.asarray(paired_scores_a) - np.asarray(paired_scores_b)
boots = np.random.default_rng(seed).choice(
    deltas, size=(10_000, len(deltas)), replace=True
).mean(axis=1)
ci_low, ci_high = np.quantile(boots, [0.025, 0.975])
```

CI 跨 0 时，结论应是“本样本未提供稳定方向证据”，而不是“提升不显著所以肯定无效”。

### 6.3 多种子

至少运行 3 个 seed，分别报告：

- 检索/模型随机性；
- 数据切分波动；
- 服务抖动。

多种子不能替代独立样本量；同一 test query 上跑 3 次，仍不是 3 倍题目。

---

## 7. LLM Judge 校准

### 风险

- 位置偏好：偏爱第一个答案；
- 长度偏好：长答案得分高；
- 风格偏好：偏爱与自身文风接近的答案；
- rubric 含糊：事实正确但引用错误仍得高分；
- 评分漂移：模型或 prompt 更新后失去可比性。

### 流程

1. 为每类任务写可操作的 rubric，明确 0/1/2 分边界；
2. 用约 100 题人工集校准，疑难样本多人复核；
3. 随机化 A/B 展示顺序，盲化系统名与模型名；
4. 固定 judge 模型、temperature、prompt hash 与 seed；
5. 报告 agreement 或 κ，并保存分歧样本；
6. 保存原始 judgment、理由和引用检查；
7. judge 更新后重新校准，不与旧结果直接拼接。

若使用多个 judge，应报告单 judge 与一致性结果，不能只挑分数最高的那个。

---

## 8. 成本、延迟与故障

### 8.1 分开计时

```text
add_total
search_total
rerank
reader
judge
retry_wait
```

Add 的同步延迟与 Search 的 p95 是不同指标。异步索引系统还应报告“写入成功”和“可检索”之间的延迟。

### 8.2 冷热缓存

分别记录冷启动与热缓存，注明缓存范围：SQLite page cache、embedding cache、prompt cache 或服务端缓存。不能让 A 冷跑、B 热跑后只比较 p50。

### 8.3 故障注入

至少覆盖：

- 同 request 重放；
- embedding 超时；
- 写入一半崩溃；
- 索引构建失败；
- 两个不同 request 并发更新；
- 删除后重放与备份恢复。

每个故障都应有可观察结果：成功、409、重试、回滚或明确失败，不能静默半提交。

---

## 9. 原始产物与目录

每次运行至少保存：

```text
runs/<run_id>/
  manifest.yaml
  query_ids.json
  predictions.jsonl
  retrievals.jsonl
  judgments.jsonl
  metrics.json
  costs.json
  failures.jsonl
  logs/
```

### predictions.jsonl

```json
{"run_id":"r1","query_id":"q17","answer":"Shanghai","citation_ids":["m12"],"latency_ms":812}
```

### retrievals.jsonl

```json
{"run_id":"r1","query_id":"q17","top_k":10,"hit_ids":["m12","m4"],"spans":[["m12",0,91]],"gold_ids":["m12"]}
```

### judgments.jsonl

```json
{"run_id":"r1","query_id":"q17","judge":"judge-v1","score":1,"rubric_sha256":"abc","reason":"correct value, wrong citation","raw_response":"<saved>"}
```

### metrics.json

```json
{
  "query_count": 30,
  "session_hit": {"numerator": 22, "denominator": 30},
  "span_recall_at_10": {"micro": 0.64, "macro": 0.61},
  "paired_delta": {"mean": 0.08, "ci95": [-0.01, 0.17], "bootstrap_runs": 10000},
  "abstention": {"correct": 4, "eligible": 6, "false_abstention": 2}
}
```

任何百分比都必须能追溯到分子/分母。

---

## 10. 失败案例分类

至少保存 3 个案例，按机制层分类：

| 类型 | 例子 | 需要的证据 |
|---|---|---|
| 召回遗漏 | gold 未进候选 | query、候选 ID、gold ID |
| 排序错误 | gold 在 top_k 外 | 名次与分数 |
| 冗余挤占 | 相似 chunk 占满预算 | 选中内容与 span |
| 过期误用 | 返回旧值 | valid/recorded 时间与版本 |
| 冲突误判 | 异域事实被合并 | scope 与 subject |
| reader 失败 | oracle 也无法回答 | reader 输入与输出 |
| 引用失败 | 答案对但证据错 | answer/citation |
| 成本失败 | 答案提升但预算爆掉 | token/latency/cost |

失败案例不是附录装饰：它们决定下一轮改检索、选择、治理还是 reader。

---

## 11. 评测报告模板

```text
1. 问题与可证伪假设
2. Benchmark 合同：数据集、版本、题量、条件
3. dev/test 分组切分与能力切片
4. Baseline 与逐项消融
5. 检索层：session-hit / Recall@k / MRR / all-recall
6. 回答层：accuracy / resolved / abstention / citation
7. 配对统计：Δ、95% CI、seed、有效样本量
8. Judge：版本、rubric、agreement/κ、分歧样本
9. 系统层：write/read token、p50/p95、存储、build/maintenance
10. relevant/noisy：improvement 与 degradation，按任务报分子分母
11. 失败案例与归因
12. 适用边界、不可比项、复现命令与 manifest hash
```

结论句式：

```text
在 [切片] 的 n 个独立任务上，A 相比 B 的平均 Δ 为 x，
paired bootstrap 95% CI 为 [l, u]；成本变化为 y。
该结果不支持跨 [不同 benchmark/answerer/top_k] 外推。
```

---

## 12. 最小可信评测清单

- [ ] 固定 dataset、variant、hash 与 query IDs
- [ ] 固定 code commit、embedding、answerer、judge、prompt
- [ ] 固定 top_k、候选深度、上下文预算与 seed
- [ ] dev/test 按主体分组，无跨组泄漏
- [ ] 有 no-memory、single-retriever baseline
- [ ] 有 full-context 或 oracle 归因实验
- [ ] 每次只消融一个机制
- [ ] 至少 30 题；编码至少 100 个任务
- [ ] 报分子/分母与各能力切片，不只报平均
- [ ] 至少 3 个 seed，使用 paired bootstrap CI
- [ ] judge 经过顺序盲化与人工校准
- [ ] relevant/noisy 使用明确方向的 improvement/degradation
- [ ] 记录 write/read token、p50/p95、build/maintenance、存储
- [ ] 保存 predictions/retrievals/judgments/failures 原始产物
- [ ] 给出干净环境复现命令与 manifest hash
