# 01 ContextBuilder：把候选信息变成上下文

> 上一章：[00 什么是上下文工程](00-context-engineering.md) · 下一章：[02 GSSC 流水线](02-gssc-pipeline.md)
> 对应 Hello Agents 第 9 章的 9.3.1–9.3.2：ContextBuilder 的设计动机与核心数据结构。

## 本章你会得到什么

- 一张 ContextBuilder 的输入/输出图；
- V0.2.8 的 `ContextPacket` 与 `ContextConfig` 快照；
- 一个把 InsightMem hits 转成上下文包的教学骨架；
- 一份文档与实现漂移清单，避免照抄出错。

## 先看为什么需要 ContextBuilder

阶段一解决了“信息从哪里来”：Memory、RAG、Store。阶段二要解决“这次调用带哪些信息”。

如果没有统一构建器，每个 Agent 都可能自己拼上下文：

```python
prompt = system_prompt + history + memories + retrieved_docs + tool_outputs
```

很快会出现：

- 不同 Agent 顺序不一致；
- 预算计算各不相同；
- 检索失败被静默忽略；
- 相同输入产生不同上下文；
- 无法判断是检索差还是装配差。

ContextBuilder 的职责是把这些规则集中到一个 Module：

```text
system instructions
memory / RAG results
conversation history
additional packets
config
          │
          ▼
     ContextBuilder
          │
          ▼
固定分区、有限预算、可调试的上下文
```

## V0.2.8 API 快照

本章绑定 Hello Agents **V0.2.8**。不要混用当前 `main` 或 V1 的字段。

```python
ContextBuilder(memory_tool=None, rag_tool=None, config=None)

ContextPacket(
    content,
    timestamp=datetime.now(),
    metadata={},
    token_count=0,
    relevance_score=0.0,
)

ContextConfig(
    max_tokens=8000,
    reserve_ratio=0.15,
    min_relevance=0.3,
    enable_mmr=True,
    mmr_lambda=0.7,
    system_prompt_template="",
    enable_compression=True,
)
```

`build()` 的签名是：

```python
build(
    user_query,
    conversation_history=None,
    system_instructions=None,
    additional_packets=None,
) -> str
```

注意真实参数名是 `additional_packets`，不是教程正文中的 `custom_packets`。

## ContextPacket：一个候选信息包

一个 packet 不只是一段文本，还带有：

| 字段 | 含义 |
|---|---|
| `content` | 原始内容 |
| `timestamp` | 新近性计算依据 |
| `metadata` | 来源、类型、ID 等 |
| `token_count` | 预算成本；0 表示自动计数 |
| `relevance_score` | 初始相关分数；Select 会重新计算并覆盖 |

自动计数优先使用 `cl100k_base`，失败时降级为 `len(text) // 4`。因此 token 数只是估算，不保证与真实模型计费完全一致。

## ContextConfig：预算与选择策略

几个关键参数：

- `max_tokens`：总预算；
- `reserve_ratio`：为输出预留比例；
- `min_relevance`：非系统包的最低相关阈值；
- `enable_compression`：超预算时是否压缩；
- `enable_mmr` / `mmr_lambda`：V0.2.8 配置存在，但构建器实际没有使用；
- `system_prompt_template`：V0.2.8 配置存在，但实际没有使用。

可用预算：

```python
available_tokens = int(max_tokens * (1 - reserve_ratio))
```

例如：

```text
max_tokens = 4000
reserve_ratio = 0.15
available_tokens = 3400
```

这 3400 是候选包的选择预算，不等于最终字符串一定不会超限；分区标题、Task、Output 和空行还需要额外空间。

## 文档与 V0.2.8 的漂移

| 项目 | 教程正文 | V0.2.8 实现 |
|---|---|---|
| `ContextPacket` 字段顺序 | content, timestamp, token_count, relevance_score, metadata | content, timestamp, metadata, token_count, relevance_score |
| `ContextConfig` 默认值 | max_tokens=3000, reserve=0.2, min=0.1 | max_tokens=8000, reserve=0.15, min=0.3 |
| 权重字段 | recency_weight / relevance_weight | 不存在 |
| MMR 字段 | 未强调 | 存在但未使用 |
| 额外包参数 | `custom_packets` | `additional_packets` |
| 历史消息 | 最近 5 条逐条成包 | 最近 10 条合并成一个包 |
| 相关性 | Jaccard | 查询词交集数 / 查询词数 |
| 新近性 | 24 小时衰减 | 一小时尺度指数衰减 |

**核心思想：** 教程必须绑定版本。位置传参、字段默认值和返回类型漂移，都会让“看起来一样”的代码行为不同。

## 把 InsightMem hits 变成 ContextPacket

本仓库没有 ContextBuilder，但可以写一个教学适配器：

```python
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ContextPacket:
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)
    token_count: int = 0
    relevance_score: float = 0.0


def hits_to_packets(hits: list[dict]) -> list[ContextPacket]:
    return [
        ContextPacket(
            content=hit["content"],
            metadata={
                "type": "knowledge_base",
                "source_id": hit["id"],
                "score": hit["score"],
            },
        )
        for hit in hits
    ]
```

然后把它作为 `additional_packets` 交给构建器。这个骨架只展示数据形状，不是本仓库已有实现。

## 一次最小构建示例

固定输入，避免时间变化影响结果：

```python
packets = [
    ContextPacket(
        content="parser drops backslashes",
        timestamp=datetime(2026, 1, 1, 12, 0),
        metadata={"type": "knowledge_base", "source_id": "doc-1"},
    ),
    ContextPacket(
        content="unrelated release notes",
        timestamp=datetime(2026, 1, 1, 12, 30),
        metadata={"type": "knowledge_base", "source_id": "doc-2"},
    ),
]

context = builder.build(
    user_query="Why does the parser drop backslashes?",
    system_instructions="Answer only from evidence.",
    additional_packets=packets,
)
```

预期观察：

- 系统指令进入 Role & Policies；
- 用户问题进入 Task；
- 相关证据进入 Evidence；
- 不相关内容可能被 Select 过滤；
- 总预算为输出预留空间。

## ContextBuilder 不负责什么

它不负责：

- 产生记忆；
- 替代 RAG；
- 执行终端命令；
- 保存长期任务状态；
- 保证答案正确。

它只负责把已有候选加工成上下文。候选质量差，构建器无法凭空修复；上下文装配差，再好的检索也可能浪费。

## 本章小结与下一步

你已经知道 ContextBuilder 的输入、输出和预算契约，也知道 V0.2.8 与文档的字段漂移。

下一章 [02 GSSC 流水线](02-gssc-pipeline.md) 会逐步拆开 Gather、Select、Structure、Compress，说明每个阶段怎样改变候选集合。
