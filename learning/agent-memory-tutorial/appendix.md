# 附录

> 配套：[八周路线](README.md) · [精读清单](reading-list.md)

---

## A. 结业自测

1. 短期记忆和长期记忆的边界是什么？checkpoint 属于哪一类？
2. 为什么 compaction 不算 agent memory？
3. episode 和 fact 的区别？谁负责溯源？
4. 双时间（`valid_from` / `valid_to` / `ingested_at`）解决什么问题？
5. RRF 为什么用 rank 而不是 score？什么情况下会失效？
6. 查询期过滤和索引期删除，各有什么风险？
7. 全量原文和抽取事实，各自最适合什么任务？
8. 如何评测“抗噪”？需要固定哪些变量？
9. 为什么 top_k 不是越大越好？
10. 设计一个跨用户隔离的存储 schema，最少需要哪些字段？
11. 写入幂等键怎么设计？payload 变了怎么办？
12. 什么时候应该选择图存储，而不是向量 + 词法？
13. 给邮件 Agent 各写一条 semantic、episodic、procedural memory。
14. LangGraph Store 的 namespace 与 thread_id 有什么区别？
15. core / recall / archival memory 分别对应哪些工程组件？
16. memory pressure 触发时，摘要、page-out、page-in 的顺序应如何安排？
17. Agent 自编辑 core memory 时，最少要记录哪些审计字段？
18. 多 Agent 共享 memory block 时，如何防止跨租户泄漏？

参考答案散落在 [00](00-orientation.md)、[01](01-boundaries.md)、[02](02-writing.md)、[03](03-storage.md)、[04](04-retrieval.md)、[05](05-fusion.md)、[06](06-governance.md)、[08 Capstone](08-capstone.md) 和 [评测手册](evaluation.md)。

---

## B. 用 InsightMem 做实验

### B.1 跑通服务

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src uvicorn insightmem.api:app --host 127.0.0.1 --port 8000 --workers 1
```

写入和查询示例见仓库根目录 `README.md` 的 Quick start。

### B.2 实验 L3 的框架

1. 准备 30 个查询，标注 gold chunk（或 gold message）；
2. 跑三组：全开、关 dense、关 view BM25；
3. 记录 Recall@5、MRR、top-10 命中；
4. 对每个失败查询标注类型：精确标识符、改写、多跳、时间；
5. 写一页结论：哪条腿在哪个类型上不可替代。

### B.3 实验 L4 的框架

1. 写入 3 段相关会话；
2. 查询并记录结果；
3. 再写入 5 段无关会话（不同项目、不同语言）；
4. 重跑同一查询，比较结果和分数；
5. 计算噪声差值，并记录被挤掉的证据。

### B.4 实验 L8 的框架

1. 定义 core / recall / archival 三个存储 Adapter；
2. 构造 20 组上下文压力场景；
3. 对比无 paging、固定 paging、自适应 paging；
4. 记录每次 page-in/page-out 的原因与 token 变化；
5. 验证自编辑回滚、后台整理 CAS 和共享 block 隔离；
6. 报告准确率、回滚成功率、泄漏数与完整成本。

---

## C. VS Code Notebook 实验环境

章节、Notebook、源码模块和覆盖状态的唯一对照见 [教程与 Notebook 对照](README.md#notebook-map)。本节只说明如何运行，不重复维护映射列表。

Notebook 适合做 baseline、单机制对照、参数扫描、失败分析和实验报告；正式 API、后台任务和自动回归测试仍应放在 `.py` 与 `tests/` 中。每次 Notebook 运行都应保存 manifest 和原始结果，而不是只看单元格输出。

### C.1 安装 VS Code 扩展

用 VS Code 打开仓库根目录 `D:\zungen\agent\InsightMem`。打开 `.vscode/extensions.json` 后 VS Code 会提示安装推荐扩展，也可以手动安装：

- Python：`ms-python.python`
- Jupyter：`ms-toolsai.jupyter`

### C.2 创建环境并安装阶段一依赖

阶段一项目是 [email-agent](../../experiments/email-agent/README.md)。PowerShell：

```powershell
cd D:\zungen\agent\InsightMem
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".\experiments\email-agent[notebooks]"
```

Git Bash：

```bash
cd /d/zungen/agent/InsightMem
python -m venv .venv
source .venv/Scripts/activate
python -m pip install --upgrade pip
python -m pip install -e "experiments/email-agent[notebooks]"
```

如果 PowerShell 阻止激活脚本：

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
```

