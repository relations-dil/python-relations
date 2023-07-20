import unittest
import unittest.mock

import relations


class SourceModel(relations.Model):
    SOURCE = "UnittestSource"

class Sis(SourceModel):
    id = int
    name = str
    bro_id = set

class Bro(SourceModel):
    id = int
    name = str
    sis_id = set

class SisBro(SourceModel):
    ID = None
    bro_id = int
    sis_id = int

relations.ManyToMany(Sis, Bro, SisBro)


class TestSource(unittest.TestCase):

    maxDiff = None

    def setUp(self):

        self.source = relations.Source("unittest")
        self.mock_source = relations.unittest.MockSource("UnittestSource")

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
    def test_init(self, mock_field):

        record = unittest.mock.MagicMock()
        record._order = [record]
        record._fields = record

        self.source.init(record)

        mock_field.assert_called_once_with(record)

    def test_field_define(self):

        self.source.field_define(None)

    @unittest.mock.patch("relations.Source.field_define")
    def test_record_define(self, mock_define):

        self.source.record_define([{}])

        mock_define.assert_called_once_with({})

    def test_define(self):

        self.source.define(None)

    def test_field_add(self):

        self.source.field_add(None)

    def test_field_remove(self):

        self.source.field_remove(None)

    def test_field_change(self):

        self.source.field_change(None, None)

    @unittest.mock.patch("relations.Source.field_add")
    @unittest.mock.patch("relations.Source.field_remove")
    @unittest.mock.patch("relations.Source.field_change")
    def test_record_change(self, mock_change, mock_remove, mock_add):

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

        self.source.record_change(record, migration)

        mock_add.assert_called_once_with({"name": "fee"})
        mock_remove.assert_called_once_with({"name": "fie"})
        mock_change.assert_called_once_with({"name": "foe"}, {"name": "fum"})

    def test_model_add(self):

        self.source.model_add(None)

    def test_model_remove(self):

        self.source.model_remove(None)

    def test_model_change(self):

        self.source.model_change(None, None)

    def test_create_field(self):

        self.source.create_field(None)

    @unittest.mock.patch("relations.Source.create_field")
    def test_create_record(self, mock_field):

        record = unittest.mock.MagicMock()
        record._order = [record]

        self.source.create_record(record)

        mock_field.assert_called_once_with(record)

    def test_create_query(self):

        self.source.create_query(None)

    def test_create_tie(self):

        sis = Sis("Sally").create()
        self.source.create_tie(sis, {})
        sis.bro_id = [2, 3, 4]
        self.source.create_tie(sis)

        bro = Bro("Tom").create()
        self.source.create_tie(bro, {})
        bro.sis_id = [5, 6, 7]
        self.source.create_tie(bro)

        self.assertEqual(self.mock_source.data, {
            "sis": {
                1: {
                    "id": 1,
                    "name": "Sally"
                }
            },
            "bro": {
                1: {
                    "id": 1,
                    "name": "Tom"
                }
            },
            "sis_bro": {
                1: {
                    "bro_id": 2,
                    "sis_id": 1
                },
                2: {
                    "bro_id": 3,
                    "sis_id": 1
                },
                3: {
                    "bro_id": 4,
                    "sis_id": 1
                },
                4: {
                    "bro_id": 1,
                    "sis_id": 5
                },
                5: {
                    "bro_id": 1,
                    "sis_id": 6
                },
                6: {
                    "bro_id": 1,
                    "sis_id": 7
                }
            }
        })

    def test_create(self):

        self.source.create(None)

    def test_retrieve_field(self):

        self.source.retrieve_field(None)

    @unittest.mock.patch("relations.Source.retrieve_field")
    def test_retrieve_record(self, mock_field):

        record = unittest.mock.MagicMock()
        record._order = [record]

        self.source.retrieve_record(record)

        mock_field.assert_called_once_with(record)

    def test_count_query(self):

        self.source.count_query(None)

    def test_count(self):

        self.source.retrieve(None)

    def test_retrieve_query(self):

        self.source.retrieve_query(None)

    def test_retrieve_tie(self):

        tom = Bro("Tom").create()
        dick = Bro("Dick").create()

        Sis("Sally", bro_id=[tom.id, dick.id]).create()

        mary = Sis("Mary").create()
        sue = Sis("Sure").create()

        Bro("Harry", sis_id=[mary.id, sue.id]).create()

        sally = Sis.one(name="Sally")
        harry = Bro.one(name="Harry")

        self.assertEqual(sally.bro_id, set([tom.id, dick.id]))
        self.assertEqual(harry.sis_id, set([mary.id, sue.id]))

    def test_retrieve(self):

        self.source.retrieve(None)

    def test_titles_query(self):

        self.source.titles_query(None)

    def test_titles(self):

        self.source.titles(None)

    def test_update_field(self):

        self.source.update_field(None)

    @unittest.mock.patch("relations.Source.update_field")
    def test_update_record(self, mock_field):

        record = unittest.mock.MagicMock()
        record._order = [record]

        self.source.update_record(record)

        mock_field.assert_called_once_with(record)

    def test_field_mass(self):

        self.source.field_mass(None)

    @unittest.mock.patch("relations.Source.field_mass")
    def test_record_mass(self, mock_field):

        record = unittest.mock.MagicMock()
        record._order = [record]

        self.source.record_mass(record)

        mock_field.assert_called_once_with(record)

    def test_update_query(self):

        self.source.update_query(None)

    def test_update(self):

        self.source.update(None)

    def test_delete_field(self):

        self.source.delete_field(None)

    @unittest.mock.patch("relations.Source.delete_field")
    def test_delete_record(self, mock_field):

        record = unittest.mock.MagicMock()
        record._order = [record]

        self.source.delete_record(record)

        mock_field.assert_called_once_with(record)

    def test_delete_query(self):

        self.source.delete_query(None)

    def test_delete_tie(self):

        Sis("Sally", bro_id=[2, 3, 4]).create()
        Bro("Tom", sis_id=[5, 6, 7]).create()

        Sis.many().delete()

        self.assertEqual(self.mock_source.data, {
            "sis": {},
            "bro": {
                1: {
                    "id": 1,
                    "name": "Tom"
                }
            },
            "sis_bro": {
                4: {
                    "bro_id": 1,
                    "sis_id": 5
                },
                5: {
                    "bro_id": 1,
                    "sis_id": 6
                },
                6: {
                    "bro_id": 1,
                    "sis_id": 7
                }
            }
        })

        Bro.many().delete()

        self.assertEqual(self.mock_source.data, {
            "sis": {},
            "bro": {},
            "sis_bro": {}
        })

    def test_delete(self):

        self.source.delete(None)

    def test_definition(self):

        self.source.definition(None, None)

    def test_migration(self):

        self.source.migration(None, None)

    def test_execute(self):

        self.source.execute(None)

    def test_list(self):

        self.source.list(None)

    def test_load(self):

        self.source.load(None)

    def test_migrate(self):

        self.source.migrate(None)
