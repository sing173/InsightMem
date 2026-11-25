# 04 RAG 系统与最小知识库

> 上一章：[03 MemoryManager 与四种记忆](03-memory-manager-and-types.md) · 下一章：[05 高级检索与本仓库实现](05-advanced-retrieval.md)
> 对应 Hello Agents 第 8 章的 8.3.1–8.3.4：RAG 基础、工作流程、快速体验与架构设计。

## 本章你会得到什么

- 一张 RAG 数据流图；
- 一次 InsightMem Add/Search 的完整观察；
- 写入路径与查询路径的模块对应表；
- 一组失败归因方法：没入库、没召回、没选中、没进入回答。

## 先看 RAG 到底解决什么

假设你有一批文档，希望 Agent 根据文档回答问题。直接把所有文档塞进 prompt 有三个问题：

1. 文档可能远超上下文窗口；
2. 大量无关内容会增加成本和噪声；
3. 无法稳定说明答案来自哪里。

RAG 的做法是：**先把文档变成可检索的索引，再只取与当前问题相关的少量证据。**

```text
文档/消息
  → 加载与清洗
  → 分块
  → 建立索引
  → 查询与召回
  → 过滤/融合/排序
  → 注入上下文
  → 生成回答
```

RAG 不是“向量数据库”的同义词。向量库只是其中一种索引；本仓库使用 SQLite 保存原文和向量，并同时运行 BM25 与 dense 召回。

## 快速体验：运行 InsightMem Quickstart

打开 [00-quickstart.ipynb](../../../experiments/insightmem/notebooks/00-quickstart.ipynb)，执行 Run All。

Notebook 会：

1. 创建独立 SQLite 数据库；
2. 写入三条样本消息；
3. 用同一 request 重放；
4. 搜索 parser 相关证据；
5. 验证用户隔离；
6. 保存 manifest 和 hits。

预期观察：

| 操作 | 预期结果 | 说明什么 |
|---|---|---|
| Add | 返回 3 个 stored chunks | 原文已被切分并写入 |
| 同 request 重放 | 仍返回 3 | 幂等生效，没有重复 source |
| Search | 返回带 source 标签的有序 hits | 检索结果可追溯 |
| 用户 A 查询 B 的哨兵 | 看不到 B 的内容 | scope 隔离生效 |

**核心思想：** 在讨论 Recall 之前，先验证写入原子、幂等、隔离和溯源。这些是 RAG 正确性的地基。

## Add 路径：文档怎样进入系统

