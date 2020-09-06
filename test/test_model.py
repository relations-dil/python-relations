import unittest
import unittest.mock

import relations.model


class TestField(unittest.TestCase):

    maxDiff = None

    def test___init__(self):

        # Extra

        field = relations.model.Field(int, unit="test")
        self.assertEqual(field.kind, int)
        self.assertEqual(field.unit, "test")

    def test___setattr__(self):

        field = relations.model.Field(int)
        field.name = "id"
        self.assertEqual(field.name, "id")
        self.assertEqual(field.store, "id")

        # Store override

        field = relations.model.Field(int, store="_id")
        field.name = "id"
        self.assertEqual(field.name, "id")
        self.assertEqual(field.store, "_id")

        def rename(name):
            field.name = name

        self.assertRaisesRegex(ValueError, "field name 'define' is reserved - use the store attribute for this name", rename, 'define')
        self.assertRaisesRegex(ValueError, "field name 'def__ine' cannot contain '__' - use the store attribute for this name", rename, 'def__ine')
        self.assertRaisesRegex(ValueError, "field name '_define' cannot start with '_' - use the store attribute for this name", rename, '_define')

        field.value = "1"
        self.assertEqual(field.value, 1)
        self.assertTrue(field.changed)

        field.value = None
        self.assertIsNone(field.value)

    def test___getattribute__(self):

        field = relations.model.Field(int)

        field.value = "1"
        self.assertEqual(field.value, 1)
        self.assertTrue(field.changed)

        field.value = None
        self.assertIsNone(field.value)

    def test_set(self):

        field = relations.model.Field(int, name="id")
        self.assertEqual(field.set("1"), 1)

        field.strict = False
        self.assertEqual(field.set("1"), "1")

        field = relations.model.Field([1], name="id")
        self.assertEqual(field.set(1.0), 1)

        self.assertRaisesRegex(ValueError, "2 not in \[1\] for id", field.set, 2)

        field = relations.model.Field({"a": 1}, name="id")
        self.assertEqual(field.set(1), "a")

        self.assertRaisesRegex(ValueError, "2 not in \[1\] for id", field.set, 2)

    def test_get(self):

        field = relations.model.Field(int, name="id")
        self.assertEqual(field.get(1), 1)

        field.strict = False
        self.assertEqual(field.get("1"), "1")

        field = relations.model.Field([1], name="id")
        self.assertEqual(field.get(1.0), 1)

        self.assertRaisesRegex(ValueError, "2 not in \[1\] for id", field.get, 2)

        field = relations.model.Field({"a": 1}, name="id")
        self.assertEqual(field.get("a"), 1)

        self.assertRaisesRegex(ValueError, "b not in \['a'\] for id", field.get, "b")

    def test_define(self):

        # With definition

        field = relations.model.Field(int, definition="test")
        self.assertEqual(field.define(), "test")

        # Without

        field = relations.model.Field(int)
        self.assertRaisesRegex(NotImplementedError, "need to implement 'define' on <class", field.define)

    def test_filter(self):

        field = relations.model.Field(int)

        field.filter("1", "in")
        self.assertEqual(field.search["in"], [1])
        field.filter(2.0, "in")
        self.assertEqual(field.search["in"], [1, 2])

        field.filter("1", "ne")
        self.assertEqual(field.search["ne"], [1])
        field.filter(2.0, "ne")
        self.assertEqual(field.search["ne"], [1, 2])

        field.filter("1")
        self.assertEqual(field.search["eq"], 1)

        field.filter("1", "gt")
        self.assertEqual(field.search["gt"], 1)

        field.filter("1", "ge")
        self.assertEqual(field.search["ge"], 1)

        field.filter("1", "lt")
        self.assertEqual(field.search["lt"], 1)

        field.filter("1", "le")
        self.assertEqual(field.search["le"], 1)

        self.assertRaisesRegex(ValueError, "unknown operator 'nope'", field.filter, 0, "nope")

    def test_match(self):

        field = relations.model.Field(int, store="_id")
        field.filter("1", "in")
        self.assertTrue(field.match({"_id": '1'}))
        self.assertFalse(field.match({"_id": '2'}))

        field = relations.model.Field(int, store="_id")
        field.filter("1", "ne")
        self.assertTrue(field.match({"_id": '2'}))
        self.assertFalse(field.match({"_id": '1'}))

        field = relations.model.Field(int, store="_id")
        field.filter("1")
        self.assertTrue(field.match({"_id": '1'}))
        self.assertFalse(field.match({"_id": '2'}))

        field = relations.model.Field(int, store="_id")
        field.filter("1", "gt")
        self.assertTrue(field.match({"_id": '2'}))
        self.assertFalse(field.match({"_id": '1'}))

        field = relations.model.Field(int, store="_id")
        field.filter("1", "ge")
        self.assertTrue(field.match({"_id": '1'}))
        self.assertFalse(field.match({"_id": '0'}))

        field = relations.model.Field(int, store="_id")
        field.filter("1", "lt")
        self.assertTrue(field.match({"_id": '0'}))
        self.assertFalse(field.match({"_id": '1'}))

        field = relations.model.Field(int, store="_id")
        field.filter("1", "le")
        self.assertTrue(field.match({"_id": '1'}))
        self.assertFalse(field.match({"_id": '2'}))

    def test_read(self):

        field = relations.model.Field(int, store="_id")
        field.changed = True
        field.read({"_id": "1"})
        self.assertEqual(field.value, 1)
        self.assertFalse(field.changed)

    def test_write(self):

        field = relations.model.Field(int, store="_id")

        field.value = 1
        field.changed = True
        values = {}
        field.write(values)
        self.assertEqual(values, {'_id': 1})
        self.assertFalse(field.changed)

        field.readonly = True
        values = {}
        field.write(values)
        self.assertEqual(values, {})


