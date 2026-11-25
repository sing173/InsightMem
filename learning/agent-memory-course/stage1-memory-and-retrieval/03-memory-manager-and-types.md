# 03 MemoryManager 与四种记忆

> 上一章：[02 MemoryTool 与记忆操作](02-memory-tool.md) · 下一章：[04 RAG 系统与最小知识库](04-rag-system.md)
> 对应 Hello Agents 第 8 章的 8.2.4–8.2.5：MemoryManager 与四种记忆类型。

## 本章你会得到什么

- 一张 Tool → Manager → Type → Store 的分层图；
- 四种记忆的准确定义与差异；
- 整合与遗忘策略的设计方法；
- 一张本仓库“已有 / 骨架 / 未实现”的能力表。

## 先区分 Tool 和 Manager

MemoryTool 面向 Agent，回答“可以做什么操作”。MemoryManager 面向系统，回答“这些操作怎样协调”。

```text
MemoryTool
  → 校验请求、scope、schema
  → 调用 MemoryManager
  → 返回工具结果

MemoryManager
  → 选择启用的记忆类型
  → 决定检索、整合、遗忘策略
  → 协调多个 Store 与索引
```

Hello Agents 第 8 章内部大致分成四层：

| 层 | 职责 | 典型组件 |
|---|---|---|
| 基础层 | 统一记录与配置 | `MemoryItem`、`MemoryConfig`、`BaseMemory` |
| 类型层 | 不同类型记忆的行为 | working / episodic / semantic / perceptual |
| 后端层 | 持久化与索引 | SQLite、Qdrant、Neo4j |
| 嵌入层 | 文本/多模态表示 | DashScope、本地 Transformer、TF-IDF 降级 |

本仓库没有完整 MemoryManager。`email_memory_lab.memory` 相当于三个轻量类型模块，`LocalStore` 相当于离线后端。

## 四种记忆：Hello Agents 的分类

注意：Hello Agents 第 8 章的第四种是**感知记忆**，不是程序记忆。本仓库的 email-agent 额外实现了 procedural memory，用来验证“规则与指令”这一类经验，两者不能混为一谈。

| 类型 | 保存什么 | Hello Agents 机制 | 典型问题 |
|---|---|---|---|
| Working memory | 当前任务临时状态 | 内存、容量、TTL、词面检索、时间衰减 | 现在正在处理什么？ |
| Episodic memory | 具体事件与经历 | SQLite + Qdrant、会话/时间过滤、recency 加权 | 上次遇到类似情况怎么处理？ |
| Semantic memory | 抽象事实、概念、关系 | Qdrant + Neo4j、实体/关系、图分数 | 我知道什么？ |
| Perceptual memory | 文本、图像、音频等感知信息 | CLIP/CLAP、不同模态不同向量集合 | 我看到/听到了什么？ |

### Working memory

工作记忆容量有限、寿命短。Hello Agents 示例默认：

- 容量 50；
- TTL 60 分钟；
- TF-IDF 词面相似度；
- 关键词匹配；
- 时间衰减。

它适合当前草稿、工具结果摘要、临时约束，不适合永久偏好。

### Episodic memory

情景记忆保存“发生过什么”。Hello Agents 使用 SQLite 保存结构化记录，用 Qdrant 做向量检索，并支持会话、时间和结构化过滤。

评分示例：

```text
episodic_score = (vector × 0.8 + recency × 0.2) × importance_factor
```

它适合历史邮件示例、故障轨迹、过去成功/失败的操作。

### Semantic memory

语义记忆保存事实、概念与关系。Hello Agents 使用 Qdrant + Neo4j，把向量检索和图检索结合起来。

评分示例：

```text
semantic_score = (vector × 0.7 + graph × 0.3) × importance_factor
```

它适合用户偏好、实体关系、稳定知识。但图检索依赖实体/边抽取，错误会沿边传播。

### Perceptual memory

感知记忆处理文本、图像、音频等模态。Hello Agents 示例使用 CLIP/CLAP，并为不同模态建立不同向量集合。

本仓库没有多模态 embedding、文件摄取或跨模态检索，因此这一部分只作为扩展设计。

## 本仓库的三类记忆怎样对应

| 本仓库类型 | 最接近 Hello Agents 类型 | 当前实现 | 差异 |
|---|---|---|---|
| Semantic | Semantic | namespace + Jaccard 检索 | 无实体抽取、图检索、真实 embedding |
| Episodic | Episodic | 历史邮件示例 + Jaccard 相似度 | 无 SQLite/Qdrant、时间过滤、recency 加权 |
| Procedural | 不在第 8 章四类中 | 固定 `email-style` 指令与规则 | 是 LangGraph/课程路线的扩展类型 |
| Working | Working | Agent 当前结果与上下文字段 | 没有独立容量/TTL Manager |
| Perceptual | Perceptual | 无 | 未实现 |

