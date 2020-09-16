import unittest
import unittest.mock

import relations.model


class TestFieldError(unittest.TestCase):

    maxDiff = None

    def test___init__(self):

        error = relations.model.FieldError("unittest", "oops")

        self.assertEqual(error.field, "unittest")
        self.assertEqual(error.message, "oops")

class TestField(unittest.TestCase):

    maxDiff = None

    def setUp(self):

        self.source = unittest.mock.MagicMock()
        relations.SOURCES["TestField"] = self.source
        self.field = relations.model.Field(int)
        self.field._source = "TestField"

    def tearDown(self):

        del relations.SOURCES["TestField"]

    def test___init__(self):

        field = relations.model.Field(int, unit="test")
        self.assertEqual(field.kind, int)
        self.assertEqual(field.unit, "test")

    def test___setattr__(self):

        field = relations.model.Field(int)
        field.name = "id"
        self.assertEqual(field.kind, int)
        self.assertEqual(field.name, "id")
        self.assertEqual(field.store, "id")

        # Store override

        field = relations.model.Field(int, store="_id")
        field.name = "id"
        self.assertEqual(field.name, "id")
        self.assertEqual(field.store, "_id")

        def rename(name):
            field.name = name

        self.assertRaisesRegex(relations.model.FieldError, "field name 'define' is reserved - use the store attribute for this name", rename, 'define')
        self.assertRaisesRegex(relations.model.FieldError, "field name 'def__ine' cannot contain '__' - use the store attribute for this name", rename, 'def__ine')
        self.assertRaisesRegex(relations.model.FieldError, "field name '_define' cannot start with '_' - use the store attribute for this name", rename, '_define')

        field.value = "1"
        self.assertEqual(field.value, 1)
        self.assertTrue(field.changed)

        field.value = None
        self.assertIsNone(field.value)

    def test___getattribute__(self):

        field = relations.model.Field(int)

        field.value = "1"
        self.assertEqual(field.value, 1)

        field.value = None
        self.assertIsNone(field.value)

    def test_set(self):

        field = relations.model.Field(int, name="id")
        self.assertEqual(field.set("1"), 1)

        field.strict = False
        self.assertEqual(field.set("1"), "1")

        field = relations.model.Field([1], name="id", not_null=True)
        self.assertEqual(field.set(1.0), 1)

        self.assertRaisesRegex(relations.model.FieldError, "None not allowed for id", field.set, None)

        field = relations.model.Field([1], name="id")
        self.assertEqual(field.set(1.0), 1)

        self.assertRaisesRegex(relations.model.FieldError, "2 not in \[1\] for id", field.set, 2)

    def test_get(self):

        field = relations.model.Field(int, name="id")
        self.assertEqual(field.get(1), 1)

        field.strict = False
        self.assertEqual(field.get("1"), "1")

        field = relations.model.Field([1], name="id")
        self.assertEqual(field.get(1.0), 1)

        self.assertRaisesRegex(relations.model.FieldError, "2 not in \[1\] for id", field.get, 2)

    def test_filter(self):

        field = relations.model.Field(int)

        field.filter("1", "in")
        self.assertEqual(field.criteria["in"], [1])
        field.filter(2.0, "in")
        self.assertEqual(field.criteria["in"], [1, 2])

        field.filter("1", "ne")
        self.assertEqual(field.criteria["ne"], [1])
        field.filter(2.0, "ne")
        self.assertEqual(field.criteria["ne"], [1, 2])

        field.filter("1")
        self.assertEqual(field.criteria["eq"], 1)

        field.filter("1", "gt")
        self.assertEqual(field.criteria["gt"], 1)

        field.filter("1", "ge")
        self.assertEqual(field.criteria["ge"], 1)

        field.filter("1", "lt")
        self.assertEqual(field.criteria["lt"], 1)

        field.filter("1", "le")
        self.assertEqual(field.criteria["le"], 1)

        self.assertRaisesRegex(relations.model.FieldError, "unknown operator 'nope'", field.filter, 0, "nope")

    def test_satisfy(self):

        field = relations.model.Field(int, store="_id")
        field.filter("1", "in")
        self.assertTrue(field.satisfy({"_id": '1'}))
        self.assertFalse(field.satisfy({"_id": '2'}))

        field = relations.model.Field(int, store="_id")
        field.filter("1", "ne")
        self.assertTrue(field.satisfy({"_id": '2'}))
        self.assertFalse(field.satisfy({"_id": '1'}))

        field = relations.model.Field(int, store="_id")
        field.filter("1")
        self.assertTrue(field.satisfy({"_id": '1'}))
        self.assertFalse(field.satisfy({"_id": '2'}))

        field = relations.model.Field(int, store="_id")
        field.filter("1", "gt")
        self.assertTrue(field.satisfy({"_id": '2'}))
        self.assertFalse(field.satisfy({"_id": '1'}))

        field = relations.model.Field(int, store="_id")
        field.filter("1", "ge")
        self.assertTrue(field.satisfy({"_id": '1'}))
        self.assertFalse(field.satisfy({"_id": '0'}))

        field = relations.model.Field(int, store="_id")
        field.filter("1", "lt")
        self.assertTrue(field.satisfy({"_id": '0'}))
        self.assertFalse(field.satisfy({"_id": '1'}))

        field = relations.model.Field(int, store="_id")
        field.filter("1", "le")
        self.assertTrue(field.satisfy({"_id": '1'}))
        self.assertFalse(field.satisfy({"_id": '2'}))

    def test_read(self):

        field = relations.model.Field(int, store="_id")
        field.read({"_id": "1"})
        self.assertEqual(field.value, 1)
        self.assertFalse(field.changed)

    def test_write(self):

        field = relations.model.Field(int, store="_id")

        field.value = 1
        values = {}
        field.write(values)
        self.assertEqual(values, {'_id': 1})
        self.assertFalse(field.changed)

        field.value = 0
        field.readonly = True
        values = {}
        field.write(values)
        self.assertEqual(values, {})
        self.assertTrue(field.changed)

