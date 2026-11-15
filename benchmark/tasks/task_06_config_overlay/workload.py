"""task_06_config_overlay 性能负载驱动。"""

import random
from target import LayeredConfig, evaluate_request_configs


def _ph(name: str) -> str:
    return "$" + "{" + name + "}"


def build_inputs(seed: int = 41) -> tuple[LayeredConfig, list[tuple[str, str, list[str]]]]:
    rng = random.Random(seed)
    defaults: dict[str, str] = {"root.domain": "svc.internal", "root.proto": "https"}
    for i in range(350):
        defaults[f"base.item_{i}"] = f"val_{i}_{_ph('root.domain')}"
    env_layer: dict[str, str] = {}
    for i in range(120):
        env_layer[f"service.ep_{i}"] = (
            f"{_ph('root.proto')}://ep{i}.{_ph(f'base.item_{i}')}:"
            f"{8000 + i}/v1/{_ph(f'base.item_{(i + 17) % 350}')}"
        )

    cfg = LayeredConfig(defaults=defaults, env_layer=env_layer)
    all_keys = [f"service.ep_{i}" for i in range(120)] + [f"base.item_{i}" for i in range(100)]

    batches: list[tuple[str, str, list[str]]] = []
    for b in range(12):
        queries = [all_keys[rng.randrange(len(all_keys))] for _ in range(1800)]
        batches.append(("root.domain", f"region{b}.svc.internal", queries))
    return cfg, batches


def run_workload(inputs: tuple[LayeredConfig, list[tuple[str, str, list[str]]]]) -> int:
    cfg, batches = inputs
    total_chars = 0
    for ov_key, ov_val, queries in batches:
        cfg.set_override(ov_key, ov_val)
        vals = evaluate_request_configs(cfg, queries)
        total_chars += sum(len(v) for v in vals)
    cfg.clear_override("root.domain")
    return total_chars
