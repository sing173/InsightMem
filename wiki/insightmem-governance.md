---
title: InsightMem 隔离、幂等与数据治理
summary: 正常运行采用 append-only，user_id 隔离检索，删除依赖离线运维流程。
status: verified
section: InsightMem
order: 22
updated: 2026-11-24
tags: [insightmem, governance, isolation, idempotency, retention]
sources:
  - src/insightmem/coding/service.py
  - docs/api-contract.md
  - docs/operations.md
  - scripts/purge_user.py
  - learning/agent-memory-tutorial/06-governance.md
---

# InsightMem 隔离、幂等与数据治理

## 更新语义

InsightMem 在正常 Add/Search 路径中是 **append-only**：

- 原始消息不会被检索选项改写。
- 新事实不会自动覆盖旧事实。
- 没有在线 Clear、Update 或 Delete 接口。
- 查询期过程叙述过滤不会删除底层数据。

因此它保留“当时写过什么”，但不知道“现在什么仍然为真”。这与 Zep 的失效语义、Letta 的离线整理语义不同。对照见 [06-governance.md:14–27](../learning/agent-memory-tutorial/06-governance.md#L14)。

## 用户隔离

`user_id` 是唯一检索隔离键，并出现在每张业务表的主键或查询条件中。`session_id` 只标识来源会话，不参与 Search 过滤。

Search 使用 `BEGIN` 和 `query_only` 读取一个已提交快照，避免看到半写入的 Add。实现见 [service.py:163–200](../src/insightmem/coding/service.py#L163)。

## 幂等与冲突

- 幂等键：`user_id + request_id`。
- 相同载荷哈希：返回已有结果，不重复写入。
- 相同 `request_id`、不同载荷：返回 409。
- 写入前和事务内都会检查，避免并发重复提交。

契约见 [api-contract.md:45–57](../docs/api-contract.md#L45)。

## 时间与版本

消息保存 `timestamp_ms`，请求保存 `ingest_seq`。它们用于来源展示和确定性排序，不构成：

- 事实生效时间与失效时间；
- 时间过滤器；
- 时间衰减；
- TTL。

数据库还记录 schema、检索 profile 和 embedding 身份。配置或模型不匹配时拒绝启动，需要重建数据库，见 [operations.md:8–17](../docs/operations.md#L8)。

## 删除与保留

AML 评测数据通常要求在运行结束后 30 天内删除，除非组织者另行书面同意。运维文档提供两种流程：

1. 整库重置；
2. 停服或对副本运行 `scripts/purge_user.py`，按外键顺序物理删除单用户数据。

脚本要求 `--apply` 才真正删除，否则只报告行数。细节见 [operations.md:60–105](../docs/operations.md#L60) 和 [purge_user.py](../scripts/purge_user.py)。

## 学习意义

InsightMem 是一个很好的“最小治理基线”：先理解追加、隔离、幂等和审计，再对照 [[memory-frameworks]] 中具备时间失效、离线整理或人格演化的系统，能更清楚治理成本的来源。

<!-- generated:backlinks:start -->
## 反向链接

- [[insightmem|InsightMem 机制审计]] — InsightMem 是全量会话轨迹持久化与确定性混合证据检索，不是抽取式记忆 OS。
<!-- generated:backlinks:end -->
