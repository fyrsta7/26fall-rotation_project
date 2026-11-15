"""结构化载荷规范化签名计算模块（用于请求幂等指纹生成）。"""

from __future__ import annotations
import hashlib
from typing import Any


def escape_string_token(s: str) -> str:
    out = ""
    for ch in s:
        if ch == "\\":
            out = out + "\\\\"
        elif ch == '"':
            out = out + '\\"'
        elif ch == "\n":
            out = out + "\\n"
        else:
            out = out + ch
    return f'"{out}"'


def canonicalize_node(value: Any, drop_null_fields: bool = True) -> str:
    """将嵌套 JSON 兼容结构确定性地序列化为规范字符串。"""
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if value == 0.0:
            return "0"
        return f"{value:.8g}"
    if isinstance(value, str):
        return escape_string_token(value)
    if isinstance(value, (list, tuple)):
        rendered = ""
        for idx, item in enumerate(value):
            piece = canonicalize_node(item, drop_null_fields=drop_null_fields)
            rendered = rendered + ("," if idx > 0 else "") + piece
        return "[" + rendered + "]"
    if isinstance(value, dict):
        keys = sorted(str(k) for k in value.keys())
        key_map = {str(k): v for k, v in value.items()}
        rendered = ""
        emitted = 0
        for k in keys:
            v = key_map[k]
            if drop_null_fields and v is None:
                continue
            pair_str = escape_string_token(k) + ":" + canonicalize_node(v, drop_null_fields=drop_null_fields)
            rendered = rendered + ("," if emitted > 0 else "") + pair_str
            emitted += 1
        return "{" + rendered + "}"
    raise TypeError(f"Unsupported type: {type(value)!r}")


def compute_payload_digests(
    payloads: list[dict[str, Any]],
    drop_null_fields: bool = True,
) -> list[str]:
    digests: list[str] = []
    for item in payloads:
        canonical = canonicalize_node(item, drop_null_fields=drop_null_fields)
        digests.append(hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16])
    return digests
