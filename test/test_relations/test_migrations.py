"""
Unittests for Migrations
"""

import unittest
import unittest.mock
import freezegun

import json

import relations

class People(relations.ModelIdentity):
    id = int
    name = str
    gender = ["free", "male", "female"]

class TestMigrations(unittest.TestCase):

    maxDiff = None

    def test___init__(self):

        migrations = relations.Migrations([1, 2, 3])
        self.assertEqual(migrations.classes, [1, 2, 3])
        self.assertEqual(migrations.directory, "ddl")

        migrations = relations.Migrations([1, 2, 3], "dll")
        self.assertEqual(migrations.classes, [1, 2, 3])
        self.assertEqual(migrations.directory, "dll")

    @unittest.mock.patch('relations.migrations.open', create=True)
    @unittest.mock.patch('os.path.exists')
    def test_current(self, mock_exists, mock_open):

        migrations = relations.Migrations([1, 2, 3], "dll")

        mock_exists.return_value = False
        self.assertEqual(migrations.current(), {})
        mock_exists.assert_called_once_with("dll/definition.json")

        mock_exists.return_value = True
        mock_open.side_effect = [
            unittest.mock.mock_open(read_data='{"a": 1}').return_value
        ]
        self.assertEqual(migrations.current(), {"a": 1})
        mock_open.assert_called_once_with("dll/definition.json", "r")

    def test_define(self):

        migrations = relations.Migrations([People])

        self.assertEqual(migrations.define(), {
            "people": {
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

        renamed = {}
        relations.Migrations.rename("unit", [], [], renamed)
        self.assertEqual(renamed, {})
        mock_print.assert_not_called()
        mock_input.assert_not_called()

        removed = ["people", "stuff"]
        added = ["things"]

        mock_input.return_value = '1'

        renamed = {}

        relations.Migrations.rename("test", added, removed, renamed)

        self.assertEqual(removed, ["stuff"])
        self.assertEqual(added, [])
        self.assertEqual(renamed, {"people": "things"})

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
            "added": [
                {
                    "name": "name",
                    "kind": "str",
                    "store": "name",
                    "none": False
                }
            ],
            "removed": [
                {
                    "name": "id",
                    "kind": "int",
                    "store": "id",
                    "none": True
                }
            ],
            "changed": {
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
            "added": {
                "moar": [2]
            },
            "removed": {
                "stuff": [2]
            },
            "renamed": {
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

        self.assertRaisesRegex(Exception, "test indexes people and things must have same fields to rename", relations.Migrations.indexes, "test", "indexes", current, define)

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
            "fields": {
                "added": [
                    {
                        "name": "name",
                        "kind": "str",
                        "store": "name",
                        "none": False
                    }
                ],
                "removed": [
                    {
                        "name": "id",
                        "kind": "int",
                        "store": "id",
                        "none": True
                    }
                ],
                "changed": {
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
                "added": {
                    "things": [1]
                },
                "removed": {
                    "people": [1]
                },
                "renamed": {
                    "stuff": "moar"
                }
            },
            "index": {
                "added": {
                    "moar": [4]
                },
                "removed": {
                    "stuff": [4]
                },
                "renamed": {
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
            "added": {
                "things": {
                    "name": "things",
                    "title": "Things",
                    "id": "id",
                    "fields": [],
                    "unique": {},
                    "index": {}
                }
            },
            "removed": {
                "stuff": {
                    "name": "stuff",
                    "title": "Stuff",
                    "id": "id",
                    "fields": [],
                    "unique": {},
                    "index": {}
                }
            },
            "changed": {
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
    @unittest.mock.patch('relations.migrations.open', create=True)
    @unittest.mock.patch('os.path.exists')
    def test_generate(self, mock_exists, mock_open):

        migrations = relations.Migrations([People])

        current = {
            "people": {
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
        }

        mock_exists.return_value = True
        mock_open.side_effect = [
            unittest.mock.mock_open(read_data=json.dumps(current)).return_value
        ]

        self.assertFalse(migrations.generate())

        mock_open.assert_called_once_with("ddl/definition.json", 'r')

        current["people"]["fields"][2]["store"] = "genders"

        migration_file = unittest.mock.mock_open().return_value
        current_file = unittest.mock.mock_open().return_value

        mock_exists.return_value = True
        mock_open.side_effect = [
            unittest.mock.mock_open(read_data=json.dumps(current)).return_value,
            migration_file,
            current_file
        ]

        self.assertTrue(migrations.generate())

        mock_open.assert_has_calls([
            unittest.mock.call("ddl/definition.json", 'r'),
            unittest.mock.call("ddl/migration_20210708111213.json", 'w'),
            unittest.mock.call("ddl/definition.json", 'w')
        ])

        self.assertEqual(json.loads(''.join([call[1][0] for call in migration_file.write.mock_calls])), {
            "changed": {
                "people": {
                    "definition": {
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
                    },
                    "migration": {
                        "fields": {
                            "changed": {
                                "gender": {
                                    "store": "gender"
                                }
                            }
                        }
                    }
                }
            }
        })

        self.assertEqual(json.loads(''.join([call[1][0] for call in current_file.write.mock_calls])), {
            "people": {
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
