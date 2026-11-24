#!/usr/bin/env python3
"""Build and validate the local Markdown wiki."""
from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WIKI = ROOT / "wiki"
INDEX = ROOT / "index.md"
REQUIRED = {"title", "summary", "status", "section", "order", "updated", "tags", "sources"}
STATUSES = {"verified", "source-reviewed", "conceptual", "maintained"}
INDEX_START = "<!-- generated:index:start -->"
INDEX_END = "<!-- generated:index:end -->"
BACKLINK_START = "<!-- generated:backlinks:start -->"
BACKLINK_END = "<!-- generated:backlinks:end -->"


@dataclass
class Page:
    path: Path
    text: str
    meta: dict
    body: str
    links: list[str]


def scalar(value: str):
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        return [item.strip().strip("'\"") for item in value[1:-1].split(",") if item.strip()]
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
        return value[1:-1]
    if value.isdigit():
        return int(value)
    return value


def parse_page(path: Path) -> Page:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise ValueError(f"{path.relative_to(ROOT)}: missing frontmatter")
    try:
        end = lines.index("---", 1)
    except ValueError as error:
        raise ValueError(f"{path.relative_to(ROOT)}: unclosed frontmatter") from error
    meta: dict = {}
    current = None
    for number, line in enumerate(lines[1:end], 2):
        if line.startswith("  - "):
            if current is None:
                raise ValueError(f"{path.relative_to(ROOT)}:{number}: list item without key")
            meta.setdefault(current, []).append(line[4:].strip())
            continue
        if line.startswith(" ") or ":" not in line:
            raise ValueError(f"{path.relative_to(ROOT)}:{number}: malformed frontmatter")
        key, value = line.split(":", 1)
        current = key.strip()
        if value.strip():
            meta[current] = scalar(value)
        else:
            meta[current] = []
    missing = REQUIRED - meta.keys()
    if missing:
        raise ValueError(f"{path.relative_to(ROOT)}: missing {', '.join(sorted(missing))}")
    if meta["status"] not in STATUSES:
        raise ValueError(f"{path.relative_to(ROOT)}: invalid status {meta['status']}")
    if not isinstance(meta["order"], int):
        raise ValueError(f"{path.relative_to(ROOT)}: order must be an integer")
    for key in ("tags", "sources"):
        if not isinstance(meta[key], list) or not meta[key]:
            raise ValueError(f"{path.relative_to(ROOT)}: {key} must be a nonempty list")
    for tag in meta["tags"]:
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", tag):
            raise ValueError(f"{path.relative_to(ROOT)}: invalid tag {tag}")
    body = "\n".join(lines[end + 1:]).strip() + "\n"
    clean = without_generated(body)
    clean = re.sub(r"```.*?```", "", clean, flags=re.S)
    clean = re.sub(r"`[^`\n]*`", "", clean)
    links = re.findall(r"\[\[([^\]\n]+)\]\]", clean)
    return Page(path, text, meta, body, links)


def target_name(raw: str) -> str:
    target = raw.split("|", 1)[0].rstrip("\\").strip()
    target = target.split("#", 1)[0]
    if target.endswith(".md"):
        target = target[:-3]
    return target


def without_generated(text: str) -> str:
    text = re.sub(re.escape(BACKLINK_START) + r".*?" + re.escape(BACKLINK_END), "", text, flags=re.S)
    return re.sub(re.escape(INDEX_START) + r".*?" + re.escape(INDEX_END), "", text, flags=re.S)


def replace_block(text: str, start: str, end: str, content: str) -> str:
    pattern = re.escape(start) + r".*?" + re.escape(end)
    replacement = start + "\n" + content.rstrip() + "\n" + end
    if re.search(pattern, text, flags=re.S):
        return re.sub(pattern, lambda _: replacement, text, flags=re.S)
    return text.rstrip() + "\n\n" + replacement + "\n"


