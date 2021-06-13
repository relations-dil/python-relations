import unittest
import unittest.mock

import ipaddress

import relations.unittest

class SourceModel(relations.Model):
    SOURCE = "UnittestSource"

class Simple(SourceModel):
    id = int
    name = str

class Plain(SourceModel):
    ID = None
    simple_id = int
    name = str

relations.OneToMany(Simple, Plain)

class Meta(SourceModel):
    id = int
    name = str
    flag = bool
    spend = float
    stuff = list
    things = dict
    pull = str, {"extract": "things__for__0___1"}
    push = str, {"inject": "stuff__-1__relations.io___1"}

def subnet_attr(values, value):

    values["address"] = str(value)
    min_ip = value[0]
    max_ip = value[-1]
    values["min_address"] = str(min_ip)
    values["min_value"] = int(min_ip)
    values["max_address"] = str(max_ip)
    values["max_value"] = int(max_ip)

class Net(SourceModel):

    id = int
    ip_address = str, {"extract": "ip__address"}
    ip_value = int, {"extract": "ip__value"}
    ip = ipaddress.IPv4Address, {
        "attr": {"compressed": "address", "__int__": "value"},
        "init": "address",
        "label": "address"
    }
    subnet = ipaddress.IPv4Network, {
        "attr": subnet_attr,
        "init": "address",
        "label": "address"
    }

    INDEX = "ip_value"

class Unit(SourceModel):
    id = int
    name = str, {"format": "fancy"}

class Test(SourceModel):
    id = int
    unit_id = int
    name = str, {"format": "shmancy"}

class Case(SourceModel):
    id = int
    test_id = int
    name = str

relations.OneToMany(Unit, Test)
relations.OneToOne(Test, Case)

