# Agent Memory 实验项目

这里用独立文件夹管理 Agent Memory 实验。现有 InsightMem API、源码、测试和学习文档保持原路径不变；`experiments/insightmem` 是它的 Notebook 实验项目。

## 当前项目

- [InsightMem](insightmem/README.md)：Add/Search、三路召回、噪声、去重、选择与评测实验。
- [email-agent](email-agent/README.md)：阶段一邮件 Agent，覆盖 baseline、语义/情景/程序记忆和评测。
- [hello-agents-v0.2.8](hello-agents-v0.2.8/EXPERIMENT.md)：Hello Agents V0.2.8 源码快照，用于 MemoryTool、ContextBuilder、NoteTool、TerminalTool 和教程 API 核对。

## 目录约定

每个实验项目使用相同结构：

```text
experiments/<project-name>/
├── pyproject.toml          # 项目自己的可选 Notebook 依赖
├── README.md               # 项目目标、运行方式与边界
├── notebooks/              # 薄 Notebook：设置、调用、展示、保存
├── src/<package_name>/     # 可复用的实验逻辑
├── tests/                  # unittest/pytest 自动测试
├── data/                   # 小样本、标注与固定输入
└── runs/                   # 每次运行的数据库、manifest 和结果；不入 Git
```

规则：

1. 一个实验项目一个文件夹，项目之间不共享可变数据库；
2. 稳定逻辑放 `src/`，Notebook 不复制核心实现；
3. 自动测试放 `tests/`，Notebook 用于探索、Demo 和报告；
4. 每次运行使用独立 `runs/<run_id>/`，保存配置、代码版本和原始结果；
5. API Key 放环境变量，不写进 Notebook 或运行产物；
6. 新项目加入后，在根目录 `.vscode/settings.json` 的 `python.analysis.extraPaths` 中添加它的 `src` 路径。

## 新增项目

以 `<project-name>` 和 `<package_name>` 为例：

```bash
mkdir -p "experiments/<project-name>/notebooks" \
         "experiments/<project-name>/src/<package_name>" \
         "experiments/<project-name>/tests" \
         "experiments/<project-name>/data" \
         "experiments/<project-name>/runs"
```

然后复制 InsightMem 项目的以下文件作为起点，并按新项目修改：

- `pyproject.toml`
- `README.md`
- `src/<package_name>/__init__.py`
- `tests/test_lab.py`
- `notebooks/00-quickstart.ipynb`

不同项目应替换包名、实验接口和样本数据，不复用 InsightMem 的数据库或运行目录。

## VS Code Notebook

1. 在仓库根目录安装项目依赖；
2. 安装实验项目的 Notebook extra；
3. 用 `Python: Select Interpreter` 选择同一个虚拟环境；
4. 打开 `experiments/<project-name>/notebooks/00-quickstart.ipynb`；
5. 选择 Python 内核，按 `Restart Kernel and Run All Cells` 验证。

根目录 `.vscode/extensions.json` 已推荐 Python 与 Jupyter 扩展；`.vscode/settings.json` 已配置源码路径和运行产物监听排除。

## 与教程的关系

实验步骤见 [Agent Memory 实战教程](../learning/agent-memory-course/README.md)；旧版 [L0–L8 实验手册](../learning/agent-memory-tutorial/labs.md) 保留为备份参考。Notebook 是实验载体，不改变验收要求：每个实验仍需 baseline、单变量变化、失败案例、成本数字和可复现产物。
