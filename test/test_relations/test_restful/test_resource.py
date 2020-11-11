import unittest
import unittest.mock
import relations.unittest
import relations.restful.unittest

import flask
import flask_restful
import werkzeug.exceptions

import relations.model
import relations.restful

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

class TestResource(relations.restful.unittest.TestCase):

    def setUp(self):

        self.source = relations.unittest.MockSource("TestRestfulResource")

        self.app = flask.Flask("resource-api")
        restful = flask_restful.Api(self.app)

        restful.add_resource(SimpleResource, '/simple', '/simple/<id>')
        restful.add_resource(PlainResource, '/plain')

        self.api = self.app.test_client()

    @unittest.mock.patch("traceback.format_exc")
    def test_exceptions(self, mock_traceback):

        @relations.restful.exceptions
        def good():
            return {"good": True}

        self.app.add_url_rule('/good', 'good', good)

        self.assertStatusValue(self.api.get("/good"), 200, "good", True)

        @relations.restful.exceptions
        def bad():
            raise werkzeug.exceptions.BadRequest("nope")

        self.app.add_url_rule('/bad', 'bad', bad)

        self.assertStatusValue(self.api.get("/bad"), 400, "message", "nope")

        @relations.restful.exceptions
        def ugly():
            raise Exception("whoops")

        mock_traceback.return_value = "adaisy"

        self.app.add_url_rule('/ugly', 'ugly', ugly)

        response = self.api.get("/ugly")

        self.assertStatusValue(response, 500, "message", "whoops")
        self.assertStatusValue(response, 500, "traceback", "adaisy")

    def test___init__(self):

        class Init(ResourceModel):
            id = int
            name = str

        class InitResource(relations.restful.Resource):
            MODEL = Init

        resource = InitResource()
        self.assertEqual(resource.SINGULAR, "init")
        self.assertEqual(resource.PLURAL, "inits")

        Init.SINGULAR = "inity"
        resource = InitResource()
        self.assertEqual(resource.SINGULAR, "inity")
        self.assertEqual(resource.PLURAL, "initys")

        Init.PLURAL = "inities"
        resource = InitResource()
        self.assertEqual(resource.SINGULAR, "inity")
        self.assertEqual(resource.PLURAL, "inities")

        InitResource.SINGULAR = "initee"
        resource = InitResource()
        self.assertEqual(resource.SINGULAR, "initee")
        self.assertEqual(resource.PLURAL, "inities")

        InitResource.PLURAL = "initiease"
        resource = InitResource()
        self.assertEqual(resource.SINGULAR, "initee")
        self.assertEqual(resource.PLURAL, "initiease")

    def test_criteria(self):

        verify = True

        @relations.restful.exceptions
        def criteria():
            return {"criteria": relations.restful.Resource.criteria(verify)}

        self.app.add_url_rule('/criteria', 'criteria', criteria)

        response = self.api.get("/criteria")
        self.assertStatusValue(response, 400, "message", "to confirm all, send a blank filter {}")

        verify = False
        response = self.api.get("/criteria")
        self.assertStatusValue(response, 200, "criteria", {})

        response = self.api.get("/criteria?a=1")
        self.assertStatusValue(response, 200, "criteria", {"a": "1"})

        response = self.api.get("/criteria?a=1", json={"filter": {"a": 2}})
        self.assertStatusValue(response, 200, "criteria", {"a": 2})

    def test_post(self):

        response = self.api.post("/simple")
        self.assertStatusValue(response, 400, "message", "either simple or simples required")

        response = self.api.post("/simple", json={"simple": {"name": "ya"}})
        self.assertStatusModel(response, 201, "simple", {"name": "ya"})
        self.assertEqual(Simple.one(id=response.json["simple"]["id"]).name, "ya")

        response = self.api.post("/plain", json={"plains": [{"name": "sure"}]})
        self.assertStatusModel(response, 201, "plains", [{"name": "sure"}])
        self.assertEqual(Plain.one().name, "sure")

    def test_get(self):

        simple = Simple("ya").create()
        response = self.api.get(f"/simple/{simple.id}")
        self.assertStatusModel(response, 200, "simple", {"id": simple.id, "name": "ya"})

        response = self.api.get("/simple", json={"filter": {"name": "ya"}})
        self.assertStatusModel(response, 200, "simples", [{"id": simple.id, "name": "ya"}])

        response = self.api.get("/simple", json={"filter": {"name": "no"}})
        self.assertStatusModel(response, 200, "simples", [])

    def test_patch(self):

        response = self.api.patch("/simple")
        self.assertStatusValue(response, 400, "message", "either simple or simples required")

        response = self.api.patch(f"/simple", json={"simple": {"name": "yep"}})
        self.assertStatusModel(response, 400, "message", "to confirm all, send a blank filter {}")

        simple = Simple("ya").create()
        response = self.api.patch(f"/simple/{simple.id}", json={"simple": {"name": "yep"}})
        self.assertStatusModel(response, 202, "updated", 1)

        response = self.api.patch("/simple", json={"filter": {"name": "yep"}, "simple": {"name": "sure"}})
        self.assertStatusModel(response, 202, "updated", 1)

        response = self.api.patch("/simple", json={"filter": {"name": "sure"}, "simples": {"name": "whatever"}})
        self.assertStatusModel(response, 202, "updated", 1)

        response = self.api.patch("/simple", json={"filter": {"name": "no"}, "simples": {}})
        self.assertStatusModel(response, 202, "updated", 0)

    def test_delete(self):

        response = self.api.delete(f"/simple")
        self.assertStatusModel(response, 400, "message", "to confirm all, send a blank filter {}")

        simple = Simple("ya").create()
        response = self.api.delete(f"/simple/{simple.id}")
        self.assertStatusModel(response, 202, "deleted", 1)

        simple = Simple("sure").create()
        response = self.api.delete("/simple", json={"filter": {"name": "sure"}})
        self.assertStatusModel(response, 202, "deleted", 1)

        response = self.api.delete("/simple", json={"filter": {"name": "no"}})
        self.assertStatusModel(response, 202, "deleted", 0)
