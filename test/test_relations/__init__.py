import unittest
import unittest.mock

import sys

import relations

class PeanutButter(relations.Model):
    pass

class Jelly(relations.Model):
    pass

class Time(Jelly):
    pass


class TestRelations(unittest.TestCase):

    maxDiff = None

    def test_index(self):

        self.assertTrue(relations.INDEX.match("0"))
        self.assertTrue(relations.INDEX.match("-1"))
        self.assertFalse(relations.INDEX.match("nope"))

    @unittest.mock.patch("relations.SOURCES", {})
    def test_register(self):

        source = unittest.mock.MagicMock()
        source.name = "a"

        relations.register(source)

        self.assertEqual(relations.SOURCES, {"a": source})

    @unittest.mock.patch("relations.SOURCES", {})
    def test_source(self):

        source = unittest.mock.MagicMock()

        relations.SOURCES["a"] = source

        self.assertEqual(relations.source("a"), source)

    def test_models(self):

        # returns with class

        module = sys.modules[__name__]
        models = relations.models(module)
        self.assertEqual(len(models), 3)
        self.assertIn(PeanutButter, models)
        self.assertIn(Jelly, models)
        self.assertIn(Time, models)

        # from base

        models = relations.models(module, from_base=Jelly)
        self.assertEqual(len(models), 1)
        self.assertNotIn(PeanutButter, models)
        self.assertNotIn(Jelly, models)
        self.assertIn(Time, models)
