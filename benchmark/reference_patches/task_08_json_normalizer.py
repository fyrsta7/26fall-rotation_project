"""task_08_json_normalizer 参考优化实现：使用底层字符串替换与 join 替代逐字符/逐项累加拼接，消除字典二次构造。"""

from __future__ import annotations
import hashlib
from typing import Any


def escape_string_token(s: str) -> str:
    escaped = s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return f'"{escaped}"'


def canonicalize_node(value: Any, drop_null_fields: bool = True) -> str:
    if value is None:
        return "null"
    t = type(value)
    if t is bool:
        return "true" if value else "false"
    if t is int:
        return str(value)
    if t is float:
        return "0" if value == 0.0 else f"{value:.8g}"
    if t is str:
        escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        return f'"{escaped}"'
    if t is list or t is tuple:
        return "[" + ",".join(canonicalize_node(item, drop_null_fields) for item in value) + "]"
    if t is dict:
        if drop_null_fields:
            pairs = sorted(
                ((k if type(k) is str else str(k)), v)
                for k, v in value.items()
                if v is not None
            )
        else:
            pairs = sorted(((k if type(k) is str else str(k)), v) for k, v in value.items())
        parts = [
            f"{escape_string_token(k)}:{canonicalize_node(v, drop_null_fields)}"
            for k, v in pairs
        ]
        return "{" + ",".join(parts) + "}"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return "0" if value == 0.0 else f"{value:.8g}"
    if isinstance(value, str):
        return escape_string_token(value)
    if isinstance(value, (list, tuple)):
        return "[" + ",".join(canonicalize_node(item, drop_null_fields) for item in value) + "]"
    if isinstance(value, dict):
        items = [
            (str(k), v)
            for k, v in value.items()
            if not (drop_null_fields and v is None)
        ]
        items.sort(key=lambda kv: kv[0])
        return "{" + ",".join(f"{escape_string_token(k)}:{canonicalize_node(v, drop_null_fields)}" for k, v in items) + "}"
    raise TypeError(f"Unsupported type: {type(value)!r}")


def compute_payload_digests(
    payloads: list[dict[str, Any]],
    drop_null_fields: bool = True,
) -> list[str]:
    sha256 = hashlib.sha256
    return [
        sha256(canonicalize_node(item, drop_null_fields).encode("utf-8")).hexdigest()[:16]
        for item in payloads
    ]