class TestRecord(unittest.TestCase):

    maxDiff = None

    def setUp(self):

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

        self.assertRaisesRegex(ValueError, "unknown field 'nope'", nope)

    def test___getitem__(self):

        self.id.value = "1"
        self.assertEqual(self.record[0], 1)
        self.assertEqual(self.record['id'], 1)

        def nope():
            self.record['nope']

        self.assertRaisesRegex(ValueError, "unknown field 'nope'", nope)

    def test_action(self):

        self.record.action("ignore")
        self.assertEqual(self.record.action(), "ignore")

        self.assertRaisesRegex(ValueError, "unknown action 'nope'", self.record.action, "nope")

    def test_filter(self):

        self.record.filter(0, "0")
        self.assertEqual(self.id.search["eq"], 0)

        self.record.filter("id", "1")
        self.assertEqual(self.id.search["eq"], 1)

        self.record.filter("id__ne", "2")
        self.assertEqual(self.id.search["ne"], [2])

        self.assertRaisesRegex(ValueError, "unknown criterion 'nope'", self.record.filter, "nope", 0)

    def test_match(self):

        self.record.filter("id", "1")
        self.record.filter("name", "unit")

        self.assertTrue(self.record.match({"_id": 1, "_name": "unit"}))
        self.assertFalse(self.record.match({"_id": 2, "_name": "unit"}))
        self.assertFalse(self.record.match({"_id": 1, "_name": "test"}))

    def test_read(self):

        self.record.read({"_id": 1, "_name": "unit"})

        self.assertEqual(self.record.id, 1)
        self.assertEqual(self.record.name, "unit")

    def test_write(self):

        self.record.id = 1
        self.record.name = "unit"

        self.assertEqual(self.record.write({}), {"_id": 1, "_name": "unit"})


class UnitTest(relations.model.Model):
    id = int
    name = relations.model.Field(str, default="unittest")
    nope = False

