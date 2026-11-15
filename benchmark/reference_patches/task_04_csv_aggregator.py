"""task_04_csv_aggregator 参考优化实现：只读聚合路径跳过无谓深拷贝，并使用 datetime.fromisoformat 轻量校验解析。"""

from __future__ import annotations
import copy
from datetime import date, datetime
from typing import Any


def sanitize_record_for_audit(record: dict[str, Any]) -> dict[str, Any]:
    cloned = copy.deepcopy(record)
    cloned["currency"] = str(cloned.get("currency", "CNY")).upper()
    return cloned


def parse_year_month(iso_date_str: str) -> str:
    clean = iso_date_str.strip()
    if "T" in clean:
        dt = datetime.fromisoformat(clean[:19])
        return f"{dt.year:04d}-{dt.month:02d}"
    d = date.fromisoformat(clean[:10])
    return f"{d.year:04d}-{d.month:02d}"


def convert_to_cny(amount_cents: int, currency: str, fx_rates: dict[str, float]) -> float:
    rate = fx_rates.get(currency.upper(), 1.0)
    return (amount_cents / 100.0) * rate


def aggregate_monthly_spend(
    records: list[dict[str, Any]],
    fx_rates: dict[str, float],
    allowed_categories: set[str] | None = None,
) -> dict[str, dict[str, float]]:
    monthly: dict[str, dict[str, float]] = {}
    rate_cache = {k.upper(): v / 100.0 for k, v in fx_rates.items()}
    default_scale = 0.01
    ym_cache: dict[str, str] = {}

    for raw in records:
        if raw.get("status") != "SETTLED":
            continue
        category = str(raw.get("category", "other"))
        if allowed_categories is not None and category not in allowed_categories:
            continue
        raw_ts = str(raw["created_at"])
        ym = ym_cache.get(raw_ts)
        if ym is None:
            ym = parse_year_month(raw_ts)
            ym_cache[raw_ts] = ym
        curr = str(raw.get("currency", "CNY")).upper()
        cny_val = int(raw["amount_cents"]) * rate_cache.get(curr, default_scale)
        bucket = monthly.get(ym)
        if bucket is None:
            monthly[ym] = {category: round(cny_val, 6)}
        else:
            bucket[category] = round(bucket.get(category, 0.0) + cny_val, 6)
    return monthly
