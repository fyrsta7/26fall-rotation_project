import copy
import unittest
from target import aggregate_monthly_spend, parse_year_month, sanitize_record_for_audit


class TestCsvAggregator(unittest.TestCase):
    def test_aggregation_and_input_immutability(self) -> None:
        records = [
            {
                "status": "SETTLED",
                "category": "compute",
                "currency": "usd",
                "amount_cents": 1000,
                "created_at": "2026-03-15T08:09:10",
                "metadata": {"nested": [1, 2, 3]},
            },
            {
                "status": "PENDING",
                "category": "compute",
                "currency": "usd",
                "amount_cents": 9999,
                "created_at": "2026-03-16",
                "metadata": {"nested": [4]},
            },
            {
                "status": "SETTLED",
                "category": "storage",
                "currency": "CNY",
                "amount_cents": 250,
                "created_at": "2026-03-20",
                "metadata": {"nested": []},
            },
        ]
        snapshot = copy.deepcopy(records)
        res = aggregate_monthly_spend(
            records,
            fx_rates={"CNY": 1.0, "USD": 7.0},
            allowed_categories={"compute", "storage"},
        )
        self.assertEqual(records, snapshot)  # 输入字典不得被原地篡改
        self.assertAlmostEqual(res["2026-03"]["compute"], 70.0)
        self.assertAlmostEqual(res["2026-03"]["storage"], 2.5)

    def test_invalid_date_still_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            parse_year_month("2026-13-40")
        with self.assertRaises(ValueError):
            parse_year_month("not-a-date")

    def test_sanitize_helper_preserves_copy_semantics(self) -> None:
        orig = {"currency": "usd", "nested": [1, 2]}
        out = sanitize_record_for_audit(orig)
        out["nested"].append(3)
        self.assertEqual(orig["currency"], "usd")
        self.assertEqual(orig["nested"], [1, 2])


if __name__ == "__main__":
    unittest.main()
