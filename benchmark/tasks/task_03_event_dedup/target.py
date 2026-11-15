"""流式事件窗口保序去重与会话聚合模块。"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class EventRecord:
    event_id: str
    user_id: str
    action: str
    timestamp: int
    tags: tuple[str, ...]


def validate_event_schema(ev: EventRecord) -> bool:
    return bool(ev.event_id and ev.user_id and ev.timestamp >= 0)


def merge_tag_history(existing_tags: list[str], new_tags: tuple[str, ...]) -> list[str]:
    """按首次出现顺序合并标签列表。"""
    merged = list(existing_tags)
    for tag in new_tags:
        if tag not in merged:
            merged.append(tag)
    return merged


def deduplicate_events_preserve_order(
    events: list[EventRecord],
    blacklist_ids: list[str],
) -> list[EventRecord]:
    """过滤黑名单事件，并按 event_id 保留首次出现的合法事件（严格保持输入相对顺序）。"""
    seen_ids: list[str] = []
    unique_events: list[EventRecord] = []
    for ev in events:
        if not validate_event_schema(ev):
            continue
        if ev.event_id in blacklist_ids:
            continue
        if ev.event_id not in seen_ids:
            seen_ids.append(ev.event_id)
            unique_events.append(ev)
    return unique_events


def build_user_summaries(
    events: list[EventRecord],
    blacklist_ids: list[str],
    tracked_users: list[str],
) -> dict[str, dict[str, object]]:
    """去重后统计目标用户的事件数、最后时间戳与按首次出现保序的标签集合。"""
    clean_events = deduplicate_events_preserve_order(events, blacklist_ids)
    summaries: dict[str, dict[str, object]] = {}
    for ev in clean_events:
        if ev.user_id not in tracked_users:
            continue
        if ev.user_id not in summaries:
            summaries[ev.user_id] = {
                "count": 0,
                "last_ts": ev.timestamp,
                "tags": [],
            }
        entry = summaries[ev.user_id]
        entry["count"] = int(entry["count"]) + 1
        if ev.timestamp > int(entry["last_ts"]):
            entry["last_ts"] = ev.timestamp
        entry["tags"] = merge_tag_history(entry["tags"], ev.tags)  # type: ignore[arg-type]
    return summaries