阶段一 Notebook 默认使用离线 `LocalStore` 和确定性策略，不需要 API Key 或模型下载。

### C.3 选择解释器与 Kernel

1. 按 `Ctrl+Shift+P`，执行 `Python: Select Interpreter`；
2. 选择 `.\.venv\Scripts\python.exe`；
3. 打开一个 `.ipynb` 文件；
4. 点击右上角 `Select Kernel`，选择 `Python Environments` 下的 `.venv`。

在 Notebook 中运行下面的单元格，确认 kernel 和解释器一致：

```python
import sys
print(sys.executable)
```

输出路径应包含仓库根目录下的 `.venv`。修改解释器或安装包后，执行 `Restart Kernel`，不要继续使用旧 kernel 的模块缓存。

### C.4 运行阶段一 Notebook

建议按里程碑顺序执行：

| 顺序 | Notebook | 里程碑 |
|---|---|---|
| 1 | [01-baseline.ipynb](../../experiments/email-agent/notebooks/01-baseline.ipynb) | M0：确认无记忆时的失败 |
| 2 | [02-semantic-memory.ipynb](../../experiments/email-agent/notebooks/02-semantic-memory.ipynb) | M1：用户事实与偏好 |
| 3 | [03-episodic-and-procedural.ipynb](../../experiments/email-agent/notebooks/03-episodic-and-procedural.ipynb) | M2/M3：示例与规则 |
| 4 | [04-evaluation.ipynb](../../experiments/email-agent/notebooks/04-evaluation.ipynb) | M4：配置对照与归因 |

`Shift+Enter` 运行当前单元格，`Run All` 运行全部单元格。每个 Notebook 都会在 `experiments/email-agent/runs/<run_id>/` 下写入 `manifest.json` 和结果 JSON；`runs/` 已被 Git 忽略。

### C.5 常见错误

| 现象 | 处理 |
|---|---|
| `ModuleNotFoundError: email_memory_lab` | 解释器选错或 editable 安装未完成；重新选择 `.venv` 后 `Restart Kernel` |
| 右上角没有可用 kernel | 确认已安装 `ipykernel`，再执行 `Developer: Reload Window` |
| PowerShell 无法激活环境 | 使用 `Set-ExecutionPolicy -Scope Process Bypass`，或直接用 `.\.venv\Scripts\python.exe -m ...` |
| 改了代码但 Notebook 仍用旧逻辑 | `Restart Kernel`，再 `Run All` |
| 输出目录或数据路径找不到 | 从仓库根目录或项目目录启动 Notebook；项目通过 `find_project_root()` 定位实验根目录 |

Notebook 中不要把 API Key 写进代码或输出，也不要把 `runs/`、`.ipynb_checkpoints/` 和 `__pycache__/` 提交到 Git。

### C.6 运行 InsightMem Quickstart

[InsightMem 实验项目](../../experiments/insightmem/README.md)还需要安装仓库根包及其 API 依赖：

```bash
python -m pip install -r requirements-api.txt -c constraints-api.txt
python -m pip install -e . --no-deps
python -m pip install -e "experiments/insightmem[notebooks]"
```

然后打开 [00-quickstart.ipynb](../../experiments/insightmem/notebooks/00-quickstart.ipynb)。它和阶段一项目使用同一个 VS Code interpreter，但运行产物写入 `experiments/insightmem/runs/`，不要与邮件 Agent 的数据库混用。

---

## D. 参考资料

所有论文、文档、榜单和社区资源集中在 [精读清单](reading-list.md) 与 [社区资源](community.md)，本附录不重复维护列表。

核心入口：

- [Anthropic: The components of agent memory](https://www.anthropic.com/research/components-of-agent-memory)
- [LangGraph Memory overview](https://docs.langchain.com/oss/python/langgraph/memory)
- [AML Add/Search 指南](https://agentmemories.ai/api-guide)
- [Awesome-AI-Memory](https://github.com/IAAR-Shanghai/Awesome-AI-Memory)