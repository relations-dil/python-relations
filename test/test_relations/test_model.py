import unittest
import unittest.mock
import relations.unittest

import ipaddress

import relations


class Whoops(relations.Model):
    id = int
    name = str

class TestModelError(unittest.TestCase):

    maxDiff = None

    def test___init__(self):

        error = relations.ModelError("unittest", "oops")

        self.assertEqual(error.model, "unittest")
        self.assertEqual(error.message, "oops")

    def test___str__(self):

        error = relations.ModelError(Whoops(), "adaisy")

        self.assertEqual(str(error), "whoops: adaisy")


class People(relations.ModelIdentity):

    EXTRA = "info"

    id = int
    name = str
    gender = ["free", "male", "female"]


def stuffit():
    return "things"

class Stuff(relations.ModelIdentity):

    TITLE = "StuffIns"
    NAME = "stuffins"
    ID = "name"

    id = (int,)
    people_id = int
    name = str, "unittest"
    nope = False
    people = stuffit

    INDEX = ["name", "people"]
    ORDER = "name"


class Things(relations.ModelIdentity):

    ID = None

    name = {"kind": str, "storage": 'id'}

    UNIQUE = False
    INDEX = {
        "no_name": ["name"]
    }

class ModelTest(relations.Model):

    SOURCE = "TestModel"

def unit():
    return "test"

class UnitTest(ModelTest):
    id = int
    name = relations.Field(str, default="unittest")
    nope = False
    deffer = unit

class Unit(ModelTest):
    id = int
    name = str

class Test(ModelTest):
    id = int
    unit_id = int
    name = str

class Case(ModelTest):
    id = int
    test_id = int
    name = str

class Run(ModelTest):
    id = int
    test_id = int
    name = str
    status = ["pass", "fail"]

class Net(ModelTest):

    id = int
    ip = ipaddress.IPv4Address, {
        "attr": {"compressed": "address", "__int__": "value"},
        "init": "address",
        "label": "address",
        "extract": ["address", "value"]
    }

    LABEL = "ip__address"
    INDEX = "ip__address"

relations.OneToMany(Unit, Test)
relations.OneToOne(Test, Case)
relations.OneToOne(Test, Run)

