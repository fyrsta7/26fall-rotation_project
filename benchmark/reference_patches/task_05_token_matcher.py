"""task_05_token_matcher 参考优化实现：预分词术语词表，单篇文档只做一次分词并按 n-gram 长度一次统计。"""

from __future__ import annotations
from collections import Counter
import re


WORD_RE = re.compile(r"[A-Za-z0-9_]+")


def tokenize_words(text: str) -> list[str]:
    return WORD_RE.findall(text.lower())


def count_term_in_document(doc_text: str, term: str) -> int:
    term_tokens = tuple(tokenize_words(term))
    if not term_tokens:
        return 0
    doc_tokens = tokenize_words(doc_text)
    width = len(term_tokens)
    if width > len(doc_tokens):
        return 0
    if width == 1:
        target_tok = term_tokens[0]
        return sum(1 for tok in doc_tokens if tok == target_tok)
    return sum(
        1
        for i in range(len(doc_tokens) - width + 1)
        if tuple(doc_tokens[i : i + width]) == term_tokens
    )


def scan_corpus_glossary(
    documents: dict[str, str],
    glossary_terms: list[str],
) -> dict[str, dict[str, int]]:
    terms_by_len: dict[int, list[tuple[str, tuple[str, ...]]]] = {}
    needed_tuples_by_len: dict[int, set[tuple[str, ...]]] = {}
    for raw_term in glossary_terms:
        toks = tuple(tokenize_words(raw_term))
        if not toks:
            continue
        w = len(toks)
        terms_by_len.setdefault(w, []).append((raw_term, toks))
        needed_tuples_by_len.setdefault(w, set()).add(toks)

    report: dict[str, dict[str, int]] = {}
    for doc_id, doc_text in documents.items():
        doc_tokens = tokenize_words(doc_text)
        n = len(doc_tokens)
        doc_hits: dict[str, int] = {}
        for width, term_entries in terms_by_len.items():
            if width > n:
                continue
            if width == 1:
                counts_1 = Counter(doc_tokens)
                for raw_term, toks in term_entries:
                    c = counts_1.get(toks[0], 0)
                    if c > 0:
                        doc_hits[raw_term] = c
            else:
                needed = needed_tuples_by_len[width]
                counts_w: Counter[tuple[str, ...]] = Counter()
                for i in range(n - width + 1):
                    gram = tuple(doc_tokens[i : i + width])
                    if gram in needed:
                        counts_w[gram] += 1
                for raw_term, toks in term_entries:
                    c = counts_w.get(toks, 0)
                    if c > 0:
                        doc_hits[raw_term] = c
        report[doc_id] = doc_hits
    return report
