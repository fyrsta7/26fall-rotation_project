"""task_01_log_router 性能负载驱动。"""

import random
from target import route_log_batch, summarize_decisions


def build_inputs(seed: int = 42) -> tuple[list[str], list[str]]:
    rng = random.Random(seed)
    services = [
        "auth-gateway",
        "payment-core",
        "order-worker",
        "search-indexer",
        "cache-proxy",
        "metrics-agent",
    ]
    levels = ["DEBUG", "INFO", "WARN", "ERROR"]
    templates = [
        "connection reset by peer host=10.0.{a}.{b} retry={r}",
        "token verification failed for uid={u} reason=expired",
        "slow query detected elapsed_ms={ms} table=orders_{a}",
        "healthcheck passed latency_ms={r}",
        "circuit breaker open upstream=payment-{a} code={u}",
        "request completed status=200 bytes={ms}",
    ]

    # 构造 32 条路由规则（包含不同正则与服务前缀）
    rule_specs: list[str] = []
    for i in range(28):
        svc = services[i % len(services)][:5]
        rule_specs.append(
            f"channel=rule_chan_{i};level=ERROR|WARN;service_prefix={svc};"
            f"pattern=(?:timeout|unavailable)_code_{i + 100}\\b"
        )
    rule_specs.extend(
        [
            "channel=security_alert;level=ERROR|WARN;service_prefix=auth;pattern=token\\s+verification\\s+failed.*uid=\\d+",
            "channel=db_slow;level=WARN|INFO;pattern=slow\\s+query\\s+detected\\s+elapsed_ms=\\d{3,}",
            "channel=payment_incident;level=ERROR;service_prefix=payment;pattern=circuit\\s+breaker\\s+open",
            "channel=net_retry;level=WARN|ERROR;pattern=connection\\s+reset.*retry=[3-9]",
        ]
    )

    lines: list[str] = []
    for i in range(3200):
        lv = levels[rng.randrange(len(levels))]
        svc = services[rng.randrange(len(services))]
        tpl = templates[rng.randrange(len(templates))]
        msg = tpl.format(
            a=rng.randint(1, 20),
            b=rng.randint(1, 250),
            r=rng.randint(0, 6),
            u=rng.randint(1000, 9999),
            ms=rng.randint(20, 1500),
        )
        lines.append(f"[2026-11-15 12:00:{i % 60:02d}] [{lv}] [{svc}] {msg}")
    return lines, rule_specs


def run_workload(inputs: tuple[list[str], list[str]]) -> dict[str, int]:
    lines, rule_specs = inputs
    decisions = route_log_batch(lines, rule_specs, fallback_channel="General Pool")
    return summarize_decisions(decisions)