class TestModelIdentity(unittest.TestCase):

    maxDiff = None

    def test_underscore(self):

        self.assertEqual(People.underscore("SomePeople"), "some_people")
        self.assertEqual(People.underscore("SomePEOPLE"), "some_people")
        self.assertEqual(People.underscore("SOMEPEOPLE"), "somepeople")

    def test_thy(self):

        people = People.thy()
        self.assertEqual(people.TITLE, "People")
        self.assertEqual(people.NAME, "people")
        self.assertEqual(people.PARENTS, {})
        self.assertEqual(people.CHILDREN, {})
        self.assertEqual(people.SISTERS, {})
        self.assertEqual(people.BROTHERS, {})
        self.assertEqual(people._fields._order[0].name, "id")
        self.assertEqual(people._fields._order[0].kind, int)
        self.assertEqual(people._fields._order[1].name, "name")
        self.assertEqual(people._fields._order[1].kind, str)
        self.assertEqual(people._fields._order[2].name, "gender")
        self.assertEqual(people._fields._order[2].kind, str)
        self.assertEqual(people._fields._order[2].options, ["free", "male", "female"])
        self.assertEqual(people._fields._order[2].default, "free")
        self.assertEqual(people._id, "id")
        self.assertEqual(people._label, ["name"])
        self.assertEqual(people._list, ["id", "name"])
        self.assertEqual(people._unique, {"name": ["name"]})
        self.assertEqual(people._order, ["+name"])

        stuff = Stuff()
        Stuff.thy(stuff)
        self.assertEqual(stuff.TITLE, "StuffIns")
        self.assertEqual(stuff.NAME, "stuffins")
        self.assertEqual(stuff._fields._names["id"].name, "id")
        self.assertEqual(stuff._fields._names["id"].kind, int)
        self.assertEqual(stuff._fields._names["name"].name, "name")
        self.assertEqual(stuff._fields._names["name"].kind, str)
        self.assertFalse(stuff._fields._names["name"].none)
        self.assertEqual(stuff._fields._names["people"].name, "people")
        self.assertEqual(stuff._fields._names["people"].kind, str)
        self.assertEqual(stuff._fields._names["people"].default, stuffit)
        self.assertEqual(stuff._id, "name")
        self.assertEqual(stuff._unique, {"id-people_id-people": ["id", "people_id", "people"]})
        self.assertEqual(stuff._order, ["+name"])

        things = Things.thy()
        self.assertEqual(things.NAME, "things")
        self.assertEqual(things._unique, {})
        self.assertEqual(things._index, {
            "no_name": ["name"]
        })
        self.assertEqual(things._fields._names["name"].name, "name")
        self.assertEqual(things._fields._names["name"].kind, str)
        self.assertEqual(things._fields._names["name"].storage, "id")
        self.assertIsNone(things._id)

        Unit.thy()

        self.assertEqual(Unit.SOURCE, "TestModel")

        Net.thy()

        test = Test.many()
        self.assertEqual(test._label, ["unit_id", "name"])

        class SomePeople(relations.ModelIdentity):

            id = int

        self.assertEqual(SomePeople.thy().NAME, "some_people")

        class Label(relations.ModelIdentity):
            id = int
            name = str

            LABEL = "nope"

        self.assertRaisesRegex(relations.ModelError, "cannot find field nope from label", Label.thy)

        class Label(relations.ModelIdentity):
            id = int
            name = str

            LIST = "nope"

        self.assertRaisesRegex(relations.ModelError, "cannot find field nope from list", Label.thy)

        class Unique(relations.ModelIdentity):
            id = int
            name = str

            UNIQUE = "nope"

        self.assertRaisesRegex(relations.ModelError, "cannot find field nope from unique nope", Unique.thy)

        class Index(relations.ModelIdentity):
            id = int
            name = str

            INDEX = "nope"

        self.assertRaisesRegex(relations.ModelError, "cannot find field nope from index nope", Index.thy)

        class Inject(relations.ModelIdentity):
            id = int
            name = str
            push = str,{"inject": "nope__value"}

        self.assertRaisesRegex(relations.FieldError, "cannot find field nope from inject nope__value", Inject.thy)

        Inject.push = str,{"inject": "name__value"}

        self.assertRaisesRegex(relations.FieldError, "field name not list or dict from inject name__value", Inject.thy)

    def test__field_name(self):

        stuff = Stuff()
        Stuff.thy(stuff)

        self.assertEqual(stuff._field_name("id"), "id")
        self.assertEqual(stuff._field_name(2), "name")

        self.assertRaisesRegex(relations.ModelError, "cannot find field nope in stuffins", stuff._field_name, "nope")

    def test_ordering(self):

        stuff = Stuff()
        Stuff.thy(stuff)

        self.assertEqual(stuff._ordering("id"), ["+id"])
        self.assertEqual(stuff._ordering("-name"), ["-name"])

        self.assertRaisesRegex(relations.ModelError, "unknown sort field nope", stuff._ordering, "nope")

    def test__ancestor(self):

        test = Test.thy()

        self.assertEqual(test._ancestor("unit_id").Parent, Unit)
        self.assertIsNone(test._ancestor("nope"))

    def test_define(self):

        people = People.thy()

        self.assertEqual(people.define(), {
            "name": "people",
            "title": "People",
            "extra": "info",
            "fields": [
                {
                    "name": "id",
                    "kind": "int",
                    "store": "id",
                    "none": True
                },
                {
                    "name": "name",
                    "kind": "str",
                    "store": "name",
                    "none": False
                },
                {
                    "name": "gender",
                    "kind": "str",
                    "store": "gender",
                    "options": [
                        "free",
                        "male",
                        "female"
                    ],
                    "default": "free",
                    "none": False
                }
            ],
            "id": "id",
            "unique": {
                "name": ["name"]
            },
            "index": {}
        })

    def test_migrate(self):

        people = People.thy()

        self.assertEqual(people.migrate({
            "name": "people",
            "title": "People",
            "fields": [
                {
                    "name": "id",
                    "kind": "int",
                    "store": "id",
                    "none": True
                },
                {
                    "name": "name",
                    "kind": "str",
                    "store": "name",
                    "none": False
                },
                {
                    "name": "gender",
                    "kind": "str",
                    "store": "genders",
                    "options": [
                        "free",
                        "male",
                        "female"
                    ],
                    "default": "free",
                    "none": False
                }
            ],
            "id": "id",
            "unique": {
                "name": ["name"]
            },
            "index": {}
        }), {
            "fields": {
                "change": {
                    "gender": {
                        "store": "gender"
                    }
                }
            }
        })