def table_text(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def validate(pages: list[Page]) -> tuple[list[str], int]:
    errors: list[str] = []
    stems: dict[str, Path] = {}
    total_links = 0
    for page in pages:
        stem = page.path.stem
        if stem in stems:
            errors.append(f"duplicate page stem: {stem}")
        stems[stem] = page.path
    for page in pages:
        location = page.path.relative_to(ROOT)
        for raw in page.links:
            total_links += 1
            target = target_name(raw)
            if target not in stems:
                errors.append(f"{location}: broken wikilink [[{raw}]]")
        clean = without_generated(page.body)
        clean = re.sub(r"```.*?```", "", clean, flags=re.S)
        clean = re.sub(r"`[^`\n]*`", "", clean)
        for link in re.findall(r"\[[^\]]*\]\(([^)]+)\)", clean):
            if link.startswith(("http://", "https://", "mailto:", "#")):
                continue
            path = unquote_path(link.split("#", 1)[0])
            if path and not (page.path.parent / path).resolve().exists():
                errors.append(f"{location}: broken local link ({link})")
        for source in page.meta["sources"]:
            if not (ROOT / source).resolve().exists():
                errors.append(f"{location}: missing source {source}")
    return errors, total_links


def unquote_path(value: str) -> str:
    return value.replace("%20", " ")


def backlink_map(pages: list[Page]) -> dict[str, list[Page]]:
    result: dict[str, list[Page]] = defaultdict(list)
    for page in pages:
        for target in {target_name(raw) for raw in page.links}:
            if target != page.path.stem:
                result[target].append(page)
    return result


def render_backlinks(page: Page, links: list[Page]) -> str:
    if not links:
        return "## 反向链接\n\n暂无其他 Wiki 页面链接到此页。"
    rows = ["## 反向链接", ""]
    for source in sorted(links, key=lambda item: (item.meta["section"], item.meta["order"], item.path.stem)):
        rows.append(f"- [[{source.path.stem}|{source.meta['title']}]] — {source.meta['summary']}")
    return "\n".join(rows)


def render_index(pages: list[Page]) -> str:
    sections: dict[str, list[Page]] = defaultdict(list)
    for page in pages:
        sections[page.meta["section"]].append(page)
    lines = [
        "# Agent Memory Wiki",
        "",
        f"共 {len(pages)} 个页面。索引导航与状态从页面 frontmatter 生成。",
        "",
        "维护入口：[Wiki 维护约定](wiki/schema.md) · [演进日志](log.md)",
        "",
    ]
    for section in sorted(sections, key=lambda name: min(page.meta["order"] for page in sections[name])):
        lines.extend([f"## {section}", "", "| 页面 | 摘要 | 状态 |", "|---|---|---|"])
        for page in sorted(sections[section], key=lambda item: (item.meta["order"], item.path.stem)):
            lines.append(
                f"| [{page.meta['title']}](wiki/{page.path.name}) | {table_text(page.meta['summary'])} | {page.meta['status']} |"
            )
        lines.append("")
    sources: dict[str, list[Page]] = defaultdict(list)
    for page in pages:
        for source in page.meta["sources"]:
            sources[source].append(page)
    lines.extend(["## 来源覆盖", "", "| 来源 | 引用页面 |", "|---|---|"])
    for source in sorted(sources):
        labels = "、".join(f"[{page.meta['title']}](wiki/{page.path.name})" for page in sorted(sources[source], key=lambda item: item.meta["order"]))
        lines.append(f"| `{source}` | {labels} |")
    lines.extend([
        "",
        "状态说明：`verified` 为代码或契约核对；`source-reviewed` 为资料综合；`conceptual` 为概念整理；`maintained` 为持续维护入口。",
        "",
    ])
    return INDEX_START + "\n" + "\n".join(lines).rstrip() + "\n" + INDEX_END + "\n"


def expected_outputs(pages: list[Page]) -> dict[Path, str]:
    links = backlink_map(pages)
    outputs = {INDEX: render_index(pages)}
    for page in pages:
        outputs[page.path] = replace_block(page.text, BACKLINK_START, BACKLINK_END, render_backlinks(page, links.get(page.path.stem, [])))
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="check generated files without writing")
    args = parser.parse_args()
    try:
        pages = [parse_page(path) for path in sorted(WIKI.glob("*.md"))]
        errors, total_links = validate(pages)
        outputs = expected_outputs(pages)
        stale = [str(path.relative_to(ROOT)) for path, content in outputs.items() if not path.exists() or path.read_text(encoding="utf-8") != content]
        if args.check:
            if errors or stale:
                for error in errors:
                    print(error, file=sys.stderr)
                for path in stale:
                    print(f"generated content stale: {path}", file=sys.stderr)
                return 1
            print(f"wiki pages: {len(pages)} | wikilinks: {total_links} | sources: {len({s for p in pages for s in p.meta['sources']})} | broken: 0")
            return 0
        if errors:
            for error in errors:
                print(error, file=sys.stderr)
            return 1
        for path, content in outputs.items():
            path.write_text(content, encoding="utf-8", newline="\n")
        print(f"built {len(pages)} pages | wikilinks: {total_links} | broken: 0")
        return 0
    except (OSError, ValueError) as error:
        print(error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
