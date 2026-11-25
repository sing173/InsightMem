# InsightMem Notebook 实验项目

目标：在不启动 HTTP 服务的前提下，直接调用 `CodingMemoryService`，用 Notebook 完成 Add/Search、隔离、噪声、去重和评测实验。

现有生产实现仍在仓库根目录 `src/insightmem/`。本项目只提供实验适配层，不复制或修改检索算法。

## 结构

```text
experiments/insightmem/
├── pyproject.toml
├── notebooks/
│   └── 00-quickstart.ipynb
├── src/insightmem_lab/
│   ├── __init__.py
│   ├── demo.py
│   ├── paths.py
│   └── runner.py
├── tests/
│   └── test_lab.py
├── data/
│   └── sample_messages.json
└── runs/
```

## 安装

在仓库根目录执行。Windows PowerShell 使用 `.venv\Scripts\Activate.ps1`，Git Bash 使用 `source .venv/bin/activate`。

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-api.txt -c constraints-api.txt
python -m pip install -e . --no-deps
python -m pip install -e "experiments/insightmem[notebooks]"
```

先安装根项目，再安装实验项目，因为 `insightmem_lab` 依赖根包 `insightmem`。

## 运行 Quickstart

1. 用 VS Code 打开仓库；
2. 选择 `.venv` 解释器；
3. 打开 [00-quickstart.ipynb](notebooks/00-quickstart.ipynb)；
4. 选择 Python 内核并运行全部单元格。

Quickstart 使用确定性的 `HashEmbedder`，不需要 API Key、网络或模型下载。它演示：

- 创建独立运行目录和 manifest；
- 写入样本消息并验证幂等重放；
- 执行 Search 并保存原始结果；
- 用双用户哨兵检查隔离；
- 保存统计信息。

## 实验接口

Notebook 只需要使用 `start_experiment` 返回的薄接口：

```python
from insightmem_lab import HashEmbedder, start_experiment

run = start_experiment("experiments/insightmem", "my-experiment", embedder=HashEmbedder())
stored_chunks = run.add("request-1", "user-a", "session-1", messages)
hits = run.search("user-a", "parser failure", top_k=5)
run.save("results.json", {"stored_chunks": stored_chunks, "hits": hits})
```

`start_experiment` 会：

- 在 `runs/<run_id>/` 创建独立 SQLite 数据库；
- 保存 `manifest.json`，记录代码 commit、Python、平台、配置和 embedding identity；
- 使用绝对项目路径，避免 Notebook 工作目录变化导致数据写错位置。

要换 embedding 或检索配置时，新建一次实验运行即可；不要把不同 fingerprint 的数据混进同一个数据库。

## 教程入口

新教程中的 RAG 路径：

- [04 RAG 系统与最小知识库](../../learning/agent-memory-course/stage1-memory-and-retrieval/04-rag-system.md)；
- [05 高级检索与本仓库实现](../../learning/agent-memory-course/stage1-memory-and-retrieval/05-advanced-retrieval.md)；
- [06 项目：智能文档问答助手](../../learning/agent-memory-course/stage1-memory-and-retrieval/06-document-qa-assistant.md)。

## 测试

在仓库根目录执行：

```bash
PYTHONPATH='src;experiments/insightmem/src' python -m unittest discover -s experiments/insightmem/tests -v
```

测试覆盖运行产物、Add/Search、幂等重放、用户隔离和输出路径限制。

## 可开展的实验

- L1/L2：表示、词法与 dense 检索对照；
- L3：三路召回消融；
- L4：同用户相关/噪声配对实验；
- L5：重复、部分重叠、bundle 与 span 选择；
- L7：读取运行产物，计算指标、配对统计和成本。

边界：当前公开 Add/Search 没有逐腿开关或 dedup 开关。L3/L5 应使用实验分支或对同一快照调用内部函数，不能写成“关闭某个不存在的配置”。L6 的双时间、冲突、删除治理和 L8 的 paging、自编辑、dreaming 属于新增能力，不是当前 InsightMem 已实现功能。

## 运行产物

每次运行目录包含：

```text
runs/<run_id>/
├── manifest.json
├── memory.sqlite3
└── *.json
```

`runs/` 和 Notebook checkpoint 已加入 `.gitignore`。提交前清空 Notebook 输出，避免把记忆内容、API Key 或本地路径带入 Git。
