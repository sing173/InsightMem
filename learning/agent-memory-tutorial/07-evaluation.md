# 07 评测（第 7 周）

> 上一章：[06 更新与治理](06-governance.md) · 下一章：[08 架构对比与 Capstone](08-capstone.md)
> 阶段：阶段一验收 LangGraph 邮件 Agent；阶段二复用同一协议评测 memory OS。
> 预计：6–8 小时
> 本章目标：能把“系统更好”拆成可验证假设；能固定 benchmark 合同、做 held-out 与配对统计、校准 judge，并报告完整成本和原始产物。

完整协议见 [评测手册](evaluation.md)，实验步骤见 [L7](labs.md#l7)。

### 两阶段验收指标

| 阶段 | 主项目 | 必测指标 |
|---|---|---|
| 阶段一 | LangGraph 邮件 Agent | 路由准确率、写作偏好一致性、few-shot 命中、错误记忆率、read/write token、p95 延迟 |
| 阶段二 | memory OS mini service | memory-pressure 触发次数、page-in/page-out 准确率、摘要保真、自编辑回滚成功率、共享隔离、完整成本 |

两阶段都使用同一套原则：固定 reader、prompt、数据、预算和 seed；报告分子/分母、失败案例与原始产物。阶段二实验步骤见 [L8](labs.md#l8)。

---

## 本章实战：给邮件 Agent 做一次可信对比

> 可运行实验：[04-evaluation.ipynb](../../experiments/email-agent/notebooks/04-evaluation.ipynb)；稳定实现：[evaluate_config()](../../experiments/email-agent/src/email_memory_lab/evaluation.py#L57)。
> 当前 Notebook 使用 10 封邮件与确定性策略，只验证离线机制；它不包含真实 LLM 的 token、p95、judge 或 paired bootstrap。

### 第一步：准备一个最小数据集

构造 20 封邮件，覆盖：

- 应忽略的推广邮件；
- 应通知的紧急事件；
- 需要回复的业务邮件；
- 需要历史偏好的写作任务；
- 需要上次承诺的跟进任务。

每封邮件标注：

```text
expected_action: ignore / notify / respond
required_memory: semantic / episodic / procedural / none
gold_fact_ids: [...]
gold_example_ids: [...]
```

### 第二步：固定四组配置

| 配置 | semantic | episodic | procedural |
|---|---|---|---|
| baseline | 无 | 无 | 无 |
| +semantic | 有 | 无 | 无 |
| +episodic | 有 | 有 | 无 |
| full memory | 有 | 有 | 有 |

只增加一种机制，保持 reader、prompt 模板、工具与 top_k 不变。

### 第三步：保存逐题轨迹

逐题执行与结果保存已有稳定实现，见 [evaluate_config()](../../experiments/email-agent/src/email_memory_lab/evaluation.py#L57) 和 [04-evaluation.ipynb](../../experiments/email-agent/notebooks/04-evaluation.ipynb)。教程不再重复维护同一份循环，实际项目至少保存：

- `email_id`、`expected_action`、`predicted_action`；
- 命中的记忆 ID、gold IDs 与是否进入上下文；
- 最终回复、失败原因与配置；
- 若使用 LLM，再记录 prompt token、memory tool 调用、p50/p95 延迟和 memory edits。

不要只保存最终回答。没有检索 ID 和 memory edits，就无法区分“没有记忆”“检索错”“选择错”和“reader 错”。

### 第四步：先算检索，再算回答

```text
memory recall = 命中的 gold memory / 应有的 gold memory
routing accuracy = 正确分类的邮件 / 全部邮件
writing compliance = 满足签名/语气约束的回复 / 应回复邮件
```

如果 memory recall 高但回答差，检查 context builder 与 reader；如果 recall 低，检查写入与检索。

### 第五步：报告成本与失败

至少报告：

- 每封邮件平均 prompt token；
- memory tool 调用次数；
- p50 / p95 延迟；
- 错误记忆条数；
- 三个失败案例及归因。

### 检查点

- 为什么 baseline 必须使用同一个 reader？
- 为什么 20 封邮件只能算探索性实验？
- memory recall 与 routing accuracy 有什么区别？
- 如果 full memory 更慢但更准，应该如何报告？
- 如果 procedural memory 让某些邮件从 respond 变成 ignore，这是收益还是污染？

### 练习

运行四组配置，做 paired bootstrap，报告平均 Δ 与 95% CI。再挑一个 full memory 失败案例，分别检查 gold memory 是否写入、是否检索、是否进入 prompt。

---

## 1. 本周要解决的问题

一个分数只有同时固定数据、范围、模型、prompt、top_k 和评分器，才有比较意义。本章把评测当成实验，而不是榜单复述。

先写一句话假设：

```text
在 [任务切片] 上，[机制] 相比 [baseline] 提升 [指标]，
且 [成本/延迟] 不超过 [预算]。
```

例如：

```text
在精确标识符查询上，raw BM25 相比 dense-only 提升 Recall@10，
且不增加 answerer token。
```

没有假设，很容易在多个指标中挑一个好看的结果。

---

## 2. Benchmark 合同

### 2.1 [LongMemEval 本地精读](../../docs/papers-zh/04-retrieval-eval.md#longmemeval)

官方当前提供三个数据文件：

| 文件 | 内容 | 用途 |
|---|---|---|
| `longmemeval_s_cleaned.json` | 约 115k tokens、约 40 个 history sessions | 标准长历史 |
| `longmemeval_m_cleaned.json` | 每题约 500 个 sessions | 更大规模 |
| `longmemeval_oracle.json` | 只包含 evidence sessions | oracle 上界与阅读归因 |

500 题覆盖五类能力：信息抽取、多会话推理、时间推理、知识更新、弃答。

关键约束：

- S/M/oracle 不是同一难度，不能混报；
- oracle 把 gold evidence 直接放进历史，不能当作真实检索系统成绩；
- 官方输出为 `question_id + hypothesis` 的 JSONL，再用统一 evaluator；
- 官方仓库已宣布 LongMemEval-V2；引用时必须注明使用的是原版还是 V2。

#### LongMemEval-V2：从聊天记忆转向环境经验

[LongMemEval-V2 本地译读](../../docs/papers-zh/05-longmemeval-v2.md) 不是 V1 的简单扩长版：它使用 451 道 Web/ServiceNow 轨迹题，考查静态状态、动态状态、工作流、环境陷阱和前提意识；记忆模块通过 `Insert/Query` 返回多模态证据，再由固定 reader 回答，并同时报告准确率与查询延迟。V1 与 V2 的数据、能力标签和分数不能混用。

### 2.2 [LoCoMo 本地精读](../../docs/papers-zh/04-retrieval-eval.md#locomo)

当前公开仓库发布 `locomo10.json`，包含 10 个长对话；论文早期版本为 50 个 conversations。当前公开版是其子集。

支持：

- QA；
- event summarization；
- multimodal dialog generation。

限制：

- 不公开原始图片，只提供 URL、caption 和 search query；
- event summarization 的官方脚本标记为 coming soon；
- 合成对话经人工验证，但仍不等于真实用户分布。

### 2.3 AML / CAMBench Coding

[AML 官方指南](https://agentmemories.ai/api-guide) 固定：

- 参赛者只提供 Add / Search；
- 平台统一 Answer、Eval、Top K 和汇总；
- 正式 Top K 为 100；
- `user_id` 是唯一检索隔离范围；
- Search 不接收 `filters`、`rerank`、`keyword_search`；
- CAMBench Coding：150 个任务 × relevant/noisy，共 300 次尝试；
- 开源方法使用规定的 embedding / LLM，商业产品规则不同。

因此 AML 成绩只反映该期协议下的 Add/Search 能力，不能外推为通用记忆架构排名。

---

## 3. Held-out 与能力切片

### 3.1 划分

```text
dev set   → 选参数、阈值、prompt、权重
test set  → 最终评估，禁止调参
```

按用户或 conversation 分组划分，避免同一用户的不同问题泄漏到两边。

### 3.2 切片

至少分别报告：

| 切片 | 例子 |
|---|---|
| 单跳 | 一个证据 span 可答 |
| 多跳 | 多个 session / fact |
| 时间 | 顺序、跨度、as-of |
| 知识更新 | 新值取代旧值 |
| 弃答 | 无答案时不编 |
| 精确匹配 | ID、路径、错误码 |
| 语义改写 | 同义表达 |
| 对抗 | 近重复、矛盾、噪声 |

总体平均可能掩盖某一能力完全失败。

---

## 4. 检索—阅读—回答归因

把系统拆开测：

```text
Recall@k
  → injected evidence
  → fixed reader
  → answer
```

### Oracle reader 实验

给同一个固定 reader 两种输入：

1. 系统检索结果；
2. gold evidence。

结论：

| 现象 | 归因 |
|---|---|
| oracle 好、检索差 | 召回/选择问题 |
| 两者都差 | reader/prompt 或任务问题 |
| 检索好、回答仍差 | 证据使用、冲突或推理问题 |

gold evidence 是证据标注，不是 gold answer。把答案直接塞进 reader 会泄漏。

---

## 5. 配对统计

同一组 query 上比较 A/B：

```text
Δᵢ = score_A(i) - score_B(i)
```

用 paired bootstrap：

1. 对 query 有放回抽样；
2. 每次计算平均 Δ；
3. 重复 1000–10000 次；
4. 报告 95% CI；
5. 同时报告分子/分母与效应量。

至少运行 3 次不同 seed，区分：

- 检索/模型随机性；
- 数据切分波动；
- 服务抖动。

若 CI 跨 0，不应写成“显著提升”。

---

## 6. LLM Judge 校准

Judge 也是评测组件，需要版本和校准。

### 风险

- 位置偏好：偏爱第一个答案；
- 长度偏好：长答案得分高；
- 风格偏好：与 judge 文风一致得分高；
- rubric 含糊：事实正确但引用错误仍可能得高分。

### 校准流程

1. 固定 rubric；
2. 随机化 A/B 顺序；
3. 盲化系统名称；
4. 用 100 题左右人工集校准；
5. 双 judge 或多人复核；
6. 报告 agreement 或 κ；
7. 保存原始 judgment 与理由。

能使用 exact match、F1、Resolved rate 的题目，不应全部交给 judge。

---

## 7. 成本与复现

完整成本：

```text
build + index maintenance + retrieval + rerank + answer + retry
```

至少记录：

- write / read tokens；
- p50 / p95 延迟；
- 冷启动与热缓存；
- 索引构建时间；
- 存储与内存；
- 失败、超时、重试次数。

### Manifest

每次运行保存：

```text
run_id
dataset_version + hash
query_ids + hash
code_commit
model / embedding / judge versions
prompt hash
top_k
seed
config hash
```

保存原始产物：

```text
predictions.jsonl
retrievals.jsonl
judgments.jsonl
metrics.json
failures.jsonl
```

没有原始产物，只有汇总表，无法复核失败。

---

## 8. 动手：L7 评测 harness

完整步骤见 [实验手册 L7](labs.md#l7)。

### 最小实验矩阵

| 配置 | 作用 |
|---|---|
| no memory | 模型基线 |
| full context | 上下文预算上界 |
| single retriever | 单腿基线 |
| hybrid retrieval | 多路召回 |
| hybrid - dedup | 去重消融 |
| hybrid - filter | 过滤消融 |

每次只改一个机制。若同时改 chunk、embedding 和 prompt，无法归因。

### 输出

1. manifest；
2. predictions / retrievals / judgments；
3. 按切片的指标与 paired CI；
4. 成本表；
5. 至少 3 个失败案例；
6. 一条干净环境复现命令。

---

## 9. 评测报告模板

```text
1. 假设
2. Benchmark 合同与版本
3. dev/test 划分与能力切片
4. Baseline 与消融
5. 检索层：Recall@k / MRR / all-recall
6. 回答层：accuracy / resolved / judge rubric
7. 配对统计：Δ、95% CI、运行次数
8. 系统层：token、p50/p95、存储、构建成本
9. 失败案例与归因
10. 适用边界与不可比项
11. 复现命令与 manifest hash
```

---

## 10. 常见陷阱

- 用 oracle 成绩冒充检索成绩；
- 在 test set 调 prompt 或权重；
- 比较不同 answerer、top_k、数据版本；
- 把 LoCoMo10 与原 50 conversations 混为一谈；
- 把 300 次尝试里 1.3% 当成 4 个独立任务之外的大规模证据；
- 只报平均，不报弃答、更新、时间切片；
- 只报线上延迟，不报索引构建；
- 用单次 judge 结果替代统计；
- 厂商论文分数直接套到当前 OSS 版本。

---

## 11. 验收

- 能写出一句可证伪的评测假设；
- 能解释 LongMemEval S/M/oracle 的差别；
- 能区分 LoCoMo 原版与当前公开 locomo10；
- 能用 oracle reader 区分检索与生成问题；
- 能报告 paired Δ 与 95% CI；
- 能校准 judge，并保存完整成本与原始产物。

---

## 12. 机制依据与延伸阅读

### 一手依据

- [LongMemEval, arXiv:2410.10813](https://arxiv.org/abs/2410.10813)：500 题与五种能力。[中文精读](../../docs/papers-zh/04-retrieval-eval.md#longmemeval)
- [LongMemEval 官方仓库](https://github.com/xiaowu0162/LongMemEval)：S/M/oracle 数据格式与评测命令。
- [LongMemEval-V2, arXiv:2605.12493](https://arxiv.org/abs/2605.12493)：451 道环境经验题、Insert/Query 与准确率—延迟评测。[本地译读](../../docs/papers-zh/05-longmemeval-v2.md)
- [LoCoMo, arXiv:2402.17753](https://arxiv.org/abs/2402.17753)：超长期对话评测。[中文精读](../../docs/papers-zh/04-retrieval-eval.md#locomo)
- [LoCoMo 官方仓库](https://github.com/snap-research/locomo)：当前 locomo10、任务与限制。
- [AML API Guide](https://agentmemories.ai/api-guide)：Add/Search、Top K、CAMBench Coding 与统一评测边界。
- [AML 官方仓库](https://github.com/AML-memory/agent-memory-leaderboard)：评测流程与复现规则。

### 课程

- [Long-Term Agentic Memory With LangGraph](https://www.deeplearning.ai/short-courses/long-term-agentic-memory-with-langgraph/)：用可运行实验理解记忆生命周期。
- [LLMs as Operating Systems: Agent Memory](https://www.deeplearning.ai/short-courses/llms-as-operating-systems-agent-memory/)：Letta 的系统视角。

下一章：[08 架构对比与 Capstone](08-capstone.md)。
