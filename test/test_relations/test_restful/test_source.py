import unittest
import unittest.mock
import relations.unittest
import relations.restful.unittest

import flask
import flask_restful
import werkzeug.exceptions

import relations.model
import relations.restful


class SourceModel(relations.model.Model):
    SOURCE = "TestRestfulSource"

class Simple(SourceModel):
    id = int
    name = str

class Plain(SourceModel):
    ID = None
    simple_id = int
    name = str

relations.model.OneToMany(Simple, Plain)

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

relations.model.OneToMany(Unit, Test)
relations.model.OneToOne(Test, Case)

class TestSource(unittest.TestCase):

    maxDiff = None

    def setUp(self):

        class ResourceModel(relations.model.Model):
            SOURCE = "TestRestfulResource"

        class Simple(ResourceModel):
            id = int
            name = str

        class Plain(ResourceModel):
            ID = None
            simple_id = int
            name = str

        relations.model.OneToMany(Simple, Plain)

        class SimpleResource(relations.restful.Resource):
            MODEL = Simple

        class PlainResource(relations.restful.Resource):
            MODEL = Plain

        class Unit(ResourceModel):
            id = int
            name = str

        class Test(ResourceModel):
            id = int
            unit_id = int
            name = str

        class Case(ResourceModel):
            id = int
            test_id = int
            name = str

        relations.model.OneToMany(Unit, Test)
        relations.model.OneToOne(Test, Case)

        class UnitResource(relations.restful.Resource):
            MODEL = Unit

        class TestResource(relations.restful.Resource):
            MODEL = Test

        class CaseResource(relations.restful.Resource):
            MODEL = Case

        self.resource = relations.unittest.MockSource("TestRestfulResource")

        self.app = flask.Flask("source-api")
        restful = flask_restful.Api(self.app)

        restful.add_resource(SimpleResource, '/simple', '/simple/<id>')
        restful.add_resource(PlainResource, '/plain')

        restful.add_resource(UnitResource, '/unit', '/unit/<id>')
        restful.add_resource(TestResource, '/test', '/test/<id>')
        restful.add_resource(CaseResource, '/case', '/case/<id>')

        self.source = relations.restful.Source("TestRestfulSource", "", self.app.test_client())

        def result(key, response):
            return response.json[key]

        self.source.result = result

    @unittest.mock.patch("relations.SOURCES", {})
    @unittest.mock.patch("requests.Session")
    def test___init__(self, mock_session):

        source = relations.restful.Source("unit", "http://test.com", a=1)
        self.assertEqual(source.name, "unit")
        self.assertEqual(source.url, "http://test.com")
        self.assertEqual(source.session.a, 1)
        self.assertEqual(relations.SOURCES["unit"], source)

        source = relations.restful.Source("test", "http://unit.com", session="sesh")
        self.assertEqual(source.name, "test")
        self.assertEqual(source.url, "http://unit.com")
        self.assertEqual(source.session, "sesh")
        self.assertEqual(relations.SOURCES["test"], source)

    @unittest.mock.patch("relations.SOURCES", {})
    def test_result(self):

        source = relations.restful.Source("test", "http://unit.com", session="sesh")

        response = unittest.mock.MagicMock()
        response.json.return_value = {"name": "value"}

        self.assertEqual(source.result("name", response), "value")
        response.raise_for_status.assert_called_once_with()

    def test_model_init(self):

        class Check(relations.model.Model):
            id = int
            name = str

        model = Check()
        self.source.model_init(model)

        self.assertEqual(model.SINGULAR, "check")
        self.assertEqual(model.PLURAL, "checks")
        self.assertEqual(model.ENDPOINT, "check")
        self.assertTrue(model._fields._names["id"].readonly)

        Check.SINGULAR = "people"
        Check.PLURAL = "stuff"
        Check.ENDPOINT = "things"

        model = Check()
        self.source.model_init(model)

        self.assertEqual(model.SINGULAR, "people")
        self.assertEqual(model.PLURAL, "stuff")
        self.assertEqual(model.ENDPOINT, "things")

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

        self.assertEqual(self.resource.ids, {
            "simple": 1,
            "plain": 1
        })

        self.assertEqual(self.resource.data, {
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
        self.assertRaisesRegex(relations.model.ModelError, "unit: more than one retrieved", models.retrieve)

        model = Unit.one(name="things")
        self.assertRaisesRegex(relations.model.ModelError, "unit: none retrieved", model.retrieve)

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

        field = relations.model.Field(int, name="id")
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

        field = relations.model.Field(int, name="id", readonly=True)
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
        self.assertRaisesRegex(relations.model.ModelError, "plain: nothing to update from", plain.update)

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
        self.assertRaisesRegex(relations.model.ModelError, "plain: nothing to delete from", plain.delete)