class TestSource(unittest.TestCase):

    maxDiff = None

    def setUp(self):

        self.source = relations.unittest.MockSource("UnittestSource")

    @unittest.mock.patch("relations.SOURCES", {})
    def test___init__(self):

        source = relations.unittest.MockSource("unit")
        self.assertEqual(source.name, "unit")
        self.assertEqual(relations.SOURCES["unit"], source)

    def test_field_init(self):

        class Field:
            pass

        field = Field()

        self.source.field_init(field)

        self.assertIsNone(field.auto_increment)

    def test_model_init(self):

        class Check(relations.Model):
            id = int
            name = str

        model = Check()

        self.source.model_init(model)

        self.assertEqual(self.source.ids, {"check": 0})
        self.assertEqual(self.source.data, {"check": {}})
        self.assertTrue(model._fields._names["id"].auto)

    def test_field_define(self):

        field = relations.Field(int, store="_id")
        self.source.field_init(field)
        definitions = {}
        self.source.field_define(field, definitions)
        self.assertEqual(definitions, {"_id": int})

    def test_model_define(self):

        self.assertEqual(Simple.define(), {
            "simple": {
                "id": int,
                "name": str
            }
        })

    def test_extract(self):

        self.assertEqual(self.source.extract(Meta(), {"things": {"for": [{"1": "yep"}]}})["pull"], "yep")

    def test_model_create(self):

        simple = Simple("sure")
        simple.plain.add("fine")

        simple.create()

        self.assertEqual(simple.id, 1)
        self.assertEqual(simple._action, "update")
        self.assertEqual(simple._record._action, "update")
        self.assertEqual(simple.plain[0].simple_id, 1)
        self.assertEqual(simple.plain._action, "update")
        self.assertEqual(simple.plain[0]._record._action, "update")

        simples = Simple.bulk().add("ya").create()

        self.assertEqual(simples._models, [])

        yep = Meta("yep", True, 3.50, [1, None], {"a": 1, "for": [{"1": "yep"}]}, "sure").create()
        self.assertTrue(Meta.one(yep.id).flag)

        nope = Meta("nope", False).create()
        self.assertFalse(Meta.one(nope.id).flag)

        self.assertEqual(self.source.ids, {
            "simple": 2,
            "plain": 1,
            "meta": 2
        })

        self.assertEqual(self.source.data, {
            "simple": {
                1: {
                    "id": 1,
                    "name": "sure"
                },
                2: {
                    "id": 2,
                    "name": "ya"
                }
            },
            "plain": {
                1: {
                    "simple_id": 1,
                    "name": "fine"
                }
            },
            "meta": {
                1: {
                    "id": 1,
                    "name": "yep",
                    "flag": True,
                    "spend": 3.50,
                    "stuff": [1, {"relations.io": {"1": "sure"}}],
                    "things": {"a": 1, "for": [{"1": "yep"}]},
                    "pull": "yep"
                },
                2: {
                    "id": 2,
                    "name": "nope",
                    "flag": False,
                    "spend": None,
                    "stuff": [{"relations.io": {"1": None}}],
                    "things": {},
                    "pull": None
                }
            }
        })

    def test_model_like(self):

        Unit([["stuff"], ["people"]]).create()

        unit = Unit.one(like="p")

        self.assertEqual(self.source.model_like(unit), [{
            "id": 2,
            "name": "people"
        }])

        unit.test.add("things")[0]
        unit.update()

        test = Test.many(like="p")
        self.assertEqual(self.source.model_like(test), [{
            "id": 1,
            "unit_id": 2,
            "name": "things"
        }])
        self.assertFalse(test.overflow)

        test = Test.many(like="p", _chunk=1)
        self.assertEqual(self.source.model_like(test), [{
            "id": 1,
            "unit_id": 2,
            "name": "things"
        }])
        self.assertTrue(test.overflow)

    def test_model_sort(self):

        unit = Unit([["stuff"], ["people"], ["things"]]).create()

        self.source.model_sort(unit)
        self.assertEqual(unit.name, ["people", "stuff", "things"])

        unit._sort = ['-id']
        self.source.model_sort(unit)
        self.assertEqual(unit.name, ["things", "people", "stuff"])
        self.assertIsNone(unit._sort)

    def test_model_limit(self):

        unit = Unit.many()

        unit._models = [1, 2, 3]
        self.source.model_limit(unit)
        self.assertEqual(unit._models, [1, 2, 3])
        self.assertFalse(unit.overflow)

        unit._models = [1, 2, 3]
        unit._limit = 4
        unit._offset = 0
        self.source.model_limit(unit)
        self.assertEqual(unit._models, [1, 2, 3])
        self.assertFalse(unit.overflow)

        unit._models = [1, 2, 3]
        unit._limit = 2
        self.source.model_limit(unit)
        self.assertEqual(unit._models, [1, 2])
        self.assertTrue(unit.overflow)

        unit._models = [1, 2, 3]
        unit._offset = 1
        self.source.model_limit(unit)
        self.assertEqual(unit._models, [2, 3])
        self.assertTrue(unit.overflow)

    def test_model_count(self):

        Unit([["stuff"], ["people"]]).create()

        self.assertEqual(Unit.many().count(), 2)

        self.assertEqual(Unit.many(name="people").count(), 1)

        self.assertEqual(Unit.many(like="p").count(), 1)

    def test_model_retrieve(self):

        Unit([["stuff"], ["people"]]).create()

        models = Unit.one(name__in=["people", "stuff"])
        self.assertRaisesRegex(relations.ModelError, "unit: more than one retrieved", models.retrieve)

        model = Unit.one(name="things")
        self.assertRaisesRegex(relations.ModelError, "unit: none retrieved", model.retrieve)

        self.assertIsNone(model.retrieve(False))

        unit = Unit.one(name="people")

        self.assertEqual(unit.id, 2)
        self.assertEqual(unit._action, "update")
        self.assertEqual(unit._record._action, "update")

        self.assertTrue(Unit.many(name="people").limit(1).retrieve().overflow)
        self.assertFalse(Unit.many(name="people").limit(2).retrieve().overflow)

        unit.test.add("things")[0].case.add("persons")
        unit.update()

        model = Unit.many(test__name="things")

        self.assertEqual(model.id, [2])
        self.assertEqual(model[0]._action, "update")
        self.assertEqual(model[0]._record._action, "update")
        self.assertEqual(model[0].test[0].id, 1)
        self.assertEqual(model[0].test[0].case.name, "persons")

        self.assertEqual(Unit.many().name, ["people", "stuff"])
        self.assertEqual(Unit.many().sort("-name").limit(1).name, ["stuff"])
        self.assertEqual(Unit.many().sort("-name").limit(0).name, [])

        model = Unit.many(like="p")
        self.assertEqual(model.name, ["people"])

        model = Test.many(like="p").retrieve()
        self.assertEqual(model.name, ["things"])
        self.assertFalse(model.overflow)

        model = Test.many(like="p", _chunk=1).retrieve()
        self.assertEqual(model.name, ["things"])
        self.assertTrue(model.overflow)

        Meta("dive", stuff=[1, 2, 3, None], things={"a": {"b": [1], "c": "sure"}, "4": 5, "for": [{"1": "yep"}]}).create()

        model = Meta.many(stuff__1=2)
        self.assertEqual(model[0].name, "dive")
        self.assertEqual(model[0].pull, "yep")

        model = Meta.many(things__a__b__0=1)
        self.assertEqual(model[0].name, "dive")

        model = Meta.many(things__a__c__like="su")
        self.assertEqual(model[0].name, "dive")

        model = Meta.many(things__a__d__null=True)
        self.assertEqual(model[0].name, "dive")

        model = Meta.many(things___4=5)
        self.assertEqual(model[0].name, "dive")

        model = Meta.many(things__a__b__0__gt=1)
        self.assertEqual(len(model), 0)

        model = Meta.many(things__a__c__notlike="su")
        self.assertEqual(len(model), 0)

        model = Meta.many(things__a__d__null=False)
        self.assertEqual(len(model), 0)

        model = Meta.many(things___4=6)
        self.assertEqual(len(model), 0)

        Net(ip="1.2.3.4", subnet="1.2.3.0/24").create()
        Net().create()

        model = Net.many(like='1.2.3.')
        self.assertEqual(model[0].ip_address, "1.2.3.4")

        model = Net.many(ip__address__like='1.2.3.')
        self.assertEqual(model[0].ip_address, "1.2.3.4")

        model = Net.many(ip__value__gt=int(ipaddress.IPv4Address('1.2.3.0')))
        self.assertEqual(model[0].ip_address, "1.2.3.4")

        model = Net.many(subnet__address__like='1.2.3.')
        self.assertEqual(model[0].ip_address, "1.2.3.4")

        model = Net.many(subnet__min_value=int(ipaddress.IPv4Address('1.2.3.0')))
        self.assertEqual(model[0].ip_address, "1.2.3.4")

        model = Net.many(ip__address__notlike='1.2.3.')
        self.assertEqual(len(model), 0)

        model = Net.many(ip__value__lt=int(ipaddress.IPv4Address('1.2.3.0')))
        self.assertEqual(len(model), 0)

        model = Net.many(subnet__address__notlike='1.2.3.')
        self.assertEqual(len(model), 0)

        model = Net.many(subnet__max_value=int(ipaddress.IPv4Address('1.2.3.0')))
        self.assertEqual(len(model), 0)

    def test_model_labels(self):

        Unit("people").create().test.add("stuff").add("things").create()

        labels = Unit.many().labels()

        self.assertEqual(labels.id, "id")
        self.assertEqual(labels.label, ["name"])
        self.assertEqual(labels.parents, {})
        self.assertEqual(labels.format, ["fancy"])

        self.assertEqual(labels.ids, [1])
        self.assertEqual(labels.labels,{1: ["people"]})

        labels = Test.many().labels()

        self.assertEqual(labels.id, "id")
        self.assertEqual(labels.label, ["unit_id", "name"])

        self.assertEqual(labels.parents["unit_id"].id, "id")
        self.assertEqual(labels.parents["unit_id"].label, ["name"])
        self.assertEqual(labels.parents["unit_id"].parents, {})
        self.assertEqual(labels.parents["unit_id"].format, ["fancy"])

        self.assertEqual(labels.format, ["fancy", "shmancy"])

        self.assertEqual(labels.ids, [1, 2])
        self.assertEqual(labels.labels, {
            1: ["people", "stuff"],
            2: ["people", "things"]
        })

        Net(ip="1.2.3.4", subnet="1.2.3.0/24").create()

        self.assertEqual(Net.many().labels().labels, {
            1: ["1.2.3.4"]
        })

    def test_model_update(self):

        Unit([["people"], ["stuff"]]).create()

        unit = Unit.many(id=2).set(name="things")

        self.assertEqual(unit.update(), 1)

        unit = Unit.one(2)

        unit.name = "thing"
        unit.test.add("moar")

        self.assertEqual(unit.update(), 1)
        self.assertEqual(unit.name, "thing")
        self.assertEqual(unit.test[0].id, 1)
        self.assertEqual(unit.test[0].name, "moar")

        plain = Plain.one()
        self.assertRaisesRegex(relations.ModelError, "plain: nothing to update from", plain.update)

        dive = Meta("dive", things={"for": [{"1": "yep"}]}).create()
        swim = Meta("swim", things={"for": [{"1": "nope"}]}).create()

        Meta.many().set(things={"for": [{"1": "um"}]}).update()

        self.assertEqual(Meta.one(dive.id).pull, "um")
        self.assertEqual(Meta.one(swim.id).pull, "um")

        Meta.one(swim.id).set(things={"for": [{"1": "nah"}]}).update()

        self.assertEqual(Meta.one(dive.id).pull, "um")
        self.assertEqual(Meta.one(swim.id).pull, "nah")

        ping = Net(ip="1.2.3.4", subnet="1.2.3.0/24").create()
        pong = Net(ip="5.6.7.8", subnet="5.6.7.0/24").create()

        Net.many().set(subnet="9.10.11.0/24").update()

        self.assertEqual(Net.one(ping.id).subnet.compressed, "9.10.11.0/24")
        self.assertEqual(Net.one(pong.id).subnet.compressed, "9.10.11.0/24")

        Net.one(ping.id).set(ip="13.14.15.16").update()
        self.assertEqual(Net.one(ping.id).ip.compressed, "13.14.15.16")
        self.assertEqual(Net.one(pong.id).ip.compressed, "5.6.7.8")

    def test_model_delete(self):

        unit = Unit("people")
        unit.test.add("stuff").add("things")
        unit.create()

        self.assertEqual(Test.one(id=2).delete(), 1)
        self.assertEqual(len(Test.many()), 1)

        self.assertEqual(Unit.one(1).test.delete(), 1)
        self.assertEqual(Unit.one(1).retrieve().delete(), 1)
        self.assertEqual(len(Unit.many()), 0)
        self.assertEqual(len(Test.many()), 0)

        plain = Plain().create()
        self.assertRaisesRegex(relations.ModelError, "plain: nothing to delete from", plain.delete)
