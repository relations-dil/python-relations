"""
Unittests for Labels
"""

import unittest
import unittest.mock

import ipaddress

import relations
import relations.unittest

class LabelsModel(relations.Model):
    SOURCE = "TestLabels"

class Unit(LabelsModel):
    id = int
    name = str, {"format": "fancy"}

class Test(LabelsModel):
    id = int
    unit_id = int
    name = str, {"format": "shmancy"}

relations.OneToMany(Unit, Test)

class Meta(LabelsModel):
    id = int
    name = str
    flag = bool
    stuff = list
    things = dict

    LABEL = "things__a__b__0___1"
    UNIQUE = False

def subnet_attr(value):

    values = {}

    values["address"] = str(value)
    min_ip = value[0]
    max_ip = value[-1]
    values["min_address"] = str(min_ip)
    values["min_value"] = int(min_ip)
    values["max_address"] = str(max_ip)
    values["max_value"] = int(max_ip)

    return values

class Net(LabelsModel):

    id = int
    name = str
    ip = ipaddress.IPv4Address, {"attr": {"compressed": "address", "__int__": "value"}, "init": "address", "label": "address"}
    subnet = ipaddress.IPv4Network, {"attr": subnet_attr, "init": "address", "label": "address"}

    LABEL = "ip__address"
    UNIQUE = False

class TestLabels(unittest.TestCase):

    maxDiff = None

    def setUp(self):

        self.source = relations.unittest.MockSource("TestLabels")

        self.labels = relations.Labels(Unit.many())
        self.labels.ids = [1, 2, 3]
        self.labels.labels = {1: "people", 2: "stuff", 3: "things"}

    def tearDown(self):

        del relations.SOURCES["TestLabels"]

    def test___init__(self):

        Unit("people").create().test.add("stuff").add("things").create()

        labels = relations.Labels(Unit.many())

        self.assertEqual(labels.id, "id")
        self.assertEqual(labels.label, ["name"])

        self.assertEqual(labels.parents, {})
        self.assertEqual(labels.format, ["fancy"])

        labels = relations.Labels(Test.many())

        self.assertEqual(labels.id, "id")
        self.assertEqual(labels.label, ["unit_id", "name"])

        self.assertEqual(labels.parents["unit_id"].id, "id")
        self.assertEqual(labels.parents["unit_id"].label, ["name"])
        self.assertEqual(labels.parents["unit_id"].parents, {})
        self.assertEqual(labels.parents["unit_id"].format, ["fancy"])

        self.assertEqual(labels.format, ["fancy", "shmancy"])

    def test___len__(self):

        self.assertEqual(len(self.labels), 3)

    def test___contains__(self):

        self.assertIn(1, self.labels)

    def test___iter__(self):

        self.assertEqual(list(self.labels), [1, 2, 3])

    def test___setitem__(self):

        self.labels[1] = "persons"

        self.assertEqual(self.labels.ids, [1, 2, 3])
        self.assertEqual(self.labels.labels[1], "persons")

        self.labels[4] = "meta"

        self.assertEqual(self.labels.ids, [1, 2, 3, 4])
        self.assertEqual(self.labels.labels[4], "meta")

    def test___getitem__(self):

        self.assertEqual(self.labels[1], "people")

    def test___delitem__(self):

        del self.labels[2]

        self.assertEqual(self.labels.ids, [1, 3])
        self.assertEqual(self.labels.labels, {1: "people", 3: "things"})

    def test_add(self):

        labels = relations.Labels(Unit.many())

        labels.add({"id": 1, "name": "people"})

        self.assertEqual(labels.ids, [1])
        self.assertEqual(labels.labels, {1: ["people"]})

        Unit("people").create().test.add("stuff").create()

        labels = relations.Labels(Test.many())

        labels.add({"id": 1, "unit_id": 1, "name": "stuff"})
        labels.add({"id": 2, "unit_id": 2, "name": "things"})

        self.assertEqual(labels.ids, [1, 2])
        self.assertEqual(labels.labels, {
            1: ["people", "stuff"],
            2: [None, "things"]
        })

        labels = relations.Labels(Meta.many())
        labels.add(Meta("special", things={"a":{"b": [{"1": "sure"}]}}).create())
        labels.add({"id": 2, "things": {"a":{"b": [{"1": "yep"}]}}})
        labels.add({"id": 3, "things": {}})

        self.assertEqual(labels.ids, [1, 2, 3])
        self.assertEqual(labels.labels, {
            1: ["sure"],
            2: ["yep"],
            3: [None]
        })

        labels = relations.Labels(Net.many())
        labels.add(Net("special", ip="1.2.3.4").create())

        self.assertEqual(labels.ids, [1])
        self.assertEqual(labels.labels, {
            1: ["1.2.3.4"]
        })
