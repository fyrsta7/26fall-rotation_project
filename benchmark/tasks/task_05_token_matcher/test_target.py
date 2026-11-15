import unittest
from target import count_term_in_document, scan_corpus_glossary


class TestTokenMatcher(unittest.TestCase):
    def test_word_boundary_and_phrases(self) -> None:
        docs = {
            "d1": "Cache miss, cache HIT! Memory-cache hit_rate is high; cache hit again.",
            "d2": "Nothing relevant here.",
        }
        terms = ["cache", "cache hit", "hit", "hit_rate", "empty   "]
        res = scan_corpus_glossary(docs, terms + ["   "])
        self.assertEqual(res["d1"]["cache"], 4)
        self.assertEqual(res["d1"]["cache hit"], 2)
        self.assertEqual(res["d1"]["hit"], 2)
        self.assertEqual(res["d1"]["hit_rate"], 1)
        self.assertNotIn("   ", res["d1"])
        self.assertEqual(res["d2"], {})

    def test_overlapping_phrase_occurrences(self) -> None:
        self.assertEqual(count_term_in_document("a a a a", "a a"), 3)
        self.assertEqual(count_term_in_document("a b", "a b c"), 0)


if __name__ == "__main__":
    unittest.main()