`LocalStore.search()` 使用 **Jaccard token overlap**，不是 BM25，也不是 dense embedding。它适合离线验证写入、scope 和行为归因，不能用来证明语义检索质量。

## Importance 与时间衰减

Hello Agents 的多种记忆使用 importance 调整分数：

```text
importance_factor = 0.8 + importance × 0.4
```

importance 表示“这条记忆对未来任务有多重要”，不等于置信度，也不等于检索相似度。

设计时要注意：

- importance 来自规则、人工标注还是 LLM；
- 是否随反馈更新；
- 高重要性错误记忆会不会长期霸榜；
- 时间衰减是否适合稳定偏好。

稳定签名可能不应该快速衰减；一次性会议安排应该快速过期。

## 整合：Consolidation

整合不是普通复制，而是改变记忆的形态、粒度或层级。Hello Agents 第 8 章展示：

```text
working → episodic
working → semantic
episodic → semantic
```

示例默认：

- working → episodic 的 `importance_threshold=0.7`；
- 遗忘阈值 `threshold=0.1`；
- 时间遗忘 `max_age_days=30`。

这些数字是示例配置，不是通用最佳值。

### 整合流程骨架

```python
def consolidate(snapshot):
    proposals = propose_transitions(snapshot)
    current = reload_current_state()
    accepted = []
    for proposal in proposals:
        if still_applicable(proposal, current):
            accepted.append(proposal)
    return commit_with_cas(accepted)
```

必须满足：

- 保留 source 与元数据；
- 不读取 gold label；
- 不覆盖新人工纠正；
- 可重试、可审计；
- 失败时回滚或保留原记忆。

Hello Agents 的 `06_Memory_Consolidation_Demo.py` 主要展示手工顺序整合，不是自动后台调度；不同阈值的统计也不能直接当成严格消融。

## 遗忘：Forgetting

Hello Agents 支持三类策略：

| 策略 | 依据 | 适合 | 风险 |
|---|---|---|---|
| Importance-based | 重要性阈值 | 清理低价值噪声 | 重要性判断错误 |
| Time-based | 超过最大年龄 | 临时事件、过期状态 | 稳定知识被误删 |
| Capacity-based | 超过容量上限 | 控制存储与检索成本 | 罕见但关键信息被挤掉 |

### 实验设计

分别测试三种策略，不要在同一 Store 上顺序执行后比较，因为前一次删除已经污染后一次输入。

```text
策略 A：新 Store + importance forget
策略 B：新 Store + time forget
策略 C：新 Store + capacity forget
```

记录：

- 删除 ID 与原因；
- 保留 ID；
- 检索召回变化；
- 误删案例；
- 存储与延迟变化。

## 一个最小 MemoryManager 教学骨架

下面代码用于说明职责，不是本仓库已有实现：

```python
class MemoryManager:
    def __init__(self, config):
        self.config = config
        self.memories = {
            "working": WorkingMemory(config.working),
            "episodic": EpisodicMemory(config.episodic),
            "semantic": SemanticMemory(config.semantic),
        }

    def add(self, memory_type, item):
        return self.memories[memory_type].add(item)

    def search(self, query, memory_types=None, limit=5):
        types = memory_types or list(self.memories)
        candidates = []
        for memory_type in types:
            candidates.extend(self.memories[memory_type].search(query, limit))
        return self.rank_and_filter(candidates, limit)

    def consolidate(self, snapshot):
        proposals = self.propose_transitions(snapshot)
        return self.commit_with_cas(proposals)

    def forget(self, strategy):
        return self.apply_forget_policy(strategy)
```

生产实现还要补：

- 并发与 CAS；
- scope 与权限；
- 持久化；
- 指标与审计；
- 外部 Store 故障；
- 嵌入模型版本。

## API 漂移提醒

Hello Agents 第 8 章正文与示例存在 API 写法差异：有的使用 `execute(action, **kwargs)`，有的使用 `run({"action": ...})`。重建教程时应固定版本，并以实际可运行调用为准。

本教程不复制这些不一致签名，而是用“操作契约 + 本仓库实现”讲解。若你后续运行 Hello Agents 示例，请以其当前源码和版本为准。

## 本章小结与下一步

你已经知道：

- MemoryTool 是 Agent 操作面，MemoryManager 是协调层；
- Hello Agents 四类是 working、episodic、semantic、perceptual；
- 本仓库额外实现 procedural，但没有感知记忆；
- 整合是类型迁移/重组，遗忘是生命周期策略；
- 当前仓库没有容量、TTL、importance、自动整合或在线遗忘。

下一章 [04 RAG 系统与最小知识库](04-rag-system.md) 转向另一条路径：外部文档怎样经过处理、索引和检索进入回答。