InsightMem 的写入入口是 [CodingMemoryService.add()](../../../src/insightmem/coding/service.py#L98)。

主要步骤：

```text
MemoryMessage[]
  → parse：识别角色、类型、稳定 message_id
  → chunk_spans：按 token/字符限制切分
  → source view：保留原文切片
  → embedding：为非空 view 生成向量
  → 单事务提交 request/message/chunk/view/vector
```

关键设计：

- **原文不可变**：返回证据来自 source slice，不由检索器改写；
- **span 可追溯**：chunk 记录 `start_char/end_char`；
- **同步可检索**：Add 返回时，所有数据已经在同一快照中；
- **fingerprint 固定**：配置或 embedding identity 改变时，不允许混用旧数据库。

对应数据表包括：

```text
coding_requests
source_messages
source_chunks
index_views
view_sources
view_embeddings
```

这也是 InsightMem 与“只把文档 embedding 后塞进向量库”的主要区别：它把原文、切片、索引表示和向量分开保存。

## Search 路径：query 怎样变成证据

InsightMem 的查询入口是 [CodingMemoryService.search()](../../../src/insightmem/coding/service.py#L163)。

主要步骤：

```text
query
  → 读取同一 user 的 committed snapshot
  → raw BM25
  → code-expanded BM25
  → exact dense cosine
  → grouped-rank fusion
  → candidate preparation
  → bundle / span 去重
  → deterministic selection
  → top_k
```

三条召回腿回答不同问题：

| 召回腿 | 适合什么 | 典型失败 |
|---|---|---|
| Raw BM25 | 精确标识符、路径、错误码 | 同义改写可能匹配不上 |
| Code-expanded BM25 | 代码符号、拆词、大小写变体 | 展开过度带来噪声 |
| Dense | 语义相近但字面不同的表达 | 精确 token 可能不如词法 |

融合后还要处理重复、相邻 span 和预算。因此“候选被召回”不等于“最终会返回”。

## 一次 Search 的结果怎样解释

Quickstart 返回的 hit 类似：

```json
{
  "id": "c1-...",
  "content": "[source role=user kind=issue_prompt] The parser drops backslashes...",
  "score": 0.0489,
  "created_at": "2025-11-24T00:00:00+00:00"
}
```

各字段含义：

- `id`：稳定 chunk/evidence ID；
- `content`：带来源标签的原文切片；
- `score`：融合与选择后的排序分数；
- `created_at`：来源消息时间。

不要只按 score 判断“答案正确”。分数表示系统如何排序，不表示内容一定满足用户问题。

## Hello Agents RAGTool 的文档处理路径

Hello Agents 第 8 章的 RAGTool 更接近完整知识库工具，典型链路是：

```text
文件
  → MarkItDown / PDF 增强路径 / 纯文本降级
  → Markdown 标题栈与 heading_path
  → 段落边界与 token 预算分块
  → 保留 start/end 偏移
  → embedding
  → Qdrant 存储
```

查询通过统一执行入口：

```python
rag.execute("add_text", text=..., document_id=...)
rag.execute("search", query=..., limit=3, min_score=0.1)
rag.execute("stats")
```

不同示例存在 `execute` 与 `run` 的 API 漂移，实际运行时应固定 Hello Agents 版本并以源码为准。

### 与本仓库的主要差异

| 能力 | Hello Agents 第 8 章 | InsightMem |
|---|---|---|
| 文档提取 | MarkItDown、PDF 增强、纯文本降级 | 当前主要接收消息文本 |
| 分块 | 标题栈、heading_path、段落/token | source chunk + code-expanded view |
| 存储 | Qdrant 等外部向量库 | SQLite 原文/视图/向量 |
| 检索 | 基础与高级搜索 | BM25 + dense + RRF |
| 生成 | RAGTool/问答助手 | 只返回证据，外部 reader 回答 |
| 多格式 | PDF/Office 等示例 | 未实现 |

因此 InsightMem 适合学习“证据索引与选择”，不能直接替代完整文档摄取工具。

## 生成阶段：本仓库目前到哪里为止

InsightMem 只负责 Add/Search，不生成最终答案。平台或外部 reader 根据 hits 回答。

一个最小 reader 骨架是：

```python
def answer_with_evidence(query: str, hits: list[dict]) -> str:
    context = "\n\n".join(hit["content"] for hit in hits)
    return fixed_reader.invoke({
        "question": query,
        "context": context,
    })
```

这里必须固定 reader、prompt、预算和模型版本，否则无法区分“检索差”与“reader 差”。

Hello Agents 的 RAGTool 还包含更完整的文档加载、向量库和生成集成；本仓库刻意把证据服务与 reader 分开，方便做检索层消融。

## 失败归因：先定位在哪一层

| 现象 | 可能原因 | 验证方法 |
|---|---|---|
| 库里没有 | Add 失败、过滤、切分问题 | 查 request/message/chunk |
| 库里有但没召回 | query 不匹配、scope 错误、候选深度不足 | 绕过检索直接读取 |
| 召回了但没返回 | 融合、过滤、bundle、预算挤掉 | 保存候选与最终 hits |
| 返回了但回答错 | reader/prompt、证据冲突、推理问题 | 用 gold evidence 跑 oracle reader |
| 其他用户可见 | scope 或缓存键缺失 | 双用户哨兵 |

**核心思想：** RAG 是一条流水线，不是一次向量相似度计算。每一层都要有可观测输出。

## 本章小结与下一步

你已经看到：

- Add 如何把原文、chunk、view 和向量原子写入；
- Search 如何用三路召回、融合和选择生成有限证据；
- 为什么检索结果必须带来源和 scope；
- 为什么最终回答错误不一定等于“召回差”。

下一章 [05 高级检索与本仓库实现](05-advanced-retrieval.md) 会讨论查询扩展、混合检索、重排、图检索和时间过滤，并说明 InsightMem 已经实现和尚未实现的部分。
