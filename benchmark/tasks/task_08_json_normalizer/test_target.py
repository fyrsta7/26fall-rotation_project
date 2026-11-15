import unittest
from target import canonicalize_node, compute_payload_digests


class TestJsonNormalizer(unittest.TestCase):
    def test_canonical_semantics_and_escaping(self) -> None:
        obj1 = {
            "b": [True, False, None, -0.0, 3.5],
            "a": 'hello "world"\nline\\2',
            "empty": None,
        }
        obj2 = {
            "a": 'hello "world"\nline\\2',
            "b": (True, False, None, 0.0, 3.5),
        }
        self.assertEqual(
            canonicalize_node(obj1, drop_null_fields=True),
            canonicalize_node(obj2, drop_null_fields=True),
        )
        self.assertNotEqual(
            canonicalize_node(obj1, drop_null_fields=False),
            canonicalize_node(obj2, drop_null_fields=False),
        )
        d = compute_payload_digests([obj1, obj2], drop_null_fields=True)
        self.assertEqual(d[0], d[1])

    def test_bool_is_not_serialized_as_int(self) -> None:
        self.assertEqual(canonicalize_node({"flag": True, "num": 1}), '{"flag":true,"num":1}')

    def test_unsupported_type_raises(self) -> None:
        with self.assertRaises(TypeError):
            canonicalize_node({"bad": {1, 2, 3}})


if __name__ == "__main__":
    unittest.main()