class TestModel(unittest.TestCase):

    maxDiff = None

    def test___init__(self):

        model = UnitTest("1", "unit")
        self.assertEqual(model.id, 1)
        self.assertEqual(model.name, "unit")

        model = UnitTest(id="1", name="unit")
        self.assertEqual(model.id, 1)
        self.assertEqual(model.name, "unit")

        models = UnitTest([])
        self.assertEqual(models._models, [])

        models = UnitTest([["1", "unit"]])
        self.assertEqual(models._models[0]._record.id, 1)
        self.assertEqual(models.name, ["unit"])

        models = UnitTest([{"id": "1", "name": "unit"}])
        self.assertEqual(models.id, [1])
        self.assertEqual(models.name, ["unit"])

        models = UnitTest(_action="list", id="1")
        self.assertEqual(models._search._names["id"].search["eq"], 1)

        models = UnitTest(_action="get", name="unit")
        self.assertEqual(models._search._names["name"].search["eq"], "unit")

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

        self.assertRaisesRegex(ValueError, "no records", nope)
        mock_retrieve.assert_called_once_with()

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

        self.assertRaisesRegex(ValueError, "no records", nope)
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

        self.assertRaisesRegex(ValueError, "no records", nope)
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

        self.assertRaisesRegex(ValueError, "no records", nope)
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

        self.assertRaisesRegex(ValueError, "no records", nope)
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

        self.assertRaisesRegex(ValueError, "no override", nope)

        models = UnitTest(_action="list", id="1")

        def nope():
            models[0] = 1

        self.assertRaisesRegex(ValueError, "no records", nope)
        mock_retrieve.assert_called_once_with()

    @unittest.mock.patch("relations.model.Model.retrieve")
    def test___getitem__(self,  mock_retrieve):

        model = UnitTest("1", "unit")

        self.assertEqual(model[0], 1)
        self.assertEqual(model["name"], "unit")

        models = UnitTest([{"id": "1", "name": "unit"}])

        self.assertEqual(models[0].id, 1)
        self.assertEqual(models["name"], ["unit"])

        models = UnitTest(_action="list", id="1")

        def nope():
            models[0]

        self.assertRaisesRegex(ValueError, "no records", nope)
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

    def test___extract(self):

        kwargs = {
            "people": 3,
            "things": 1
        }

        self.assertEqual(relations.model.Model._extract(kwargs, "people"), 3)
        self.assertEqual(relations.model.Model._extract(kwargs, "stuff", 2), 2)
        self.assertEqual(kwargs, {"things": 1})

    def test___input(self):

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

    def test___build(self):

        model = UnitTest("0", "")

        record = model._build("create", 1)
        self.assertEqual(record.id, 1)
        self.assertEqual(record.name, "unittest")

        record = model._build("create", _defaults=False, _read={"id": 2})
        self.assertEqual(record.id, 2)
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

    def test__records(self,):

        model = UnitTest("1", "unit")
        self.assertEqual(model._records()[0].id, 1)
        self.assertEqual(model._records("create")[0].id, 1)
        self.assertEqual(model._records("ignore"), [])

        models = UnitTest([{"id": "1", "name": "unit"}, {"id": "2", "name": "test"}])

        self.assertEqual(models._records()[1].id, 2)
        self.assertEqual(models._records("create")[1].id, 2)
        self.assertEqual(models._records("ignore"), [])

        models = UnitTest(_action="list", id="1")
        self.assertEqual(models._records(), [])

    def test_filter(self):

        models = UnitTest(_action="list").filter(1).filter(name__ne="unittest")

        self.assertEqual(models._search._action, "list")
        self.assertEqual(models._search._names["id"].search["eq"], 1)
        self.assertEqual(models._search._names["name"].search["ne"], ["unittest"])

    def test_list(self):

        models = UnitTest.list(1, name__ne="unittest")

        self.assertEqual(models._search._action, "list")
        self.assertEqual(models._search._names["id"].search["eq"], 1)
        self.assertEqual(models._search._names["name"].search["ne"], ["unittest"])

    def test_get(self):

        models = UnitTest.get(1)

        self.assertEqual(models._search._action, "get")
        self.assertEqual(models._search._names["id"].search["eq"], 1)

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

        models = model.add(2, name="test")
        self.assertEqual(models.id, [1, 2])
        self.assertEqual(models.name, ["unit", "test"])

        models = models.add(_count=2, name="more")
        self.assertEqual(models.name, ["unit", "test", "more", "more"])

    def test_define(self):

        model = UnitTest()
        self.assertRaisesRegex(NotImplementedError, "need to implement 'define' on <class", model.define)

    def test_create(self):

        model = UnitTest()
        self.assertRaisesRegex(NotImplementedError, "need to implement 'create' on <class", model.create)

    def test_retrieve(self):

        model = UnitTest()
        self.assertRaisesRegex(NotImplementedError, "need to implement 'retrieve' on <class", model.retrieve)

    def test_update(self):

        model = UnitTest()
        self.assertRaisesRegex(NotImplementedError, "need to implement 'update' on <class", model.update)

    def test_delete(self):

        model = UnitTest()
        self.assertRaisesRegex(NotImplementedError, "need to implement 'delete' on <class", model.delete)

    @unittest.mock.patch("relations.model.Model.create")
    @unittest.mock.patch("relations.model.Model.update")
    @unittest.mock.patch("relations.model.Model.delete")
    def test_execute(self,  mock_delete, mock_update, mock_create):

        model = UnitTest()
        model.execute()

        mock_create.assert_called_once_with(False)
        mock_update.assert_called_once_with(False)
        mock_delete.assert_called_once_with()

        model.execute(True)
        mock_create.assert_called_with(True)
        mock_update.assert_called_with(True)


