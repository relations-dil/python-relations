import unittest
import unittest.mock

import os
import pymysql.cursors

import relations.model
import relations.pymysql

class SourceModel(relations.model.Model):
    SOURCE = "PyMySQLSource"

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

        self.source = relations.pymysql.Source("PyMySQLSource", "test_source", host=os.environ["MYSQL_HOST"], port=int(os.environ["MYSQL_PORT"]))

        cursor = self.source.connection.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS `test_source`")
        cursor.close()

    def tearDown(self):

        cursor = self.source.connection.cursor()
        cursor.execute("DROP DATABASE IF EXISTS `test_source`")
        self.source.connection.close()

    @unittest.mock.patch("relations.SOURCES", {})
    @unittest.mock.patch("pymysql.connect", unittest.mock.MagicMock())
    def test___init__(self):

        source = relations.pymysql.Source("unit", "init", connection="corkneckshurn")
        self.assertEqual(source.name, "unit")
        self.assertEqual(source.database, "init")
        self.assertEqual(source.connection, "corkneckshurn")
        self.assertEqual(relations.SOURCES["unit"], source)

        source = relations.pymysql.Source("test", "init", host="db.com", extra="stuff")
        self.assertEqual(source.name, "test")
        self.assertEqual(source.database, "init")
        self.assertEqual(source.connection, pymysql.connect.return_value)
        self.assertEqual(relations.SOURCES["test"], source)
        pymysql.connect.assert_called_once_with(cursorclass=pymysql.cursors.DictCursor, host="db.com", extra="stuff")

    def test_table(self):

        model = unittest.mock.MagicMock()
        model.DATABASE = None

        model.TABLE = "people"
        self.assertEqual(self.source.table(model), "`test_source`.`people`")

        model.DATABASE = "stuff"
        self.assertEqual(self.source.table(model), "`stuff`.`people`")

    def test_field_init(self):

        class Field:
            pass

        field = Field()

        self.source.field_init(field)

        self.assertIsNone(field.auto_increment)
        self.assertIsNone(field.definition)

    def test_model_init(self):

        class Check(relations.model.Model):
            id = int
            name = str

        model = Check()

        self.source.model_init(model)

        self.assertIsNone(model.DATABASE)
        self.assertEqual(model.TABLE, "check")
        self.assertEqual(model.QUERY.get(), "SELECT * FROM `test_source`.`check`")
        self.assertIsNone(model.DEFINITION)
        self.assertTrue(model._fields._names["id"].auto_increment)
        self.assertTrue(model._fields._names["id"].readonly)

    def test_field_define(self):

        # Specific

        field = relations.model.Field(int, definition="id")
        self.source.field_init(field)
        definitions = []
        self.source.field_define(field, definitions)
        self.assertEqual(definitions, ["id"])

        # INTEGER

        field = relations.model.Field(int, store="_id")
        self.source.field_init(field)
        definitions = []
        self.source.field_define(field, definitions)
        self.assertEqual(definitions, ["`_id` INTEGER"])

        # INTEGER default

        field = relations.model.Field(int, store="_id", default=0)
        self.source.field_init(field)
        definitions = []
        self.source.field_define(field, definitions)
        self.assertEqual(definitions, ["`_id` INTEGER DEFAULT 0"])

        # INTEGER not_null

        field = relations.model.Field(int, store="_id", not_null=True)
        self.source.field_init(field)
        definitions = []
        self.source.field_define(field, definitions)
        self.assertEqual(definitions, ["`_id` INTEGER NOT NULL"])

        # INTEGER auto_increment

        field = relations.model.Field(int, store="_id", auto_increment=True)
        self.source.field_init(field)
        definitions = []
        self.source.field_define(field, definitions)
        self.assertEqual(definitions, ["`_id` INTEGER AUTO_INCREMENT"])

        # INTEGER full

        field = relations.model.Field(int, store="_id", not_null=True, auto_increment=True, default=0)
        self.source.field_init(field)
        definitions = []
        self.source.field_define(field, definitions)
        self.assertEqual(definitions, ["`_id` INTEGER NOT NULL AUTO_INCREMENT DEFAULT 0"])

        # VARCHAR

        field = relations.model.Field(str, name="name")
        self.source.field_init(field)
        definitions = []
        self.source.field_define(field, definitions)
        self.assertEqual(definitions, ["`name` VARCHAR(255)"])

        # VARCHAR length

        field = relations.model.Field(str, name="name", length=32)
        self.source.field_init(field)
        definitions = []
        self.source.field_define(field, definitions)
        self.assertEqual(definitions, ["`name` VARCHAR(32)"])

        # VARCHAR default

        field = relations.model.Field(str, name="name", default='ya')
        self.source.field_init(field)
        definitions = []
        self.source.field_define(field, definitions)
        self.assertEqual(definitions, ["`name` VARCHAR(255) DEFAULT 'ya'"])

        # VARCHAR not_null

        field = relations.model.Field(str, name="name", not_null=True)
        self.source.field_init(field)
        definitions = []
        self.source.field_define(field, definitions)
        self.assertEqual(definitions, ["`name` VARCHAR(255) NOT NULL"])

        # VARCHAR full

        field = relations.model.Field(str, name="name", length=32, not_null=True, default='ya')
        self.source.field_init(field)
        definitions = []
        self.source.field_define(field, definitions)
        self.assertEqual(definitions, ["`name` VARCHAR(32) NOT NULL DEFAULT 'ya'"])

    def test_model_define(self):

        class Simple(relations.model.Model):

            SOURCE = "PyMySQLSource"
            DEFINITION = "whatever"

            id = int
            name = str

        self.assertEqual(Simple.define(), "whatever")

        Simple.DEFINITION = None
        self.assertEqual(Simple.define(), """CREATE TABLE IF NOT EXISTS `test_source`.`simple` (
  `id` INTEGER AUTO_INCREMENT,
  `name` VARCHAR(255),
  PRIMARY KEY (`id`)
)""")

        cursor = self.source.connection.cursor()
        cursor.execute(Simple.define())
        cursor.close()

    def test_field_create(self):

        # Standard

        field = relations.model.Field(int, name="id")
        self.source.field_init(field)
        fields = []
        clause = []
        self.source.field_create( field, fields, clause)
        self.assertEqual(fields, ["`id`"])
        self.assertEqual(clause, ["%(id)s"])
        self.assertFalse(field.changed)

        # readonly

        field = relations.model.Field(int, name="id", readonly=True)
        self.source.field_init(field)
        fields = []
        clause = []
        self.source.field_create( field, fields, clause)
        self.assertEqual(fields, [])
        self.assertEqual(clause, [])

    def test_model_create(self):

        simple = Simple("sure")
        simple.plain.add("fine")

        cursor = self.source.connection.cursor()
        cursor.execute(Simple.define())
        cursor.execute(Plain.define())

        simple.create()

        self.assertEqual(simple.id, 1)
        self.assertEqual(simple._action, "update")
        self.assertEqual(simple._record._action, "update")
        self.assertEqual(simple.plain[0].simple_id, 1)
        self.assertEqual(simple.plain._action, "update")
        self.assertEqual(simple.plain[0]._record._action, "update")

        cursor.execute("SELECT * FROM test_source.simple")
        self.assertEqual(cursor.fetchone(), {"id": 1, "name": "sure"})

        cursor.execute("SELECT * FROM test_source.plain")
        self.assertEqual(cursor.fetchone(), {"simple_id": 1, "name": "fine"})

        cursor.close()

    def test_field_retrieve(self):

        # IN

        field = relations.model.Field(int, name="id")
        self.source.field_init(field)
        field.filter([1, 2, 3], "in")
        query = relations.query.Query()
        values = []
        self.source.field_retrieve( field, query, values)
        self.assertEqual(query.wheres, "`id` IN (%s,%s,%s)")
        self.assertEqual(values, [1, 2, 3])

        # NOT IN

        field = relations.model.Field(int, name="id")
        self.source.field_init(field)
        field.filter([1, 2, 3], "ne")
        query = relations.query.Query()
        values = []
        self.source.field_retrieve( field, query, values)
        self.assertEqual(query.wheres, "`id` NOT IN (%s,%s,%s)")
        self.assertEqual(values, [1, 2, 3])

        # =

        field = relations.model.Field(int, name="id")
        self.source.field_init(field)
        field.filter(1)
        query = relations.query.Query()
        values = []
        self.source.field_retrieve( field, query, values)
        self.assertEqual(query.wheres, "`id`=%s")
        self.assertEqual(values, [1])

        # >

        field = relations.model.Field(int, name="id")
        self.source.field_init(field)
        field.filter(1, "gt")
        query = relations.query.Query()
        values = []
        self.source.field_retrieve( field, query, values)
        self.assertEqual(query.wheres, "`id`>%s")
        self.assertEqual(values, [1])

        # >=

        field = relations.model.Field(int, name="id")
        self.source.field_init(field)
        field.filter(1, "ge")
        query = relations.query.Query()
        values = []
        self.source.field_retrieve( field, query, values)
        self.assertEqual(query.wheres, "`id`>=%s")
        self.assertEqual(values, [1])

        # <

        field = relations.model.Field(int, name="id")
        self.source.field_init(field)
        field.filter(1, "lt")
        query = relations.query.Query()
        values = []
        self.source.field_retrieve( field, query, values)
        self.assertEqual(query.wheres, "`id`<%s")
        self.assertEqual(values, [1])

        # <=

        field = relations.model.Field(int, name="id")
        self.source.field_init(field)
        field.filter(1, "le")
        query = relations.query.Query()
        values = []
        self.source.field_retrieve( field, query, values)
        self.assertEqual(query.wheres, "`id`<=%s")
        self.assertEqual(values, [1])

    def test_model_retrieve(self):

        model = Unit()

        cursor = self.source.connection.cursor()

        cursor.execute(Unit.define())
        cursor.execute(Test.define())
        cursor.execute(Case.define())

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
        clause = []
        values = []
        field.value = 1
        self.source.field_update(field, clause, values)
        self.assertEqual(clause, ["`id`=%s"])
        self.assertEqual(values, [1])
        self.assertFalse(field.changed)

        # not changed

        clause = []
        values = []
        self.source.field_update(field, clause, values, changed=True)
        self.assertEqual(clause, [])
        self.assertEqual(values, [])
        self.assertFalse(field.changed)

        # readonly

        field = relations.model.Field(int, name="id", readonly=True)
        self.source.field_init(field)
        clause = []
        values = []
        field.value = 1
        self.source.field_update( field, clause, values)
        self.assertEqual(clause, [])
        self.assertEqual(values, [])

    def test_model_update(self):

        cursor = self.source.connection.cursor()

        cursor.execute(Unit.define())
        cursor.execute(Test.define())
        cursor.execute(Case.define())

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

        cursor = self.source.connection.cursor()

        cursor.execute(Unit.define())
        cursor.execute(Test.define())
        cursor.execute(Case.define())

        unit = Unit("people")
        unit.test.add("stuff").add("things")
        unit.create()

        self.assertEqual(Test.one(id=2).delete(), 1)
        self.assertEqual(len(Test.many()), 1)

        self.assertEqual(Unit.one(1).test.delete(), 1)
        self.assertEqual(Unit.one(1).retrieve().delete(), 1)
        self.assertEqual(len(Unit.many()), 0)
        self.assertEqual(len(Test.many()), 0)

        cursor.execute(Plain.define())

        plain = Plain().create()
        self.assertRaisesRegex(relations.model.ModelError, "plain: nothing to delete from", plain.delete)