class TestRecordError(unittest.TestCase):

    maxDiff = None

    def test___init__(self):

        error = relations.model.RecordError("unittest", "oops")

        self.assertEqual(error.record, "unittest")
        self.assertEqual(error.message, "oops")

class TestRecord(unittest.TestCase):

    maxDiff = None

    def setUp(self):

        self.source = unittest.mock.MagicMock()

        self.record = relations.model.Record()

        self.id = relations.model.Field(int, name="id", store="_id")
        self.name = relations.model.Field(str, name="name", store="_name")

        self.record.append(self.id)
        self.record.append(self.name)

    def test___init__(self):

        record = relations.model.Record()

        self.assertEqual(record._order, [])
        self.assertEqual(record._names, {})

    def test_insert(self):

        record = relations.model.Record()

        id = relations.model.Field(int, name="id", store="_id")
        record.insert(0, id)
        self.assertEqual(record._order, [id])
        self.assertEqual(record._names, {"id": id})

        name = relations.model.Field(str, name="name", store="_name")
        record.insert(0, name)
        self.assertEqual(record._order, [name, id])
        self.assertEqual(record._names, {"id": id, "name": name})

    def test_append(self):

        record = relations.model.Record()

        id = relations.model.Field(int, name="id", store="_id")
        record.append(id)
        self.assertEqual(record._order, [id])
        self.assertEqual(record._names, {"id": id})

        name = relations.model.Field(str, name="name", store="_name")
        record.append(name)
        self.assertEqual(record._order, [id, name])
        self.assertEqual(record._names, {"id": id, "name": name})

    def test___setattr__(self):

        self.record.id = "1"
        self.assertEqual(self.id.value, 1)

    def test___getattr__(self):
        self.id.value = "1"
        self.assertEqual(self.record.id, 1)

        def nope():
            self.record.nope

    def test___len__(self):

        self.assertEqual(len(self.record), 2)

    def test___iter__(self):

        self.assertEqual([name for name in self.record], ["id", "name"])

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

        def nope():
            self.record['nope'] = 1

        self.assertRaisesRegex(relations.model.RecordError, "unknown field 'nope'", nope)

    def test___getitem__(self):

        self.id.value = "1"
        self.assertEqual(self.record[0], 1)
        self.assertEqual(self.record['id'], 1)

        def nope():
            self.record['nope']

        self.assertRaisesRegex(relations.model.RecordError, "unknown field 'nope'", nope)

    def test_action(self):

        self.record.action("ignore")
        self.assertEqual(self.record.action(), "ignore")

        self.assertRaisesRegex(relations.model.RecordError, "unknown action 'nope'", self.record.action, "nope")

    def test_filter(self):

        self.record.filter(0, "0")
        self.assertEqual(self.id.criteria["eq"], 0)

        self.record.filter("id", "1")
        self.assertEqual(self.id.criteria["eq"], 1)

        self.record.filter("id__ne", "2")
        self.assertEqual(self.id.criteria["ne"], [2])

        self.assertRaisesRegex(relations.model.RecordError, "unknown criterion 'nope'", self.record.filter, "nope", 0)

    def test_satisfy(self):

        self.record.filter("id", "1")
        self.record.filter("name", "unit")

        self.assertTrue(self.record.satisfy({"_id": 1, "_name": "unit"}))
        self.assertFalse(self.record.satisfy({"_id": 2, "_name": "unit"}))
        self.assertFalse(self.record.satisfy({"_id": 1, "_name": "test"}))

    def test_read(self):

        self.record.read({"_id": 1, "_name": "unit"})

        self.assertEqual(self.record.id, 1)
        self.assertEqual(self.record.name, "unit")

    def test_write(self):

        self.record.id = 1
        self.record.name = "unit"

        self.assertEqual(self.record.write({}), {"_id": 1, "_name": "unit"})