class TestRelation(unittest.TestCase):

    maxDiff = None

    def test_field_name(self):

        unittest = UnitTest()

        self.assertEqual(relations.model.Relation.field_name("id", unittest), "id")
        self.assertEqual(relations.model.Relation.field_name(1, unittest), "name")

        self.assertRaisesRegex(ValueError, "cannot find field nope in unittest", relations.model.Relation.field_name, "nope", unittest)

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

        testunit = TestUnit()
        test = Test()
        unit = Unit()

        self.assertEqual(relations.model.Relation.relative_field(testunit, unit), "testunit_id")
        self.assertEqual(relations.model.Relation.relative_field(test, unit), "test_ident")
        self.assertEqual(relations.model.Relation.relative_field(test, testunit), "ident")
        self.assertEqual(relations.model.Relation.relative_field(unit, testunit, same=True), "id")

        self.assertRaisesRegex(ValueError, "cannot determine field for unit in testunit", relations.model.Relation.relative_field, unit, testunit)


class TestOneToMany(unittest.TestCase):

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

        relation = relations.model.OneToMany(Mom, Son)

        self.assertEqual(relation.Parent, Mom)
        self.assertEqual(relation.Child, Son)

        self.assertEqual(relation.parent_child, "son")
        self.assertEqual(relation.child_parent, "mom")
        self.assertEqual(relation.parent_field, "id")
        self.assertEqual(relation.child_field, "mom_id")

        relation = relations.model.OneToMany(Mom, Son, "sons", "mommy", "ident", "mom_ident")

        self.assertEqual(relation.parent_child, "sons")
        self.assertEqual(relation.child_parent, "mommy")
        self.assertEqual(relation.parent_field, "ident")
        self.assertEqual(relation.child_field, "mom_ident")


class TestOneToOne(unittest.TestCase):

    maxDiff = None

    def test___init__(self):

        class Sis(relations.model.Model):
            id = int
            name = str
            ident = int

        class Bro(relations.model.Model):
            id = int
            name = str
            sis_ident = int

        relation = relations.model.OneToOne(Sis, Bro)

        self.assertEqual(relation.Sister, Sis)
        self.assertEqual(relation.Brother, Bro)

        self.assertEqual(relation.sister_brother, "bro")
        self.assertEqual(relation.brother_sister, "sis")
        self.assertEqual(relation.sister_field, "id")
        self.assertEqual(relation.brother_field, "id")

        relation = relations.model.OneToOne(Sis, Bro, "bros", "sistahs", "ident", "sis_ident")

        self.assertEqual(relation.sister_brother, "bros")
        self.assertEqual(relation.brother_sister, "sistahs")
        self.assertEqual(relation.sister_field, "ident")
        self.assertEqual(relation.brother_field, "sis_ident")