class TestModel(unittest.TestCase):

    maxDiff = None

    def setUp(self):

        self.source = relations.unittest.MockSource("TestModel")

    def tearDown(self):

        del relations.SOURCES["TestModel"]

    def test__extract(self):

        kwargs = {
            "people": 3,
            "things": 1
        }

        self.assertEqual(relations.Model._extract(kwargs, "people"), 3)
        self.assertEqual(relations.Model._extract(kwargs, "stuff", 2), 2)
        self.assertEqual(kwargs, {"things": 1})

    def test___init__(self):

        model = UnitTest()

        # initializations

        self.assertEqual(model._parents, {})
        self.assertEqual(model._children, {})
        self.assertEqual(model._sisters, {})
        self.assertEqual(model._brothers, {})
        self.assertEqual(model._related, {})

        # fields

        self.assertEqual(model._fields._names["id"].name, "id")
        self.assertEqual(model._fields._names["id"].kind, int)
        self.assertTrue(model._fields._names["id"].auto)
        self.assertEqual(model._fields._names["name"].name, "name")
        self.assertEqual(model._fields._names["name"].kind, str)
        self.assertNotIn("nope", model._fields)

        # chunk and options

        model = Run(_chunk=5)
        self.assertEqual(model._chunk, 5)
        self.assertEqual(model._record._names["status"].options, ["pass", "fail"])

        # read

        model = UnitTest(_read={"id": 1, "name": "unit", "deffer": "test"})

        self.assertEqual(model._record["id"], 1)
        self.assertEqual(model._record["name"], "unit")
        self.assertEqual(model._record._action, "update")

        self.assertEqual(model._role, "model")
        self.assertEqual(model._mode, "one")
        self.assertEqual(model._action, "update")

        # parent

        model = Unit(_child={"id": 1})

        self.assertEqual(model._record._names["id"].criteria["eq"], 1)
        self.assertEqual(model._record._action, "retrieve")

        self.assertEqual(model._role, "parent")
        self.assertEqual(model._mode, "one")
        self.assertEqual(model._action, "retrieve")
        self.assertEqual(model._related, {"id": 1})

        # child one create

        model = Test(_parent={"unit_id": None}, _mode="one")

        self.assertEqual(model._role, "child")
        self.assertEqual(model._mode, "one")
        self.assertEqual(model._action, "create")
        self.assertEqual(model._related, {"unit_id": None})

        # child many retrieve

        models = Test(_parent={"unit_id": 1}, _mode="many")

        self.assertEqual(models._record._names["unit_id"].criteria["eq"], 1)
        self.assertEqual(models._record._action, "retrieve")

        self.assertEqual(models._role, "child")
        self.assertEqual(models._mode, "many")
        self.assertEqual(models._action, "retrieve")
        self.assertEqual(models._related, {"unit_id": 1})

        # retrieve

        model = Test(1, _action="retrieve", _mode="one")

        self.assertEqual(model._record._names["id"].criteria["eq"], 1)
        self.assertEqual(model._record._action, "retrieve")

        self.assertEqual(model._role, "model")
        self.assertEqual(model._mode, "one")
        self.assertEqual(model._action, "retrieve")
        self.assertEqual(model._related, {})

        # create

        model = UnitTest("unit")

        self.assertEqual(model._id, "id")
        self.assertEqual(model._record["name"], "unit")

        self.assertEqual(model._role, "model")
        self.assertEqual(model._mode, "one")
        self.assertEqual(model._action, "create")
        self.assertEqual(model._related, {})

        # With names

        model = UnitTest(id="1", name="unit")
        self.assertEqual(model._record["id"], 1)
        self.assertEqual(model._record["name"], "unit")

        # Create multiple

        models = UnitTest([{"id": "1", "name": "unit"}])
        self.assertEqual(models._models[0]._record["id"], 1)
        self.assertEqual(models._models[0]._record["name"], "unit")

        self.assertEqual(models._role, "model")
        self.assertEqual(models._mode, "many")
        self.assertEqual(models._action, "create")
        self.assertEqual(models._related, {})

        # Create bulk

        models = UnitTest(_bulk=True, _size=4)
        self.assertEqual(models._models, [])

        self.assertEqual(models._role, "model")
        self.assertEqual(models._mode, "many")
        self.assertEqual(models._action, "create")
        self.assertEqual(models._related, {})
        self.assertTrue(models._bulk)
        self.assertEqual(models._size, 4)

    def test___setattr__(self):

        # model

        # single

        model = UnitTest("unit")
        model.id = 2
        self.assertEqual(model._record['id'], 2)

        net = Net("1.2.3.4")
        net.ip__address = "1.2.3.4"
        self.assertEqual(net._record['ip'].compressed, "1.2.3.4")

        # multiple, with records

        models = UnitTest([{"name": "unit"}, {"name": "test"}])
        models.id = 3
        self.assertEqual(models._models[0]._record.id, 3)
        self.assertEqual(models._models[1]._record.id, 3)

        # multiple, no records

        models = UnitTest([])

        def nope():

            models.id = 4

        self.assertRaisesRegex(relations.ModelError, "unit_test: no records", nope)

        # child

        # one to one, no records

        test = Test()

        def nope():

            test.case.name = "nope"

        self.assertRaisesRegex(relations.ModelError, "case: no record", nope)

        # one to one. with record

        test.case.add()

        test.case.name = "yep"

        self.assertEqual(test.case._models[0]._record._names["name"].value, "yep")

        # make sure ensure is called

        Unit("sure").create()

        unit = Unit.one(1)

        unit.id = 2
        self.assertEqual(unit._record['id'], 2)

    def test___getattr__(self):

        unit = Unit("ya")
        unit.test.add("sure")[0]
        unit.create()

        # All id's will be 1

        test = Test.one(1)

        self.assertEqual(test.unit.name, "ya")
        self.assertEqual(test.unit.test.name, ["sure"])
        self.assertRaisesRegex(relations.ModelError, "no record")

        test.case.add("whatever")
        test.update()

        self.assertEqual(test.case.name, "whatever")

        net = Net("1.2.3.4")

        self.assertEqual(net.ip__address, "1.2.3.4")

        def get():

            test.fail

        self.assertRaisesRegex(AttributeError, "has no attribute 'fail'", get)

    def test___getattribute__(self):

        # model

        # single

        model = UnitTest("unit")
        self.assertEqual(model.name, "unit")

        # multiple, with records

        models = UnitTest([{"name": "unit"}, {"name": "test"}])
        self.assertEqual(models.name, ["unit", "test"])

        # multiple, no records

        models = UnitTest([])

        models._models = None

        def nope():

            models.name

        self.assertRaisesRegex(relations.ModelError, "unit_test: no records", nope)

        # child

        # one to one, no records

        test = Test()

        def nope():

            test.case.name

        self.assertRaisesRegex(relations.ModelError, "case: no record", nope)

        # one to one, with record

        test.case.add()

        test.case.name = "yep"

        self.assertEqual(test.case.name, "yep")

        # make sure ensure is called

        Unit("sure").create()

        unit = Unit.one(1)

        self.assertEqual(unit.name, "sure")

    def test___len__(self):

        # model

        # single

        model = UnitTest("unit")
        self.assertEqual(len(model), 3)
        self.assertTrue(model)

        # multiple, with records

        models = UnitTest([{"name": "unit"}])
        self.assertEqual(len(models), 1)
        self.assertTrue(models)

        # multiple, no records

        models = UnitTest([])

        self.assertEqual(len(models), 0)
        self.assertFalse(models)

        # child

        # one to one, no records

        test = Test()

        self.assertEqual(len(test.case), 0)
        self.assertFalse(test.case)

        # one to one. with record

        test.case.add()

        test.case.name = "yep"

        self.assertEqual(len(test.case), 3)
        self.assertTrue(test.case)

        # make sure ensure is called

        Unit("sure").create()

        unit = Unit.one(1)

        self.assertEqual(len(unit), 2)

        unit = Unit.many()

        self.assertEqual(len(unit), 1)

    def test___iter__(self):

        # model

        # single

        model = UnitTest("unit")
        self.assertEqual(list(model), ["id", "name", "deffer"])

        # multiple, with records

        models = UnitTest([{"name": "unit"}, {"name": "test"}])
        self.assertEqual([model.name for model in models], ["unit", "test"])

        # multiple, no records

        models = UnitTest([])

        self.assertEqual(list(models), [])

        # child

        # one to one, no records

        test = Test()

        self.assertEqual(list(test.case), [])

        # one to one. with record

        test.case.add()

        test.case.name = "yep"

        self.assertEqual(list(test.case), ["id", "test_id", "name"])

        # make sure ensure is called

        Unit("sure").create()

        unit = Unit.one(1)

        self.assertEqual(list(unit), ["id", "name"])

    def test_keys(self):

        # many, VERBOTTEN

        self.assertRaisesRegex(relations.ModelError, "no keys with many", UnitTest([]).keys)

        # single

        model = UnitTest("unit")
        self.assertEqual(list(model.keys()), ["id", "name", "deffer"])
        self.assertEqual(dict(model), {"id": None, "name": "unit", "deffer": "test"})

        # child, one

        self.assertEqual(list(Test().case.keys()), [])
        self.assertEqual(list(Test().case.add().keys()), ["id", "test_id", "name"])

    def test___contains__(self):

       # model

        # single

        model = UnitTest("unit")
        self.assertIn("id", model)

        # multiple, with records

        models = UnitTest([{"name": "unit"}, {"name": "test"}])
        self.assertIn("id", models)

        # multiple, no records

        models = UnitTest([])

        self.assertNotIn("id", models)

        # child

        # one to one, no records

        test = Test()

        self.assertNotIn("id", test.case)

        # one to one. with record

        test.case.add()

        test.case.name = "yep"

        self.assertIn("id", test.case)

        # make sure ensure is called

        Unit("sure").create()

        unit = Unit.one(1)

        self.assertIn("id", unit)

    def test___setitem__(self):

        # model

        # single

        model = UnitTest("unit")
        model['id'] = 2
        self.assertEqual(model._record['id'], 2)

        # multiple, with records

        models = UnitTest([{"name": "unit"}, {"name": "test"}])
        models['id'] = 3
        self.assertEqual(models._models[0]._record.id, 3)
        self.assertEqual(models._models[1]._record.id, 3)

        # multiple, no overtiding models

        def nope():
            models[0] = 1

        self.assertRaisesRegex(relations.ModelError, "unit_test: no override", nope)

        # multiple, no records

        models = UnitTest([])

        def nope():

            models['id'] = 4

        self.assertRaisesRegex(relations.ModelError, "unit_test: no records", nope)

        # child

        # one to one, no records

        test = Test()

        def nope():

            test.case['name'] = "nope"

        self.assertRaisesRegex(relations.ModelError, "case: no record", nope)

        # one to one. with record

        test.case.add()

        test.case['name'] = "yep"

        self.assertEqual(test.case._models[0]._record._names["name"].value, "yep")

        # make sure ensure is called

        Unit("sure").create()

        unit = Unit.one(1)

        unit['id'] = 2
        self.assertEqual(unit._record['id'], 2)

    def test___getitem__(self):

        # model

        # single

        model = UnitTest("unit")
        self.assertEqual(model['name'], "unit")

        # multiple, with records

        models = UnitTest([{"name": "unit"}, {"name": "test"}])
        self.assertEqual(models['name'], ["unit", "test"])
        self.assertEqual(models[0]['name'], "unit")

        # multiple, no records

        models = UnitTest([])
        models._models = None

        def nope():

            models['name']

        self.assertRaisesRegex(relations.ModelError, "unit_test: no records", nope)

        # child

        # one to one, no records

        test = Test()

        def nope():

            test.case['name']

        self.assertRaisesRegex(relations.ModelError, "case: no record", nope)

        # one to one. with record

        test.case.add()

        test.case.name = "yep"

        self.assertEqual(test.case['name'], "yep")

        # make sure ensure is called

        Unit("sure").create()

        unit = Unit.one(1)

        self.assertEqual(unit['name'], "sure")

        unit = Unit("ya")
        unit.test.add("sure")[0]
        unit.create()

        # All id's will be 1

        test = Test.one(1)

        self.assertEqual(test['unit'].name, "ya")
        self.assertEqual(test['unit']['test'].name, ["sure"])

    def test__parent(self):

        class TestUnit(relations.Model):
            pass

        relation = unittest.mock.MagicMock()
        relation.child_parent = "unittest"

        TestUnit._parent(relation)

        self.assertEqual(TestUnit.PARENTS, {"unittest": relation})

    def test__child(self):

        class TestUnit(relations.Model):
            pass

        relation = unittest.mock.MagicMock()
        relation.parent_child = "unittest"

        TestUnit._child(relation)

        self.assertEqual(TestUnit.CHILDREN, {"unittest": relation})

    def test__sister(self):

        class TestUnit(relations.Model):
            pass

        relation = unittest.mock.MagicMock()
        relation.brother_sister = "unittest"

        TestUnit._sister(relation)

        self.assertEqual(TestUnit.SISTERS, {"unittest": relation})

    def test__brother(self):

        class TestUnit(relations.Model):
            pass

        relation = unittest.mock.MagicMock()
        relation.sister_brother = "unittest"

        TestUnit._brother(relation)

        self.assertEqual(TestUnit.BROTHERS, {"unittest": relation})

    def test__relate(self):

        Unit("ya").create()

        test = Test()

        # parents

        self.assertEqual(test.unit._related, {"id": None})
        self.assertEqual(test.unit._role, "parent")
        self.assertEqual(test.unit._mode, "one")
        self.assertEqual(test.unit._action, "retrieve")
        self.assertEqual(test.unit._record._action, "retrieve")
        self.assertIsNone(test.unit._record._names["id"].criteria["eq"])

        test.unit_id = 1
        self.assertEqual(test.unit._related, {"id": 1})
        self.assertEqual(test.unit.name, "ya")
        self.assertEqual(test.unit._action, "update")
        self.assertEqual(test.unit._record._action, "update")
        self.assertIsNone(test.unit._record._names["id"].criteria)

        # children

        # one to many

        unit = Unit()

        self.assertEqual(unit.test._related, {"unit_id": None})
        self.assertEqual(unit.test._role, "child")
        self.assertEqual(unit.test._mode, "many")
        self.assertEqual(unit.test._action, "create")

        unit.test.add("sure")
        self.assertEqual(unit.test[0]._record._action, "create")
        self.assertEqual(unit.test[0].name, "sure")
        self.assertIsNone(unit.test[0].unit_id)

        unit.id = 2

        self.assertEqual(unit.test._related, {"unit_id": 2})
        self.assertEqual(unit.test[0].unit_id, 2)

        unit = Unit.one(1)
        unit.test.add("sure")
        unit.update()

        unit = Unit.one(1)
        self.assertEqual(unit.test._related, {"unit_id": 1})
        self.assertEqual(unit.test._role, "child")
        self.assertEqual(unit.test._mode, "many")
        self.assertEqual(unit.test._action, "retrieve")
        self.assertEqual(unit.test._record._action, "retrieve")
        self.assertEqual(unit.test._record._names["unit_id"].criteria["eq"], 1)

        self.assertEqual(unit.test[0].id, 1)
        self.assertEqual(unit.test._role, "child")
        self.assertEqual(unit.test._mode, "many")
        self.assertEqual(unit.test._action, "update")
        self.assertEqual(unit.test[0]._record._action, "update")
        self.assertIsNone(unit.test[0]._record._names["unit_id"].criteria)

        # one to one

        unit.test.add("yessah")

        self.assertEqual(unit.test[1].case._related, {"test_id": None})
        self.assertEqual(unit.test[1].case._role, "child")
        self.assertEqual(unit.test[1].case._mode, "one")
        self.assertEqual(unit.test[1].case._action, "create")

        unit.test[1].case.add("whatever")
        self.assertEqual(unit.test[1].case._models[0]._action, "create")
        self.assertEqual(unit.test[1].case.name, "whatever")
        self.assertIsNone(unit.test[1].case.test_id)

        unit.test[1].id = 3

        self.assertEqual(unit.test[1].case._related, {"test_id": 3})
        self.assertEqual(unit.test[1].case.test_id, 3)

        test = Test.one(1)
        test.case.add("whatever")
        test.update()

        test = Test.one(1)
        self.assertEqual(test.case._related, {"test_id": 1})
        self.assertEqual(test.case._role, "child")
        self.assertEqual(test.case._mode, "one")
        self.assertEqual(test.case._action, "retrieve")
        self.assertEqual(test.case._record._action, "retrieve")
        self.assertEqual(test.case._record._names["test_id"].criteria["eq"], 1)

        self.assertEqual(test.case.id, 1)
        self.assertEqual(test.case._role, "child")
        self.assertEqual(test.case._mode, "one")
        self.assertEqual(test.case._action, "update")
        self.assertEqual(test.case._models[0]._action, "update")
        self.assertIsNone(test.case._models[0]._record._names["test_id"].criteria)

    def test__collate(self):

        unit = Unit("ya")
        unit.test.add("sure").add("yessah")[1].case.add("whatever")
        unit.create()

        test = Test.one(unit__name="ya", case__name="whatever")
        test._collate()

        self.assertEqual(test._record._names['unit_id'].criteria["in"], [1])
        self.assertEqual(test._record._names['id'].criteria["in"], [2])
        self.assertEqual(test.case[0].id, 1)

        test = Test.one()

        self.assertFalse(test.overflow)

        test = Test.one(unit__name="ya", _chunk=1)
        test._collate()

        self.assertTrue(test.overflow)

        test = Test.one(case__name="whatever", _chunk=1)
        test._collate()

        self.assertTrue(test.overflow)

    def test__propagate(self):

        unit = Unit(name="ya")
        test = Test(name="sure")
        case = Case(name="whatever")

        self.assertNotIn("test", unit._children)
        self.assertNotIn("unit", test._parents)
        self.assertNotIn("case", test._children)
        self.assertNotIn("test", case._parents)

        test.unit_id = 1

        self.assertEqual(test.unit._role, "parent")
        self.assertEqual(test.unit._mode, "one")
        self.assertEqual(test.unit._action, "retrieve")
        self.assertEqual(test.unit._record._action, "retrieve")
        self.assertEqual(test.unit._record._names["id"].criteria, {"eq": 1})

        unit.create()

        self.assertEqual(test.unit.id, 1)
        self.assertEqual(test.unit.name, "ya")

        test.unit_id = 2

        self.assertIsNone(test._parents["unit"])

        self.assertEqual(test.unit._role, "parent")
        self.assertEqual(test.unit._mode, "one")
        self.assertEqual(test.unit._action, "retrieve")
        self.assertEqual(test.unit._record._action, "retrieve")

        test.set(unit_id=1).create()

        unit = Unit("yep")
        unit.test.add("sup")

        self.assertIsNone(unit.test[0].unit_id)
        self.assertEqual(unit.test._related, {"unit_id": None})
        self.assertEqual(unit.test[0]._related, {"unit_id": None})

        unit.create()

        self.assertEqual(unit.test[0].unit_id, 2)
        self.assertEqual(unit.test._related, {"unit_id": 2})
        self.assertEqual(unit.test[0]._related, {"unit_id": 2})

    def test__input(self):

        model = UnitTest()

        model._input(model._record, "unit")
        self.assertEqual(model.name, "unit")

        model._input(model._record, id=2, name="test")
        self.assertEqual(model.id, 2)
        self.assertEqual(model.name, "test")

        model._record._order[0].readonly = True
        model._input(model._record, "write")
        self.assertEqual(model.id, 2)
        self.assertEqual(model.name, "write")

        model._record._order[0].readonly = False
        model._related = {"id": None}
        model._input(model._record, "relate")
        self.assertEqual(model.id, 2)
        self.assertEqual(model.name, "relate")

    def test__build(self):

        model = UnitTest()

        record = model._build("create", "unittest")
        self.assertEqual(record.name, "unittest")
        self.assertEqual(record.deffer, "test")

        record = model._build("create", _defaults=False, _read={"id": 2, "name": "test", "deffer": "unit"})
        self.assertEqual(record.id, 2)

        model._related = {"id": 3}
        record = model._build("create", _defaults=False)
        self.assertEqual(record.id, 3)
        self.assertIsNone(record.name)

    def test__ensure(self):

        Unit([["ya"], ["sure"], ["whatever"]]).create()

        units = Unit.many()
        units._ensure()
        self.assertEqual(units.name, ["sure", "whatever", "ya"])

        units = units.many(name="sure").set(name="shore")
        self.assertRaisesRegex(relations.ModelError, "unit: need to update", units._ensure)

    def test__each(self):

        unit = Unit("ya")
        self.assertEqual(len(unit._each()), 1)
        self.assertEqual(len(unit._each("create")), 1)
        self.assertEqual(len(unit._each("update")), 0)
        self.assertEqual(unit._each()[0].name, "ya")

        unit.create()
        self.assertEqual(len(unit._each()), 1)
        self.assertEqual(len(unit._each("create")), 0)
        self.assertEqual(len(unit._each("update")), 1)

        unit.test.add("sure")
        self.assertEqual(len(unit.test._each()), 1)
        self.assertEqual(len(unit.test._each("create")), 1)
        self.assertEqual(len(unit.test._each("update")), 0)
        self.assertEqual(unit.test._each()[0].name, "sure")

        unit.update()
        unit.test.add("whatever")
        self.assertEqual(len(unit.test._each()), 2)
        self.assertEqual(len(unit.test._each("create")), 1)
        self.assertEqual(len(unit.test._each("update")), 1)
        self.assertEqual(unit.test._each("update")[0].name, "sure")
        self.assertEqual(unit.test._each("create")[0].name, "whatever")

    def test_filter(self):

        models = UnitTest(_action="retrieve", _mode="many").filter(1).filter(name__ne="unittest")

        self.assertEqual(models._record._action, "retrieve")
        self.assertEqual(models._record._names["id"].criteria["eq"], 1)
        self.assertEqual(models._record._names["name"].criteria["ne"], ["unittest"])

        unit = Unit.many().filter(test__id__in=[1], like="fuzzy")

        self.assertEqual(unit._children['test']._record._names['id'].criteria['in'], [1])
        self.assertEqual(unit._children['test']._record._names['id'].criteria['in'], [1])

        test = Test.many().filter(like="fuzzy")

        self.assertEqual(test._like, "fuzzy")

    def test_bulk(self):

        models = UnitTest.bulk(4)

        self.assertEqual(models._models, [])
        self.assertEqual(models._role, "model")
        self.assertEqual(models._mode, "many")
        self.assertEqual(models._action, "create")
        self.assertEqual(models._related, {})
        self.assertTrue(models._bulk)
        self.assertEqual(models._size, 4)

    def test_one(self):

        models = UnitTest.one(1)

        self.assertEqual(models._mode, "one")
        self.assertEqual(models._action, "retrieve")
        self.assertEqual(models._record._action, "retrieve")
        self.assertEqual(models._record._names["id"].criteria["eq"], 1)

    def test_many(self):

        models = UnitTest.many(1, name__ne="unittest")

        self.assertEqual(models._mode, "many")
        self.assertEqual(models._action, "retrieve")
        self.assertEqual(models._record._action, "retrieve")
        self.assertEqual(models._record._names["id"].criteria["eq"], 1)
        self.assertEqual(models._record._names["name"].criteria["ne"], ["unittest"])

    def test_sort(self):

        models = Unit.many().sort().sort("id").sort("-name")

        self.assertEqual(models._sort, ["+id", "-name"])

        units = Unit([["ya"], ["sure"], ["whatever"]]).create().sort("name")
        self.assertEqual(units.name, ["sure", "whatever", "ya"])

        self.assertRaisesRegex(relations.ModelError, "unit: unknown sort field nope", Unit.many().sort, "nope")
        self.assertRaisesRegex(relations.ModelError, "unit: cannot sort one", Unit.one(name="ya").retrieve().sort)

    def test_limt(self):

        models = Unit.many().limit()
        self.assertEqual(models._limit, 100)
        self.assertEqual(models._offset, 0)

        models = Unit.many().limit(5, 2)

        self.assertEqual(models._limit, 5)
        self.assertEqual(models._offset, 2)

        models = Unit.many().limit(page=4, per_page=5)

        self.assertEqual(models._limit, 5)
        self.assertEqual(models._offset, 15)

        Unit([["ya"], ["sure"], ["whatever"]]).create()
        units = Unit.many().sort("name").limit(2)
        self.assertEqual(units.name, ["sure", "whatever"])

        self.assertRaisesRegex(relations.ModelError, "unit: can only limit retrieve", Unit.one(name="ya").retrieve().limit)

    def test_set(self):

        model = UnitTest().set("unit")
        self.assertEqual(model.name, "unit")
        model.create()

        model = UnitTest.one(name="unit").set(name="test")
        self.assertEqual(model.id, 1)
        self.assertEqual(model._action, "update")

        models = UnitTest.many(name="unit").set(name="test")
        self.assertEqual(models._record.name, "test")
        self.assertEqual(models._action, "retrieve")
        self.assertEqual(models._record._action, "update")
        self.assertEqual(models._record._names["name"].criteria["eq"], "unit")

    def test_add(self):

        model = UnitTest(name="unit")
        self.assertEqual(model.name, "unit")

        self.assertRaisesRegex(relations.ModelError, "only one allowed", model.add)

        models = UnitTest([{"name": "unit"}])
        models = models.add(_count=2, name="more")
        self.assertEqual(models.name, ["unit", "more", "more"])

        test = Test()

        self.assertRaisesRegex(relations.ModelError, "only one allowed", test.case.add, _count=2)

        test.case.add("sure")
        self.assertEqual(test.case.name, "sure")

        models = UnitTest.bulk(2)

        models.add("unit")

        self.assertIsNone(UnitTest.one().retrieve(False))

        models.add("test")

        self.assertEqual(models._models, [])

        self.assertEqual(len(UnitTest.many()), 2)

    def test_export(self):

        models = Net.many()
        self.assertEqual(models.export(), [])

        model = Net("1.2.3.4").create()
        self.assertEqual(model.export(), {
            "id": 1,
            "ip": {
                "address": "1.2.3.4",
                "value": 16909060
            }
        })

        models = Net.many()
        self.assertEqual(models.export(), [{
            "id": 1,
            "ip": {
                "address": "1.2.3.4",
                "value": 16909060
            }
        }])

    def test_define(self):

        Unit.define()

        self.assertEqual(Unit.define(), [{
            "ACTION": "add",
            "source": "TestModel",
            "name": "unit",
            "title": "Unit",
            "fields": [
                {
                    "name": "id",
                    "kind": "int",
                    "store": "id",
                    "none": True,
                    "auto": True
                },
                {
                    "name": "name",
                    "kind": "str",
                    "store": "name",
                    "none": False
                }
            ],
            "id": "id",
            "unique": {
                "name": ["name"]
            },
            "index": {}
        }])

    def test_create(self):

        Unit("yep").create()
        self.assertEqual(Unit.one(name="yep").id, 1)

        unit = Unit.one(0)
        self.assertRaisesRegex(relations.ModelError, "unit: cannot create during retrieve", unit.create)

    def test_count(self):

        self.assertEqual(Unit.many(name="yep").count(), 0)

        Unit("yep").create()
        self.assertEqual(Unit.many(name="yep").count(), 1)

        unit = Unit("sure")
        self.assertRaisesRegex(relations.ModelError, "unit: cannot count during create", unit.count)

    def test_retrieve(self):

        self.assertIsNone(Unit.one(name="yep").retrieve(False))

        Unit("yep").create()
        self.assertEqual(Unit.one(name="yep").retrieve().id, 1)

        unit = Unit("sure")
        self.assertRaisesRegex(relations.ModelError, "unit: cannot retrieve during create", unit.retrieve)

    def test_labels(self):

        Unit("yep").create()
        self.assertEqual(Unit.one(name="yep").labels().ids, [1])

        unit = Unit("sure")
        self.assertRaisesRegex(relations.ModelError, "unit: cannot labels during create", unit.labels)

    def test_update(self):

        unit = Unit("yep").create()
        unit.name = "sure"

        self.assertEqual(unit.update(), 1)
        self.assertEqual(Unit.one(name="sure").retrieve().id, 1)

        self.assertEqual(Unit.one(name="sure").set(name="whatever").update(), 1)

        unit = Unit("sure")
        self.assertRaisesRegex(relations.ModelError, "unit: cannot update during create", unit.update)

    def test_delete(self):

        unit = Unit("yep").create()

        self.assertEqual(unit.delete(), 1)
        self.assertIsNone(Unit.one(name="yep").retrieve(False))

        unit = Unit("sure").create()
        self.assertEqual(Unit.one(name="sure").delete(), 1)

        unit = Unit("sure")
        self.assertRaisesRegex(relations.ModelError, "unit: cannot delete during create", unit.delete)
