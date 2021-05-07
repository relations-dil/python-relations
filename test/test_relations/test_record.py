import unittest
import unittest.mock

import relations

class TestRecordError(unittest.TestCase):

    maxDiff = None

    def test___init__(self):

        error = relations.RecordError("unittest", "oops")

        self.assertEqual(error.record, "unittest")
        self.assertEqual(error.message, "oops")

class TestRecord(unittest.TestCase):

    maxDiff = None

    def setUp(self):

        self.source = unittest.mock.MagicMock()

        self.record = relations.Record()

        self.id = relations.Field(int, name="id", store="_id")
        self.name = relations.Field(str, name="name", store="_name")

        self.record.append(self.id)
        self.record.append(self.name)

    def test___init__(self):

        record = relations.Record()

        self.assertEqual(record._order, [])
        self.assertEqual(record._names, {})

    def test_insert(self):

        record = relations.Record()

        id = relations.Field(int, name="id", store="_id")
        record.insert(0, id)
        self.assertEqual(record._order, [id])
        self.assertEqual(record._names, {"id": id})

        name = relations.Field(str, name="name", store="_name")
        record.insert(0, name)
        self.assertEqual(record._order, [name, id])
        self.assertEqual(record._names, {"id": id, "name": name})

    def test_append(self):

        record = relations.Record()

        id = relations.Field(int, name="id", store="_id")
        record.append(id)
        self.assertEqual(record._order, [id])
        self.assertEqual(record._names, {"id": id})

        name = relations.Field(str, name="name", store="_name")
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

        self.assertEqual(list(self.record), ["id", "name"])

    def test_keys(self):

        self.record.id = 1
        self.record.name = "ya"

        self.assertEqual(dict(self.record), {"id": 1, "name": "ya"})

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

        self.assertRaisesRegex(relations.RecordError, "unknown field 'nope'", nope)

    def test___getitem__(self):

        self.id.value = "1"
        self.assertEqual(self.record[0], 1)
        self.assertEqual(self.record['id'], 1)

        def nope():
            self.record['nope']

        self.assertRaisesRegex(relations.RecordError, "unknown field 'nope'", nope)

    def test_filter(self):

        self.record.filter(0, "0")
        self.assertEqual(self.id.criteria["eq"], 0)

        self.record.filter("id", "1")
        self.assertEqual(self.id.criteria["eq"], 1)

        self.record.filter("id__ne", "2")
        self.assertEqual(self.id.criteria["ne"], [2])

        self.assertRaisesRegex(relations.RecordError, "unknown criterion 'nope'", self.record.filter, "nope", 0)

    def test_satisfy(self):

        self.record.filter("id", "1")
        self.record.filter("name", "unit")

        self.assertTrue(self.record.satisfy({"_id": 1, "_name": "unit"}))
        self.assertFalse(self.record.satisfy({"_id": 2, "_name": "unit"}))
        self.assertFalse(self.record.satisfy({"_id": 1, "_name": "test"}))

    def test_match(self):

        self.assertTrue(self.record.match({"_id": 1, "_name": "test"}, ["id", "name"], "unit", {'_id': [1]}))
        self.assertTrue(self.record.match({"_id": 2, "_name": "unit"}, ["id", "name"], "unit", {'_id': [1]}))
        self.assertFalse(self.record.match({"_id": 2, "_name": "test"}, ["id", "name"], "unit", {'_id': [1]}))

    def test_read(self):

        self.record.read({"_id": 1, "_name": "unit"})

        self.assertEqual(self.record.id, 1)
        self.assertEqual(self.record.name, "unit")

    def test_write(self):

        self.record.id = 1
        self.record.name = "unit"

        self.assertEqual(self.record.write({}), {"_id": 1, "_name": "unit"})
