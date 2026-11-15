"""日志分级路由模块（包含多级调用链与格式校验辅助函数）。"""

from __future__ import annotations
from dataclasses import dataclass
import re
from typing import Iterable


@dataclass(frozen=True)
class RouteDecision:
    line_index: int
    channel: str
    severity: str
    service: str


def normalize_channel_name(raw_name: str) -> str:
    cleaned = raw_name.strip().lower().replace(" ", "_")
    return cleaned or "default"


def summarize_decisions(decisions: Iterable[RouteDecision]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in decisions:
        counts[item.channel] = counts.get(item.channel, 0) + 1
    return counts


def parse_rule_spec(spec_text: str) -> dict[str, str]:
    """将规则描述串解析为键值字典，例如 'channel=sec;level=ERROR|WARN;pattern=auth.*failed'。"""
    parsed: dict[str, str] = {}
    for part in spec_text.split(";"):
        part = part.strip()
        if not part or "=" not in part:
            continue
        key, val = part.split("=", 1)
        parsed[key.strip()] = val.strip()
    parsed["channel"] = normalize_channel_name(parsed.get("channel", "default"))
    return parsed


def extract_log_fields(line: str) -> tuple[str, str, str]:
    """解析形如 '[2026-11-15 12:00:01] [ERROR] [auth-gateway] message...' 的日志行。"""
    header_regex = re.compile(r"^\[[^\]]+\]\s+\[([A-Z]+)\]\s+\[([a-z0-9_-]+)\]\s+(.*)$")
    match = header_regex.match(line)
    if not match:
        return ("INFO", "unknown", line)
    return (match.group(1), match.group(2), match.group(3))


def match_single_rule(spec_text: str, severity: str, service: str, message: str) -> str | None:
    """判断单条日志是否命中规则，命中则返回目标 channel，否则返回 None。"""
    spec = parse_rule_spec(spec_text)
    allowed_levels = [lv.strip() for lv in spec.get("level", "").split("|") if lv.strip()]
    if allowed_levels and severity not in allowed_levels:
        return None

    service_prefix = spec.get("service_prefix", "")
    if service_prefix and not service.startswith(service_prefix):
        return None

    pattern = spec.get("pattern", "")
    if pattern:
        # 超过 re 内部小缓存容量（或动态组合标志）时，重复编译开销显著
        compiled = re.compile(pattern, re.IGNORECASE)
        if compiled.search(message) is None:
            return None
    return spec["channel"]


def route_log_batch(lines: list[str], rule_specs: list[str], fallback_channel: str = "general") -> list[RouteDecision]:
    """按顺序匹配规则列表，为每条日志生成路由结果。"""
    normalized_fallback = normalize_channel_name(fallback_channel)
    decisions: list[RouteDecision] = []
    for idx, line in enumerate(lines):
        severity, service, message = extract_log_fields(line)
        chosen = normalized_fallback
        for spec_text in rule_specs:
            matched_channel = match_single_rule(spec_text, severity, service, message)
            if matched_channel is not None:
                chosen = matched_channel
                break
        decisions.append(
            RouteDecision(
                line_index=idx,
                channel=chosen,
                severity=severity,
                service=service,
            )
        )
    return decisions
