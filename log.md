# Wiki 演进日志

## [2026-11-24] ingest | InsightMem 与 Agent Memory 机制梳理

- 依据附件 `docs/karpathy_llm_wiki.zh.md` 的 LLM Wiki 模式建立 `wiki/`。
- 综合本轮对话、现有教程、论文精读和核心代码，新增概念地图、InsightMem 机制、检索、治理、框架对比、MemGPT/Letta、MemOS/MemoryOS、混合检索、AML 定位和学习路线页面。
- 现有 `docs/`、`learning/` 与 `src/` 保持为详细来源，Wiki 页面负责导航和综合。
- 索引与反向链接由 `scripts/wiki.py` 从 frontmatter 和 wikilink 生成。

## [2026-11-24] check | Wiki lint

- 11 个页面、26 个 wikilink、33 个来源路径通过生成器校验。
- 索引、日志和页面的 93 个本地 Markdown 链接全部有效。
- 已修正生成器读取旧反向链接导致重复生长的问题。
