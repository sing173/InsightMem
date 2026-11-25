# Stage 1：带长期记忆的邮件 Agent

这是教程阶段一的 VS Code Notebook 实验项目，对应课程 [Long-Term Agentic Memory With LangGraph](https://www.deeplearning.ai/short-courses/long-term-agentic-memory-with-langgraph/) 的工程顺序：

```text
M0 baseline → M1 semantic → M2 episodic → M3 procedural → M4 evaluation
```

项目默认使用离线 `LocalStore` 和确定性策略，不需要 API Key、模型下载或 LangGraph 安装。记忆接口保持 `put/get/search`、namespace 和 key 的形态，后续可以把后端替换成真实 LangGraph Store，把模板回复替换成 LLM。

## 结构

```text
experiments/email-agent/
├── pyproject.toml
├── notebooks/
│   ├── 01-baseline.ipynb
│   ├── 02-semantic-memory.ipynb
│   ├── 03-episodic-and-procedural.ipynb
│   └── 04-evaluation.ipynb
├── src/email_memory_lab/
│   ├── agent.py
│   ├── evaluation.py
│   ├── memory.py
│   ├── models.py
│   ├── runner.py
│   └── store.py
├── tests/test_email_memory.py
├── data/
│   ├── emails.json
│   └── memories.json
└── runs/
```

## 安装与打开

在仓库根目录执行：

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e "experiments/email-agent[notebooks]"
```

Windows PowerShell 的激活命令是 `.venv\Scripts\Activate.ps1`。

用 VS Code 打开仓库根目录，然后：

1. `Python: Select Interpreter` 选择 `.venv`；
2. 打开 `notebooks/01-baseline.ipynb`；
3. 选择 Python kernel；
4. 执行 `Restart Kernel and Run All Cells`。

根目录 `.vscode/settings.json` 已加入本项目 `src` 路径；`runs/`、Notebook checkpoint 和缓存不会进入 Git。

## Notebook 顺序

| Notebook | 里程碑 | 要观察什么 |
|---|---|---|
| [01-baseline](notebooks/01-baseline.ipynb) | M0 | 没有记忆时，哪些路由和写作任务失败 |
| [02-semantic-memory](notebooks/02-semantic-memory.ipynb) | M1 | 用户事实和偏好是否改善回复 |
| [03-episodic-and-procedural](notebooks/03-episodic-and-procedural.ipynb) | M2/M3 | few-shot 示例能否修正路由，程序性规则能否改变行为 |
| [04-evaluation](notebooks/04-evaluation.ipynb) | M4 | 四组配置的 routing、writing、memory recall 对照 |

每个 Notebook 都使用同一个 `data/emails.json`，并把原始结果保存到独立 `runs/<run_id>/`。

## 当前基线

- 10 封标注邮件；
- baseline：routing 8/10，writing compliance 0/4，required-memory recall 0/6；
- semantic：补齐签名偏好，writing compliance 4/4；
- episodic：从历史示例修正 vendor pricing 路由；
- procedural：从反馈规则修正 event invite 路由；
- full memory：routing 10/10、writing 4/4、required-memory recall 6/6。

这些数字只用于验证离线机制，不代表真实 LLM Agent 性能。

## 代码与课程边界

当前项目验证的是记忆的**工程行为**：

- namespace、key、语义/情景/程序记忆的写入与读取；
- 记忆如何改变选择与生成上下文；
- 用户隔离、运行产物与评测归因。

它尚未接入：

- LangGraph `StateGraph`、checkpointer 与官方 `Store`；
- LLM 结构化 triage、工具调用与真实邮件发送；
- 后台 consolidation、冲突与删除治理。

这些是后续 M1–M4 的替换和扩展点，不应把当前离线结果当成真实模型收益。

## 测试

```bash
PYTHONPATH='experiments/email-agent/src' python -m unittest discover -s experiments/email-agent/tests -v
```

测试覆盖 baseline 失败、三类记忆效果、用户隔离、完整配置评测和运行产物保存。

## 与教程对应

新教程入口：[Agent Memory 实战教程](../../learning/agent-memory-course/README.md)。

- [00 快速开始](../../learning/agent-memory-course/stage1-memory-and-retrieval/00-quick-start.md)：运行 baseline 并理解记忆与 RAG 的区别；
- [01 记忆系统的工作流程](../../learning/agent-memory-course/stage1-memory-and-retrieval/01-memory-workflow.md)：写入、检索、注入与使用；
- [02 MemoryTool 与记忆操作](../../learning/agent-memory-course/stage1-memory-and-retrieval/02-memory-tool.md)：add/search/update/forget/consolidate；
- [03 MemoryManager 与四种记忆](../../learning/agent-memory-course/stage1-memory-and-retrieval/03-memory-manager-and-types.md)：类型、重要性与遗忘；
- [07 总结、练习与实现缺口](../../learning/agent-memory-course/stage1-memory-and-retrieval/07-review.md)：阶段一验收与扩展方向。