import unittest

from headerlib import merge_headers


class MergeHeadersTests(unittest.TestCase):
    def test_empty_input(self):
        self.assertEqual(merge_headers([]), [])

    def test_single_header(self):
        self.assertEqual(merge_headers([("Content-Type", "text/plain")]), [("Content-Type", "text/plain")])

    def test_duplicate_exact_name_values_are_combined(self):
        self.assertEqual(merge_headers([("X-Trace", "a"), ("X-Trace", "b")]), [("X-Trace", "a, b")])

    def test_duplicate_names_are_case_insensitive_and_keep_first_spelling(self):
        self.assertEqual(merge_headers([("X-Trace", "a"), ("x-trace", "b")]), [("X-Trace", "a, b")])

    def test_first_seen_order_is_preserved(self):
        self.assertEqual(merge_headers([("X-A", "1"), ("X-B", "2"), ("x-a", "3")]), [("X-A", "1, 3"), ("X-B", "2")])

    def test_input_is_not_mutated(self):
        source = [("X-Trace", "a"), ("x-trace", "b")]
        before = source.copy()
        merge_headers(source)
        self.assertEqual(source, before)


if __name__ == "__main__":
    unittest.main()
