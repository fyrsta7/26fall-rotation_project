import unittest
from target import LayeredConfig, evaluate_request_configs


class TestConfigOverlay(unittest.TestCase):
    def test_nested_expansion_and_invalidation(self) -> None:
        ph_host = "$" + "{host}"
        ph_port = "$" + "{port}"
        cfg = LayeredConfig(
            defaults={"host": "localhost", "port": "8080", "url": f"http://{ph_host}:{ph_port}/api"},
            env_layer={"port": "9090"},
        )
        self.assertEqual(cfg.get_resolved("url"), "http://localhost:9090/api")
        self.assertEqual(cfg.get_resolved("nonexistent", default="N/A"), "N/A")

        cfg.set_override("host", "prod.internal")
        self.assertEqual(cfg.get_resolved("url"), "http://prod.internal:9090/api")

        cfg.clear_override("host")
        self.assertEqual(cfg.get_resolved("url"), "http://localhost:9090/api")

        cfg.update_env({"port": "7070"})
        self.assertEqual(
            evaluate_request_configs(cfg, ["url", "missing"]),
            ["http://localhost:7070/api", "MISSING"],
        )

    def test_circular_reference_raises(self) -> None:
        ph_a = "$" + "{a}"
        ph_b = "$" + "{b}"
        cfg = LayeredConfig(defaults={"a": ph_b, "b": ph_a})
        with self.assertRaises(ValueError):
            cfg.get_resolved("a")


if __name__ == "__main__":
    unittest.main()
