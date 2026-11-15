import unittest
from target import EventRecord, build_user_summaries, deduplicate_events_preserve_order


class TestEventDedup(unittest.TestCase):
    def test_preserve_order_and_tag_sequence(self) -> None:
        events = [
            EventRecord("e1", "u1", "view", 10, ("b", "a", "b")),
            EventRecord("e2", "u1", "click", 25, ("c", "a")),
            EventRecord("e1", "u1", "dup", 99, ("z",)),  # 重复 event_id 应忽略
            EventRecord("e3", "u2", "buy", 15, ("x",)),
            EventRecord("e4", "u1", "bad", -1, ("neg",)),  # 非法时间戳应忽略
            EventRecord("e5", "u1", "blk", 30, ("blk_tag",)),
        ]
        deduped = deduplicate_events_preserve_order(events, blacklist_ids=["e5"])
        self.assertEqual([e.event_id for e in deduped], ["e1", "e2", "e3"])

        summary = build_user_summaries(events, blacklist_ids=["e5"], tracked_users=["u1"])
        self.assertEqual(list(summary.keys()), ["u1"])
        self.assertEqual(summary["u1"]["count"], 2)
        self.assertEqual(summary["u1"]["last_ts"], 25)
        self.assertEqual(summary["u1"]["tags"], ["b", "a", "c"])


if __name__ == "__main__":
    unittest.main()
