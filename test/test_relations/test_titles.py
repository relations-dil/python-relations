"""
Unittests for Titles
"""

import unittest
import unittest.mock

import ipaddress

import relations
import relations.unittest

class TitlesModel(relations.Model):
    SOURCE = "TestTitles"

class Unit(TitlesModel):
    id = int
    name = str, {"format": "fancy"}

class Test(TitlesModel):
    id = int
    unit_id = int
    name = str, {"format": "shmancy"}

relations.OneToMany(Unit, Test)

class Meta(TitlesModel):
    id = int
    name = str
    flag = bool
    stuff = list
    things = dict

    TITLES = "things__a__b__0____1"
    UNIQUE = False

def subnet_attr(values, value):

    values["address"] = str(value)
    min_ip = value[0]
    max_ip = value[-1]
    values["min_address"] = str(min_ip)
    values["min_value"] = int(min_ip)
    values["max_address"] = str(max_ip)
    values["max_value"] = int(max_ip)

class Net(TitlesModel):

    id = int
    name = str
    ip = ipaddress.IPv4Address, {"attr": {"compressed": "address", "__int__": "value"}, "init": "address", "titles": "address"}
    subnet = ipaddress.IPv4Network, {"attr": subnet_attr, "init": "address", "titles": "address"}

    TITLES = ["ip", "subnet__address"]
    UNIQUE = False

class TestTitles(unittest.TestCase):

    maxDiff = None

    def setUp(self):

        self.source = relations.unittest.MockSource("TestTitles")

        self.titles = relations.Titles(Unit.many())
        self.titles.ids = [1, 2, 3]
        self.titles.titles = {1: "people", 2: "stuff", 3: "things"}

    def tearDown(self):

        del relations.SOURCES["TestTitles"]

    def test___init__(self):

        Unit("people").create().test.add("stuff").add("things").create()

        titles = relations.Titles(Unit.many())

        self.assertEqual(titles.id, "id")
        self.assertEqual(titles.fields, ["name"])

        self.assertEqual(titles.parents, {})
        self.assertEqual(titles.format, ["fancy"])

        titles = relations.Titles(Test.many())

        self.assertEqual(titles.id, "id")
        self.assertEqual(titles.fields, ["unit_id", "name"])

        self.assertEqual(titles.parents["unit_id"].id, "id")
        self.assertEqual(titles.parents["unit_id"].fields, ["name"])
        self.assertEqual(titles.parents["unit_id"].parents, {})
        self.assertEqual(titles.parents["unit_id"].format, ["fancy"])

        self.assertEqual(titles.format, ["fancy", "shmancy"])

        titles = relations.Titles(Meta.many())
        self.assertEqual(titles.format, [None])

        titles = relations.Titles(Net.many())
        self.assertEqual(titles.format, [None, None])

    def test___len__(self):

        self.assertEqual(len(self.titles), 3)

    def test___contains__(self):

        self.assertIn(1, self.titles)

    def test___iter__(self):

        self.assertEqual(list(self.titles), [1, 2, 3])

    def test___setitem__(self):

        self.titles[1] = "persons"

        self.assertEqual(self.titles.ids, [1, 2, 3])
        self.assertEqual(self.titles.titles[1], "persons")

        self.titles[4] = "meta"

        self.assertEqual(self.titles.ids, [1, 2, 3, 4])
        self.assertEqual(self.titles.titles[4], "meta")

    def test___getitem__(self):

        self.assertEqual(self.titles[1], "people")

    def test___delitem__(self):

        del self.titles[2]

        self.assertEqual(self.titles.ids, [1, 3])
        self.assertEqual(self.titles.titles, {1: "people", 3: "things"})

    def test_add(self):

        titles = relations.Titles(Unit.many())

        titles.add(Unit("people").create())

        self.assertEqual(titles.ids, [1])
        self.assertEqual(titles.titles, {1: ["people"]})

        Unit.one(name="people").test.add("stuff").create()

        titles = relations.Titles(Test.many())

        titles.add(Test(unit_id=1, name="stuff").create())
        titles.add(Test(unit_id=2, name="things").create())

        self.assertEqual(titles.ids, [2, 3])
        self.assertEqual(titles.titles, {
            2: ["people", "stuff"],
            3: [None, "things"]
        })

        titles = relations.Titles(Meta.many())
        titles.add(Meta("special", things={"a":{"b": [{"1": "sure"}]}}).create())
        titles.add(Meta(things={"a":{"b": [{"1": "yep"}]}}).create())
        titles.add(Meta(things={}).create())

        self.assertEqual(titles.ids, [1, 2, 3])
        self.assertEqual(titles.titles, {
            1: ["sure"],
            2: ["yep"],
            3: [None]
        })

        titles = relations.Titles(Net.many())
        titles.add(Net("special", ip="1.2.3.4").create())
        titles.add(Net("special", subnet="1.2.3.0/24").create())

        self.assertEqual(titles.ids, [1, 2])
        self.assertEqual(titles.titles, {
            1: ["1.2.3.4", None],
            2: [None, "1.2.3.0/24"]
        })
