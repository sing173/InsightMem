---
title: Wiki 维护约定
summary: 说明源文档、Wiki 页面、frontmatter、生成索引与反向链接的维护方式。
status: maintained
section: 维护
order: 0
updated: 2026-11-24
tags: [wiki, maintenance, schema]
sources:
  - docs/karpathy_llm_wiki.zh.md
  - scripts/wiki.py
---

# Wiki 维护约定

这个 Wiki 采用附件中的 LLM Wiki 模式：**原始资料保持不可变，Wiki 负责综合、导航和交叉引用，维护脚本负责生成容易漂移的视图。**

## 三层结构

| 层 | 位置 | 职责 |
|---|---|---|
| 原始来源 | `docs/`、`learning/`、`src/`、`configs/` | 保存论文精读、教程、代码与配置等详细证据 |
| Wiki | `wiki/*.md` | 用较短页面回答概念、机制、对比和学习问题，并链接回来源 |
| 维护规则 | 本页 + `scripts/wiki.py` | 约定元数据、摄入流程、索引和反向链接生成方式 |

Wiki 不替代现有文档。代码行为以源码为准，论文机制以精读页面为准，教程以学习路线为准。

## 页面 frontmatter

每个页面必须包含：

- `title`：页面标题。
- `summary`：一句话摘要，也是索引中的唯一摘要来源。
- `status`：`verified`、`source-reviewed`、`conceptual` 或 `maintained`。
- `section` 与 `order`：索引分组和排序。
- `updated`：最近核对日期。
- `tags`：小写连字符标签。
- `sources`：相对仓库根目录的来源路径。

修改事实时先修改 canonical page 或源文档，再重新生成导航；不要手工维护第二份状态表。

## 摄入与查询

1. **摄入**：阅读来源，更新对应 Wiki 页面，在 `log.md` 追加一条记录。
2. **查询**：先看 `index.md`，再进入相关页面和来源。
3. **综合**：新的比较、问答或结论形成独立页面，用 `[[wikilink]]` 接入现有知识网络。
4. **检查**：重新生成索引与反向链接，运行 `python scripts/wiki.py --check`。

## 生成内容

`index.md` 和每个页面末尾的“反向链接”由脚本生成。不要直接编辑标记之间的内容：

```text
<!-- generated:index:start -->
<!-- generated:index:end -->
<!-- generated:backlinks:start -->
## 反向链接

暂无其他 Wiki 页面链接到此页。
<!-- generated:backlinks:end -->
```

相关入口：[[agent-memory]] · [[insightmem]] · [[learning-path]]
