# 01 记忆系统的工作流程

> 上一章：[00 快速开始](00-quick-start.md) · 下一章：[02 MemoryTool 与记忆操作](02-memory-tool.md)
> 对应 Hello Agents 第 8 章的 8.2.1：记忆系统的工作流程。

## 本章你会得到什么

- 一条完整的记忆生命周期图；
- 一次 semantic memory 从写入到使用的 trace；
- 一张“代码模块 ↔ 记忆动作”的对应表；
- 一组可检查的失败问题：没写入、没检索、没注入、没使用。

## 先看一条记忆怎样产生

假设用户说：

> “以后回复邮件简短一点，签名写 John Doe。”

系统不能只把这句话打印出来。它需要完成至少六件事：

```text
输入事件
  → 编码：这段话值得记成什么？
  → 保存：放在哪个用户、哪个 namespace？
  → 检索：下次遇到相关任务时怎样找到？
  → 注入：怎样放进本次上下文？
  → 使用：怎样改变路由或回复？
  → 治理：过时、冲突、删除时怎样处理？
```

Hello Agents 第 8 章把记忆系统拆成工具、管理器和存储三层。本仓库用更小的离线实现展示同一条链路：

```text
EmailAgent
  → SemanticMemory / EpisodicMemory / ProceduralMemory
  → LocalStore
```

它没有实现完整的 MemoryManager，但足够让你看清写入、读取和使用之间的边界。

## 第 1 步：写入一条 semantic memory

打开 [02-semantic-memory.ipynb](../../../experiments/email-agent/notebooks/02-semantic-memory.ipynb)。Notebook 会从 `data/memories.json` 读取种子记忆，其中包含：

```json
{
  "key": "signature",
  "value": {
    "kind": "signature",
    "value": "John Doe",
    "content": "Always sign email replies as John Doe."
  }
}
```

这条记录被写入：

```text
namespace = ("email", "semantic", "user-a")
key       = "signature"
value     = { kind, value, content }
```

对应代码是：

```python
semantic.add("signature", {
    "kind": "signature",
    "value": "John Doe",
    "content": "Always sign email replies as John Doe.",
})
```

`SemanticMemory.add()` 最终调用 `LocalStore.put()`。注意：此时只是**保存**，还没有影响任何回答。

## 第 2 步：运行 baseline 与 semantic 两组配置

Notebook 使用同一批 10 封邮件，只改变 `use_semantic`：

| 配置 | semantic | episodic | procedural |
|---|---|---|---|
| baseline | 否 | 否 | 否 |
| semantic | 是 | 否 | 否 |

预期结果：

```text
baseline: routing 8/10, writing 0/4, memory recall 0/6
semantic: routing 8/10, writing 4/4, memory recall 4/6
```

**结果说明什么：**

- routing 不变，说明 semantic memory 在这批数据里只影响回复个性化；
- writing 从 0/4 变成 4/4，说明签名偏好确实进入回复；
- memory recall 从 0/6 变成 4/6，说明只有需要 semantic 的四封邮件命中了对应记忆。

这就是单变量对照：没有同时改 prompt、模型、数据或路由规则，只开启一种记忆。

## 第 3 步：查看一条完整 trace

Notebook 中的 `docs-question` 会返回：

```text
used_memory: ('semantic:signature',)
context:
  fact=tone ...
  fact=signature ...
response:
  ...
  John Doe
```

把这条 trace 拆开：

| 字段 | 含义 | 对应动作 |
|---|---|---|
| `used_memory` | 哪些记忆实际参与了本次处理 | 使用 |
| `context` | 检索到了哪些事实及分数 | 检索 |
| `response` | 最终行为是否改变 | 结果 |

实现位于 [EmailAgent.handle()](../../../experiments/email-agent/src/email_memory_lab/agent.py#L29)：

```python
facts = self.semantic.recall(f"{email.subject} signature tone", limit=3)
signature = ...
return AgentResult(
    action=action,
    response=self._write_response(email, action, signature),
    used_memory=tuple(used_memory),
    context="\n".join(context),
)
```

**核心思想：** 评测记忆不能只看“库里有没有”，要看“检索到了什么、注入了什么、行为是否改变”。这三个问题分别对应召回、装配和使用。

## 第 4 步：制造三种失败，理解链路

### 失败 A：没有写入

如果 `signature` 不存在，`recall()` 返回空，回复退回通用签名。

判断方法：

```python
store.get(("email", "semantic", "user-a"), "signature") is None
```

问题在写入或 namespace，不在生成。

### 失败 B：写入了但没检索

如果 key 写错，或 query 与内容完全不匹配，记录仍在 Store 中，但本次没有命中。

判断方法：直接 `get()` 能拿到记录，`search()` 却为空。问题在检索 query、索引或过滤。

### 失败 C：检索到了但没注入

如果代码打印了 fact，却没有把 signature 传给 `_write_response()`，`used_memory` 可能仍显示命中，但回复不会改变。

判断方法：对比 `context` 与最终 `response`。问题在装配或使用。

这也是为什么后续评测必须保存 retrieval、context 和 final output，而不是只保存答案。

## 第 5 步：验证 scope

`LocalStore` 的 namespace 包含 `user_id`。给用户 B 写入不同签名，再用用户 B 处理同一封邮件：

```text
user-a → John Doe
user-b → Jane Smith
```

测试见 [test_email_memory.py](../../../experiments/email-agent/tests/test_email_memory.py)。它验证两件事：

- 用户 B 不能读到用户 A 的签名；
- 用户 A 的检索结果不会因为用户 B 写入而变化。

**核心思想：** scope 不是检索后的装饰，它必须进入存储键、检索条件和缓存键。

## 代码模块与记忆动作对应

| 记忆动作 | 本仓库模块 | 当前能力 |
|---|---|---|
| 写入 | `SemanticMemory.add` / `EpisodicMemory.add` / `ProceduralMemory.add` | 可运行 |
| 读取 | `LocalStore.get` | 可运行 |
| 检索 | `LocalStore.search` / `SemanticMemory.recall` / `EpisodicMemory.similar` | 可运行，离线词面相似度 |
| 注入 | `EmailAgent.handle` 中的 `context` 与 `used_memory` | 可运行 |
| 使用 | `_write_response` 与路由规则 | 可运行，确定性策略 |
| 更新/失效 | 需要新版本或覆盖策略 | 教学骨架 |
| 遗忘/整合 | 需要 MemoryManager | 尚未实现 |

## 与 Hello Agents MemoryTool 的关系

Hello Agents 把上述能力包装成 Agent 可调用的工具，并由 MemoryManager 管理类型、重要性、容量和整合。本仓库当前由应用代码显式调用记忆，不让模型自主决定何时写入或搜索。

因此：

- 本仓库适合验证记忆的**数据流和效果归因**；
- Hello Agents 的 MemoryTool 更强调**Agent 自主操作记忆**；
- 两者都离不开存储、scope、检索和注入这些基础契约。

## 本章小结与下一步

你已经看到一条记忆从写入到使用的完整路径，也知道失败可能发生在任何一层：

```text
没写入 → 没检索 → 没注入 → 没使用
```

下一章 [02 MemoryTool 与记忆操作](02-memory-tool.md) 会把这些动作拆成 add、search、update、forget 和 consolidate，说明每一步的输入、输出和风险。
