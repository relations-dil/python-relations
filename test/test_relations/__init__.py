import unittest
import unittest.mock

import sys

import relations

class Base(relations.Model):
    pass

class PeanutButter(Base):
    id = int
    jelly_id = set

class Jelly(Base):
    id = int
    peanut_butter_id = set

class PeanutButterJelly(Base):
    peanut_butter_id = int
    jelly_id = set

relations.ManyToMany(PeanutButter, Jelly, PeanutButterJelly)

class Special(Base):
    id = int

class Time(Special):
    id = int

class TestRelations(unittest.TestCase):

    maxDiff = None

    def test_index(self):

        self.assertTrue(relations.INDEX.match("0"))
        self.assertTrue(relations.INDEX.match("-1"))
        self.assertFalse(relations.INDEX.match("nope"))

    def test_dns(self):

        for name in ["a", "A", "0", "a-b", "relations-restx", "TestModel", "a" * 63]:
            self.assertTrue(relations.DNS.match(name), name)

        for name in ["", "_", "a_b", "-ab", "ab-", "a b", "a.b", "ab\n", "a" * 64]:
            self.assertFalse(relations.DNS.match(name), name)

    @unittest.mock.patch("relations.SOURCES", {})
    def test_register(self):

        source = unittest.mock.MagicMock()
        source.name = "a"

        relations.register(source)

        self.assertEqual(relations.SOURCES, {"a": source})

        # Names have to be dns compliant

        for name in [None, 1, "", "a_b", "-ab", "ab-", "a b", "a.b", "a" * 64]:

            nope = unittest.mock.MagicMock()
            nope.name = name

            self.assertRaisesRegex(relations.SourceError, f"source {name} is not dns compliant", relations.register, nope)

        self.assertEqual(relations.SOURCES, {"a": source})

    @unittest.mock.patch("relations.SOURCES", {})
    def test_source(self):

        source = unittest.mock.MagicMock()

        relations.SOURCES["a"] = source

        self.assertEqual(relations.source("a"), source)

    def test_models(self):

        # returns with class

        module = sys.modules[__name__]
        models = relations.models(module, from_base=Base)
        self.assertEqual(len(models), 5)
        self.assertIn(PeanutButter, models)
        self.assertIn(Jelly, models)
        self.assertIn(PeanutButterJelly, models)
        self.assertIn(Special, models)

        # from base

        models = relations.models(module, from_base=Special)
        self.assertEqual(len(models), 1)
        self.assertNotIn(PeanutButter, models)
        self.assertNotIn(Jelly, models)
        self.assertIn(Time, models)