class TestModelError(unittest.TestCase):

    maxDiff = None

    def test___init__(self):

        error = relations.model.ModelError("unittest", "oops")

        self.assertEqual(error.model, "unittest")
        self.assertEqual(error.message, "oops")

class UnitTest(relations.model.Model):

    SOURCE = "TestModel"

    id = (int,)
    name = relations.model.Field(str, default="unittest")
    nope = False

class Unit(relations.model.Model):
    id = {"kind": int}
    name = str

class Test(relations.model.Model):
    id = int
    unit_id = int
    name = str

class Case(relations.model.Model):
    id = int
    test_id = int
    name = str

relations.model.OneToMany(Unit, Test)
relations.model.OneToOne(Test, Case)

class TestModel(unittest.TestCase):

    maxDiff = None

    def setUp(self):

        self.source = unittest.mock.MagicMock()
        relations.SOURCES["TestModel"] = self.source

    def tearDown(self):

        del relations.SOURCES["TestModel"]

    def test___init__(self):

        model = UnitTest("1", "unit")
        self.assertEqual(model._id, "id")
        self.assertEqual(model.id, 1)
        self.assertEqual(model.name, "unit")
        self.assertEqual(model._parents, {})
        self.assertEqual(model._children, {})
        self.assertEqual(model._sisters, {})
        self.assertEqual(model._brothers, {})
        self.assertFalse(model._single)

        model = UnitTest(id="1", name="unit")
        self.assertEqual(model.id, 1)
        self.assertEqual(model.name, "unit")

        models = UnitTest([], _single=True, _related={'id': 1})
        self.assertEqual(models._models, [])
        self.assertTrue(models._related, {'id': 1})
        self.assertTrue(models._single)

        models = UnitTest([["unit"]], _related={'id': 1})
        self.assertEqual(models._models[0]._record.id, 1)
        self.assertEqual(models.name, ["unit"])

        models = UnitTest([{"id": "1", "name": "unit"}])
        self.assertEqual(models.id, [1])
        self.assertEqual(models.name, ["unit"])

        model = UnitTest(_action="update", _read={"id": 1, "name": "unit"})
        self.assertEqual(model._record._action, "update")
        self.assertEqual(model.id, 1)
        self.assertEqual(model.name, "unit")

        models = UnitTest(_action="list", id="1")
        self.assertEqual(models._criteria._names["id"].criteria["eq"], 1)

        models = UnitTest(_action="get", name="unit")
        self.assertEqual(models._criteria._names["name"].criteria["eq"], "unit")

    @unittest.mock.patch("relations.model.Model.retrieve")
    def test___setattr__(self,  mock_retrieve):

        model = UnitTest("1", "unit")
        model.id = 2
        self.assertEqual(model.id, 2)

        models = UnitTest([{"id": "1", "name": "unit"}, {"id": "2", "name": "test"}])
        models.id = 3
        self.assertEqual(models.id, [3, 3])

        models = UnitTest(_action="list", id="1")

        def nope():
            models.id = 3

        self.assertRaisesRegex(relations.model.ModelError, "no records", nope)
        mock_retrieve.assert_called_once_with()

    def test___getattr__(self):

        unit = Unit()

        self.assertIsNotNone(unit.test)

    @unittest.mock.patch("relations.model.Model.retrieve")
    def test___getattribute__(self,  mock_retrieve):

        model = UnitTest("1", "unit")
        model.id = 2
        self.assertEqual(model.id, 2)

        models = UnitTest([{"id": "1", "name": "unit"}, {"id": "2", "name": "test"}])
        models.id = 3
        self.assertEqual(models.id, [3, 3])

        models = UnitTest(_action="list", id="1")

        def nope():
            models.id

        self.assertRaisesRegex(relations.model.ModelError, "no records", nope)
        mock_retrieve.assert_called_once_with()

    @unittest.mock.patch("relations.model.Model.retrieve")
    def test___len__(self,  mock_retrieve):

        model = UnitTest("1", "unit")
        self.assertEqual(len(model), 2)

        models = UnitTest([{"id": "1", "name": "unit"}])
        self.assertEqual(len(models), 1)

        models = UnitTest(_action="list", id="1")

        def nope():
            len(models)

        self.assertRaisesRegex(relations.model.ModelError, "no records", nope)
        mock_retrieve.assert_called_once_with()

    @unittest.mock.patch("relations.model.Model.retrieve")
    def test___iter__(self,  mock_retrieve):

        model = UnitTest("1", "unit")
        self.assertEqual([name for name in model], ["id", "name"])

        models = UnitTest([{"id": "1", "name": "unit"}])
        self.assertEqual([record.id for record in models], [1])

        models = UnitTest(_action="list", id="1")

        def nope():
            [nope for nope in models]

        self.assertRaisesRegex(relations.model.ModelError, "no records", nope)
        mock_retrieve.assert_called_once_with()

    @unittest.mock.patch("relations.model.Model.retrieve")
    def test___contains__(self,  mock_retrieve):

        model = UnitTest("1", "unit")

        self.assertIn(1, model)
        self.assertNotIn(2, model)

        self.assertIn("id", model)
        self.assertNotIn("nope", model)

        models = UnitTest([{"id": "1", "name": "unit"}])

        self.assertIn(0, models)
        self.assertNotIn(2, models)

        self.assertIn("id", models)
        self.assertNotIn("nope", models)

        models = UnitTest(_action="list", id="1")

        def nope():
            0 in models

        self.assertRaisesRegex(relations.model.ModelError, "no records", nope)
        mock_retrieve.assert_called_once_with()

    @unittest.mock.patch("relations.model.Model.retrieve")
    def test___setitem__(self,  mock_retrieve):

        model = UnitTest("1", "unit")

        model[0] = 2
        model["name"] = "test"

        self.assertEqual(model[0], 2)
        self.assertEqual(model["name"], "test")

        models = UnitTest([{"id": "1", "name": "unit"}])

        models["name"] = "test"

        self.assertEqual(models["name"], ["test"])

        def nope():
            models[0] = 1

        self.assertRaisesRegex(relations.model.ModelError, "no override", nope)

        models = UnitTest(_action="list", id="1")

        def nope():
            models[0] = 1

        self.assertRaisesRegex(relations.model.ModelError, "no records", nope)
        mock_retrieve.assert_called_once_with()

    @unittest.mock.patch("relations.model.Model.retrieve")
    def test___getitem__(self,  mock_retrieve):

        unit = Unit()

        self.assertIsNotNone(unit['test'])

        model = UnitTest("1", "unit")

        self.assertEqual(model[0], 1)
        self.assertEqual(model["name"], "unit")

        models = UnitTest([{"id": "1", "name": "unit"}])

        self.assertEqual(models[0].id, 1)
        self.assertEqual(models["name"], ["unit"])

        models = UnitTest(_action="list", id="1")

        def nope():
            models[0]

        self.assertRaisesRegex(relations.model.ModelError, "no records", nope)
        mock_retrieve.assert_called_once_with()

    def test__parent(self):

        class TestUnit(relations.model.Model):
            pass

        relation = unittest.mock.MagicMock()
        relation.child_parent = "unittest"

        TestUnit._parent(relation)

        self.assertEqual(TestUnit.PARENTS, {"unittest": relation})

    def test__child(self):

        class TestUnit(relations.model.Model):
            pass

        relation = unittest.mock.MagicMock()
        relation.parent_child = "unittest"

        TestUnit._child(relation)

        self.assertEqual(TestUnit.CHILDREN, {"unittest": relation})

    def test__sister(self):

        class TestUnit(relations.model.Model):
            pass

        relation = unittest.mock.MagicMock()
        relation.brother_sister = "unittest"

        TestUnit._sister(relation)

        self.assertEqual(TestUnit.SISTERS, {"unittest": relation})

    def test__brother(self):

        class TestUnit(relations.model.Model):
            pass

        relation = unittest.mock.MagicMock()
        relation.sister_brother = "unittest"

        TestUnit._brother(relation)

        self.assertEqual(TestUnit.BROTHERS, {"unittest": relation})

    def test__relate(self):

        test = Test()

        # parents

        # can't determine parent

        def nope():

            test.unit

        self.assertRaisesRegex(relations.model.ModelError, "can't access unit if unit_id not set", nope)

        # single parents

        test.unit_id = 1
        unit = test.unit
        self.assertEqual(unit._criteria._action, "get")
        self.assertEqual(unit._criteria._names["id"].criteria["eq"], 1)

        # multiple parents

        tests = Test([{"unit_id": 1}, {"unit_id": 2}, {"unit_id": 3}])

        unit = tests.unit
        self.assertEqual(unit._criteria._action, "list")
        self.assertEqual(unit._criteria._names["id"].criteria["in"], [1, 2, 3])

        # searching for parents (so sad)

        tests = Test.list()

        unit = tests.unit
        self.assertEqual(unit._criteria._action, "list")
        self.assertIsNone(unit._criteria._names["id"].criteria)

        # children

        # searching for children (even sadder)

        cases = tests.case
        self.assertEqual(cases._criteria._action, "list")

        # creating children (much better) from single create

        # one to one

        test = Test()

        test.id = 4
        cases = test.case
        self.assertTrue(cases._single)
        self.assertEqual(cases._related, {"test_id": 4})
        self.assertEqual(cases._models, [])

        # one to many

        unit = Unit()

        unit.id = 5
        tests = unit.test
        self.assertFalse(tests._single)
        self.assertEqual(tests._related, {"unit_id": 5})
        self.assertEqual(tests._models, [])

        # creating children from single update

        # one to one

        test = Test()
        test._record.action("update")

        test.id = 4
        cases = test.case
        self.assertTrue(cases._single)
        self.assertEqual(cases._related, {"test_id": 4})
        self.assertEqual(cases._criteria._names["test_id"].criteria["eq"], 4)

        # one to many

        unit = Unit()
        unit._record.action("update")

        unit.id = 5
        tests = unit.test
        self.assertFalse(tests._single)
        self.assertEqual(tests._related, {"unit_id": 5})
        self.assertEqual(tests._criteria._names["unit_id"].criteria["eq"], 5)

        # creating children from multiple create with id's

        units = Unit([[6], [7], [8]])

        tests = units.test
        self.assertEqual(tests._related, {})
        self.assertEqual(tests._criteria._action, "list")
        self.assertEqual(tests._criteria._names["unit_id"].criteria["in"], [6, 7, 8])

        # creating children from multiple create without

        units = Unit([[], [], []])

        tests = units.test
        self.assertEqual(tests._related, {})
        self.assertEqual(tests._models, [])

        # children from criteria

        units = Unit().list()

        tests = units.test
        self.assertEqual(tests._criteria._action, "list")
        self.assertIsNone(tests._criteria._names["unit_id"].criteria)

    def test__collate(self):

        Test()._collate()

        test = Test.list()

        test._parents['unit'] = Unit(1, "unit")
        test._children['case'] = Case(3, 2, "case")

        test._collate()

        self.assertEqual(test._criteria._names["id"].criteria["in"], [2])
        self.assertEqual(test._criteria._names["unit_id"].criteria["in"], [1])

    def test__propagate(self):

        test = Test()
        test.unit_id = 1

        test.unit
        self.assertIsNotNone(test._parents['unit'])
        test.unit_id = 2
        self.assertIsNone(test._parents['unit'])

        test.case.add()
        self.assertIsNotNone(test._children['case'])
        test.id = 3
        self.assertEqual(test._children['case']._related['test_id'], 3)
        self.assertEqual(test._children['case']._models[0]._related['test_id'], 3)
        self.assertEqual(test._children['case'][0].test_id, 3)

    def test__extract(self):

        kwargs = {
            "people": 3,
            "things": 1
        }

        self.assertEqual(relations.model.Model._extract(kwargs, "people"), 3)
        self.assertEqual(relations.model.Model._extract(kwargs, "stuff", 2), 2)
        self.assertEqual(kwargs, {"things": 1})

    def test__input(self):

        model = UnitTest("0", "")

        model._input(model._record, 1, "unit")
        self.assertEqual(model.id, 1)
        self.assertEqual(model.name, "unit")

        model._input(model._record, id=2, name="test")
        self.assertEqual(model.id, 2)
        self.assertEqual(model.name, "test")

        model._record._order[0].readonly = True
        model._input(model._record, "write")
        self.assertEqual(model.id, 2)
        self.assertEqual(model.name, "write")

    def test__build(self):

        model = UnitTest("0", "")

        record = model._build("create", 1)
        self.assertEqual(record.id, 1)
        self.assertEqual(record.name, "unittest")

        record = model._build("create", _defaults=False, _read={"id": 2})
        self.assertEqual(record.id, 2)
        self.assertIsNone(record.name)

        model._related = {"id": 3}
        record = model._build("create", _defaults=False)
        self.assertEqual(record.id, 3)
        self.assertIsNone(record.name)

    @unittest.mock.patch("relations.model.Model.update")
    @unittest.mock.patch("relations.model.Model.retrieve")
    def test__ensure_(self,  mock_retrieve, mock_update):

        models = UnitTest.list()
        models._ensure()
        mock_retrieve.assert_called_once_with()

        models.set()
        models._ensure()
        mock_update.assert_called_once_with(True)
        mock_retrieve.assert_called_once_with()

    def test_each(self,):

        model = UnitTest("1", "unit")
        self.assertEqual(model.each()[0].id, 1)
        self.assertEqual(model.each("create")[0].id, 1)
        self.assertEqual(model.each("ignore"), [])

        models = UnitTest([{"id": "1", "name": "unit"}, {"id": "2", "name": "test"}])

        self.assertEqual(models.each()[1].id, 2)
        self.assertEqual(models.each("create")[1].id, 2)
        self.assertEqual(models.each("ignore"), [])

        models = UnitTest(_action="list", id="1")
        self.assertEqual(models.each(), [])

    def test_filter(self):

        models = UnitTest(_action="list").filter(1).filter(name__ne="unittest")

        self.assertEqual(models._criteria._action, "list")
        self.assertEqual(models._criteria._names["id"].criteria["eq"], 1)
        self.assertEqual(models._criteria._names["name"].criteria["ne"], ["unittest"])

        unit = Unit.list().filter(test__id__in=[1])

        self.assertEqual(unit._children['test']._criteria._names['id'].criteria['in'], [1])

    def test_list(self):

        models = UnitTest.list(1, name__ne="unittest")

        self.assertEqual(models._criteria._action, "list")
        self.assertEqual(models._criteria._names["id"].criteria["eq"], 1)
        self.assertEqual(models._criteria._names["name"].criteria["ne"], ["unittest"])

    def test_get(self):

        models = UnitTest.get(1)

        self.assertEqual(models._criteria._action, "get")
        self.assertEqual(models._criteria._names["id"].criteria["eq"], 1)

    def test_set(self):

        model = UnitTest().set(name="unit")
        self.assertEqual(model.name, "unit")

        models = UnitTest.list().set(2, name="test")
        self.assertEqual(models._record.id, 2)
        self.assertEqual(models._record.name, "test")

    def test_set(self):

        model = UnitTest().set(name="unit")
        self.assertEqual(model.name, "unit")

        models = UnitTest.list().set(2, name="test")
        self.assertEqual(models._record.id, 2)
        self.assertEqual(models._record.name, "test")

    def test_add(self):

        model = UnitTest(1, name="unit")
        self.assertEqual(model.name, "unit")

        self.assertRaisesRegex(relations.model.ModelError, "only one allowed", model.add)

        models = UnitTest([{"id": 1, "name": "unit"}])
        models = models.add(_count=2, name="more")
        self.assertEqual(models.name, ["unit", "more", "more"])

        test = Test()

        self.assertRaisesRegex(relations.model.ModelError, "only one allowed", test.case.add, _count=2)

        test.case.add(3, "sure")
        self.assertEqual(test.case[0].id, 3)
        self.assertEqual(test.case[0].name, "sure")

        self.assertRaisesRegex(relations.model.ModelError, "only one allowed", test.case.add)

    def test_define(self):

        model = UnitTest()
        model.define()
        self.source.model_define.assert_called_with(model)

    def test_create(self):

        model = UnitTest()
        model.create()
        self.source.model_create.assert_called_with(model)

    def test_retrieve(self):

        model = UnitTest()
        model.retrieve()
        self.source.model_retrieve.assert_called_with(model, True)

    def test_update(self):

        model = UnitTest()
        model.update()
        self.source.model_update.assert_called_with(model)

    def test_delete(self):

        model = UnitTest()
        model.delete()
        self.source.model_delete.assert_called_with(model)

    @unittest.mock.patch("relations.model.Model.create")
    @unittest.mock.patch("relations.model.Model.update")
    @unittest.mock.patch("relations.model.Model.delete")
    def test_execute(self,  mock_delete, mock_update, mock_create):

        model = UnitTest([]).add(_count=3)

        model._models[1]._record.action("update")
        model._models[2]._record.action("delete")

        model.execute()

        mock_create.assert_called_once_with(False)
        mock_update.assert_called_once_with(False)
        mock_delete.assert_called_once_with()

        model.execute(True)
        mock_create.assert_called_with(True)
        mock_update.assert_called_with(True)


