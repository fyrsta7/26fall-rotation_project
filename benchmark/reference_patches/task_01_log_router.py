"""task_01_log_router 参考优化实现：预编译头部正则与规则列表，消除内层循环重复解析与编译。"""

from __future__ import annotations
from dataclasses import dataclass
from functools import lru_cache
import re
from typing import Iterable


HEADER_REGEX = re.compile(r"^\[[^\]]+\]\s+\[([A-Z]+)\]\s+\[([a-z0-9_-]+)\]\s+(.*)$")


@dataclass(frozen=True)
class RouteDecision:
    line_index: int
    channel: str
    severity: str
    service: str


@dataclass(frozen=True)
class _CompiledRule:
    channel: str
    allowed_levels: frozenset[str]
    service_prefix: str
    regex: re.Pattern[str] | None


def normalize_channel_name(raw_name: str) -> str:
    cleaned = raw_name.strip().lower().replace(" ", "_")
    return cleaned or "default"


def summarize_decisions(decisions: Iterable[RouteDecision]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in decisions:
        counts[item.channel] = counts.get(item.channel, 0) + 1
    return counts


def parse_rule_spec(spec_text: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for part in spec_text.split(";"):
        part = part.strip()
        if not part or "=" not in part:
            continue
        key, val = part.split("=", 1)
        parsed[key.strip()] = val.strip()
    parsed["channel"] = normalize_channel_name(parsed.get("channel", "default"))
    return parsed


@lru_cache(maxsize=512)
def _compile_rule(spec_text: str) -> _CompiledRule:
    spec = parse_rule_spec(spec_text)
    levels = frozenset(lv.strip() for lv in spec.get("level", "").split("|") if lv.strip())
    prefix = spec.get("service_prefix", "")
    pat = spec.get("pattern", "")
    compiled = re.compile(pat, re.IGNORECASE) if pat else None
    return _CompiledRule(
        channel=spec["channel"],
        allowed_levels=levels,
        service_prefix=prefix,
        regex=compiled,
    )


def extract_log_fields(line: str) -> tuple[str, str, str]:
    match = HEADER_REGEX.match(line)
    if match is None:
        return ("INFO", "unknown", line)
    return (match.group(1), match.group(2), match.group(3))


def match_single_rule(spec_text: str, severity: str, service: str, message: str) -> str | None:
    rule = _compile_rule(spec_text)
    if rule.allowed_levels and severity not in rule.allowed_levels:
        return None
    if rule.service_prefix and not service.startswith(rule.service_prefix):
        return None
    if rule.regex is not None and rule.regex.search(message) is None:
        return None
    return rule.channel


def route_log_batch(lines: list[str], rule_specs: list[str], fallback_channel: str = "general") -> list[RouteDecision]:
    normalized_fallback = normalize_channel_name(fallback_channel)
    compiled_rules = [_compile_rule(spec_text) for spec_text in rule_specs]
    header_match = HEADER_REGEX.match
    decisions: list[RouteDecision] = []
    for idx, line in enumerate(lines):
        m = header_match(line)
        if m is None:
            severity, service, message = "INFO", "unknown", line
        else:
            severity, service, message = m.group(1), m.group(2), m.group(3)
        chosen = normalized_fallback
        for rule in compiled_rules:
            if rule.allowed_levels and severity not in rule.allowed_levels:
                continue
            if rule.service_prefix and not service.startswith(rule.service_prefix):
                continue
            if rule.regex is not None and rule.regex.search(message) is None:
                continue
            chosen = rule.channel
            break
        decisions.append(RouteDecision(idx, chosen, severity, service))
    return decisions
