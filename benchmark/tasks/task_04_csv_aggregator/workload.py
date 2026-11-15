"""task_04_csv_aggregator 性能负载驱动。"""

import random
from target import aggregate_monthly_spend


def build_inputs(seed: int = 23) -> tuple[list[dict[str, object]], dict[str, float], set[str]]:
    rng = random.Random(seed)
    categories = ["compute", "storage", "network", "database", "analytics", "other"]
    currencies = ["cny", "usd", "eur", "hkd"]
    statuses = ["SETTLED", "SETTLED", "PENDING", "CANCELLED"]
    fx = {"CNY": 1.0, "USD": 7.18, "EUR": 7.82, "HKD": 0.92}

    records: list[dict[str, object]] = []
    for i in range(9000):
        month = (i % 12) + 1
        day = (i % 28) + 1
        ts = f"2026-{month:02d}-{day:02d}T14:25:30" if i % 2 == 0 else f"2026-{month:02d}-{day:02d}"
        # 每条记录附带较大的嵌套 metadata，模拟真实业务宽表对象
        records.append(
            {
                "order_id": f"ord_{i:06d}",
                "status": statuses[rng.randrange(len(statuses))],
                "category": categories[rng.randrange(len(categories))],
                "currency": currencies[rng.randrange(len(currencies))],
                "amount_cents": rng.randint(100, 250000),
                "created_at": ts,
                "metadata": {
                    "region": "cn-north",
                    "tags": ["prod", "batch", f"shard_{i % 16}"],
                    "line_items": [{"sku": f"s_{k}", "qty": k} for k in range(5)],
                },
            }
        )
    allowed = {"compute", "storage", "network", "database"}
    return records, fx, allowed


def run_workload(inputs: tuple[list[dict[str, object]], dict[str, float], set[str]]) -> dict[str, dict[str, float]]:
    records, fx, allowed = inputs
    return aggregate_monthly_spend(records, fx, allowed_categories=allowed)
