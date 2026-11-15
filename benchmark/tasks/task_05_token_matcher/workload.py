"""task_05_token_matcher 性能负载驱动。"""

import random
from target import scan_corpus_glossary


def build_inputs(seed: int = 31) -> tuple[dict[str, str], list[str]]:
    rng = random.Random(seed)
    vocab = [f"tok{i:03d}" for i in range(300)]
    documents: dict[str, str] = {}
    for d in range(25):
        words = [vocab[rng.randrange(len(vocab))] for _ in range(900)]
        documents[f"doc_{d:03d}"] = " ".join(words)

    glossary: list[str] = []
    for i in range(160):
        if i % 4 == 0:
            glossary.append(f"{vocab[i]} {vocab[(i + 7) % len(vocab)]}")
        elif i % 9 == 0:
            glossary.append(f"{vocab[i]} {vocab[(i + 3) % len(vocab)]} {vocab[(i + 5) % len(vocab)]}")
        else:
            glossary.append(vocab[i])
    return documents, glossary


def run_workload(inputs: tuple[dict[str, str], list[str]]) -> int:
    documents, glossary = inputs
    report = scan_corpus_glossary(documents, glossary)
    return sum(sum(v.values()) for v in report.values())
