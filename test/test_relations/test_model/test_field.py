"""
Unittests for Model Field
"""

import unittest
import unittest.mock

import relations

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
