"""task_02_graph_reach 参考优化实现：在批量查询调用方复用同一批内的可达集合备忘录，不污染可变图对象。"""

from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class DependencyGraph:
    adjacency: dict[str, list[str]] = field(default_factory=dict)

    def add_edge(self, src: str, dst: str) -> None:
        self.adjacency.setdefault(src, []).append(dst)
        self.adjacency.setdefault(dst, [])

    def remove_edge(self, src: str, dst: str) -> None:
        if src in self.adjacency and dst in self.adjacency[src]:
            self.adjacency[src].remove(dst)

    def nodes(self) -> list[str]:
        return sorted(self.adjacency.keys())


def format_impact_report(scores: dict[str, int], top_k: int = 5) -> list[str]:
    ranked = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))[:top_k]
    return [f"{node}:{count}" for node, count in ranked]


def collect_reachable(
    graph: DependencyGraph,
    start: str,
    blocked: frozenset[str] = frozenset(),
) -> set[str]:
    adj = graph.adjacency
    if start in blocked or start not in adj:
        return set()
    visited: set[str] = {start}
    stack = [start]
    while stack:
        curr = stack.pop()
        for nxt in adj.get(curr, ()):
            if nxt not in visited and nxt not in blocked:
                visited.add(nxt)
                stack.append(nxt)
    return visited


def count_pair_reachability(
    graph: DependencyGraph,
    queries: list[tuple[str, str]],
    blocked: set[str] | None = None,
) -> list[bool]:
    blocked_set = frozenset(blocked or ())
    memo: dict[str, set[str]] = {}
    results: list[bool] = []
    for src, target in queries:
        if src in blocked_set or target in blocked_set:
            results.append(False)
            continue
        reach = memo.get(src)
        if reach is None:
            reach = collect_reachable(graph, src, blocked_set)
            memo[src] = reach
        results.append(target in reach)
    return results


def compute_transitive_fanout(
    graph: DependencyGraph,
    candidate_nodes: list[str],
    blocked: set[str] | None = None,
) -> dict[str, int]:
    blocked_set = frozenset(blocked or ())
    memo: dict[str, set[str]] = {}
    scores: dict[str, int] = {}
    for node in candidate_nodes:
        reach = memo.get(node)
        if reach is None:
            reach = collect_reachable(graph, node, blocked_set)
            memo[node] = reach
        scores[node] = max(0, len(reach) - (1 if node in reach else 0))
    return scores
