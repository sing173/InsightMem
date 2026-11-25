# 04 TerminalTool：安全的文件系统探索

> 上一章：[03 NoteTool：结构化任务笔记](03-note-tool.md) · 下一章：[05 项目：长程代码库维护助手](05-codebase-maintainer.md)
> 对应 Hello Agents 第 9 章的 9.5：TerminalTool 的设计、安全机制、探索模式与工具协同。

## 本章你会得到什么

- V0.2.8 TerminalTool 的准确白名单与执行方式；
- 一份“为什么不是可靠沙箱”的审计表；
- 正常文件探索模式；
- 一个更安全的工具设计骨架。

## 先看为什么需要 TerminalTool

预先索引所有文件成本高，而且文件会变化。TerminalTool 采用 JIT（Just-In-Time）探索：

```text
先看目录
  → 找到相关文件
  → 读取片段
  → 搜索关键词
  → 统计与过滤
```

它适合代码库、日志、CSV 等本地数据。但“给 Agent 终端权限”也意味着高风险，所以本章不是只讲怎么用，还要讲怎么审计。

## V0.2.8 构造参数

```python
TerminalTool(
    workspace=".",
    timeout=30,
    max_output_size=10 * 1024 * 1024,
    allow_cd=True,
)
```

维护助手使用 `timeout=60`。

## 实际白名单

V0.2.8 共 31 个命令：

```text
ls, dir, tree
cat, head, tail, less, more
find, grep, egrep, fgrep
wc, sort, uniq, cut, awk, sed
pwd, cd
file, stat, du, df
echo, which, whereis
python, node, bash, sh
```

重要事实：

- `git` 不在白名单；
- `tr` 不在白名单；
- `python/node/bash/sh` 可以执行任意代码，不是只读命令；
- 教程正文遗漏了最后四项，却宣称“只允许只读命令”。

## 实际执行方式

实现只做：

1. `shlex.split()`；
2. 检查第一个 token 是否在白名单；
3. 对 `cd` 用 `Path.relative_to(workspace)` 检查目标；
4. `subprocess.run(shell=True, cwd=current_dir, timeout=...)`；
5. 捕获 stdout/stderr；
6. 按字符长度截断输出；
7. 附带返回码。

这能阻止一部分明显命令，但不是可靠沙箱。

## 安全审计：为什么不够

| 攻击面 | 当前行为 | 风险 |
|---|---|---|
| 绝对路径 | 普通命令不检查路径 | 可读取 workspace 外文件 |
| `..` | 只有 `cd` 做相对路径检查 | 其他命令可逃逸 |
| shell 分隔符 | `shell=True` | 分号、替换、重定向可执行额外命令 |
| 管道 | 只检查首命令 | 可管道给解释器执行 |
| 解释器 | python/bash/sh 在白名单 | 任意代码执行 |
| 符号链接 | 未解析 realpath | 链接可指向外部 |
| 环境变量 | 完整环境传给子进程 | 可能泄露 API Key |
| 超时 | 不一定清理子进程树 | 后台进程可能继续运行 |
| 输出限制 | 先完整捕获再截断 | 不能防止内存耗尽 |
| 限制单位 | 字符而非字节 | 与配置描述不一致 |
| 审计与审批 | 无 | 难以追踪和拦截高风险操作 |

**核心思想：** `cwd` 是工作目录，不是安全边界；白名单是起点，不是沙箱。

## 正常探索模式

### 探索项目结构

```text
ls / tree
  → cd 到目标目录
  → head/cat 查看文件
```

### 分析数据文件

```text
head 看前几行
  → wc -l 统计行数
  → cut 选列
  → sort/uniq 统计分布
```

### 分析日志

```text
tail 看最新错误
  → grep 找关键词
  → awk/sort/uniq 聚合
```

### 探索代码

```text
统计行数
  → grep TODO/函数名
  → 定位文件
  → head/cat 查看片段
```

Hello Agents 示例数据存在漂移：实际 CSV 是 7 列、40 条记录，`category` 是第 3 列；README 提到的 `logs/app.log` 在上游目录中不存在。教程应使用固定 fixture，不把展示输出当实测。

## 安全审计实验

在临时 workspace 中创建无害文件，记录工具是否拒绝，而不是直接在生产环境测试。

| 用例 | 目的 | 预期安全行为 |
|---|---|---|
| 读取 workspace 内文件 | 正常路径 | 允许 |
| 读取 workspace 外绝对路径 | 路径逃逸 | 拒绝 |
| 使用 `..` 逃逸 | 路径逃逸 | 拒绝 |
| 分号连接第二条命令 | shell 注入 | 拒绝 |
| 管道到解释器 | 任意代码执行 | 拒绝或人工审批 |
| 符号链接指向外部 | realpath 逃逸 | 拒绝 |
| 子进程超时 | 资源清理 | 终止整个进程树 |
| 超大输出 | 内存保护 | 流式读取并限制字节 |

V0.2.8 的预期结果不是“全部拒绝”，而是暴露哪些策略缺失。修复后再跑同一组测试，记录拒绝原因。

## 更安全的设计骨架

### 1. 不使用 shell

```python
subprocess.run(argv, cwd=workspace, env=safe_env, timeout=timeout)
```

### 2. 解析并限制子命令

白名单不能只看第一个 token，还要限制：

- 参数；
- 路径；
- 重定向；
- 管道；
- 解释器执行。

### 3. 解析真实路径

```python
resolved = Path(path).resolve()
resolved.relative_to(workspace.resolve())
```

并检查符号链接和文件类型。

### 4. 隔离环境

只传递必要环境变量，不继承全部密钥。

### 5. 资源限制

- CPU；
- 内存；
- 进程数；
- 输出字节；
- 子进程树超时。

### 6. 审批与审计

高风险操作要求人工审批，并记录：

```text
actor
command
argv
resolved paths
cwd
exit code
stdout/stderr hash
timestamp
approval
```

## 与其他工具协同

```text
TerminalTool：即时取证
NoteTool：保存可复用结论
ContextBuilder：控制本轮注入
MemoryTool：保存偏好或高层状态
```

不要把全部终端输出复制进 Memory。应该：

1. Terminal 找到证据；
2. 提取关键片段与来源；
3. Note 记录结论；
4. Builder 只注入相关笔记；
5. 原始输出保留在日志或 artifact。

## 本仓库映射

当前仓库没有 TerminalTool。InsightMem 的源码、测试和运行产物可以作为固定探索对象，但教程不会声称已经给 Agent 终端权限。

如果后续实现，第一版应优先支持：

- 只读文件列表；
- 文本搜索；
- 受限读取；
- 明确审批；
- 完整审计。

不要一开始开放解释器或任意 shell。

## 本章小结与下一步

你已经知道：

- TerminalTool 的价值是按需探索；
- V0.2.8 白名单包含解释器，且 `shell=True` 带来明显绕过面；
- cwd 不是沙箱；
- 安全工具需要路径、参数、环境、资源和审计多层约束。

下一章 [05 项目：长程代码库维护助手](05-codebase-maintainer.md) 会把 Terminal、Note、ContextBuilder 和 Memory 组合成跨天工作流。
