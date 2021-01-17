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

relations.OneToMany(Simple, Plain)

class Unit(SourceModel):
    id = int
    name = str

class Test(SourceModel):
    id = int
    unit_id = int
    name = str

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

        self.assertEqual(self.source.ids, {
            "simple": 1,
            "plain": 1
        })

        self.assertEqual(self.source.data, {
            "simple": {
                1: {
                    "id": 1,
                    "name": "sure"
                }
            },
            "plain": {
                1: {
                    "simple_id": 1,
                    "name": "fine"
                }
            }
        })

    def test_model_retrieve(self):

        Unit([["people"], ["stuff"]]).create()

        models = Unit.one(name__in=["people", "stuff"])
        self.assertRaisesRegex(relations.ModelError, "unit: more than one retrieved", models.retrieve)

        model = Unit.one(name="things")
        self.assertRaisesRegex(relations.ModelError, "unit: none retrieved", model.retrieve)

        self.assertIsNone(model.retrieve(False))

        unit = Unit.one(name="people")

        self.assertEqual(unit.id, 1)
        self.assertEqual(unit._action, "update")
        self.assertEqual(unit._record._action, "update")

        unit.test.add("things")[0].case.add("persons")
        unit.update()

        model = Unit.many(test__name="things")

        self.assertEqual(model.id, [1])
        self.assertEqual(model[0]._action, "update")
        self.assertEqual(model[0]._record._action, "update")
        self.assertEqual(model[0].test[0].id, 1)
        self.assertEqual(model[0].test[0].case.name, "persons")

    def test_field_update(self):

        # Standard

        field = relations.Field(int, name="id")
        self.source.field_init(field)
        values = {}
        field.value = 1
        self.source.field_update(field, values)
        self.assertEqual(values, {"id": 1})
        self.assertFalse(field.changed)

        # not changed

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