class TestRelation(unittest.TestCase):

    maxDiff = None

    def setUp(self):

        self.source = unittest.mock.MagicMock()
        relations.SOURCES["TestModel"] = self.source

    def tearDown(self):

        del relations.SOURCES["TestModel"]

    def test_field_name(self):

        unittest = UnitTest()

        self.assertEqual(relations.model.Relation.field_name("id", unittest), "id")
        self.assertEqual(relations.model.Relation.field_name(1, unittest), "name")

        self.assertRaisesRegex(relations.model.ModelError, "cannot find field nope in unittest", relations.model.Relation.field_name, "nope", unittest)

    def test_relative_field(self):

        class TestUnit(relations.model.Model):
            id = int
            name = str
            ident = int

        class Test(relations.model.Model):
            ident = int
            unit_id = int
            name = str

        class Unit(relations.model.Model):
            id = int
            testunit_id = int
            test_ident = int
            name = str

        class Equal(relations.model.Relation):
            SAME = True

        class Unequal(relations.model.Relation):
            SAME = False

        testunit = TestUnit()
        test = Test()
        unit = Unit()

        self.assertEqual(relations.model.Relation.relative_field(testunit, unit), "testunit_id")
        self.assertEqual(relations.model.Relation.relative_field(test, unit), "test_ident")
        self.assertEqual(relations.model.Relation.relative_field(test, testunit), "ident")
        self.assertEqual(Equal.relative_field(unit, testunit), "id")

        self.assertRaisesRegex(relations.model.ModelError, "cannot determine field for unit in testunit", Unequal.relative_field, unit, testunit)

