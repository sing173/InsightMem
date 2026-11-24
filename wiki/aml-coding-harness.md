---
title: AML Coding Track 与 InsightMem 定位
summary: InsightMem 是 AML 兼容的同步 Add/Search 记忆服务，平台负责固定答案生成与评分。
status: verified
section: 评测
order: 50
updated: 2026-11-24
tags: [aml, coding, harness, evaluation]
sources:
  - README.md
  - docs/api-contract.md
  - learning/agent-memory-tutorial/evaluation.md
  - learning/agent-memory-tutorial/07-evaluation.md
  - docs/papers-zh/04-retrieval-eval.md
---

# AML Coding Track 与 InsightMem 定位

## Add / Search 契约

AML 把记忆系统与答案生成分开：

- **Add**：提交会话消息，系统同步持久化并立即可检索。
- **Search**：针对 query 返回最多 `top_k` 条证据。
- **Answerer**：由平台统一或固定，不在 InsightMem 内。
- **评分**：平台根据最终任务结果计算，不只看检索分数。

InsightMem 只实现 Add/Search，不实现完整 agent harness。契约见 [api-contract.md](../docs/api-contract.md)。

## Coding Track 的评测形态

CAMBench Coding / AML 使用 150 个 SWE 任务，并在 relevant/noisy 两种条件下运行：

- relevant：只提供相关历史；
- noisy：在相关历史之外加入无关会话；
- 正式 Search 通常要求 `top_k=100`；
- 平台关注 Overall Resolved 等任务级指标。

数据与指标背景见 [evaluation.md:7–19](../learning/agent-memory-tutorial/evaluation.md#L7)。

## InsightMem 的适配点

1. 保存每条提交消息，不提前丢掉失败尝试和工具输出。
2. Add 同步完成，符合不允许异步任务 ID 的契约。
3. `user_id` 隔离每次评测会话。
4. 三路检索兼顾精确代码词与自然语言语义。
5. 噪声过滤、重复内容处理和跨度去重直接针对证据注入。
6. 返回顺序比分数更重要，最终选择是确定性的。

## 不应混淆的层次

| 层次 | InsightMem 是否负责 |
|---|---|
| 记忆写入与持久化 | 是 |
| 证据检索与筛选 | 是 |
| 当前 agent 上下文管理 | 否 |
| 答案生成 | 否 |
| 任务执行与评分 | 否 |

因此，竞赛表现验证的是**给定 harness 下的记忆证据质量**，不等于证明它具备完整 Agent Memory 生命周期。进一步阅读 [[insightmem]] 与 [[learning-path]]。

<!-- generated:backlinks:start -->
## 反向链接

- [[insightmem|InsightMem 机制审计]] — InsightMem 是全量会话轨迹持久化与确定性混合证据检索，不是抽取式记忆 OS。
<!-- generated:backlinks:end -->
