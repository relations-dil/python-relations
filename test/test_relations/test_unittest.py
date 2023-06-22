import unittest
import unittest.mock

import os
import shutil
import pathlib
import json
import ipaddress

import relations.unittest

class SourceModel(relations.Model):
    SOURCE = "UnittestSource"

class Simple(SourceModel):
    id = int
    name = str

class Plain(SourceModel):
    ID = None
    simple_id = int
    name = str

relations.OneToMany(Simple, Plain)

class Meta(SourceModel):
    id = int
    name = str
    flag = bool
    spend = float
    people = set
    stuff = list
    things = dict, {"extract": "for__0____1"}
    push = str, {"inject": "stuff___1__relations.io____1"}

def subnet_attr(values, value):

    values["address"] = str(value)
    min_ip = value[0]
    max_ip = value[-1]
    values["min_address"] = str(min_ip)
    values["min_value"] = int(min_ip)
    values["max_address"] = str(max_ip)
    values["max_value"] = int(max_ip)

class Net(SourceModel):

    id = int
    ip = ipaddress.IPv4Address, {
        "attr": {"compressed": "address", "__int__": "value"},
        "init": "address",
        "titles": "address",
        "extract": ["address", "value"]
    }
    subnet = ipaddress.IPv4Network, {
        "attr": subnet_attr,
        "init": "address",
        "titles": "address"
    }

    TITLES = "ip__address"
    INDEX = "ip__address"

class Unit(SourceModel):
    id = int
    name = str, {"format": "fancy"}

class Test(SourceModel):
    id = int
    unit_id = int
    name = str, {"format": "shmancy"}

class Case(SourceModel):
    id = int
    test_id = int
    name = str

relations.OneToMany(Unit, Test)
relations.OneToOne(Test, Case)


class TestQuery(unittest.TestCase):

    maxDiff = None

    def test___init__(self):

        query = relations.unittest.MockQuery("ACTION")
        self.assertEqual(query.action, "ACTION")

    def test_bind(self):

        query = relations.unittest.MockQuery("QUERY").bind("MODEL")
        self.assertEqual(query.model, "MODEL")


