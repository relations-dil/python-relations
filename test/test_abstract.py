import unittest
import unittest.mock

import relations.abstract

class TestAbstract(unittest.TestCase):

    maxDiff = None

    @unittest.mock.patch("relations.abstract.SOURCES", {})
    def test_register(self):

        relations.abstract.register("a", 1)

        self.assertEqual(relations.abstract.SOURCES, {"a": 1})

    @unittest.mock.patch("relations.abstract.SOURCES", {})
    def test_access(self):

        relations.abstract.SOURCES["a"] = 1

        self.assertEqual(relations.abstract.access("a"), 1)
