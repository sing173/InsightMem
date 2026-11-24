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

参考答案散落在 [00](00-orientation.md)、[04](04-retrieval.md)、[05](05-fusion.md)、[06](06-governance.md) 和 [评测手册](evaluation.md)。

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

---

## C. 参考资料

所有论文、文档、榜单和社区资源集中在 [精读清单](reading-list.md) 与 [社区资源](community.md)，本附录不重复维护列表。

核心入口：

- [Anthropic: The components of agent memory](https://www.anthropic.com/research/components-of-agent-memory)
- [LangGraph Memory overview](https://docs.langchain.com/oss/python/langgraph/memory)
- [AML Add/Search 指南](https://agentmemories.ai/api-guide)
- [Awesome-AI-Memory](https://github.com/IAAR-Shanghai/Awesome-AI-Memory)