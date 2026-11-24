---
name: lint-wiki
description: Validate Wiki frontmatter, wikilinks, local source links, generated index and backlinks. Use after any Wiki ingest, rename or delete.
---

# Wiki link lint

The canonical validator is `scripts/wiki.py`.

1. Run `python scripts/wiki.py --check`.
2. The checker reads every `wiki/*.md` page and validates required frontmatter, slug tags, duplicate page stems, `[[wikilinks]]`, local Markdown links and frontmatter source paths.
3. It also compares `index.md` and every generated backlink block with the expected output. Stale generated content fails the check.
4. If content changed, run `python scripts/wiki.py` to rebuild, then run `--check` again.
5. Report broken links first. Only claim a pass after `--check` exits successfully in the current session.

Do not hand-edit content between `generated:index` or `generated:backlinks` markers.
