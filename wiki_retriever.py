"""Keyword retrieval of explicitly approved customer Q&A Wiki pages.

The Wiki is the source of truth. This module reads only reviewed, brand-scoped
pages and intentionally has no database or embedding dependency.
"""
from __future__ import annotations

import re
from pathlib import Path

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
QA_RE = re.compile(
    r"^\s*(?:###\s*)?Q:\s*(.+?)\s*\n\s*A:\s*(.+?)(?=\n\s*(?:###\s*)?Q:|\Z)",
    re.MULTILINE | re.DOTALL,
)
TOKEN_RE = re.compile(r"[0-9A-Za-z가-힣]{2,}")


def _frontmatter_value(frontmatter: str, key: str) -> str:
    match = re.search(rf"^{re.escape(key)}:\s*(.+?)\s*$", frontmatter, re.MULTILINE)
    return match.group(1).strip().strip("'\"") if match else ""


def _tokens(text: str) -> set[str]:
    return {token.lower() for token in TOKEN_RE.findall(text)}


def _approved_customer_page(path: Path, brand: str) -> str | None:
    if "raw" in path.parts:
        return None
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        return None
    frontmatter = match.group(1)
    if _frontmatter_value(frontmatter, "qna_export").lower() != "true":
        return None
    if _frontmatter_value(frontmatter, "brand").lower() != brand.lower():
        return None
    if _frontmatter_value(frontmatter, "status").lower() != "approved":
        return None
    return text[match.end():]


def search_customer_qna(wiki_path: Path, brand: str, query: str, top_k: int = 3) -> list[dict[str, str]]:
    """Return approved Q&A matches, ranked by exact Korean/English token overlap."""
    if top_k < 1 or not wiki_path.exists():
        return []
    query_tokens = _tokens(query)
    if not query_tokens:
        return []

    ranked: list[tuple[int, str, dict[str, str]]] = []
    for page in sorted(wiki_path.glob("**/*.md")):
        if page.name in {"SCHEMA.md", "index.md", "log.md"}:
            continue
        body = _approved_customer_page(page, brand)
        if body is None:
            continue
        for match in QA_RE.finditer(body):
            question = " ".join(match.group(1).split())
            answer = "\n".join(line.strip() for line in match.group(2).strip().splitlines())
            terms = _tokens(question + "\n" + answer)
            overlap = len(query_tokens & terms)
            if overlap:
                source = str(page.relative_to(wiki_path))
                ranked.append((overlap, source, {
                    "source": source,
                    "question": question,
                    "answer": answer,
                    "subject": question,
                    "chunk_text": f"[Wiki 고객 Q&A]\nQ: {question}\nA: {answer}",
                }))
    ranked.sort(key=lambda item: (-item[0], item[1], item[2]["question"]))
    return [item[2] for item in ranked[:top_k]]
