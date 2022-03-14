"""
Unittests for Migrations
"""

import unittest
import unittest.mock
import freezegun

import os
import shutil
import pathlib
import json

import relations

class People(relations.ModelIdentity):
    SOURCE = "MigrationsSource"
    id = int
    name = str
    gender = ["free", "male", "female"]

class TestMigrations(unittest.TestCase):

    maxDiff = None

    def setUp(self):

        shutil.rmtree("ddl", ignore_errors=True)
        os.makedirs("ddl", exist_ok=True)

    def test___init__(self):

        migrations = relations.Migrations()
        self.assertEqual(migrations.directory, "ddl")

        migrations = relations.Migrations("dll")
        self.assertEqual(migrations.directory, "dll")

    def test_current(self):

        migrations = relations.Migrations()

        self.assertEqual(migrations.current(), {})

        with open("ddl/definition.json", 'w') as ddl_file:
            json.dump({"a": 1}, ddl_file)

        self.assertEqual(migrations.current(), {"a": 1})

    def test_define(self):

        migrations = relations.Migrations()

        self.assertEqual(migrations.define([People]), {
            "people": {
                "source": "MigrationsSource",
                "name": "people",
                "title": "People",
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
            }
        })

    @unittest.mock.patch('relations.migrations.print')
    @unittest.mock.patch('relations.migrations.input')
    def test_rename(self, mock_input, mock_print):

        rename = {}
        relations.Migrations.rename("unit", [], [], rename)
        self.assertEqual(rename, {})
        mock_print.assert_not_called()
        mock_input.assert_not_called()

        remove = ["people", "stuff"]
        add = ["things"]

        mock_input.return_value = '1'

        rename = {}

        relations.Migrations.rename("test", add, remove, rename)

        self.assertEqual(remove, ["stuff"])
        self.assertEqual(add, [])
        self.assertEqual(rename, {"people": "things"})

        mock_print.assert_has_calls([
            unittest.mock.call("Please indicate if any test were renamed:"),
            unittest.mock.call("[1] things")
        ])

        mock_input.assert_called_once_with("Which was people renamed to? (return if none)")

    def test_lookup(self):

        fields = [
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
        ]

        self.assertEqual(relations.Migrations.lookup("gender", fields), {
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
        })

        self.assertIsNone(relations.Migrations.lookup("nope", fields))

    def test_field(self):

        current = {
            "name": "gender",
            "kind": "str",
            "store": "genders",
            "options": [
                "male",
                "female"
            ],
            "default": "free",
            "none": False
        }

        define = {
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

        self.assertEqual(relations.Migrations.field(current, define), {
            "store": "gender",
            "options": [
                "free",
                "male",
                "female"
            ]
        })

    @unittest.mock.patch('relations.migrations.print')
    @unittest.mock.patch('relations.migrations.input')
    def test_fields(self, mock_input, mock_print):

        mock_input.side_effect = ['', '2']

        current = [
            {
                "name": "id",
                "kind": "int",
                "store": "id",
                "none": True
            },
            {
                "name": "genders",
                "kind": "str",
                "store": "genders",
                "options": [
                    "male",
                    "female"
                ],
                "default": "free",
                "none": False
            }
        ]

        define = [
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
        ]

        self.assertEqual(relations.Migrations.fields("test", current, define), {
            "add": [
                {
                    "name": "name",
                    "kind": "str",
                    "store": "name",
                    "none": False
                }
            ],
            "remove": [
                "id"
            ],
            "change": {
                "genders": {
                    "name": "gender",
                    "store": "gender",
                    "options": [
                        "free",
                        "male",
                        "female"
                    ]
                }
            }
        })

        mock_print.assert_has_calls([
            unittest.mock.call("Please indicate if any test fields were renamed:"),
            unittest.mock.call("[1] name"),
            unittest.mock.call("[2] gender"),
            unittest.mock.call("[1] name"),
            unittest.mock.call("[2] gender")
        ])

        mock_input.assert_has_calls([
            unittest.mock.call("Which was id renamed to? (return if none)"),
            unittest.mock.call("Which was genders renamed to? (return if none)")
        ])

    @unittest.mock.patch('relations.migrations.print')
    @unittest.mock.patch('relations.migrations.input')
    def test_indexes(self, mock_input, mock_print):

        mock_input.side_effect = ['2', '']

        current = {
            "people": [1],
            "stuff": [2]
        }

        define = {
            "things": [1],
            "moar": [2]
        }

        self.assertEqual(relations.Migrations.indexes("test", "indexes", current, define), {
            "add": {
                "moar": [2]
            },
            "remove": ["stuff"],
            "rename": {
                "people": "things"
            }
        })

        mock_print.assert_has_calls([
            unittest.mock.call("Please indicate if any test indexes were renamed:"),
            unittest.mock.call("[1] moar"),
            unittest.mock.call("[2] things"),
            unittest.mock.call("[1] moar")
        ])

        mock_input.assert_has_calls([
            unittest.mock.call("Which was people renamed to? (return if none)"),
            unittest.mock.call("Which was stuff renamed to? (return if none)")
        ])

        mock_input.side_effect = ['1']

        current = {
            "people": [1]
        }

        define = {
            "things": [2]
        }

        self.assertRaisesRegex(relations.MigrationsError, "test indexes people and things must have same fields to rename", relations.Migrations.indexes, "test", "indexes", current, define)

    @unittest.mock.patch('relations.migrations.print')
    @unittest.mock.patch('relations.migrations.input')
    def test_model(self, mock_input, mock_print):

        mock_input.side_effect = ['', '2', '', '1', '2', '']

        current = {
            "name": "people",
            "title": "People",
            "id": "id",
            "fields": [
                {
                    "name": "id",
                    "kind": "int",
                    "store": "id",
                    "none": True
                },
                {
                    "name": "genders",
                    "kind": "str",
                    "store": "genders",
                    "options": [
                        "male",
                        "female"
                    ],
                    "default": "free",
                    "none": False
                }
            ],
            "unique": {
                "people": [1],
                "stuff": [2]
            },
            "index": {
                "people": [3],
                "stuff": [4]
            }
        }

        define = {
            "name": "persons",
            "title": "Persons",
            "id": "idd",
            "extra": "info",
            "fields": [
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
            "unique": {
                "things": [1],
                "moar": [2]
            },
            "index": {
                "things": [3],
                "moar": [4]
            }
        }

        self.assertEqual(relations.Migrations.model(current, define), {
            "name": "persons",
            "title": "Persons",
            "id": "idd",
            "extra": "info",
            "fields": {
                "add": [
                    {
                        "name": "name",
                        "kind": "str",
                        "store": "name",
                        "none": False
                    }
                ],
                "remove": [
                    "id"
                ],
                "change": {
                    "genders": {
                        "name": "gender",
                        "store": "gender",
                        "options": [
                            "free",
                            "male",
                            "female"
                        ]
                    }
                }
            },
            "unique": {
                "add": {
                    "things": [1]
                },
                "remove": ["people"],
                "rename": {
                    "stuff": "moar"
                }
            },
            "index": {
                "add": {
                    "moar": [4]
                },
                "remove": ["stuff"],
                "rename": {
                    "people": "things"
                }
            }
        })

        mock_print.assert_has_calls([
            unittest.mock.call("Please indicate if any people/persons fields were renamed:"),
            unittest.mock.call("[1] name"),
            unittest.mock.call("[2] gender"),
            unittest.mock.call("[1] name"),
            unittest.mock.call("[2] gender"),
            unittest.mock.call("Please indicate if any people/persons unique indexes were renamed:"),
            unittest.mock.call("[1] moar"),
            unittest.mock.call("[2] things"),
            unittest.mock.call("[1] moar"),
            unittest.mock.call("[2] things"),
            unittest.mock.call("Please indicate if any people/persons indexes were renamed:"),
            unittest.mock.call("[1] moar"),
            unittest.mock.call("[2] things"),
            unittest.mock.call("[1] moar")
        ])

        mock_input.assert_has_calls([
            unittest.mock.call("Which was id renamed to? (return if none)"),
            unittest.mock.call("Which was genders renamed to? (return if none)"),
            unittest.mock.call("Which was people renamed to? (return if none)"),
            unittest.mock.call("Which was stuff renamed to? (return if none)"),
            unittest.mock.call("Which was people renamed to? (return if none)"),
            unittest.mock.call("Which was stuff renamed to? (return if none)")
        ])

    @unittest.mock.patch('relations.migrations.print')
    @unittest.mock.patch('relations.migrations.input')
    def test_models(self, mock_input, mock_print):

        mock_input.side_effect = ['1', '']

        current = {
            "people": {
                "name": "people",
                "title": "People",
                "id": "id",
                "fields": [],
                "unique": {},
                "index": {}
            },
            "stuff": {
                "name": "stuff",
                "title": "Stuff",
                "id": "id",
                "fields": [],
                "unique": {},
                "index": {}
            }
        }

        define = {
            "persons": {
                "name": "persons",
                "title": "Persons",
                "id": "idd",
                "fields": [],
                "unique": {},
                "index": {}
            },
            "things": {
                "name": "things",
                "title": "Things",
                "id": "id",
                "fields": [],
                "unique": {},
                "index": {}
            }
        }

        self.assertEqual(relations.Migrations.models(current, define), {
            "add": {
                "things": {
                    "name": "things",
                    "title": "Things",
                    "id": "id",
                    "fields": [],
                    "unique": {},
                    "index": {}
                }
            },
            "remove": {
                "stuff": {
                    "name": "stuff",
                    "title": "Stuff",
                    "id": "id",
                    "fields": [],
                    "unique": {},
                    "index": {}
                }
            },
            "change": {
                "people": {
                    "definition": {
                        "name": "people",
                        "title": "People",
                        "id": "id",
                        "fields": [],
                        "unique": {},
                        "index": {}
                    },
                    "migration": {
                        "name": "persons",
                        "title": "Persons",
                        "id": "idd"
                    }
                }
            }
        })

        mock_print.assert_has_calls([
            unittest.mock.call("Please indicate if any models were renamed:"),
            unittest.mock.call("[1] persons"),
            unittest.mock.call("[2] things"),
            unittest.mock.call("[1] things")
        ])

        mock_input.assert_has_calls([
            unittest.mock.call("Which was people renamed to? (return if none)"),
            unittest.mock.call("Which was stuff renamed to? (return if none)")
        ])

    @freezegun.freeze_time("2021-07-08 11:12:13")
    def test_generate(self):

        migrations = relations.Migrations()

        self.assertTrue(migrations.generate([People]))

        with open("ddl/definition.json", 'r') as ddl_file:

            current = json.load(ddl_file)

            self.assertEqual(current, {
                "people": {
                    "source": "MigrationsSource",
                    "name": "people",
                    "title": "People",
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
                }
            })

        self.assertFalse(migrations.generate([People]))

        current["people"]["fields"][2]["store"] = "genders"

        with open("ddl/definition.json", 'w') as ddl_file:
            json.dump(current, ddl_file)

        self.assertTrue(migrations.generate([People]))

        with open("ddl/definition-2021-07-08-11-12-13-000000.json", 'r') as ddl_file:
            self.assertEqual(json.load(ddl_file), {
                "people": {
                    "source": "MigrationsSource",
                    "name": "people",
                    "title": "People",
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
                }
            })

        with open("ddl/migration-2021-07-08-11-12-13-000000.json", 'r') as ddl_file:
            self.assertEqual(json.load(ddl_file), {
                "change": {
                    "people": {
                        "definition": {
                            "source": "MigrationsSource",
                            "name": "people",
                            "title": "People",
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
                        },
                        "migration": {
                            "fields": {
                                "change": {
                                    "gender": {
                                        "store": "gender"
                                    }
                                }
                            }
                        }
                    }
                }
            })

        with open("ddl/definition.json", 'r') as ddl_file:
            self.assertEqual(json.load(ddl_file), {
                "people": {
                    "source": "MigrationsSource",
                    "name": "people",
                    "title": "People",
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
                }
            })

    def test_convert(self):

        relations.unittest.MockSource("MigrationsSource")

        with open("ddl/definition.json", 'w') as ddl_file:
            json.dump({"people": People.thy().define()}, ddl_file)

        with open("ddl/migration-1234.json", 'w') as ddl_file:
            json.dump({
                "change": {
                    "migs": {
                        "definition": {
                            "source": "MigrationsSource",
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
                            "source": "MigrationsSource",
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
            }, ddl_file)

        migrations = relations.Migrations()

        migrations.convert("MigrationsSource")

        with open("ddl/MigrationsSource/mock/definition.json", 'r') as ddl_file:
            self.assertEqual(json.load(ddl_file), [{
                "ACTION": "add",
                "source": "MigrationsSource",
                "name": "people",
                "title": "People",
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
            }])

        with open("ddl/MigrationsSource/mock/migration-1234.json", 'r') as ddl_file:
            self.assertEqual(json.load(ddl_file), [
                {
                    "ACTION": "change",
                    "DEFINITION": {
                        "source": "MigrationsSource",
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
                        "source": "MigrationsSource",
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

    def test_list(self):

        source = relations.unittest.MockSource("MigrationsSource")

        os.makedirs(f"ddl/{source.name}/{source.KIND}")

        pathlib.Path(f"ddl/{source.name}/{source.KIND}/definition.json").touch()
        pathlib.Path(f"ddl/{source.name}/{source.KIND}/definition-2012-07-07.json").touch()
        pathlib.Path(f"ddl/{source.name}/{source.KIND}/migration-2012-07-07.json").touch()
        pathlib.Path(f"ddl/{source.name}/{source.KIND}/definition-2012-07-08.json").touch()
        pathlib.Path(f"ddl/{source.name}/{source.KIND}/migration-2012-07-08.json").touch()

        migrations = relations.Migrations()

        self.assertEqual(migrations.list("MigrationsSource"), {
            "2012-07-07": {
                "definition": f"ddl/{source.name}/{source.KIND}/definition-2012-07-07.json",
                "migration": f"ddl/{source.name}/{source.KIND}/migration-2012-07-07.json"
            },
            "2012-07-08": {
                "definition": f"ddl/{source.name}/{source.KIND}/definition-2012-07-08.json",
                "migration": f"ddl/{source.name}/{source.KIND}/migration-2012-07-08.json"
            }
        })

    def test_list(self):

        source = relations.unittest.MockSource("MigrationsSource")

        os.makedirs(f"ddl/{source.name}/{source.KIND}")

        pathlib.Path(f"ddl/{source.name}/{source.KIND}/definition.json").touch()
        pathlib.Path(f"ddl/{source.name}/{source.KIND}/definition-2012-07-07.json").touch()
        pathlib.Path(f"ddl/{source.name}/{source.KIND}/migration-2012-07-07.json").touch()
        pathlib.Path(f"ddl/{source.name}/{source.KIND}/definition-2012-07-08.json").touch()
        pathlib.Path(f"ddl/{source.name}/{source.KIND}/migration-2012-07-08.json").touch()

        migrations = relations.Migrations()

        self.assertEqual(migrations.list("MigrationsSource"), {
            "2012-07-07": {
                "definition": "definition-2012-07-07.json",
                "migration": "migration-2012-07-07.json"
            },
            "2012-07-08": {
                "definition": "definition-2012-07-08.json",
                "migration": "migration-2012-07-08.json"
            }
        })

    def test_load(self):

        source = relations.unittest.MockSource("MigrationsSource")

        source.ids = {}
        source.data = {}

        definition = [{
            "ACTION": "add",
            "source": "MigrationsSource",
            "name": "people",
            "title": "People",
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
        }]

        os.makedirs("ddl/MigrationsSource/mock", exist_ok=True)

        with open("ddl/MigrationsSource/mock/definition.json", 'w') as ddl_file:
            json.dump(definition, ddl_file)

        migrations = relations.Migrations()

        migrations.load("MigrationsSource", "definition.json")

        self.assertEqual(source.ids, {
            "people": 0
        })
        self.assertEqual(source.data, {
            "people": {}
        })

    def test_apply(self):

        source = relations.unittest.MockSource("MigrationsSource")

        source.ids = {}
        source.data = {}
        source.migrations = []

        # Apply on definition alone

        definition = [{
            "ACTION": "add",
            "source": "MigrationsSource",
            "name": "people",
            "title": "People",
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
        }]

        os.makedirs("ddl/MigrationsSource/mock", exist_ok=True)

        with open("ddl/MigrationsSource/mock/definition.json", 'w') as ddl_file:
            json.dump(definition, ddl_file)

        with open("ddl/MigrationsSource/mock/migration-2021-07-07-11-12-13-000000.json", 'w') as ddl_file:
            json.dump(definition, ddl_file)

        migrations = relations.Migrations()

        self.assertTrue(migrations.apply("MigrationsSource"))

        self.assertEqual(source.ids, {
            "people": 0
        })
        self.assertEqual(source.data, {
            "people": {}
        })
        self.assertEqual(source.migrations, [
            "2021-07-07-11-12-13-000000"
        ])

        self.assertFalse(migrations.apply("MigrationsSource"))