class TestOneTo(unittest.TestCase):

    maxDiff = None

    def test___init__(self):

        class Mom(relations.model.Model):
            id = int
            name = str
            ident = int

        class Son(relations.model.Model):
            id = int
            mom_id = int
            name = str
            mom_ident = int

        relation = relations.model.OneTo(Mom, Son)

        self.assertEqual(relation.Parent, Mom)
        self.assertEqual(relation.Child, Son)

        self.assertEqual(relation.parent_child, "son")
        self.assertEqual(relation.child_parent, "mom")
        self.assertEqual(relation.parent_field, "id")
        self.assertEqual(relation.child_field, "mom_id")

        relation = relations.model.OneTo(Mom, Son, "sons", "mommy", "ident", "mom_ident")

        self.assertEqual(relation.parent_child, "sons")
        self.assertEqual(relation.child_parent, "mommy")
        self.assertEqual(relation.parent_field, "ident")
        self.assertEqual(relation.child_field, "mom_ident")

class TestOneToMany(unittest.TestCase):

    maxDiff = None

    def test___init__(self):

        class Mom(relations.model.Model):
            id = int
            name = str

        class Son(relations.model.Model):
            id = int
            mom_id = int
            name = str

        relation = relations.model.OneToMany(Mom, Son)

        self.assertEqual(relation.Parent, Mom)
        self.assertEqual(relation.Child, Son)

        self.assertEqual(relation.parent_child, "son")
        self.assertEqual(relation.child_parent, "mom")
        self.assertEqual(relation.parent_field, "id")
        self.assertEqual(relation.child_field, "mom_id")

class TestOneToOne(unittest.TestCase):

    maxDiff = None

    def test___init__(self):

        class Mom(relations.model.Model):
            id = int
            name = str

        class Son(relations.model.Model):
            id = int
            name = str

        relation = relations.model.OneToOne(Mom, Son)

        self.assertEqual(relation.Parent, Mom)
        self.assertEqual(relation.Child, Son)

        self.assertEqual(relation.parent_child, "son")
        self.assertEqual(relation.child_parent, "mom")
        self.assertEqual(relation.parent_field, "id")
        self.assertEqual(relation.child_field, "id")
