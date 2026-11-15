import unittest
from target import RouteDecision, match_single_rule, parse_rule_spec, route_log_batch, summarize_decisions


class TestLogRouter(unittest.TestCase):
    def test_basic_routing_and_order(self) -> None:
        rules = [
            "channel=Sec Team;level=ERROR;service_prefix=auth;pattern=failed.*uid=\\d+",
            "channel=warn_pool;level=WARN|ERROR;pattern=failed",
        ]
        lines = [
            "[2026-11-15 10:00:00] [ERROR] [auth-api] Login FAILED for uid=42",
            "[2026-11-15 10:00:01] [ERROR] [billing] Charge failed for uid=42",
            "[2026-11-15 10:00:02] [INFO] [auth-api] Login succeeded",
            "malformed raw line without brackets",
        ]
        res = route_log_batch(lines, rules, fallback_channel="Default Sink")
        self.assertEqual(
            res,
            [
                RouteDecision(0, "sec_team", "ERROR", "auth-api"),
                RouteDecision(1, "warn_pool", "ERROR", "billing"),
                RouteDecision(2, "default_sink", "INFO", "auth-api"),
                RouteDecision(3, "default_sink", "INFO", "unknown"),
            ],
        )
        self.assertEqual(
            summarize_decisions(res),
            {"sec_team": 1, "warn_pool": 1, "default_sink": 2},
        )

    def test_single_rule_helpers_preserved(self) -> None:
        spec = parse_rule_spec(" channel = Ops Alert ; level = WARN ; ")
        self.assertEqual(spec["channel"], "ops_alert")
        self.assertEqual(
            match_single_rule("channel=ops;level=WARN;pattern=timeout", "WARN", "svc", "db TIMEOUT"),
            "ops",
        )
        self.assertIsNone(
            match_single_rule("channel=ops;level=ERROR;pattern=timeout", "WARN", "svc", "db TIMEOUT")
        )

    def test_multiple_rule_lists_do_not_cross_contaminate(self) -> None:
        lines = ["[2026-11-15 10:00:00] [ERROR] [api] boom"]
        r1 = route_log_batch(lines, ["channel=a;level=ERROR;pattern=boom"])
        r2 = route_log_batch(lines, ["channel=b;level=ERROR;pattern=boom"])
        self.assertEqual(r1[0].channel, "a")
        self.assertEqual(r2[0].channel, "b")


if __name__ == "__main__":
    unittest.main()
