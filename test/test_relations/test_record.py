import unittest
import unittest.mock

import ipaddress

import relations

class TestRecordError(unittest.TestCase):

    maxDiff = None

    def test___init__(self):

        error = relations.RecordError("unittest", "oops")

        self.assertEqual(error.record, "unittest")
        self.assertEqual(error.message, "oops")

class TestRecord(unittest.TestCase):

    maxDiff = None

    def setUp(self):

        self.source = unittest.mock.MagicMock()

        self.record = relations.Record()

        self.id = relations.Field(int, name="id", store="_id")
        self.name = relations.Field(str, name="name", store="_name")

        self.record.append(self.id)
        self.record.append(self.name)

    def test___init__(self):

        record = relations.Record()

        self.assertEqual(record._order, [])
        self.assertEqual(record._names, {})

    def test_insert(self):

        record = relations.Record()

        id = relations.Field(int, name="id", store="_id")
        record.insert(0, id)
        self.assertEqual(record._order, [id])
        self.assertEqual(record._names, {"id": id})

        name = relations.Field(str, name="name", store="_name")
        record.insert(0, name)
        self.assertEqual(record._order, [name, id])
        self.assertEqual(record._names, {"id": id, "name": name})

    def test_append(self):

        record = relations.Record()

        id = relations.Field(int, name="id", store="_id")
        record.append(id)
        self.assertEqual(record._order, [id])
        self.assertEqual(record._names, {"id": id})

        name = relations.Field(str, name="name", store="_name")
        record.append(name)
        self.assertEqual(record._order, [id, name])
        self.assertEqual(record._names, {"id": id, "name": name})

    def test___setattr__(self):

        self.record.id = "1"
        self.assertEqual(self.id.value, 1)

        self.things = relations.Field(dict, name="things", store="_things", default=dict)
        self.record.append(self.things)
        self.record.things__a__b__0___1 = "yep"
        self.assertEqual(self.things.value, {"a":{"b": [{"1": "yep"}]}})

    def test___getattr__(self):

        self.id.value = "1"
        self.assertEqual(self.record.id, 1)

        self.things = relations.Field(dict, name="things", store="_things", default=dict)
        self.record.append(self.things)
        self.things.value = {"a":{"b": [{"1": "yep"}]}}
        self.assertEqual(self.record.things__a__b__0___1, "yep")

        def nope():
            self.record.nope

        self.assertRaisesRegex(AttributeError, "has no attribute 'nope'", nope)

    def test___len__(self):

        self.assertEqual(len(self.record), 2)

    def test___iter__(self):

        self.assertEqual(list(self.record), ["id", "name"])

    def test_keys(self):

        self.record.id = 1
        self.record.name = "ya"

        self.assertEqual(dict(self.record), {"id": 1, "name": "ya"})

    def test___contains__(self):

        self.assertIn(1, self.record)
        self.assertNotIn(2, self.record)

        self.assertIn("id", self.record)
        self.assertNotIn("nope", self.record)

    def test___setitem__(self):

        self.record[0] = "1"
        self.record["name"] = "unit"
        self.assertEqual(self.id.value, 1)
        self.assertEqual(self.name.value, "unit")

        self.things = relations.Field(dict, name="things", store="_things", default=dict)
        self.record.append(self.things)
        self.record['things__a__b__0___1'] = "yep"
        self.assertEqual(self.things.value, {"a":{"b": [{"1": "yep"}]}})

        def nope():
            self.record['nope'] = 1

        self.assertRaisesRegex(relations.RecordError, "unknown field 'nope'", nope)

    def test___getitem__(self):

        self.id.value = "1"
        self.assertEqual(self.record[0], 1)
        self.assertEqual(self.record['id'], 1)

        self.things = relations.Field(dict, name="things", store="_things", default=dict)
        self.record.append(self.things)
        self.things.value = {"a":{"b": [{"1": "yep"}]}}
        self.assertEqual(self.record["things__a__b__0___1"], "yep")

        def nope():
            self.record['nope']

        self.assertRaisesRegex(relations.RecordError, "unknown field 'nope'", nope)

    def test_define(self):

        self.assertEqual(self.record.define(), [
            {
                "name": "id",
                "kind": "int",
                "store": "_id",
                "none": True
            },
            {
                "name": "name",
                "kind": "str",
                "store": "_name",
                "none": True
            }
        ])

    def test_filter(self):

        self.meta = relations.Field(dict, name="meta")
        self.record.append(self.meta)

        self.record.filter(0, "0")
        self.assertEqual(self.id.criteria["eq"], 0)

        self.record.filter("id", "1")
        self.assertEqual(self.id.criteria["eq"], 1)

        self.record.filter("id__ne", "2")
        self.assertEqual(self.id.criteria["ne"], {2})

        self.record.filter("meta__a__ne", 2)
        self.assertEqual(self.meta.criteria["a__ne"], {2})

        self.assertRaisesRegex(relations.RecordError, "unknown criterion 'nope'", self.record.filter, "nope", 0)

    def test_export(self):

        self.things = relations.Field(dict, name="things", store="_things", default=dict)
        self.push = relations.Field(str, name="push", inject="things__a__b__0___1")
        self.ip = relations.Field(ipaddress.IPv4Address, name="ip", attr={"compressed": "address", "__int__": "value"})

        self.record.append(self.things)
        self.record.append(self.push)
        self.record.append(self.ip)

        self.record.read({"_id": 1, "_name": "unit", "_things": {"a":{"b": [{"1": "yep"}]}}, "ip": "1.2.3.4"})

        self.assertEqual(self.record.export(), {
            "id": 1,
            "name": "unit",
            "things": {"a":{"b": [{"1": "yep"}]}},
            "push": "yep",
            "ip": {
                "address": "1.2.3.4",
                "value": 16909060
            }
        })

    def test_create(self):

        self.things = relations.Field(dict, name="things", store="_things", default=dict)
        self.push = relations.Field(str, name="push", inject="things__a__b__0___1")

        self.record.append(self.things)
        self.record.append(self.push)

        self.record.id = 1
        self.record.name = "unit"
        self.record.things = {}
        self.record.push = "yep"

        self.assertEqual(self.record.create({}), {"_id": 1, "_name": "unit", "_things": {"a":{"b": [{"1": "yep"}]}}})

    def test_retrieve(self):

        self.record.filter("id", "1")
        self.record.filter("name", "unit")

        self.assertTrue(self.record.retrieve({"_id": 1, "_name": "unit"}))
        self.assertFalse(self.record.retrieve({"_id": 2, "_name": "unit"}))
        self.assertFalse(self.record.retrieve({"_id": 1, "_name": "test"}))

    def test_like(self):

        self.things = relations.Field(dict, name="things", store="_things", default=dict)
        self.record.append(self.things)

        self.assertTrue(self.record.like({"_id": 1, "_name": "test"}, ["id", "name"], "unit", {'_id': [1]}))
        self.assertTrue(self.record.like({"_id": 2, "_name": "unit"}, ["id", "name"], "unit", {'_id': [1]}))
        self.assertFalse(self.record.like({"_id": 2, "_name": "test"}, ["id", "name"], "unit", {'_id': [1]}))

        self.assertTrue(self.record.like({"_id": 1, "_name": "unit", "_things": {"a":{"b": [{"1": "yep"}]}}}, ["things__a__b__0___1"], "y", {'things': [1]}))
        self.assertFalse(self.record.like({"_id": 1, "_name": "unit", "_things": {"a":{"b": [{"1": "yep"}]}}}, ["things__a__b__0___1"], "n", {'things': [1]}))

    def test_read(self):

        self.things = relations.Field(dict, name="things", store="_things", default=dict)
        self.push = relations.Field(str, name="push", inject="things__a__b__0___1")

        self.record.append(self.things)
        self.record.append(self.push)

        self.record.read({"_id": 1, "_name": "unit", "_things": {"a":{"b": [{"1": "yep"}]}}})

        self.assertEqual(self.record.id, 1)
        self.assertEqual(self.record.name, "unit")
        self.assertEqual(self.record.things, {"a":{"b": [{"1": "yep"}]}})
        self.assertEqual(self.record.push, "yep")

    def test_update(self):

        self.things = relations.Field(dict, name="things", store="_things", default=dict)
        self.push = relations.Field(str, name="push", inject="things__a__b__0___1")

        self.record.append(self.things)
        self.record.append(self.push)

        self.assertEqual(self.record.update({}), {})

        self.record.id = 1
        self.record.name = "unit"
        self.record.things = {}
        self.record.push = "yep"

        self.things.original = {}

        self.assertEqual(self.record.update({}), {"_id": 1, "_name": "unit", "_things": {"a":{"b": [{"1": "yep"}]}}})

    def test_mass(self):

        self.things = relations.Field(dict, name="things", store="_things", default=dict)
        self.push = relations.Field(str, name="push", inject="things__a__b__0___1")

        self.record.append(self.things)
        self.record.append(self.push)

        self.assertEqual(self.record.mass({}), {})

        self.record.id = 1
        self.record.name = "unit"

        self.assertEqual(self.record.mass({}), {"_id": 1, "_name": "unit"})

        self.record.things = {}
        self.record.push = "yep"

        self.things.changed = False

        self.assertRaisesRegex(relations.FieldError, "no mass update with inject", self.record.mass, {})
