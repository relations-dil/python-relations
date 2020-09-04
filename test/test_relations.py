import unittest
import unittest.mock

import relations

class TestSource(unittest.TestCase):

    maxDiff = None

    @unittest.mock.patch("relations.SOURCES", {})
    def test_Source(self):

        source = relations.Source("a")

        self.assertEqual(relations.SOURCES, {"a": source})

    @unittest.mock.patch("relations.SOURCES", {})
    def test_access(self):

        source = relations.Source("a")

        self.assertEqual(relations.a, source)
