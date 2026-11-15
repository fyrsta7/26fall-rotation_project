import unittest
from target import DependencyGraph, collect_reachable, compute_transitive_fanout, count_pair_reachability


class TestGraphReach(unittest.TestCase):
    def test_dag_and_cycle_with_blocked(self) -> None:
        g = DependencyGraph()
        g.add_edge("a", "b")
        g.add_edge("b", "c")
        g.add_edge("c", "a")  # 环
        g.add_edge("c", "d")
        g.add_edge("d", "e")

        self.assertEqual(collect_reachable(g, "a"), {"a", "b", "c", "d", "e"})
        self.assertEqual(collect_reachable(g, "a", frozenset({"d"})), {"a", "b", "c"})
        self.assertEqual(collect_reachable(g, "d", frozenset({"d"})), set())

        q = [("a", "e"), ("d", "a"), ("a", "d")]
        self.assertEqual(count_pair_reachability(g, q, blocked=None), [True, False, True])
        self.assertEqual(count_pair_reachability(g, q, blocked={"c"}), [False, False, False])

    def test_graph_mutation_invalidates_any_cache(self) -> None:
        """关键边界测试：同一 DependencyGraph 实例在增删边后，再次查询必须反映最新拓扑。"""
        g = DependencyGraph()
        g.add_edge("x", "y")
        self.assertEqual(count_pair_reachability(g, [("x", "z")]), [False])

        g.add_edge("y", "z")
        self.assertEqual(count_pair_reachability(g, [("x", "z")]), [True])
        self.assertEqual(compute_transitive_fanout(g, ["x"])["x"], 2)

        g.remove_edge("y", "z")
        self.assertEqual(count_pair_reachability(g, [("x", "z")]), [False])
        self.assertEqual(compute_transitive_fanout(g, ["x"])["x"], 1)


if __name__ == "__main__":
    unittest.main()
