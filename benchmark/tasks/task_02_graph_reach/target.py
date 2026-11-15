"""任务依赖图关键节点分析模块。"""

from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class DependencyGraph:
    """有向依赖图：u -> v 表示任务 u 依赖任务 v。"""

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
    """返回从 start 出发（不经过 blocked 集合中的节点）可到达的所有节点（含 start 自身，若未阻塞）。"""
    if start in blocked or start not in graph.adjacency:
        return set()

    visited: set[str] = set()

    def _dfs(curr: str) -> None:
        if curr in visited or curr in blocked:
            return
        visited.add(curr)
        for nxt in graph.adjacency.get(curr, ()):
            if nxt not in visited and nxt not in blocked:
                _dfs(nxt)

    _dfs(start)
    return visited


def count_pair_reachability(
    graph: DependencyGraph,
    queries: list[tuple[str, str]],
    blocked: set[str] | None = None,
) -> list[bool]:
    """批量判断给定 (src, target) 查询对在阻塞集合下是否可达。"""
    blocked_set = frozenset(blocked or ())
    results: list[bool] = []
    for src, target in queries:
        if src in blocked_set or target in blocked_set:
            results.append(False)
            continue
        reachable = collect_reachable(graph, src, blocked_set)
        results.append(target in reachable)
    return results


def compute_transitive_fanout(
    graph: DependencyGraph,
    candidate_nodes: list[str],
    blocked: set[str] | None = None,
) -> dict[str, int]:
    """统计每个候选节点可传递到达的下游节点数量（不含自身）。"""
    blocked_set = frozenset(blocked or ())
    scores: dict[str, int] = {}
    for node in candidate_nodes:
        reachable = collect_reachable(graph, node, blocked_set)
        scores[node] = max(0, len(reachable) - (1 if node in reachable else 0))
    return scores
