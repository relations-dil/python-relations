import unittest
import unittest.mock

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

class Meta(SourceModel):
    id = int
    name = str
    flag = bool
    stuff = list
    things = dict

relations.OneToMany(Simple, Plain)

class Unit(SourceModel):
    id = int
    name = str, {"style": "fancy"}

class Test(SourceModel):
    id = int
    unit_id = int
    name = str, {"style": "shmancy"}

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
        self.assertTrue(model._fields._names["id"].auto_increment)
        self.assertTrue(model._fields._names["id"].readonly)

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

        yep = Meta("yep", True, [1], {"a": 1}).create()
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
                    "stuff": [1],
                    "things": {"a": 1}
                },
                2: {
                    "id": 2,
                    "name": "nope",
                    "flag": False,
                    "stuff": [],
                    "things": {}
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

    def test_model_labels(self):

        Unit("people").create().test.add("stuff").add("things").create()

        labels = Unit.many().labels()

        self.assertEqual(labels.id, "id")
        self.assertEqual(labels.label, ["name"])
        self.assertEqual(labels.parents, {})
        self.assertEqual(labels.style, ["fancy"])

        self.assertEqual(labels.ids, [1])
        self.assertEqual(labels.labels,{1: ["people"]})

        labels = Test.many().labels()

        self.assertEqual(labels.id, "id")
        self.assertEqual(labels.label, ["unit_id", "name"])

        self.assertEqual(labels.parents["unit_id"].id, "id")
        self.assertEqual(labels.parents["unit_id"].label, ["name"])
        self.assertEqual(labels.parents["unit_id"].parents, {})
        self.assertEqual(labels.parents["unit_id"].style, ["fancy"])

        self.assertEqual(labels.style, ["fancy", "shmancy"])

        self.assertEqual(labels.ids, [1, 2])
        self.assertEqual(labels.labels, {
            1: ["people", "stuff"],
            2: ["people", "things"]
        })

    def test_field_update(self):

        # Standard

        field = relations.Field(int, name="id")
        self.source.field_init(field)
        values = {}
        field.value = 1
        self.source.field_update(field, values)
        self.assertEqual(values, {"id": 1})
        self.assertFalse(field.changed)

        # replace

        field = relations.Field(int, name="id", default=-1, replace=True)
        field.value = 1
        values = {}
        self.source.field_update(field, values)
        self.assertEqual(values, {'id': 1})

        field.changed = False
        values = {}
        self.source.field_update(field, values)
        self.assertEqual(values, {'id': -1})
        self.assertEqual(field.value, -1)


        # not changed

        field = relations.Field(int, name="id")
        values = {}
        self.source.field_update(field, values, changed=True)
        self.assertEqual(values, {})
        self.assertFalse(field.changed)

        # readonly

        field = relations.Field(int, name="id", readonly=True)
        self.source.field_init(field)
        values = {}
        field.value = 1
        self.source.field_update( field, values)
        self.assertEqual(values, {})

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
