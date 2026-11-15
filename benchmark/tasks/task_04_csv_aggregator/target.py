"""账单明细快照审计与按月分类汇总模块。"""

from __future__ import annotations
import copy
from datetime import datetime
from typing import Any


def sanitize_record_for_audit(record: dict[str, Any]) -> dict[str, Any]:
    """为只读审计流水线准备单条记录（原始实现防御性地执行了深拷贝）。"""
    cloned = copy.deepcopy(record)
    cloned["currency"] = str(cloned.get("currency", "CNY")).upper()
    return cloned


def parse_year_month(iso_date_str: str) -> str:
    """从 'YYYY-MM-DD' 或 'YYYY-MM-DDTHH:MM:SS' 提取 'YYYY-MM'。"""
    clean = iso_date_str.strip()
    if "T" in clean:
        dt = datetime.strptime(clean[:19], "%Y-%m-%dT%H:%M:%S")
    else:
        dt = datetime.strptime(clean[:10], "%Y-%m-%d")
    return f"{dt.year:04d}-{dt.month:02d}"


def convert_to_cny(amount_cents: int, currency: str, fx_rates: dict[str, float]) -> float:
    rate = fx_rates.get(currency.upper(), 1.0)
    return (amount_cents / 100.0) * rate


def aggregate_monthly_spend(
    records: list[dict[str, Any]],
    fx_rates: dict[str, float],
    allowed_categories: set[str] | None = None,
) -> dict[str, dict[str, float]]:
    """按 (月份, 类别) 汇总已结算订单的折算人民币总额，不得修改输入 records。"""
    monthly: dict[str, dict[str, float]] = {}
    for raw in records:
        rec = sanitize_record_for_audit(raw)
        if rec.get("status") != "SETTLED":
            continue
        category = str(rec.get("category", "other"))
        if allowed_categories is not None and category not in allowed_categories:
            continue
        ym = parse_year_month(str(rec["created_at"]))
        cny_val = convert_to_cny(int(rec["amount_cents"]), rec["currency"], fx_rates)
        bucket = monthly.setdefault(ym, {})
        bucket[category] = round(bucket.get(category, 0.0) + cny_val, 6)
    return monthly
