"""task_02_graph_reach 性能负载驱动。"""

import random
from target import DependencyGraph, compute_transitive_fanout, count_pair_reachability, format_impact_report


def build_inputs(seed: int = 7) -> tuple[DependencyGraph, list[tuple[str, str]], list[str], set[str]]:
    rng = random.Random(seed)
    graph = DependencyGraph()
    num_nodes = 420
    names = [f"pkg_{i:03d}" for i in range(num_nodes)]
    # 构造带局部环与多层共享下游的依赖图
    for i in range(num_nodes):
        for _ in range(4):
            j = min(num_nodes - 1, i + rng.randint(1, 35))
            graph.add_edge(names[i], names[j])
        if i % 25 == 0 and i + 8 < num_nodes:
            graph.add_edge(names[i + 8], names[i])

    blocked = {names[50], names[180], names[310]}
    queries = [
        (names[rng.randrange(num_nodes)], names[rng.randrange(num_nodes)])
        for _ in range(3600)
    ]
    candidates = names[:260]
    return graph, queries, candidates, blocked


def run_workload(inputs: tuple[DependencyGraph, list[tuple[str, str]], list[str], set[str]]) -> tuple[int, list[str]]:
    graph, queries, candidates, blocked = inputs
    flags = count_pair_reachability(graph, queries, blocked=blocked)
    fanout = compute_transitive_fanout(graph, candidates, blocked=blocked)
    return sum(flags), format_impact_report(fanout, top_k=5)
