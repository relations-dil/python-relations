"""
Unittests for Field
"""

import unittest
import unittest.mock

import ipaddress

import relations

class TestFieldError(unittest.TestCase):

    maxDiff = None

    def test___init__(self):

        error = relations.FieldError("unittest", "oops")

        self.assertEqual(error.field, "unittest")
        self.assertEqual(error.message, "oops")

class TestField(unittest.TestCase):

    maxDiff = None

    def setUp(self):

        self.source = unittest.mock.MagicMock()
        relations.SOURCES["TestField"] = self.source
        self.field = relations.Field(int)
        self.field._source = "TestField"

    def tearDown(self):

        del relations.SOURCES["TestField"]

    def test___init__(self):

        field = relations.Field(int, unit="test")
        self.assertEqual(field.kind, int)
        self.assertEqual(field.unit, "test")
        self.assertTrue(field.none)
        self.assertIsNone(field._none)
        self.assertIsNone(field.attr)
        self.assertIsNone(field.init)
        self.assertIsNone(field.titles)
        self.assertEqual(field.format, None)

        field = relations.Field(int, {"unit": "test"})
        self.assertEqual(field.kind, int)
        self.assertEqual(field.unit, "test")
        self.assertTrue(field.none)

        field = relations.Field(int, False)
        self.assertEqual(field.kind, int)
        self.assertFalse(field.none)

        field = relations.Field(int, 0)
        self.assertEqual(field.kind, int)
        self.assertEqual(field.default, 0)
        self.assertFalse(field.none)

        field = relations.Field(list)
        self.assertEqual(field.kind, list)
        self.assertEqual(field.default, list)
        self.assertFalse(field.none)

        field = relations.Field(dict)
        self.assertEqual(field.kind, dict)
        self.assertEqual(field.default, dict)
        self.assertFalse(field.none)

        field = relations.Field(int, options=[])
        self.assertEqual(field.kind, int)
        self.assertFalse(field.none)

        field = relations.Field(int, validation="yep")
        self.assertEqual(field.kind, int)
        self.assertFalse(field.none)

        field = relations.Field(ipaddress.IPv4Address, attr="compressed")
        self.assertEqual(field.kind, ipaddress.IPv4Address)
        self.assertTrue(field.none)
        self.assertEqual(field.attr, {"compressed": "compressed"})
        self.assertEqual(field.init, {"compressed": "compressed"})
        self.assertEqual(field.titles, ["compressed"])
        self.assertEqual(field.format, [None])

        field = relations.Field(ipaddress.IPv4Address, attr="compressed", init="exploded", titles="packed")
        self.assertEqual(field.kind, ipaddress.IPv4Address)
        self.assertTrue(field.none)
        self.assertEqual(field.attr, {"compressed": "compressed"})
        self.assertEqual(field.init, {"exploded": "exploded"})
        self.assertEqual(field.titles, ["packed"])

        field = relations.Field(str, extract="field__from")
        self.assertEqual(field.kind, str)
        self.assertIsNone(field.default)
        self.assertEqual(field.extract, {"field__from": str})

        self.assertRaisesRegex(relations.FieldError, "1 default not <class 'str'> for opt", relations.Field, str, name="opt", default=1)
        self.assertRaisesRegex(relations.FieldError, "1 option not <class 'str'> for opt", relations.Field, str, name="opt", options=[1])
        self.assertRaisesRegex(relations.FieldError, "1 validation not regex or method for val", relations.Field, str, name="val", validation=1)
        self.assertRaisesRegex(relations.FieldError, "IPv4Address requires at least attr", relations.Field, ipaddress.IPv4Address)

    def test___setattr__(self):

        field = relations.Field(int)
        field.name = "id"
        self.assertEqual(field.kind, int)
        self.assertEqual(field.name, "id")
        self.assertEqual(field.store, "id")

        # Store override

        field = relations.Field(int, store="_id")
        field.name = "id"
        self.assertEqual(field.name, "id")
        self.assertEqual(field.store, "_id")

        def rename(name):
            field.name = name

        self.assertRaisesRegex(relations.FieldError, "field name 'define' is reserved - use the store attribute for this name", rename, 'define')
        self.assertRaisesRegex(relations.FieldError, "field name 'def__ine' cannot contain '__' - use the store attribute for this name", rename, 'def__ine')
        self.assertRaisesRegex(relations.FieldError, "field name '_define' cannot start with '_' - use the store attribute for this name", rename, '_define')

        field.value = "1"
        self.assertEqual(field.value, 1)
        self.assertTrue(field.changed)

        field.value = None
        self.assertIsNone(field.value)

    def test_define(self):

        field = relations.Field(int, name="test", default=False)
        self.assertEqual(field.define(), {
            "kind": 'int',
            "name": "test",
            "store": "test",
            "none": False,
            "default": False
        })

        field = relations.Field(int, name="test", default=int)
        self.assertEqual(field.define(), {
            "kind": 'int',
            "name": "test",
            "store": "test",
            "none": False
        })

        field = relations.Field(dict, name='grab', extract={
            "a__b__0___1": bool,
            "c__b__0___1": int,
            "c__d__0___1": float,
            "c__d__1___1": str,
            "c__d__1___2": list
        })
        self.assertEqual(field.define(), {
            "kind": 'dict',
            "name": "grab",
            "store": "grab",
            "none": False,
            "extract": {
                "a__b__0___1": 'bool',
                "c__b__0___1": 'int',
                "c__d__0___1": 'float',
                "c__d__1___1": 'str',
                "c__d__1___2": 'list'
            }
        })

    def test_valid(self):

        field = relations.Field(int, name="id", none=False)
        self.assertEqual(field.valid("1"), 1)
        self.assertRaisesRegex(relations.FieldError, "None not allowed for id", field.valid, None)

        field = relations.Field(ipaddress.IPv4Address, store="ip", attr={"compressed": "address"}, init="address")
        self.assertEqual(field.valid({"address": '1.2.3.4'}).compressed, '1.2.3.4')

        field = relations.Field(ipaddress.IPv4Address, store="ip", attr={"compressed": "address"}, init="address")
        self.assertEqual(field.valid('1.2.3.4').compressed, '1.2.3.4')

        field = relations.Field(ipaddress.IPv4Address, attr={"compressed": "ip__address", "__int__": "ip__value"}, init={"address": "ip__address"})
        self.assertEqual(field.valid({"ip": {"address": '1.2.3.4'}}).compressed, '1.2.3.4')

        field = relations.Field(ipaddress.IPv4Address, store="ip", attr={"compressed": "address"}, init="address")
        self.assertIsNone(field.valid(None))

        def slurp(value):

            return ipaddress.IPv4Network(value["addy"])

        field = relations.Field(ipaddress.IPv4Network, store="subnet", attr={"compressed": "address"}, init=slurp)
        field.read({"subnet": {"addy": '1.2.3.0/24'}})
        self.assertEqual(str(field.value), '1.2.3.0/24')
        self.assertEqual(field.original, {"address": "1.2.3.0/24"})

        field = relations.Field(int, name="id", options=[1])
        self.assertEqual(field.valid("1"), 1)
        self.assertRaisesRegex(relations.FieldError, "2 not in \[1\] for id", field.valid, 2)

        field = relations.Field(set, name="id", options=[1])
        self.assertEqual(field.valid({1}), {1})
        self.assertRaisesRegex(relations.FieldError, "2 not in \[1\] for id", field.valid, {2})

        field = relations.Field(str, name="name", validation="yep")
        self.assertEqual(field.valid("yepyep"), "yepyep")
        self.assertRaisesRegex(relations.FieldError, "nope doesn't match yep for name", field.valid, "nope")

        def yeppers(value):
            return "yep" in value

        field = relations.Field(str, name="name", validation=yeppers)
        self.assertEqual(field.valid("yepyep"), "yepyep")
        self.assertRaisesRegex(relations.FieldError, "nope invalid for name", field.valid, "nope")

    def test_filter(self):

        field = relations.Field(int)

        field.filter("1")
        self.assertEqual(field.criteria["eq"], 1)

        field.filter("1", "eq")
        self.assertEqual(field.criteria["eq"], 1)

        field.filter("1", "not_eq")
        self.assertEqual(field.criteria["not_eq"], 1)

        field.filter(None)
        self.assertEqual(field.criteria["null"], True)

        field.filter("true", "null")
        self.assertEqual(field.criteria["null"], True)

        field.filter("true", "not_null")
        self.assertEqual(field.criteria["not_null"], True)

        field.filter("false", "null")
        self.assertEqual(field.criteria["null"], False)

        field.filter("no", "null")
        self.assertEqual(field.criteria["null"], False)

        field.filter("0", "null")
        self.assertEqual(field.criteria["null"], False)

        field.filter(0, "null")
        self.assertEqual(field.criteria["null"], False)

        field.filter(False, "null")
        self.assertEqual(field.criteria["null"], False)

        field.filter("1", "gt")
        self.assertEqual(field.criteria["gt"], 1)

        field.filter("1", "not_gt")
        self.assertEqual(field.criteria["not_gt"], 1)

        field.filter("1", "gte")
        self.assertEqual(field.criteria["gte"], 1)

        field.filter("1", "lt")
        self.assertEqual(field.criteria["lt"], 1)

        field.filter("1", "lte")
        self.assertEqual(field.criteria["lte"], 1)

        field.filter("1", "like")
        self.assertEqual(field.criteria["like"], 1)

        field.filter("1", "start")
        self.assertEqual(field.criteria["start"], 1)

        field.filter("1", "end")
        self.assertEqual(field.criteria["end"], 1)

        field.filter("1", "in")
        self.assertEqual(field.criteria["in"], [1])
        field.filter(2.0, "in")
        self.assertEqual(field.criteria["in"], [1, 2])

        field = relations.Field(list)
        field.filter("1", "has")
        self.assertEqual(field.criteria["has"], ["1"])
        field.filter("2", "has")
        self.assertEqual(field.criteria["has"], ["1", "2"])

        field.filter("1", "any")
        self.assertEqual(field.criteria["any"], ["1"])
        field.filter("2", "any")
        self.assertEqual(field.criteria["any"], ["1", "2"])

        field.filter("1", "all")
        self.assertEqual(field.criteria["all"], ["1"])
        field.filter("2", "all")
        self.assertEqual(field.criteria["all"], ["1", "2"])

        field = relations.Field(dict)
        field.filter("1", "a")
        self.assertEqual(field.criteria["a__eq"], "1")

        field = relations.Field(dict)
        field.filter("1", "a__in")
        self.assertEqual(field.criteria["a__in"], ["1"])

        field = relations.Field(int)
        self.assertRaisesRegex(relations.FieldError, "no path \['nope'\] with kind int", field.filter, 0, "nope")

    def test_export(self):

        field = relations.Field(int)
        field.value = 1
        self.assertEqual(field.export(), 1)

        field = relations.Field(set)
        field.value = {"people", "stuff", "things"}
        self.assertEqual(field.export(), ["people", "stuff", "things"])

        field.options = ["stuff", "people", "things"]
        field.value = {"people", "stuff"}
        self.assertEqual(field.export(), ["stuff", "people"])

        field = relations.Field(dict)
        field.value = {"a": 1}
        value = field.export()
        self.assertEqual(value, {"a": 1})
        value["a"] = 2
        self.assertEqual(field.export(), {"a": 1})

        field = relations.Field(ipaddress.IPv4Address, attr={"compressed": "ip__address", "__int__": "ip__value"})
        field.value = "1.2.3.4"
        self.assertEqual(field.export(), {
            "ip": {
                "address": "1.2.3.4",
                "value": 16909060
            }
        })

        def hurl(values, value):

            values["address"] = str(value)
            min_ip = value[0]
            max_ip = value[-1]
            values["min_address"] = str(min_ip)
            values["min_value"] = int(min_ip)
            values["max_address"] = str(max_ip)
            values["max_value"] = int(max_ip)

        field = relations.Field(ipaddress.IPv4Network, attr=hurl, init="address", titles="address")
        field.value = '1.2.3.0/24'
        self.assertEqual(field.export(), {
            "address": "1.2.3.0/24",
            "min_address": "1.2.3.0",
            "min_value": 16909056,
            "max_address": "1.2.3.255",
            "max_value": 16909311
        })

    def test_apply(self):

        field = relations.Field(int)
        field.value = 1
        self.assertRaisesRegex(relations.FieldError, "no apply for int", field.apply, 0, 0)

        field = relations.Field(ipaddress.IPv4Address, attr={"compressed": "ip__address", "__int__": "ip__value"}, init={"address": "ip__address"})
        field.apply("ip__address", "1.2.3.4")
        self.assertEqual(field.access("ip__address"), "1.2.3.4")

    def test_access(self):

        field = relations.Field(int)
        field.value = 1
        self.assertRaisesRegex(relations.FieldError, "no access for int", field.access, 0)

        field = relations.Field(ipaddress.IPv4Address, attr={"compressed": "ip__address", "__int__": "ip__value"})
        field.value = "1.2.3.4"
        self.assertEqual(field.access("ip__address"), "1.2.3.4")

    def test_delta(self):

        field = relations.Field(int)
        field.original = 0
        field.value = 1
        self.assertTrue(field.delta())

        field.value = "0"
        self.assertFalse(field.delta())

        field = relations.Field(ipaddress.IPv4Address, attr={"compressed": "ip__address", "__int__": "ip__value"})
        field.value = "1.2.3.4"
        self.assertTrue(field.delta())

        field.original = field.export()
        field.value = ipaddress.IPv4Address("1.2.3.4")
        self.assertFalse(field.delta())

    def test_write(self):

        field = relations.Field(int, store="_id", default=-1, refresh=True)

        field.value = 1
        values = {}
        field.write(values)
        self.assertEqual(values, {'_id': 1})

        field = relations.Field(ipaddress.IPv4Address, store="ip", attr={"compressed": "address", "__int__": "value"})
        field.value = ipaddress.IPv4Address('1.2.3.4')
        values = {}
        field.write(values)
        self.assertEqual(values, {'ip': {"address": "1.2.3.4", "value": 16909060}})

        field = relations.Field(str, inject="things__a__b__0____1")
        field.value = "yep"
        values = {}
        field.write(values)
        self.assertEqual(values, {"a":{"b": [{"1": "yep"}]}})

        field = relations.Field(str, store=False)
        field.value = "yep"
        values = {}
        field.write(values)
        self.assertEqual(values, {})

    def test_create(self):

        field = relations.Field(int, store="_id")

        field.value = 1
        values = {}
        field.create(values)
        self.assertEqual(values, {'_id': 1})
        self.assertEqual(field.original, 1)

        field = relations.Field(int, store="_id")
        field.auto = True
        values = {}
        field.create(values)
        self.assertEqual(values, {})
        self.assertIsNone(field.original)

    def test_retrieve(self):

        field = relations.Field(str, store="name")
        field.filter("yes", "null")
        self.assertTrue(field.retrieve({"name": None}))
        self.assertFalse(field.retrieve({"name": ''}))

        field = relations.Field(str, store="name")
        field.filter("no", "null")
        self.assertTrue(field.retrieve({"name": ''}))
        self.assertFalse(field.retrieve({"name": None}))

        field = relations.Field(str, store="name")
        field.filter("no", "not_null")
        self.assertTrue(field.retrieve({"name": None}))
        self.assertFalse(field.retrieve({"name": ''}))

        field = relations.Field(int, store="_id")
        field.filter("1")
        self.assertTrue(field.retrieve({"_id": '1'}))
        self.assertFalse(field.retrieve({"_id": '2'}))

        field = relations.Field(int, store="_id")
        field.filter("1", "gt")
        self.assertTrue(field.retrieve({"_id": '2'}))
        self.assertFalse(field.retrieve({"_id": '1'}))

        field = relations.Field(int, store="_id")
        field.filter("1", "gte")
        self.assertTrue(field.retrieve({"_id": '1'}))
        self.assertFalse(field.retrieve({"_id": '0'}))

        field = relations.Field(int, store="_id")
        field.filter("1", "lt")
        self.assertTrue(field.retrieve({"_id": '0'}))
        self.assertFalse(field.retrieve({"_id": '1'}))

        field = relations.Field(int, store="_id")
        field.filter("1", "lte")
        self.assertTrue(field.retrieve({"_id": '1'}))
        self.assertFalse(field.retrieve({"_id": '2'}))

        field = relations.Field(str, store="name")
        field.filter("Yes", "like")
        self.assertTrue(field.retrieve({"name": ' yES adsfadsf'}))
        self.assertFalse(field.retrieve({"name": 'no'}))

        field = relations.Field(str, store="name")
        field.filter("Yes", "start")
        self.assertTrue(field.retrieve({"name": 'yES adsfadsf'}))
        self.assertFalse(field.retrieve({"name": 'no yes'}))

        field = relations.Field(str, store="name")
        field.filter("Yes", "end")
        self.assertTrue(field.retrieve({"name": 'sure yes'}))
        self.assertFalse(field.retrieve({"name": 'yes no'}))

        field = relations.Field(dict, store="meta")
        field.filter(1, "a")
        self.assertTrue(field.retrieve({"meta": {"a": 1}}))
        self.assertFalse(field.retrieve({"meta": {"a": '1'}}))

        field = relations.Field(dict, store="meta")
        field.filter(1, "a__in")
        self.assertTrue(field.retrieve({"meta": {"a": 1}}))
        self.assertFalse(field.retrieve({"meta": {"a": '1'}}))

        field = relations.Field(dict, store="meta")
        field.filter(1, "a__not_eq")
        self.assertTrue(field.retrieve({"meta": {"a": '1'}}))
        self.assertFalse(field.retrieve({"meta": {"a": 1}}))

        field = relations.Field(dict, store="meta")
        field.filter(1, "a__b__1__in")
        self.assertTrue(field.retrieve({"meta": {"a": {"b": [0, 1]}}}))
        self.assertFalse(field.retrieve({"meta": {"a": {"b": ['0', '1']}}}))
        self.assertFalse(field.retrieve({"meta": {}}))

        field = relations.Field(dict, store="meta")
        field.filter(1, "a__b____1__in")
        self.assertTrue(field.retrieve({"meta": {"a": {"b": {"1": 1}}}}))
        self.assertFalse(field.retrieve({"meta": {"a": {"b": {"1": '1'}}}}))
        self.assertFalse(field.retrieve({"meta": {}}))

        field = relations.Field(dict, store="meta")
        field.filter(1, "__1__in")
        self.assertTrue(field.retrieve({"meta": {"1": 1}}))
        self.assertFalse(field.retrieve({"meta": {"1": '1'}}))
        self.assertFalse(field.retrieve({"meta": {}}))

        field = relations.Field(dict, store="meta")
        field.filter(1, "a__b__1__null")
        self.assertTrue(field.retrieve({"meta": {"a": {"b": [0, None]}}}))
        self.assertTrue(field.retrieve({"meta": {}}))
        self.assertFalse(field.retrieve({"meta": {"a": {"b": [0, '1']}}}))

        field = relations.Field(int, store="_id")
        field.filter("1", "in")
        self.assertTrue(field.retrieve({"_id": '1'}))
        self.assertFalse(field.retrieve({"_id": '2'}))

        field = relations.Field(list, store="meta")
        field.filter(1, "1__in")
        self.assertTrue(field.retrieve({"meta": [0, 1]}))
        self.assertFalse(field.retrieve({"meta": ['0', '1']}))
        self.assertFalse(field.retrieve({"meta": []}))

        field = relations.Field(list, store="meta")
        field.filter(1, "1__null")
        self.assertTrue(field.retrieve({"meta": [0, None]}))
        self.assertTrue(field.retrieve({"meta": []}))
        self.assertFalse(field.retrieve({"meta": ['0', '1']}))

        field = relations.Field(list, store="meta")
        field.filter("1", "has")
        self.assertTrue(field.retrieve({"meta": ['1', '2']}))
        self.assertFalse(field.retrieve({"meta": ['2']}))

        field = relations.Field(list, store="meta")
        field.filter(["1", "2"], "any")
        self.assertTrue(field.retrieve({"meta": ['1']}))
        self.assertFalse(field.retrieve({"meta": ['3']}))

        field = relations.Field(list, store="meta")
        field.filter(["1", "2"], "all")
        self.assertTrue(field.retrieve({"meta": ['1', '2']}))
        self.assertFalse(field.retrieve({"meta": ['3', '2', '1']}))

    def test_like(self):

        field = relations.Field(int, store="_id")
        self.assertTrue(field.like({"_id": '1'}, 1, {}))
        self.assertFalse(field.like({"_id": '2'}, 1, {}))
        self.assertTrue(field.like({"_id": '1'}, None, {'_id': [1]}))
        self.assertFalse(field.like({"_id": '2'}, None, {'_id': [1]}))

        field = relations.Field(str, store="name")
        self.assertTrue(field.like({"name": ' yES adsfadsf'}, "Yes", {}))
        self.assertFalse(field.like({"name": 'no'}, "Yes", {}))

        field = relations.Field(ipaddress.IPv4Address, store="ip", attr={"compressed": "address"}, titles="address")
        self.assertTrue(field.like({"ip": {"address": '1.2.3.4'}}, "1.2.3.", {}))
        self.assertTrue(field.like({"ip": {"address": '1.2.3.4'}}, "1.2.3.", {}, "address"))
        self.assertFalse(field.like({"ip": {"address": '1.2.3.4'}}, "1.3.2.", {}))
        self.assertFalse(field.like({}, "1.3.2.4", {}))

    def test_read(self):

        field = relations.Field(int, store="_id")
        field.read({"_id": "1"})
        self.assertEqual(field.value, 1)
        self.assertFalse(field.delta())

        field = relations.Field(str, inject="things__a__b__0____1")
        field.read({"a":{"b": [{"1": "yep"}]}})
        self.assertEqual(field.value, "yep")
        self.assertFalse(field.delta())

    def test_title(self):

        field = relations.Field(bool)
        field.value = False
        self.assertEqual(field.title(), [False])

        field = relations.Field(int)
        field.value = 1
        self.assertEqual(field.title(), [1])

        field = relations.Field(float)
        field.value = 1.0
        self.assertEqual(field.title(), [1.0])

        field = relations.Field(str)
        field.value = "yep"
        self.assertEqual(field.title(), ["yep"])

        field = relations.Field(list)
        field.value = [1, 2, [3, 4]]
        self.assertEqual(field.title(), [[1, 2, [3, 4]]])
        self.assertEqual(field.title("2__1"), [4])

        field = relations.Field(dict)
        field.value = {"a":{"b": [{"1": "yep"}]}}
        self.assertEqual(field.title(), [{"a":{"b": [{"1": "yep"}]}}])
        self.assertEqual(field.title("a__b__0____1"), ["yep"])

        field = relations.Field(ipaddress.IPv4Address, attr={"compressed": "ip__address", "__int__": "ip__value"}, titles=["ip__address", "ip__value"])
        field.value = "1.2.3.4"
        self.assertEqual(field.title("ip__value"), [16909060])
        self.assertEqual(field.title(), ["1.2.3.4", 16909060])

    def test_update(self):

        field = relations.Field(int, store="_id")

        field.value = 1
        field.original = 2
        values = {}
        field.update(values)
        self.assertEqual(values, {'_id': 1})
        self.assertEqual(field.original, 1)

        values = {}
        field.update(values)
        self.assertEqual(values, {})
        self.assertEqual(field.original, 1)

        field.refresh = True
        field.default = 2
        values = {}
        field.update(values)
        self.assertEqual(values, {'_id': 2})
        self.assertEqual(field.value, 2)
        self.assertEqual(field.original, 2)

        values = {}
        field.value = 1
        values = {}
        field.update(values)
        self.assertEqual(values, {'_id': 1})
        self.assertEqual(field.original, 1)

        field = relations.Field(ipaddress.IPv4Address, store="ip", attr={"compressed": "address", "__int__": "value"})
        field.value = ipaddress.IPv4Address('1.2.3.4')
        values = {}
        field.update(values)
        self.assertEqual(values, {'ip': {"address": "1.2.3.4", "value": 16909060}})
        self.assertEqual(field.original, {"address": "1.2.3.4", "value": 16909060})

    def test_mass(self):

        field = relations.Field(int, store="_id")

        field.value = 1
        field.changed = True
        values = {}
        field.mass(values)
        self.assertEqual(values, {'_id': 1})

        field.changed = False
        values = {}
        field.mass(values)
        self.assertEqual(values, {})

        field.refresh = True
        field.default = 2
        values = {}
        field.mass(values)
        self.assertEqual(values, {'_id': 2})
        self.assertEqual(field.value, 2)

        values = {}
        field.value = 1
        values = {}
        field.mass(values)
        self.assertEqual(values, {'_id': 1})

        field = relations.Field(ipaddress.IPv4Address, store="ip", attr={"compressed": "address", "__int__": "value"})
        field.value = ipaddress.IPv4Address('1.2.3.4')
        values = {}
        field.mass(values)
        self.assertEqual(values, {'ip': {"address": "1.2.3.4", "value": 16909060}})

        field.inject = True
        self.assertRaisesRegex(relations.FieldError, "no mass update with inject", field.mass, {})

    def test_tie(self):

        field = relations.Field(int, name="tie", tied=True)
        values = {}
        field.tie(values)
        self.assertEqual(values, {})

        field.value = 1
        field.changed = True
        values = {}
        field.tie(values)
        self.assertEqual(values, {'tie': 1})

        values = {}
        field.changed = False
        field.tie(values)
        self.assertEqual(values, {})

        field.changed = True
        field.tied = False
        values = {}
        field.tie(values)
        self.assertEqual(values, {})
