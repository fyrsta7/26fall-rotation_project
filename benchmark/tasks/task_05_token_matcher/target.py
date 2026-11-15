"""敏感词与术语词表多文档扫描模块。"""

from __future__ import annotations
import re


def tokenize_words(text: str) -> list[str]:
    """按字母数字下划线切分单词并转为小写。"""
    return re.findall(r"[A-Za-z0-9_]+", text.lower())


def count_term_in_document(doc_text: str, term: str) -> int:
    """统计单个词或词组（空格分隔的多词短语）在文档中按整词边界出现的次数（忽略大小写）。"""
    term_tokens = tokenize_words(term)
    if not term_tokens:
        return 0
    doc_tokens = tokenize_words(doc_text)
    width = len(term_tokens)
    if width > len(doc_tokens):
        return 0
    hits = 0
    for i in range(len(doc_tokens) - width + 1):
        if doc_tokens[i : i + width] == term_tokens:
            hits += 1
    return hits


def scan_corpus_glossary(
    documents: dict[str, str],
    glossary_terms: list[str],
) -> dict[str, dict[str, int]]:
    """扫描全部文档，返回每篇文档中出现次数大于 0 的术语及频次。"""
    report: dict[str, dict[str, int]] = {}
    for doc_id, doc_text in documents.items():
        doc_hits: dict[str, int] = {}
        for term in glossary_terms:
            cnt = count_term_in_document(doc_text, term)
            if cnt > 0:
                doc_hits[term] = cnt
        report[doc_id] = doc_hits
    return report
