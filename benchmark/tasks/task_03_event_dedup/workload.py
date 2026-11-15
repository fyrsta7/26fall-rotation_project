"""task_03_event_dedup 性能负载驱动。"""

import random
from target import EventRecord, build_user_summaries


def build_inputs(seed: int = 19) -> tuple[list[EventRecord], list[str], list[str]]:
    rng = random.Random(seed)
    tag_vocab = [f"tag_{i:03d}" for i in range(180)]
    users = [f"user_{i:04d}" for i in range(900)]
    event_pool = [f"evt_{i:05d}" for i in range(4500)]

    events: list[EventRecord] = []
    for step in range(8500):
        eid = event_pool[rng.randrange(len(event_pool))]
        uid = users[rng.randrange(len(users))]
        tags = tuple(tag_vocab[rng.randrange(len(tag_vocab))] for _ in range(4))
        events.append(
            EventRecord(
                event_id=eid,
                user_id=uid,
                action="click",
                timestamp=1_700_000_000 + step,
                tags=tags,
            )
        )
    blacklist = [f"evt_{i:05d}" for i in range(0, 4500, 3)]
    tracked_users = users[:650]
    return events, blacklist, tracked_users


def run_workload(inputs: tuple[list[EventRecord], list[str], list[str]]) -> tuple[int, int]:
    events, blacklist, tracked_users = inputs
    summaries = build_user_summaries(events, blacklist, tracked_users)
    total_count = sum(int(v["count"]) for v in summaries.values())
    total_tags = sum(len(v["tags"]) for v in summaries.values())  # type: ignore[arg-type]
    return len(summaries), total_count + total_tags
