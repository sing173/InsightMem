# 05 项目：长程代码库维护助手

> 上一章：[04 TerminalTool：安全的文件系统探索](04-terminal-tool.md) · 下一章：[06 总结、练习与实现缺口](06-review.md)
> 对应 Hello Agents 第 9 章的 9.6：长程智能体实战——代码库维护助手。

## 本章你会得到什么

- 一张维护助手的工具与状态架构图；
- 一次三天工作流的完整拆解；
- 上游示例的真实限制与失败点；
- 一个适合本仓库的、可核验的 Capstone 设计。

## 项目场景

你要让 Agent 用三天时间维护一个代码库：

```text
第一天：探索结构，记录问题
第二天：深入模块，处理 blocker
第三天：回顾进展，规划重构
一周后：检查状态，生成报告
```

难点不是单次回答，而是跨请求保持：

- 任务目标；
- 已完成事项；
- 当前 blocker；
- 证据来源；
- 下一步行动；
- 工具调用与成本。

## 上游实际架构

`codebase_maintainer.py` 是一个“编排器 + 工具型 Agent”，不是旧版预处理 Agent。

```text
CodebaseMaintainer
  ├─ MemoryTool（仅 working）
  ├─ NoteTool（磁盘 Markdown）
  ├─ TerminalTool（文件系统探索）
  ├─ ContextBuilder（4000 tokens）
  └─ FunctionCallAgent（最多 30 次工具迭代）
```

关键配置：

```text
ContextBuilder:
  max_tokens = 4000
  reserve_ratio = 0.15
  min_relevance = 0.2

Conversation history:
  最多保留 20 条 Message

Note workspace:
  ./<project_name>_notes
```

MemoryTool 只启用 working memory，不是可靠的跨进程持久层。真正跨会话延续主要依赖磁盘笔记。

## 每轮工作循环

```text
1. 检索 blocker 与相关笔记
2. 转成 ContextPacket
3. ContextBuilder 构建上下文
4. 更新 Agent system prompt
5. Agent 自主调用工具
6. 更新最近 20 条历史
7. 记录统计
```

模式 `auto/explore/analyze/plan` 只是提示建议，不是强制状态机。Agent 是否调用工具、是否创建笔记，取决于模型行为。

## 三天工作流

### 第一天：探索

- 查看项目结构；
- 阅读 `data_processor.py`；
- 记录数据验证、模型校验等问题；
- 形成项目结构总结。

### 第二天：分析

- 深入 `api_client.py`；
- 检查错误处理、重试、超时；
- 把发现记录为 blocker 或 action；
- 决定修复优先级。

### 第三天：规划

- 回顾已有笔记；
- 创建 task_state；
- 生成重构计划；
- 列出风险与下一步。

### 一周后：恢复

- 新进程读取同一笔记目录；
- 查看 summary；
- 生成 JSON 报告；
- 核对任务是否延续。

## 预期产物

```text
<project>_notes/
  note_*.md

maintainer_report_<session_id>.json
```

报告应包含：

- 会话开始时间；
- 命令数；
- 笔记数；
- 问题数；
- 工具调用数；
- 当前 blocker；
- 下一步计划。

## 上游示例不能证明什么

这份案例很有教学价值，但不能把展示结果当成确定事实：

- 三天实际在同一进程、同一会话内运行，只 `sleep(1)`；
- 多个路径硬编码作者 Mac 环境；
- `06` 读取不存在的 `stats["activity"]["tool_calls"]`，会触发 KeyError；
- `_track_tool_usage()` 可能重复计数；
- `issues_found` 基本不更新；
- `main()` 使用不存在的 `./my_flask_app`；
- README 提到的日志文件不存在；
- 文档中的 50 文件、3500 行、覆盖率、24 次命令、8 条笔记属于案例叙述，不是所附小样本的确定输出。

**核心思想：** 演示能说明工具如何组合，不能替代可复现评测。

## 更适合本仓库的 Capstone

不要从零复制上游，先用 InsightMem 仓库作为固定 fixture：

```text
src/insightmem/coding/parse.py
src/insightmem/coding/service.py
tests/test_coding.py
experiments/insightmem/runs/
```

先人工形成一份可核验清单：

| 检查项 | 预期证据 |
|---|---|
| parser 是否保留原始分隔符 | parse.py + test_coding.py |
| Add 是否幂等 | service.py + test_lab.py |
| Search 是否隔离用户 | service.py + Quickstart |
| 运行产物是否可追溯 | runs/<run_id>/manifest.json |

然后让 Agent 或固定脚本工具逐项取证，避免“凭感觉说维护完成”。

## 一个确定性工作流骨架

先用脚本工具代替 LLM，验证状态闭环：

```python
def maintain_once(workspace, notes, builder, tools):
    evidence = tools.explore(workspace)
    findings = tools.check(evidence)
    notes.record(findings)
    packets = notes.to_packets()
    context = builder.build(current_task, additional_packets=packets)
    return {
        "context": context,
        "new_notes": notes.new_ids,
        "evidence_ids": evidence.ids,
    }
```

这个骨架不是本仓库已有实现，但能先验证：

- 取证是否可追溯；
- 笔记是否可恢复；
- Builder 是否展示 note；
- 工具调用是否重复；
- 中断后能否继续。

## 对照实验

### 实验 A：无笔记 vs 有笔记

固定同一任务和工具：

- 无笔记：每轮重新探索；
- 有笔记：第二轮读取已有 blocker。

记录：

- 重复探索次数；
- 工具调用数；
- 关键证据覆盖率；
- 恢复后遗漏；
- token/字符预算。

### 实验 B：同进程 vs 新进程

第一天创建笔记后：

1. 同进程继续；
2. 重启进程；
3. 从同一 workspace 恢复；
4. 对比任务状态与下一步是否一致。

### 实验 C：Builder 是否真正注入 note

创建 blocker 笔记，转成 `ContextPacket`，检查最终上下文是否包含。若没有，优先修 Structure 分类或返回类型解析，不要先换模型。

## 安全与治理要求

- TerminalTool 默认只读，解释器执行需审批；
- NoteTool 保存来源与版本；
- ContextBuilder 记录候选、选中和注入；
- 删除或归档笔记不能破坏任务历史；
- 所有报告保留失败与超时；
- 不把 API Key 写进笔记或日志。

## 当前实现状态

| 组件 | 状态 |
|---|---|
| MemoryTool / NoteTool / TerminalTool | 本仓库未实现 |
| ContextBuilder / GSSC | 教学骨架 |
| FunctionCallAgent 工具循环 | 本仓库未实现 |
| InsightMem 证据检索 | 可运行 |
| email-agent 记忆注入归因 | 可运行 |
| 维护助手报告 | 教学骨架 |

## 本章小结与下一步

你已经看到长程助手的核心不是“更多工具”，而是工具之间的状态闭环：

```text
Terminal 取证
  → Note 持久化
  → Builder 回注
  → Agent 决策
  → 新证据更新 Note
```

上游示例同时暴露了 API 漂移、统计错误、路径硬编码和“演示不等于事实”的问题。

下一章 [06 总结、练习与实现缺口](06-review.md) 会给出阶段二验收清单，以及把这些骨架变成真实项目前必须补齐的工程能力。
