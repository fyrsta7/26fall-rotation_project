"""task_03_event_dedup 参考优化实现：用哈希集合替代列表线性查找，并利用 dict 保序特性合并用户标签。"""

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
    seen = dict.fromkeys(existing_tags)
    for tag in new_tags:
        seen[tag] = None
    return list(seen.keys())


def deduplicate_events_preserve_order(
    events: list[EventRecord],
    blacklist_ids: list[str],
) -> list[EventRecord]:
    blacklist_set = set(blacklist_ids)
    seen_ids: set[str] = set()
    unique_events: list[EventRecord] = []
    for ev in events:
        eid = ev.event_id
        if not eid or not ev.user_id or ev.timestamp < 0:
            continue
        if eid in blacklist_set or eid in seen_ids:
            continue
        seen_ids.add(eid)
        unique_events.append(ev)
    return unique_events


def build_user_summaries(
    events: list[EventRecord],
    blacklist_ids: list[str],
    tracked_users: list[str],
) -> dict[str, dict[str, object]]:
    clean_events = deduplicate_events_preserve_order(events, blacklist_ids)
    tracked_set = set(tracked_users)
    counts: dict[str, int] = {}
    last_ts: dict[str, int] = {}
    tag_maps: dict[str, dict[str, None]] = {}

    for ev in clean_events:
        uid = ev.user_id
        if uid not in tracked_set:
            continue
        if uid not in counts:
            counts[uid] = 1
            last_ts[uid] = ev.timestamp
            tag_maps[uid] = dict.fromkeys(ev.tags)
        else:
            counts[uid] += 1
            if ev.timestamp > last_ts[uid]:
                last_ts[uid] = ev.timestamp
            tmap = tag_maps[uid]
            for tag in ev.tags:
                tmap[tag] = None

    return {
        uid: {
            "count": counts[uid],
            "last_ts": last_ts[uid],
            "tags": list(tag_maps[uid].keys()),
        }
        for uid in counts
    }
