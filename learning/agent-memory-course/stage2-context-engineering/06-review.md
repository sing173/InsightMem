# 06 总结、练习与实现缺口

> 上一章：[05 项目：长程代码库维护助手](05-codebase-maintainer.md) · 返回：[教程入口](../README.md)
> 对应 Hello Agents 第 9 章的 9.7：本章总结与习题。

## 阶段二你已经完成什么

你现在应该能把上下文工程看成一个可检查的流水线：

```text
候选信息
  → Gather
  → Select
  → Structure
  → Compress
  → Agent / Reader
```

同时应该知道长程任务需要三类外部状态：

```text
笔记：任务进度与 blocker
终端：即时证据
检索/记忆：可复用知识与经验
```

## 核心概念清单

| 概念 | 一句话解释 | 当前状态 |
|---|---|---|
| Context engineering | 主动设计信息收集、选择、组织、压缩和注入 | 概念讲解 |
| ContextPacket | 带来源、时间、成本和初始相关分的候选包 | 教学骨架 |
| ContextConfig | 预算、预留、阈值与策略配置 | V0.2.8 快照 |
| Gather | 从指令、记忆、RAG、历史、额外包收集候选 | 教学骨架 |
| Select | 按相关性、新近性和预算选择 | 教学骨架 |
| Structure | 按固定分区组织上下文 | 教学骨架 |
| Compress | 超预算时压缩或截断 | 教学骨架 |
| NoteTool | 用 Markdown 保存任务状态、blocker、action | 未实现 |
| TerminalTool | 按需探索文件系统 | 未实现 |
| 长程维护助手 | 组合工具形成跨天工作流 | 综合设计 |

## 必须记住的版本边界

本阶段绑定 Hello Agents **V0.2.8**，因为第 9 章示例要求 `hello-agents[all]==0.2.8`。

但文档、示例和实现存在漂移：

- `ContextPacket` 字段顺序不同；
- `ContextConfig` 默认值和字段不同；
- `custom_packets` 实际是 `additional_packets`；
- NoteTool 返回字符串，不是字典；
- V0.2.8 的 `invoke()` 返回字符串，示例却访问 `.content`；
- V1.0.0 删除 NoteTool、TerminalTool、FunctionCallAgent，并改变 LLM 返回类型；
- 当前 `main` 的 ContextBuilder 已重构，MMR 和消息角色边界与 V0.2.8 不同。

不要混用版本。运行上游示例时，以固定版本源码和测试为准。

## 练习

### 练习 1：预算诊断

构造 8 个 ContextPacket，逐步降低 `max_tokens`，记录：

- 第一个被过滤的包；
- 第一个被截断的分区；
- 最终估算 token；
- 丢失的关键证据。

### 练习 2：GSSC 确定性

固定 timestamp，创建：

- 高相关旧包；
- 低相关新包；
- 系统包；
- note 包。

运行 Select 和 Structure，解释排序，并检查 note 是否显示。

### 练习 3：NoteTool 生命周期

创建 task_state、blocker、action：

1. 更新 blocker 为 resolved；
2. 人工编辑正文；
3. 新进程恢复；
4. 检查索引一致性；
5. 并发创建 20 条，检查 ID 碰撞。

### 练习 4：TerminalTool 安全审计

在临时 workspace 测试：

- 绝对路径；
- `..`；
- shell 分隔符；
- 管道到解释器；
- 符号链接；
- 超时子进程；
- 超大输出。

记录拒绝结果，不把 cwd 当沙箱。

### 练习 5：跨进程恢复

第一天创建笔记，重启进程，再执行：

- 读取 blocker；
- 生成下一步计划；
- 对比恢复前后状态；
- 检查证据来源是否仍可追溯。

### 练习 6：固定工具维护工作流

不用 LLM，用确定性脚本完成一次：

```text
探索 → 取证 → 记录笔记 → 构建上下文 → 输出报告
```

统计工具调用、重复探索、笔记新增和预算使用。

## 实现路线

如果要把骨架变成真实项目，建议按以下顺序：

1. **ContextPacket 适配器**：把 InsightMem hits 转成带 source ID 的包；
2. **确定性 GSSC**：先实现 Gather/Select/Structure，不接 LLM；
3. **预算诊断**：记录候选、选中、注入和截断；
4. **NoteTool**：Markdown + YAML、版本、状态、路径安全；
5. **安全 TerminalTool**：只读、argv、realpath、环境隔离、审批与审计；
6. **工具循环**：Agent 自主调用工具，设置最大迭代与停止条件；
7. **评测**：任务连续性、证据覆盖、恢复成功率、安全拒绝率与完整成本。

## 验收清单

- 无 LLM 也能运行确定性测试；
- 每条结论能追溯到文件或检索 hit；
- token/字符预算可诊断；
- 笔记人类可读且可机器解析；
- Terminal 攻击用例有明确拒绝结果；
- 新进程能从同一 workspace 恢复；
- 文档明确区分“已实现、骨架、未实现”；
- 所有展示数字来自实际运行，而不是案例叙述。

## 当前仓库能力边界

| 能力 | 状态 |
|---|---|
| InsightMem Add/Search、混合召回、证据选择 | 可运行 |
| email-agent 三类记忆与注入归因 | 可运行 |
| ContextBuilder / GSSC | 教学骨架 |
| NoteTool / TerminalTool | 未实现 |
| FunctionCallAgent / 工具循环 | 未实现 |
| memory OS / 长程维护助手 | 综合设计 |

## 来源与延伸阅读

- [Hello Agents 第九章：上下文工程](https://github.com/datawhalechina/hello-agents/blob/main/docs/chapter9/%E7%AC%AC%E4%B9%9D%E7%AB%A0%20%E4%B8%8A%E4%B8%8B%E6%96%87%E5%B7%A5%E7%A8%8B.md)
- [第九章示例目录](https://github.com/datawhalechina/hello-agents/tree/main/code/chapter9)
- [HelloAgents V0.2.8 ContextBuilder](https://github.com/jjyaoao/helloagents/blob/V0.2.8/hello_agents/context/builder.py)
- [HelloAgents V0.2.8 NoteTool](https://github.com/jjyaoao/helloagents/blob/V0.2.8/hello_agents/tools/builtin/note_tool.py)
- [HelloAgents V0.2.8 TerminalTool](https://github.com/jjyaoao/helloagents/blob/V0.2.8/hello_agents/tools/builtin/terminal_tool.py)
- [InsightMem 机制审计](../../../wiki/insightmem.md)
- [旧版备份：上下文与治理相关章节](../../agent-memory-tutorial/05-fusion.md)

## 最终总结

阶段一解决“信息从哪里来、怎样检索”，阶段二解决“这次调用带什么、怎样组织、怎样跨请求保持”。

两者组合起来才是完整的 Agent Memory 工程：

```text
记忆/检索提供候选
  → 上下文构建器选择与组织
  → 工具执行并产生新证据
  → 笔记保存任务状态
  → 下一轮继续
```

不要把高 Recall 当成最终答案质量，也不要把 TerminalTool 的白名单当成安全保证。每一个环节都需要可观测、可测试、可恢复。
