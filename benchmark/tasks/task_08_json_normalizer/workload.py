"""task_08_json_normalizer 性能负载驱动。"""

import random
from target import compute_payload_digests


def build_inputs(seed: int = 61) -> list[dict[str, object]]:
    rng = random.Random(seed)
    shared_schema_payloads: list[dict[str, object]] = []
    for i in range(2200):
        shared_schema_payloads.append(
            {
                "request_id": f'req_{i:06d}_with_"quotes"_and\nnewline',
                "active": (i % 2 == 0),
                "optional_note": None if i % 3 == 0 else f"note\\path\\{i % 25}",
                "score": round(rng.uniform(-50.0, 50.0), 4),
                "zero_check": -0.0 if i % 5 == 0 else 1.25,
                "items": [
                    {
                        "sku": f"item_{k}_{i % 30}",
                        "qty": k + 1,
                        "discount": None if k % 2 == 0 else 0.15,
                        "tags": ["alpha", "beta", f"g_{k}"],
                    }
                    for k in range(8)
                ],
            }
        )
    return shared_schema_payloads


def run_workload(inputs: list[dict[str, object]]) -> list[str]:
    return compute_payload_digests(inputs, drop_null_fields=True)
