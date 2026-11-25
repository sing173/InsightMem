# 实验手册（L0–L8）

> 配套：[八周路线](README.md) · [评测手册](evaluation.md)
> 可运行入口：阶段一使用 `experiments/email-agent/notebooks/`，确定性证据实验使用 `experiments/insightmem/notebooks/`；完整覆盖关系见 [教程与 Notebook 对照](README.md#notebook-map)。
> 每个实验都要求：一个 baseline、一个固定变量、一个失败案例、一个成本数字。
> 所有结果必须能追溯到原始数据、配置和命令；只记“感觉更好”不算完成。

---

## 1. 总表与共同约定

| 编号 | 实验 | 时长 | 依赖 | 核心产出 |
|---|---|---|---|---|
| L0 | 记忆审计 | 2h | 任意工具 | 四层映射、隔离哨兵、删除链 |
| L1 | 表示 × 检索器 | 6h | LLM API、词法/dense | 六格对照、抽取误差 |
| L2 | 双索引对照 | 6h | SQLite + 向量索引 | 查询类型命中矩阵 |
| L3 | 三路召回消融 | 6h | InsightMem + 实验分支 | 逐腿消融、gold span |
| L4 | 噪声注入 | 4h | InsightMem | paired improvement/degradation |
| L5 | 去重与合并 | 4h | InsightMem + 实验分支 | 冗余占位与 span 校验 |
| L6 | 矛盾序列 | 6h | 自建小型存储 | 双时间、并发、删除验证 |
| L7 | 评测 harness | 8h | 任意 | manifest、CI、成本、复现报告 |
| L8 | memory OS mini | 8h | Store/文件后端 + 固定 reader | paging、自编辑、dreaming、共享隔离 |

### 每个实验先冻结

```text
数据与 hash · query IDs · gold evidence · code commit
embedding/answerer/judge · prompt · top_k · 候选深度 · seed
```

- dev 用于调参，test 用于最终确认；按 user/conversation/repository 分组；
- 30 题是探索下限，不是普遍统计保证；编码任务至少 100 个独立任务；
- 同题多种子运行不能冒充独立样本量；
- 记录失败、超时和重试，不把失败样本静默删掉。

### InsightMem 实验边界

当前公开 Add/Search 没有逐腿开关、dedup 开关、时间过滤器或全局预算配置。L3/L5 需要：

1. 在独立实验分支暴露内部候选与选择阶段；或
2. 对现有快照离线调用内部函数构造消融；
3. 保持生产接口与数据库不变，记录实验 commit。

不能写成“关闭某个配置”而不说明配置实际不存在。

---

<a id="l0"></a>
## L0 记忆审计（2h）

**目标**：把一个真实工具的记忆层拆成可检查的系统，而不是只看“它有没有记忆”。

### 步骤

1. 选一个工具：Claude Code、Cursor、ChatGPT、Copilot 或本项目；
2. 找原始记录：对话、工具调用与结果、文件、issue；
3. 找派生表示：`MEMORY.md`、rules、notes、索引、wiki、向量；
4. 找注入路径：会话开头、工具返回、上下文压缩分别加载什么；
5. 找更新路径：追加、覆盖、失效、后台整理分别由谁触发；
6. 找纠错/删除路径：主库、派生 facts、索引、缓存、备份；
7. 建立双用户哨兵，检查相同 session 名或相同 query 是否串扰。

### 证据分级

| 级别 | 证据 | 可信结论 |
|---|---|---|
| A | 源码、schema、可执行测试 | 当前实现确实如此 |
| B | 官方文档、API 合同 | 官方声明的行为，仍需版本核对 |
| C | 论文、官方课程 | 机制设计，不等于当前产品实现 |
| D | 二手文章、视频 | 只作线索，不作事实依据 |

每条审计结论标注来源级别。看不到内部实现时，写“未观察到”而不是“没有”。

### 产出

- 四层映射：source → derived representation → index → injected context；
- 一条失败传播链：错误/遗漏 → 写入 → 索引 → 选择 → 注入 → 行动；
- 双用户隔离哨兵结果；
- 删除后直接 ID、词法、dense、缓存与恢复检查表。

### 验收

- 能指出一个错误记忆从哪一层进入；
- 能区分“淘汰出上下文”“归档”“忘记”“法律擦除”；
- 每条项目现状结论都有 A/B 级证据；
- 明确指出至少一个未验证面，而不是猜答案。

---

<a id="l1"></a>
## L1 表示 × 检索器（6h）

**目标**：区分“写入表示”与“检索器”的贡献。原实验让 A 用 BM25、B/C 用向量，无法判断收益来自表示还是检索器。

### 输入

- 100 条编码会话消息，保持原始顺序、role、session、timestamp；
- 30 个 gold query，按精确标识符、语义改写、多跳、时间/更新分类；
- gold 标到 message/span；无证据题单独标 abstention。

### 六格矩阵

| 表示 \ 检索器 | BM25 | Dense |
|---|---|---|
| 全量原文 | A1 | A2 |
| LLM notes | B1 | B2 |
| 抽取 facts | C1 | C2 |

固定 chunk 规则、embedding、top_k、候选深度与 reader。B/C 还要固定抽取模型、prompt 与 seed，并保存原始输出。

### 步骤

1. 冻结语料与 30 题，在 dev 上选参数；
2. 建 A1/A2，再在相同文本表示上建 B1/B2、C1/C2；
3. 对 B/C 人工抽查：遗漏关键约束、错误主体、错误时间、无 source span；
4. 记录 Hit@5、Recall@5、span 可追溯率、存储字节；
5. 记录抽取/embedding/检索 token 与 p50/p95 延迟；
6. 在 test 上只运行最终配置，保存逐题结果；
7. 分析三个失败案例：抽取错误、检索错误、reader 错误。

### 产出

```text
表示 × 检索器六格表
+ 每种表示的 precision / recall / 无依据率
+ 成本表
+ 选型结论
```

### 验收

- 不把“notes 更好”误写成“dense 更好”；
- 能说出哪类信息在抽取后丢失，且无法从原文恢复；
- 所有百分比有分子/分母；
- 至少一个案例证明误差来自写入而不是检索。

---

<a id="l2"></a>
## L2 双索引对照（6h）

**目标**：看清词法索引与向量索引各自适合什么查询，以及精确索引与 ANN 的差别。

### 步骤

1. 对同一批 chunk 建词法索引；
2. 对同一批 chunk 建 dense 索引；
3. 准备 30 个查询：精确标识符、自然语言改写、多跳、时间；
4. 每类分别测 Hit@5、Recall@5、MRR，记录候选深度；
5. 对 dense 再比较精确点积与 ANN，记录 ANN recall@k 与端到端 QA；
6. 比较 pre-filter 与 post-filter 对召回和延迟的影响；
7. 保存每个失败 query 的 gold 与候选。

### 实现提醒

- InsightMem 当前使用 Python 全量 BM25 和精确 dense 点积，不是 FTS5 或 ANN；
- 如果要复现 InsightMem，就使用它的实际索引；
- 如果要比较 FTS5/ANN，明确这是另一个 Adapter，不能把差异归因于“同一个系统换参数”。

### 产出

查询类型 × 索引命中矩阵，外加 ANN recall 与精确召回对照。

### 验收

- 能解释为什么代码场景必须保留词法信号；
- 不把 ANN recall 等同于回答准确率；
- 能说明过滤发生在召回前还是融合后，以及它如何改变候选集合。

---

<a id="l3"></a>
## L3 三路召回消融（6h）

**目标**：验证 raw BM25、code-expanded view BM25、dense 三条腿的互补性。

### 前置

- 标好 30 个 query 的 gold chunk/span；
- 固定 snapshot、embedding、top_k、候选深度、融合参数；
- 准备实验分支或离线 harness，暴露三腿名次与 fused candidates。

### 步骤

1. 跑 all；
2. 分别跑 no raw、no view、no dense；
3. 再跑 raw only、view only、dense only；
4. 对每题保存三腿名次、fused 名次、最终选中项；
5. 记录 Recall@5、Recall@10、MRR、all-recall；
6. 单独做 chunk 大小实验，不与逐腿消融混在同一结论里；
7. 将失败分为：gold 未进候选、候选内排后、最终被去重/预算挤掉。

### 关键问题

如果 gold 进入某腿但未进入 fused top_k，问题在候选深度或融合；如果三腿都没有 gold，问题在表示、chunk 或 query。不能把所有失败都称为“召回差”。

### 产出

逐腿消融表 + 候选归因表 + 3 个失败案例。

### 验收

- 能指出哪条腿在哪个查询类型上不可替代；
- 能区分腿内召回、融合召回、最终证据召回；
- 实验 commit 与配置进入 manifest；
- 不声称当前生产配置可以直接关闭某腿。

---

<a id="l4"></a>
## L4 噪声注入（4h）

**目标**：验证同一 user 内无关记忆是否挤占相关证据，而不是测试跨用户隔离。

### 步骤

1. 为同一 `user_id` 写入 3 段相关会话；
2. 跑 query，保存 relevant 条件结果；
3. 在同一 user 下追加 5 段无关会话，覆盖不同项目/语言/主题；
4. 保持 query、模型、top_k、候选深度不变，重跑得到 noisy 条件；
5. 对齐相同 query，计算 paired improvement/degradation；
6. 检查每条 gold 在哪一步消失，并记录噪声来源腿；
7. 单独做跨 user 哨兵，确认隔离正常，不把它混入噪声收益。

### 指标

```text
improvement(q) = relevant_score(q) - noisy_score(q)
degradation(q)  = max(0, noisy_score(q) - relevant_score(q))
```

报告 mean Δ、95% paired bootstrap CI、被挤掉的 gold 数、p95 延迟与候选扫描成本。

### 产出

relevant/noisy 配对表，按项目/语言/主题切片。

### 验收

- 差值方向明确，不使用含义模糊的“noisy − relevant”；
- 能解释噪声从哪条腿进入；
- 区分“隔离失败”与“同 scope 内干扰”；
- 不用单次点估计宣称稳定提升。

---

<a id="l5"></a>
## L5 去重与合并（4h）

**目标**：看清重复内容如何占满 top_k，以及去重、bundle、span 抑制的收益与风险。

### 前置

当前实现没有公开 dedup 开关。使用实验分支关闭对应阶段，或对同一候选池离线比较不同 selector。不要用同一个 `request_id` 重复提交来制造重复，因为请求幂等会阻止重复写入；应使用不同 request/session 提交相同正文。

### 步骤

1. 构造 exact duplicate、同 message 相邻 chunk、部分重叠、不同 source 同正文；
2. 分别运行 no dedup、exact dedup、span suppression、full selection；
3. 检查 bundle 与成员是否共存，成员是否只在 bundle 实际选中后被抑制；
4. 验证 content 与 source span 逐字一致；
5. 记录 unique evidence 数、重复占位数、字符预算、Hit@k；
6. 构造“部分重叠但含新条件”的反例，防止误删；
7. 对相同输入重复运行，检查 tie-break 的确定性。

### 产出

重复类型 × selector 的结果表，加 span 校验与一个误删反例。

### 验收

- 能解释为什么 exact duplicate 可以后移，而不同 occurrence 未必能直接丢；
- bundle 不替代成员，成员不会无条件消失；
- 去重没有降低部分重叠证据的必要覆盖；
- 最终 content 始终是原文 slice。

---

<a id="l6"></a>
## L6 矛盾序列（6h）

**目标**：验证追加、覆盖、失效三种语义，并补齐当前 InsightMem 不具备的双时间、冲突、并发与删除实验。

### 数据族

| 测试族 | 建议规模 | 测什么 |
|---|---:|---|
| 顺序 old → new | 20+ | 当前值、历史值 |
| 同时冲突 | 50+ | retain_both 与仲裁 |
| 异域 | 50+ | 项目/租户不互相覆盖 |
| 迟到证据 | 50+ | valid time 与 recorded time |
| 并发/崩溃 | 1000 请求 | 幂等、CAS、恢复 |
| 撤回/删除 | 20+ | 派生记录、缓存、备份不复活 |

### 步骤

1. 定义 Fact schema：subject、predicate、object、scope、source_span、valid/recorded interval、version；
2. 分别实现 append-only、overwrite、bitemporal invalidation；
3. 对每题运行 current、as-of valid、as-of knowledge 三种查询；
4. 对 unresolved 冲突保留双方并标记 disputed，不随机选一条；
5. 用版本/CAS 模拟两个 request 同时更新同一 fact；
6. 注入 dreaming：读取旧快照 → 人工纠正 → CAS 提交，验证旧任务不覆盖新版本；
7. 删除 source 后检查 facts、notes、postings、vectors、cache、导出与备份恢复；
8. 保存旧事实误用率、as-of 准确率、冲突误判率、删除后泄漏率。

### 产出

三种更新语义对照表 + 双时间查询结果 + 删除传播清单。

### 验收

- 能写出半开区间查询；
- 区分“当时为真”与“系统当时知道”；
- 删除后泄漏率为零；任何非零结果都阻断验收；
- 明确 InsightMem 当前不提供这些治理 API，本实验属于新增能力。

---

<a id="l7"></a>
## L7 评测 harness（8h）

**目标**：搭一个可复现、可归因、能报告成本的评测，而不是只打印一个 accuracy。

### 步骤

1. 写一句可证伪假设与预算；
2. 冻结数据版本/hash、query IDs、gold、code commit；
3. 固定 answerer、prompt、embedding、judge、top_k、候选深度、seed；
4. 按主体分组划分 dev/test，dev 调参，test 最终确认；
5. 跑 no memory、full context、single retriever、full system；
6. 做两个单机制消融；
7. 至少运行 3 个 seed，保存逐题分数；
8. 计算 paired Δ 与 1000–10000 次 bootstrap 95% CI；
9. 用 gold evidence 跑 oracle reader，区分检索与 reader 问题；
10. 若使用 judge，随机化 A/B 顺序、盲化系统名、保存 rubric 与原始理由；
11. 记录 write/read token、p50/p95、build/maintenance、存储、失败与重试；
12. 保存至少 3 个失败案例，按机制层归因；
13. 在干净环境按文档命令复现，核对 manifest hash。

### 目录

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
```

### 报告

按 [评测手册第 11 节](evaluation.md#11-评测报告模板) 输出。至少包括：

- 样本数与分子/分母；
- baseline 与消融；
- 检索层、回答层、系统层指标；
- paired CI 与 seed；
- judge 校准或“未使用 judge”；
- 成本、失败案例、适用边界；
- 复现命令与 manifest hash。

### 验收

- 别人能在干净环境复现；
- test 没有用于调参；
- oracle 不冒充真实召回成绩；
- 不只报平均，还报能力切片与失败类型；
- 结果包含 build/maintenance，而不只是线上 Search 延迟。

---

<a id="l8"></a>
## L8 memory OS mini（8h）

**目标**：实现一个可观察、可回滚的 memory manager，验证 core / recall / archival、memory pressure、自编辑和共享记忆。

**步骤**

1. 定义 `CoreMemory`、`RecallMemory`、`ArchivalMemory` 三个 Adapter；
2. 为 core block 实现版本化编辑：`old → new + reason + diff`；
3. 实现上下文预算与 memory-pressure 阈值；
4. 至少实现一种策略：摘要低优先级历史、page-out 冷 block、page-in archival item；
5. 实现后台 consolidation，使用 CAS，不覆盖新人工纠正；
6. 增加第二个 Agent，共享一个只读 memory block；
7. 构造 20 组压力场景与 20 组共享/隔离场景；
8. 对比无 paging、固定 paging、自适应 paging；
9. 记录 page-in/page-out 准确率、摘要保真、回滚成功率、隔离泄漏、token 与 p95；
10. 保存 `memory_events.jsonl`、`memory_diff.jsonl` 与评测 manifest。

**产出**：memory OS 设计图、事件日志、消融表与失败案例。

**验收**

- 每次上下文变化都有原因与前后 token 记录；
- 自编辑可回滚，后台整理不覆盖新版本；
- 共享 block 的读写权限生效；
- 跨用户、跨 Agent、跨项目无泄漏；
- eviction 未被误报为 deletion；
- 成本包含 consolidation，而不只是 query latency。

---

## 4. 实验设计的最低要求

每个实验必须包含：

1. 一个 baseline；
2. 一个明确的单变量变化；
3. 固定数据、query、模型、prompt、top_k 中的至少三项；
4. 一个失败案例；
5. 一个成本数字；
6. 原始产物与可复现命令。

没有这六项，实验只能算 demo。
