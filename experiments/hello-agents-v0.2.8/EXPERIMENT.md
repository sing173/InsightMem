# Hello Agents V0.2.8 实验快照

本目录是 `jjyaoao/HelloAgents` 的 **V0.2.8** 源码快照，用于本仓库的阶段一/阶段二教程实验和 API 核对。

## 来源

- 上游仓库：https://github.com/jjyaoao/HelloAgents
- 标签：`V0.2.8`
- Commit：`707949e4f76927146acf142db607cbf6d22bce5f`
- 下载日期：2026-11-25
- 上游许可证：`CC-BY-NC-SA-4.0`，见 [LICENSE](LICENSE)

本快照不包含 `.git`。除本说明和 `.gitignore` 的本地实验忽略项外，上游源码未修改。根仓库的 MIT 许可证不覆盖本目录；使用、修改或再分发时需遵守上游 CC-BY-NC-SA-4.0 条款，尤其是非商业和相同方式共享要求。

## 用途

- 核对 MemoryTool、MemoryManager、RAGTool 的 V0.2.8 实现；
- 运行 ContextBuilder、NoteTool、TerminalTool 和第 8/9 章相关实验；
- 与本仓库 `experiments/email-agent`、`experiments/insightmem` 做机制对照；
- 作为教学参考，不作为生产服务或安全沙箱。

Datawhale 第 8/9 章的示例脚本位于另一个仓库 `datawhalechina/hello-agents`，本快照只包含框架源码。教程入口见 [Agent Memory 实战教程](../../learning/agent-memory-course/README.md)。

## 安装

在本目录创建独立环境：

```bash
cd experiments/hello-agents-v0.2.8
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

Windows PowerShell：

```powershell
cd experiments\hello-agents-v0.2.8
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

按需安装额外能力：

```bash
# 记忆 + RAG
python -m pip install -e ".[memory-rag]"

# 第 8 章 PDF 问答 Gradio 界面
python -m pip install -e ".[memory-rag]" "gradio>=4,<5"
```

`memory-rag` 会安装 Qdrant、Neo4j、Transformer、Torch、MarkItDown、pypdf 等较重依赖。只读源码或做 ContextBuilder 实验时，先安装基础包即可。

## 环境配置

复制上游模板：

```bash
cp .env.example .env
```

至少配置：

```dotenv
LLM_MODEL_ID=your-model-name
LLM_API_KEY=your-private-key
LLM_BASE_URL=your-base-url
```

记忆/RAG 还可能需要：

```dotenv
QDRANT_URL=...
QDRANT_API_KEY=...
NEO4J_URI=...
NEO4J_USERNAME=...
NEO4J_PASSWORD=...
EMBED_MODEL_TYPE=...
EMBED_MODEL_NAME=...
EMBED_API_KEY=...
EMBED_BASE_URL=...
```

不要把真实密钥写进 Notebook、笔记或提交到 Git。

## 版本核对

```python
import hello_agents
print(hello_agents.__file__)
```

并检查包元数据：

```bash
python -m pip show hello-agents
```

应显示版本 `0.2.8`，且路径指向本目录。教程中的 API 以 V0.2.8 为准；不要混用 V1 或当前 `main` 的返回类型和字段。

## 重要边界

- `ContextBuilder` 的文档、示例和 V0.2.8 实现存在字段与参数漂移；
- `NoteTool.run()` 返回字符串，不是字典；
- `TerminalTool` 使用 `shell=True`，白名单不是可靠沙箱；
- Memory/RAG 示例可能调用外部模型、Qdrant、Neo4j 或嵌入服务；
- 第 8/9 章展示数字不一定能在本机复现，应保存自己的 manifest 和原始产物。

运行 TerminalTool 实验时，只使用临时 workspace，不传入真实密钥，不开放生产文件系统。

## 本地产物

建议把实验输出放到：

```text
experiments/hello-agents-v0.2.8/runs/<run_id>/
```

`runs/`、`.venv*`、笔记目录、报告、数据库和缓存已加入忽略规则。提交前清空 Notebook 输出，并检查是否包含 API Key 或用户数据。
