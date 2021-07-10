import unittest
import unittest.mock

import relations

class TestSource(unittest.TestCase):

    maxDiff = None

    def setUp(self):

        self.source = relations.Source("unittest")

    def test___new__(self):

        source = relations.Source("testunit", reverse=True)

        self.assertEqual(relations.source("testunit"), source)
        self.assertTrue(source.reverse)

    def test_ensure_attribute(self):

        class Item:
            pass

        item = Item()

        item.already = False

        self.source.ensure_attribute(item, "already", True)
        self.assertFalse(item.already)

        self.source.ensure_attribute(item, "nothing")
        self.assertIsNone(item.nothing)

        self.source.ensure_attribute(item, "something", True)
        self.assertTrue(item.something)

    def test_field_init(self):

        self.source.field_init(None)

    @unittest.mock.patch("relations.Source.field_init")
    def test_record_init(self, mock_field):

        record = unittest.mock.MagicMock()
        record._order = [record]

        self.source.record_init(record)

        mock_field.assert_called_once_with(record)

    @unittest.mock.patch("relations.Source.field_init")
    def test_model_init(self, mock_field):

        record = unittest.mock.MagicMock()
        record._order = [record]
        record._fields = record

        self.source.model_init(record)

        mock_field.assert_called_once_with(record)

    def test_field_define(self):

        self.source.field_define(None)

    @unittest.mock.patch("relations.Source.field_define")
    def test_record_define(self, mock_define):

        self.source.record_define([{}])

        mock_define.assert_called_once_with({})

    def test_model_define(self):

        self.source.model_define(None)

    def test_field_add(self):

        self.source.field_add(None)

    def test_field_remove(self):

        self.source.field_remove(None)

    def test_field_change(self):

        self.source.field_change(None, None)

    @unittest.mock.patch("relations.Source.field_add")
    @unittest.mock.patch("relations.Source.field_remove")
    @unittest.mock.patch("relations.Source.field_change")
    def test_record_migratee(self, mock_change, mock_remove, mock_add):

        record = [
            {"name": "fie"},
            {"name": "foe"}
        ]

        migration = {
            "add": [
                {"name": "fee"}
            ],
            "remove": ["fie"],
            "change": {
                "foe": {"name": "fum"}
            }
        }

        self.source.record_migrate(record, migration)

        mock_add.assert_called_once_with({"name": "fee"})
        mock_remove.assert_called_once_with({"name": "fie"})
        mock_change.assert_called_once_with({"name": "foe"}, {"name": "fum"})

    def test_model_migrate(self):

        self.source.model_define(None)

    def test_field_create(self):

        self.source.field_create(None)

    @unittest.mock.patch("relations.Source.field_create")
    def test_record_create(self, mock_field):

        record = unittest.mock.MagicMock()
        record._order = [record]

        self.source.record_create(record)

        mock_field.assert_called_once_with(record)

    def test_model_create(self):

        self.source.model_create(None)

    def test_field_retrieve(self):

        self.source.field_retrieve(None)

    @unittest.mock.patch("relations.Source.field_retrieve")
    def test_record_retrieve(self, mock_field):

        record = unittest.mock.MagicMock()
        record._order = [record]

        self.source.record_retrieve(record)

        mock_field.assert_called_once_with(record)

    def test_model_retrieve(self):

        self.source.model_retrieve(None)

    def test_field_update(self):

        self.source.field_update(None)

    @unittest.mock.patch("relations.Source.field_update")
    def test_record_update(self, mock_field):

        record = unittest.mock.MagicMock()
        record._order = [record]

        self.source.record_update(record)

        mock_field.assert_called_once_with(record)

    def test_field_mass(self):

        self.source.field_mass(None)

    @unittest.mock.patch("relations.Source.field_mass")
    def test_record_mass(self, mock_field):

        record = unittest.mock.MagicMock()
        record._order = [record]

        self.source.record_mass(record)

        mock_field.assert_called_once_with(record)

    def test_model_update(self):

        self.source.model_update(None)

    def test_field_delete(self):

        self.source.field_delete(None)

    @unittest.mock.patch("relations.Source.field_delete")
    def test_record_delete(self, mock_field):

        record = unittest.mock.MagicMock()
        record._order = [record]

        self.source.record_delete(record)

        mock_field.assert_called_once_with(record)

    def test_model_delete(self):

        self.source.model_delete(None)