class TestSource(unittest.TestCase):

    maxDiff = None

    def setUp(self):

        self.source = relations.unittest.MockSource("UnittestSource")

        shutil.rmtree("ddl", ignore_errors=True)
        os.makedirs("ddl", exist_ok=True)

    @unittest.mock.patch("relations.SOURCES", {})
    def test___init__(self):

        source = relations.unittest.MockSource("unit")
        self.assertEqual(source.name, "unit")
        self.assertEqual(relations.SOURCES["unit"], source)

    def test_init(self):

        class Check(relations.Model):
            id = int
            name = str

        model = Check()

        self.source.init(model)

        self.assertEqual(self.source.ids, {"check": 0})
        self.assertEqual(self.source.data, {"check": {}})
        self.assertEqual(self.source.unique, {"check": {"name": {}}})
        self.assertTrue(model._fields._names["id"].auto)

    def test_field_define(self):

        field = relations.Field(int, store="_id")
        self.source.field_init(field)
        definitions = []
        self.source.field_define(field.define(), definitions)
        self.assertEqual(definitions, [{
            "kind": "int",
            "store": "_id",
            "none": True
        }])

    def test_define(self):

        self.assertEqual(Simple.define(), [{
            "ACTION": "add",
            "source": "UnittestSource",
            "name": "simple",
            "title": "Simple",
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

    def test_field_add(self):

        field = relations.Field(int, store="_id")
        self.source.field_init(field)
        migrations = []
        self.source.field_add(field.define(), migrations)
        self.assertEqual(migrations, [{
            "ACTION": "add",
            "kind": "int",
            "store": "_id",
            "none": True
        }])

    def test_field_remove(self):

        field = relations.Field(int, store="_id")
        self.source.field_init(field)
        migrations = []
        self.source.field_remove(field.define(), migrations)
        self.assertEqual(migrations, [{
            "ACTION": "remove",
            "kind": "int",
            "store": "_id",
            "none": True
        }])

    def test_field_change(self):

        field = relations.Field(int, store="_id")
        self.source.field_init(field)
        migrations = []
        self.source.field_change(field.define(), {"kind": "float"}, migrations)
        self.assertEqual(migrations, [{
            "ACTION": "change",
            "DEFINITION": {
                "kind": "int",
                "store": "_id",
                "none": True
            },
            "MIGRATION": {
                "kind": "float"
            }
        }])

    def test_model_add(self):

        self.assertEqual(self.source.model_add(Simple.thy().define()), [{
            "ACTION": "add",
            "source": "UnittestSource",
            "name": "simple",
            "title": "Simple",
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

    def test_model_remove(self):

        self.assertEqual(self.source.model_remove(Simple.thy().define()), [{
            "ACTION": "remove",
            "source": "UnittestSource",
            "name": "simple",
            "title": "Simple",
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

    def test_model_change(self):

        definition = {
            "source": "UnittestSource",
            "name": "migs",
            "fields": [
                {
                    "name": "fie",
                    "store": "fie",
                    "kind": "int"
                },
                {
                    "name": "foe",
                    "store": "foe",
                    "kind": "int"
                }
            ]
        }

        migration = {
            "source": "UnittestSource",
            "name": "mig",
            "fields": {
                "add": [
                    {
                        "name": "fee",
                        "store": "fee",
                        "kind": "int"
                    }
                ],
                "remove": ["fie"],
                "change": {
                    "foe": {
                        "name": "fum",
                        "kind": "float"
                    }
                }
            }
        }

        self.assertEqual(self.source.model_change(definition, migration), [{
            "ACTION": "change",
            "DEFINITION": {
                "source": "UnittestSource",
                "name": "migs",
                "fields": [
                    {
                        "name": "fie",
                        "store": "fie",
                        "kind": "int"
                    },
                    {
                        "name": "foe",
                        "store": "foe",
                        "kind": "int"
                    }
                ]
            },
            "MIGRATION": {
                "source": "UnittestSource",
                "name": "mig",
                "fields": [
                    {
                        "ACTION": "add",
                        "name": "fee",
                        "store": "fee",
                        "kind": "int"
                    },
                    {
                        "ACTION": "remove",
                        "name": "fie",
                        "store": "fie",
                        "kind": "int"
                    },
                    {
                        "ACTION": "change",
                        "DEFINITION": {
                            "name": "foe",
                            "store": "foe",
                            "kind": "int"
                        },
                        "MIGRATION": {
                            "name": "fum",
                            "kind": "float"
                        }
                    }
                ]
            }
        }])

    def test_extract(self):

        self.assertEqual(self.source.extract(Meta(), {"things": {"for": [{"1": "yep"}]}})["things__for__0____1"], "yep")
        self.assertIsNone(self.source.extract(Meta(), {})["things__for__0____1"])

    def test_create_query(self):

        self.assertEqual(self.source.create_query(None).action, "CREATE")

    def test_create(self):

        simple = Simple("sure")
        simple.plain.add("fine")

        simple.create()

        self.assertEqual(simple.id, 1)
        self.assertEqual(simple._action, "update")
        self.assertEqual(simple._record._action, "update")
        self.assertEqual(simple.plain[0].simple_id, 1)
        self.assertEqual(simple.plain._action, "update")
        self.assertEqual(simple.plain[0]._record._action, "update")

        simples = Simple.bulk().add("ya").create()

        self.assertEqual(simples._models, [])

        yep = Meta("yep", True, 3.50, {"tom"}, [1, None], {"a": 1, "for": [{"1": "yep"}]}, "sure").create()
        self.assertTrue(Meta.one(yep.id).flag)

        nope = Meta("nope", False).create()
        self.assertFalse(Meta.one(nope.id).flag)

        self.assertEqual(self.source.ids, {
            "simple": 2,
            "plain": 1,
            "meta": 2
        })

        self.assertEqual(self.source.data, {
            "simple": {
                1: {
                    "id": 1,
                    "name": "sure"
                },
                2: {
                    "id": 2,
                    "name": "ya"
                }
            },
            "plain": {
                1: {
                    "simple_id": 1,
                    "name": "fine"
                }
            },
            "meta": {
                1: {
                    "id": 1,
                    "name": "yep",
                    "flag": True,
                    "spend": 3.50,
                    "people": ["tom"],
                    "stuff": [1, {"relations.io": {"1": "sure"}}],
                    "things": {"a": 1, "for": [{"1": "yep"}]},
                    "things__for__0____1": "yep"
                },
                2: {
                    "id": 2,
                    "name": "nope",
                    "flag": False,
                    "spend": None,
                    "people": [],
                    "stuff": [{"relations.io": {"1": None}}],
                    "things": {},
                    "things__for__0____1": None
                }
            }
        })

        self.assertEqual(self.source.unique, {
            "simple": {
                "name": {
                    1: '{"name": "sure"}',
                    2: '{"name": "ya"}'
                }
            },
            "plain": {
                "simple_id-name": {
                    1: '{"name": "fine", "simple_id": 1}'
                }
            },
            "meta": {
                "name": {
                    1: '{"name": "yep"}',
                    2: '{"name": "nope"}'
                }
            }
        })

        simple = Simple("sure")

        self.assertRaisesRegex(relations.ModelError, 'simple: value {"name": "sure"} violates unique name', simple.create)

    def test_model_like(self):

        Unit([["stuff"], ["people"]]).create()

        unit = Unit.one(like="p")

        self.assertEqual(self.source.model_like(unit), [{
            "id": 2,
            "name": "people"
        }])

        unit.test.add("things")[0]
        unit.update()

        test = Test.many(like="p")
        self.assertEqual(self.source.model_like(test), [{
            "id": 1,
            "unit_id": 2,
            "name": "things"
        }])
        self.assertFalse(test.overflow)

        test = Test.many(like="p", _chunk=1)
        self.assertEqual(self.source.model_like(test), [{
            "id": 1,
            "unit_id": 2,
            "name": "things"
        }])
        self.assertTrue(test.overflow)

    def test_model_sort(self):

        unit = Unit([["stuff"], ["people"], ["things"]]).create()

        self.source.model_sort(unit)
        self.assertEqual(unit.name, ["people", "stuff", "things"])

        unit._sort = ['-id']
        self.source.model_sort(unit)
        self.assertEqual(unit.name, ["things", "people", "stuff"])
        self.assertIsNone(unit._sort)

    def test_model_limit(self):

        unit = Unit.many()

        unit._models = [1, 2, 3]
        self.source.model_limit(unit)
        self.assertEqual(unit._models, [1, 2, 3])
        self.assertFalse(unit.overflow)

        unit._models = [1, 2, 3]
        unit._limit = 4
        unit._offset = 0
        self.source.model_limit(unit)
        self.assertEqual(unit._models, [1, 2, 3])
        self.assertFalse(unit.overflow)

        unit._models = [1, 2, 3]
        unit._limit = 2
        self.source.model_limit(unit)
        self.assertEqual(unit._models, [1, 2])
        self.assertTrue(unit.overflow)

        unit._models = [1, 2, 3]
        unit._offset = 1
        self.source.model_limit(unit)
        self.assertEqual(unit._models, [2, 3])
        self.assertTrue(unit.overflow)

    def test_count_query(self):

        self.assertEqual(self.source.count_query(None).action, "COUNT")

    def test_count(self):

        Unit([["stuff"], ["people"]]).create()

        self.assertEqual(Unit.many().count(), 2)

        self.assertEqual(Unit.many(name="people").count(), 1)

        self.assertEqual(Unit.many(like="p").count(), 1)

    def test_retrieve_query(self):

        self.assertEqual(self.source.retrieve_query(None).action, "RETRIEVE")

    def test_retrieve(self):

        Unit([["stuff"], ["people"]]).create()

        models = Unit.one(name__in=["people", "stuff"])
        self.assertRaisesRegex(relations.ModelError, "unit: more than one retrieved", models.retrieve)

        model = Unit.one(name="things")
        self.assertRaisesRegex(relations.ModelError, "unit: none retrieved", model.retrieve)

        self.assertIsNone(model.retrieve(False))

        unit = Unit.one(name="people")

        self.assertEqual(unit.id, 2)
        self.assertEqual(unit._action, "update")
        self.assertEqual(unit._record._action, "update")

        self.assertTrue(Unit.many(name="people").limit(1).retrieve().overflow)
        self.assertFalse(Unit.many(name="people").limit(2).retrieve().overflow)

        unit.test.add("things")[0].case.add("persons")
        unit.update()

        Meta("yep", True, 1.1, {"tom"}, [1, None], {"a": 1}).create()
        model = Meta.one(name="yep")

        self.assertEqual(model.flag, True)
        self.assertEqual(model.spend, 1.1)
        self.assertEqual(model.people, {"tom"})
        self.assertEqual(model.stuff, [1, {"relations.io": {"1": None}}])
        self.assertEqual(model.things, {"a": 1})

        self.assertEqual(Unit.many().name, ["people", "stuff"])
        self.assertEqual(Unit.many().sort("-name").limit(1).name, ["stuff"])
        self.assertEqual(Unit.many().sort("-name").limit(0).name, [])

        model = Unit.many(like="p")
        self.assertEqual(model.name, ["people"])

        model = Test.many(like="p").retrieve()
        self.assertEqual(model.name, ["things"])
        self.assertFalse(model.overflow)

        model = Test.many(like="p", _chunk=1).retrieve()
        self.assertEqual(model.name, ["things"])
        self.assertTrue(model.overflow)

        Meta("dive", people={"tom", "mary"}, stuff=[1, 2, 3, None], things={"a": {"b": [1, 2], "c": "sure"}, "4": 5, "for": [{"1": "yep"}]}).create()

        model = Meta.many(people={"tom", "mary"})
        self.assertEqual(model[0].name, "dive")

        model = Meta.many(stuff=[1, 2, 3, {"relations.io": {"1": None}}])
        self.assertEqual(model[0].name, "dive")

        model = Meta.many(stuff__not_in=[1, [1, 2, 3, {"relations.io": {"1": None}}]])
        self.assertEqual(model[0].name, "yep")

        model = Meta.many(things={"a": {"b": [1, 2], "c": "sure"}, "4": 5, "for": [{"1": "yep"}]})
        self.assertEqual(model[0].name, "dive")

        model = Meta.many(things__in={"a": {"b": [1, 2], "c": "sure"}, "4": 5, "for": [{"1": "yep"}]})
        self.assertEqual(model[0].name, "dive")

        model = Meta.many(things__not_in={"a": {"b": [1, 2], "c": "sure"}, "4": 5, "for": [{"1": "yep"}]})
        self.assertEqual(model[0].name, "yep")

        model = Meta.many(stuff__1=2)
        self.assertEqual(model[0].name, "dive")

        model = Meta.many(things__a__b__0=1)
        self.assertEqual(model[0].name, "dive")

        model = Meta.many(things__a__c__like="su")
        self.assertEqual(model[0].name, "dive")

        model = Meta.many(things__a__d__null=True)
        self.assertEqual(model[0].name, "dive")

        model = Meta.many(things____4=5)
        self.assertEqual(model[0].name, "dive")

        model = Meta.many(things__a__b__0__gt=1)
        self.assertEqual(len(model), 0)

        model = Meta.many(things__a__c__notlike="su")
        self.assertEqual(len(model), 0)

        model = Meta.many(things__a__d__null=False)
        self.assertEqual(len(model), 0)

        model = Meta.many(things___4=6)
        self.assertEqual(len(model), 0)

        model = Meta.many(things___4=6)
        self.assertEqual(len(model), 0)

        model = Meta.many(things__a__b__has=1)
        self.assertEqual(len(model), 1)

        model = Meta.many(things__a__b__has=3)
        self.assertEqual(len(model), 0)

        model = Meta.many(things__a__b__any=[1, 3])
        self.assertEqual(len(model), 1)

        model = Meta.many(things__a__b__any=[4, 3])
        self.assertEqual(len(model), 0)

        model = Meta.many(things__a__b__all=[2, 1])
        self.assertEqual(len(model), 1)

        model = Meta.many(things__a__b__all=[3, 2, 1])
        self.assertEqual(len(model), 0)

        model = Meta.many(people__has="mary")
        self.assertEqual(len(model), 1)

        model = Meta.many(people__has="dick")
        self.assertEqual(len(model), 0)

        model = Meta.many(people__any=["mary", "dick"])
        self.assertEqual(len(model), 1)

        model = Meta.many(people__any=["harry", "dick"])
        self.assertEqual(len(model), 0)

        model = Meta.many(people__all=["mary", "tom"])
        self.assertEqual(len(model), 1)

        model = Meta.many(people__all=["tom", "dick", "mary"])
        self.assertEqual(len(model), 0)

        Net(ip="1.2.3.4", subnet="1.2.3.0/24").create()
        Net().create()

        model = Net.many(like='1.2.3.')
        self.assertEqual(model[0].ip.compressed, "1.2.3.4")

        model = Net.many(ip__address__like='1.2.3.')
        self.assertEqual(model[0].ip.compressed, "1.2.3.4")

        model = Net.many(ip__value__gt=int(ipaddress.IPv4Address('1.2.3.0')))
        self.assertEqual(model[0].ip.compressed, "1.2.3.4")

        model = Net.many(subnet__address__like='1.2.3.')
        self.assertEqual(model[0].ip.compressed, "1.2.3.4")

        model = Net.many(subnet__min_value=int(ipaddress.IPv4Address('1.2.3.0')))
        self.assertEqual(model[0].ip.compressed, "1.2.3.4")

        model = Net.many(ip__address__notlike='1.2.3.')
        self.assertEqual(len(model), 0)

        model = Net.many(ip__value__lt=int(ipaddress.IPv4Address('1.2.3.0')))
        self.assertEqual(len(model), 0)

        model = Net.many(subnet__address__notlike='1.2.3.')
        self.assertEqual(len(model), 0)

        model = Net.many(subnet__max_value=int(ipaddress.IPv4Address('1.2.3.0')))
        self.assertEqual(len(model), 0)

    def test_titles_query(self):

        self.assertEqual(self.source.titles_query(None).action, "TITLES")

    def test_titles(self):

        Unit("people").create().test.add("stuff").add("things").create()

        titles = Unit.many().titles()

        self.assertEqual(titles.id, "id")
        self.assertEqual(titles.fields, ["name"])
        self.assertEqual(titles.parents, {})
        self.assertEqual(titles.format, ["fancy"])

        self.assertEqual(titles.ids, [1])
        self.assertEqual(titles.titles,{1: ["people"]})

        titles = Test.many().titles()

        self.assertEqual(titles.id, "id")
        self.assertEqual(titles.fields, ["unit_id", "name"])

        self.assertEqual(titles.parents["unit_id"].id, "id")
        self.assertEqual(titles.parents["unit_id"].fields, ["name"])
        self.assertEqual(titles.parents["unit_id"].parents, {})
        self.assertEqual(titles.parents["unit_id"].format, ["fancy"])

        self.assertEqual(titles.format, ["fancy", "shmancy"])

        self.assertEqual(titles.ids, [1, 2])
        self.assertEqual(titles.titles, {
            1: ["people", "stuff"],
            2: ["people", "things"]
        })

        Net(ip="1.2.3.4", subnet="1.2.3.0/24").create()

        self.assertEqual(Net.many().titles().titles, {
            1: ["1.2.3.4"]
        })

    def test_update_query(self):

        self.assertEqual(self.source.update_query(None).action, "UPDATE")

    def test_update(self):

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
        self.assertRaisesRegex(relations.ModelError, "plain: nothing to update from", plain.update)

        ping = Net(ip="1.2.3.4", subnet="1.2.3.0/24").create()
        pong = Net(ip="5.6.7.8", subnet="5.6.7.0/24").create()

        Net.many().set(subnet="9.10.11.0/24").update()

        self.assertEqual(Net.one(ping.id).subnet.compressed, "9.10.11.0/24")
        self.assertEqual(Net.one(pong.id).subnet.compressed, "9.10.11.0/24")

        Net.one(ping.id).set(ip="13.14.15.16").update()
        self.assertEqual(Net.one(ping.id).ip.compressed, "13.14.15.16")
        self.assertEqual(Net.one(pong.id).ip.compressed, "5.6.7.8")

    def test_delete_query(self):

        self.assertEqual(self.source.delete_query(None).action, "DELETE")

    def test_delete(self):

        unit = Unit("people")
        unit.test.add("stuff").add("things")
        unit.create()

        self.assertEqual(Test.one(id=2).delete(), 1)
        self.assertEqual(len(Test.many()), 1)

        self.assertEqual(self.source.unique, {
            "unit": {
                "name": {
                    1: '{"name": "people"}'
                }
            },
            "test": {
                "unit_id-name": {
                    1: '{"name": "stuff", "unit_id": 1}'
                }
            },
            "case": {"test_id-name": {}}
        })

        self.assertEqual(Unit.one(1).test.delete(), 1)
        self.assertEqual(Unit.one(1).retrieve().delete(), 1)
        self.assertEqual(len(Unit.many()), 0)
        self.assertEqual(len(Test.many()), 0)

        plain = Plain().create()
        self.assertRaisesRegex(relations.ModelError, "plain: nothing to delete from", plain.delete)

    def test_definition(self):

        with open("ddl/general.json", 'w') as from_file:
            json.dump({"simple": Simple.thy().define()}, from_file)

        os.makedirs("ddl/sourced", exist_ok=True)

        self.source.definition("ddl/general.json", "ddl/sourced")

        with open("ddl/sourced/general.json", 'r') as ddl_file:
            self.assertEqual(json.load(ddl_file), [{
                "ACTION": "add",
                "source": "UnittestSource",
                "name": "simple",
                "title": "Simple",
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

    def test_migration(self):

        migration = {
            "add": {"simple": Simple.thy().define()},
            "remove": {"simple": Simple.thy().define()},
            "change": {
                "migs": {
                    "definition": {
                        "source": "UnittestSource",
                        "name": "migs",
                        "fields": [
                            {
                                "name": "fie",
                                "store": "fie",
                                "kind": "int"
                            },
                            {
                                "name": "foe",
                                "store": "foe",
                                "kind": "int"
                            }
                        ]
                    },
                    "migration": {
                        "source": "UnittestSource",
                        "name": "mig",
                        "fields": {
                            "add": [
                                {
                                    "name": "fee",
                                    "store": "fee",
                                    "kind": "int"
                                }
                            ],
                            "remove": ["fie"],
                            "change": {
                                "foe": {
                                    "name": "fum",
                                    "kind": "float"
                                }
                            }
                        }
                    }
                }
            }
        }

        with open("ddl/general.json", 'w') as ddl_file:
            json.dump(migration, ddl_file)

        os.makedirs("ddl/sourced", exist_ok=True)

        self.source.migration("ddl/general.json", "ddl/sourced")

        with open("ddl/sourced/general.json", 'r') as ddl_file:
            self.assertEqual(json.load(ddl_file), [
                {
                    "ACTION": "add",
                    "source": "UnittestSource",
                    "name": "simple",
                    "title": "Simple",
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
                },
                {
                    "ACTION": "remove",
                    "source": "UnittestSource",
                    "name": "simple",
                    "title": "Simple",
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
                },
                {
                    "ACTION": "change",
                    "DEFINITION": {
                        "source": "UnittestSource",
                        "name": "migs",
                        "fields": [
                            {
                                "name": "fie",
                                "store": "fie",
                                "kind": "int"
                            },
                            {
                                "name": "foe",
                                "store": "foe",
                                "kind": "int"
                            }
                        ]
                    },
                    "MIGRATION": {
                        "source": "UnittestSource",
                        "name": "mig",
                        "fields": [
                            {
                                "ACTION": "add",
                                "name": "fee",
                                "store": "fee",
                                "kind": "int"
                            },
                            {
                                "ACTION": "remove",
                                "name": "fie",
                                "store": "fie",
                                "kind": "int"
                            },
                            {
                                "ACTION": "change",
                                "DEFINITION": {
                                    "name": "foe",
                                    "store": "foe",
                                    "kind": "int"
                                },
                                "MIGRATION": {
                                    "name": "fum",
                                    "kind": "float"
                                }
                            }
                        ]
                    }
                }
            ])

    def test_execute(self):

        self.source.ids = {}
        self.source.data = {}

        self.source.execute({
            "ACTION": "add",
            "source": "UnittestSource",
            "name": "simple",
            "title": "Simple",
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
                },
                {
                    "name": "fie",
                    "store": "fie",
                    "kind": "int"
                },
                {
                    "name": "foe",
                    "store": "foe",
                    "kind": "int"
                }
            ],
            "id": "id",
            "unique": {
                "name": ["name"]
            },
            "index": {}
        })

        self.assertEqual(self.source.ids, {"simple": 0})
        self.assertEqual(self.source.data, {"simple": {}})

        self.source.execute({
            "ACTION": "remove",
            "source": "UnittestSource",
            "name": "simple",
            "title": "Simple",
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
                },
                {
                    "name": "fie",
                    "store": "fie",
                    "kind": "int"
                },
                {
                    "name": "foe",
                    "store": "foe",
                    "kind": "int"
                }
            ],
            "id": "id",
            "unique": {
                "name": ["name"]
            },
            "index": {}
        })

        self.assertEqual(self.source.ids, {})
        self.assertEqual(self.source.data, {})

        self.source.ids = {"simples": 2}
        self.source.data = {
            "simples": {
                1: {
                    "id": 1,
                    "name": "one",
                    "fie": 3,
                    "foe": 4
                },
                2: {
                    "id": 2,
                    "name": "two",
                    "fie": 5,
                    "foe": 6
                }
            }
        }

        self.source.execute({
            "ACTION": "change",
            "DEFINITION": {
                "source": "UnittestSource",
                "name": "simples",
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
                    },
                    {
                        "name": "fie",
                        "store": "fie",
                        "kind": "int"
                    },
                    {
                        "name": "foe",
                        "store": "foe",
                        "kind": "int"
                    }
                ]
            },
            "MIGRATION": {
                "source": "UnittestSource",
                "name": "simple",
                "fields": [
                    {
                        "ACTION": "add",
                        "name": "fee",
                        "store": "fee",
                        "kind": "int"
                    },
                    {
                        "ACTION": "remove",
                        "name": "fie",
                        "store": "fie",
                        "kind": "int"
                    },
                    {
                        "ACTION": "change",
                        "DEFINITION": {
                            "name": "foe",
                            "store": "foe",
                            "kind": "int"
                        },
                        "MIGRATION": {
                            "name": "fum",
                            "store": "fum",
                            "kind": "float"
                        }
                    }
                ]
            }
        })

        self.assertEqual(self.source.ids, {"simple": 2})
        self.assertEqual(self.source.data, {"simple": {
            1: {
                "id": 1,
                "name": "one",
                "fee": None,
                "fum": 4
            },
            2: {
                "id": 2,
                "name": "two",
                "fee": None,
                "fum": 6
            }
        }})

    def test_load(self):

        self.source.ids = {}
        self.source.data = {}

        migrations = relations.Migrations()

        migrations.generate([Unit])
        migrations.convert(self.source.name)

        self.source.load(f"ddl/{self.source.name}/{self.source.KIND}/definition.json")

        self.assertEqual(Unit.many().count(), 0)

    def test_list(self):

        os.makedirs(f"ddl/{self.source.name}/{self.source.KIND}")

        pathlib.Path(f"ddl/{self.source.name}/{self.source.KIND}/definition.json").touch()
        pathlib.Path(f"ddl/{self.source.name}/{self.source.KIND}/definition-2012-07-07.json").touch()
        pathlib.Path(f"ddl/{self.source.name}/{self.source.KIND}/migration-2012-07-07.json").touch()
        pathlib.Path(f"ddl/{self.source.name}/{self.source.KIND}/definition-2012-07-08.json").touch()
        pathlib.Path(f"ddl/{self.source.name}/{self.source.KIND}/migration-2012-07-08.json").touch()

        self.assertEqual(self.source.list(f"ddl/{self.source.name}/{self.source.KIND}"), {
            "2012-07-07": {
                "definition": "definition-2012-07-07.json",
                "migration": "migration-2012-07-07.json"
            },
            "2012-07-08": {
                "definition": "definition-2012-07-08.json",
                "migration": "migration-2012-07-08.json"
            }
        })

    def test_migrate(self):

        self.source.ids = {}
        self.source.data = {}

        migrations = relations.Migrations()

        migrations.generate([Unit])
        migrations.generate([Unit, Test])
        migrations.convert(self.source.name)

        self.assertTrue(self.source.migrate(f"ddl/{self.source.name}/{self.source.KIND}"))

        self.assertEqual(Unit.many().count(), 0)
        self.assertEqual(Test.many().count(), 0)

        self.assertFalse(self.source.migrate(f"ddl/{self.source.name}/{self.source.KIND}"))

        migrations.generate([Unit, Test, Case])
        migrations.convert(self.source.name)

        self.assertTrue(self.source.migrate(f"ddl/{self.source.name}/{self.source.KIND}"))

        self.assertEqual(Case.many().count(), 0)

        self.assertFalse(self.source.migrate(f"ddl/{self.source.name}/{self.source.KIND}"))


class TestUnitTest(relations.unittest.TestCase):

    def test_consistent(self):

        # dict

        self.assertTrue(self.consistent({"a": 1}, {"a": 1, "b": 2}))
        self.assertFalse(self.consistent({"a": 2}, {"a": 1, "b": 2}))

        # list

        self.assertTrue(self.consistent([1, 2], [1, 2, 3]))
        self.assertFalse(self.consistent([1, 2, 4], [2, 1]))
        self.assertFalse(self.consistent([1, 2], [2, 1]))

        # else

        self.assertTrue(self.consistent("a", "a"))
        self.assertFalse(self.consistent("a", "b"))

    def test_contains(self):

        self.assertTrue(self.contains({"a": 1}, [{"a": 1, "b": 2}]))
        self.assertFalse(self.contains({"a": 2}, [{"a": 1, "b": 2}]))

    def test_assertConsistent(self):

        self.assertConsistent({"a": 1}, {"a": 1, "b": 2})

        with unittest.mock.patch('relations.unittest.TestCase.assertEqual') as mock_equal:

            self.assertConsistent({"a": 2}, {"a": 1, "b": 2}, "nope")
            mock_equal.assert_called_once_with({"a": 2}, {"a": 1, "b": 2}, "nope")

    def test_assertContains(self):

        self.assertContains({"a": 1}, [{"a": 1, "b": 2}])

        with unittest.mock.patch('relations.unittest.TestCase.assertIn') as mock_in:

            self.assertContains({"a": 2}, [{"a": 1, "b": 2}], "nope")
            mock_in.assert_called_once_with({"a": 2}, [{"a": 1, "b": 2}], "nope")

    def test_assertFields(self):

        fields = unittest.mock.MagicMock()

        fields.to_list.return_value = [1, 2, 3]

        self.assertFields(fields, [1, 2, 3])

    def test_assertassertStatusValue(self):

        response = unittest.mock.MagicMock()

        response.status_code = 200
        response.json = {"a": 1}

        self.assertStatusValue(response, 200, "a", 1)

    def test_assertStatusFields(self):

        response = unittest.mock.MagicMock()

        response.status_code = 200
        response.json = {
            "fields": [1, 2, 3],
            "errors": True
        }

        self.assertStatusFields(response, 200, [1, 2, 3], errors=True)

    def test_assertStatusModel(self):

        response = unittest.mock.MagicMock()

        response.status_code = 200
        response.json = {
            "model": {"a": 1}
        }

        self.assertStatusModel(response, 200, "model", {"a": 1})

    def test_assertStatusModels(self):

        response = unittest.mock.MagicMock()

        response.status_code = 200
        response.json = {
            "models": [
                {"a": 1}
            ]
        }

        self.assertStatusModels(response, 200, "models", [{"a": 1}])
