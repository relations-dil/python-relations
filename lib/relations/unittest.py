"""
Unittest Tools for Relations
"""

# pylint: disable=unused-argument,arguments-differ,too-many-public-methods,invalid-name

import glob
import copy
import json
import unittest
import relations


class MockQuery: # pylint: disable=too-few-public-methods
    """
    Mock Query for testing
    """

    action = None
    model = None

    def __init__(self, action):

        self.action = action

    def bind(self, model):
        """
        Mimic bind
        """

        self.model = model

        return self

class MockSource(relations.Source):

    """
    Mock Source for Testing
    """

    KIND = "mock"

    SELECT = MockQuery
    INSERT = MockQuery
    UPDATE = MockQuery
    DELETE = MockQuery

    ids = None  # ID's keyed by model names
    data = None # Data keyed by model names
    migrations = None # Migrations applied so far

    def __init__(self, name, **kwargs):

        self.ids = {}
        self.data = {}
        self.migrations = None

    def init(self, model):
        """
        Init the model
        """

        self.record_init(model._fields)

        # Even models without ids will have id's internally
        # They just won't be set in the model

        self.ids.setdefault(model.NAME, 0)
        self.data.setdefault(model.NAME, {})

        if model._id is not None and model._fields._names[model._id].auto is None:
            model._fields._names[model._id].auto = True

    def field_define(self, field, definitions):
        """
        define the field
        """
        definitions.append(field)

    def define(self, model):
        """
        define the model
        """

        definitions = []

        self.record_define(model['fields'], definitions)

        return [{"ACTION": "add", **model, "fields": definitions}]

    def field_add(self, migration, migrations):
        """
        add the field
        """

        definitions = []

        self.field_define(migration, definitions)

        migrations.extend([{**definition, "ACTION": "add"} for definition in definitions])

    def field_remove(self, definition, migrations):
        """
        remove the field
        """

        migrations.append({"ACTION": "remove", **definition})

    def field_change(self, definition, migration, migrations):
        """
        change the field
        """

        migrations.append({"ACTION": "change", "DEFINITION": definition, "MIGRATION": migration})

    def model_add(self, definition):
        """
        add the model
        """

        return self.define(definition)

    def model_remove(self, definition):
        """
        remove the model
        """

        return [{"ACTION": "remove", **definition}]

    def model_change(self, definition, migration):
        """
        change the model
        """

        migrations = []

        self.record_change(definition['fields'], migration.get("fields", {}), migrations)

        return [{"ACTION": "change", "DEFINITION": definition, "MIGRATION": {**migration, "fields": migrations}}]

    @staticmethod
    def extract(model, values):
        """
        Extracts from fields and injects into values
        """

        for extracting in [field for field in model._fields._order if field.extract]:
            for extract in extracting.extract:
                values[f"{extracting.store}__{extract}"] = extracting.get(values.get(extracting.store), extract)

        return values

    def create_query(self, model):
        """
        create query
        """

        return self.INSERT("CREATE")

    def create(self, model):
        """
        Executes the create
        """

        for creating in model._each("create"):

            values = creating._record.create({})

            self.ids[model.NAME] += 1

            if model._id is not None and values.get(model._id) is None:
                values[model._fields._names[model._id].store] = self.ids[model.NAME]
                creating[model._id] = self.ids[model.NAME]

            self.data[model.NAME][self.ids[model.NAME]] = self.extract(creating, values)

            if not model._bulk:

                for parent_child in creating.CHILDREN:
                    if creating._children.get(parent_child):
                        creating._children[parent_child].create()

                creating._action = "update"
                creating._record._action = "update"

        if model._bulk:
            model._models = []
        else:
            model._action = "update"

        return model

    def model_like(self, model):
        """
        Gets the like matching records
        """

        parents = {}

        for field in model._titles:
            relation = model._ancestor(field)
            if relation:
                parent = relation.Parent.many(like=model._like).limit(model._chunk)
                parents[model._fields._names[field].store] = parent[relation.parent_field]
                model.overflow = model.overflow or parent.overflow

        likes = []

        for record in self.data[model.NAME].values():
            if model._record.like(record, model._titles, model._like, parents):
                likes.append(record)

        return likes

    @staticmethod
    def model_sort(model):
        """
        Sorts the resuls
        """

        sort = model._sort or model._order

        if sort:
            model.sort(*sort)._sort = None

    @staticmethod
    def model_limit(model):
        """
        Limits the results
        """

        if model._limit is None:
            return

        model._models = model._models[model._offset:model._offset + model._limit]
        model.overflow = model.overflow or len(model._models) >= model._limit

    def count_query(self, model):
        """
        count query
        """

        return self.SELECT("COUNT")

    def count(self, model):
        """
        Executes the retrieve
        """

        model._collate()

        values = self.model_like(model) if model._like is not None else self.data[model.NAME].values()

        matches = 0

        for record in values:
            if model._record.retrieve(record):
                matches += 1

        return matches

    def retrieve_query(self, model):
        """
        retrieve query
        """

        return self.SELECT("RETRIEVE")

    def retrieve(self, model, verify=True):
        """
        Executes the retrieve
        """

        model._collate()

        values = self.model_like(model) if model._like is not None else self.data[model.NAME].values()

        matches = []

        for record in values:
            if model._record.retrieve(record):
                matches.append(record)

        if model._mode == "one" and len(matches) > 1:
            raise relations.model.ModelError(model, "more than one retrieved")

        if model._mode == "one" and model._role != "child":

            if len(matches) < 1:

                if verify:
                    raise relations.model.ModelError(model, "none retrieved")

                return None

            model._record = model._build("update", _read=matches[0])

        else:

            model._models = []

            for match in matches:
                model._models.append(model.__class__(_read=match))

            model._record = None

        model._action = "update"

        if model._mode == "many":
            self.model_sort(model)
            self.model_limit(model)

        return model

    def titles_query(self, model):
        """
        titles query
        """

        return self.SELECT("TITLES")

    def titles(self, model):
        """
        Creates the titles structure
        """

        if model._action == "retrieve":
            self.retrieve(model)

        titles = relations.Titles(model)

        for titling in model._each():
            titles.add(titling)

        return titles

    def update_query(self, model):
        """
        update query
        """

        return self.UPDATE("UPDATE")

    def update(self, model):
        """
        Executes the update
        """

        updated = 0

        # If the overall model is retrieving and the record has values set

        if model._action == "retrieve" and model._record._action == "update":

            values = model._record.mass({})

            for data in self.data[model.NAME].values():
                if model._record.retrieve(data):
                    updated += 1
                    data.update(self.extract(model, copy.deepcopy(values)))

        elif model._id:

            for updating in model._each("update"):

                self.data[model.NAME][updating[model._id]].update(self.extract(updating, updating._record.update({})))

                updated += 1

                for parent_child in updating.CHILDREN:
                    if updating._children.get(parent_child):
                        updating._children[parent_child].create().update()

        else:

            raise relations.model.ModelError(model, "nothing to update from")

        return updated

    def delete_query(self, model):
        """
        delete query
        """

        return self.DELETE("DELETE")

    def delete(self, model):
        """
        Executes the delete
        """

        ids = []

        if model._action == "retrieve":

            for id, record in self.data[model.NAME].items():
                if model._record.retrieve(record):
                    ids.append(id)

        elif model._id:

            for deleting in model._each():
                ids.append(deleting[model._id])
                deleting._action = "create"

            model._action = "create"

        else:

            raise relations.model.ModelError(model, "nothing to delete from")

        for id in ids:
            del self.data[model.NAME][id]

        return len(ids)

    def definition(self, file_path, source_path):
        """"
        Converts a definition file to a source definition file
        """

        definitions = []

        with open(file_path, "r") as definition_file:
            definition = json.load(definition_file)
            for name in sorted(definition.keys()):
                if definition[name]["source"] == self.name:
                    definitions.extend(self.define(definition[name]))

        if definitions:
            file_name = file_path.split("/")[-1].split('.')[0]
            with open(f"{source_path}/{file_name}.json", "w") as source_file:
                source_file.write(json.dumps(definitions))
                source_file.write("\n")

    def migration(self, file_path, source_path):
        """"
        Converts a migration file to a source definition file
        """

        migrations = []

        with open(file_path, "r") as migration_file:
            migration = json.load(migration_file)

            for add in sorted(migration.get('add', {}).keys()):
                if migration['add'][add]["source"] == self.name:
                    migrations.extend(self.model_add(migration['add'][add]))

            for remove in sorted(migration.get('remove', {}).keys()):
                if migration['remove'][remove]["source"] == self.name:
                    migrations.extend(self.model_remove(migration['remove'][remove]))

            for change in sorted(migration.get('change', {}).keys()):
                if migration['change'][change]['definition']["source"] == self.name:
                    migrations.extend(
                        self.model_change(migration['change'][change]['definition'], migration['change'][change]['migration'])
                    )

        if migrations:
            file_name = file_path.split("/")[-1].split('.')[0]
            with open(f"{source_path}/{file_name}.json", "w") as source_file:
                source_file.write(json.dumps(migrations))
                source_file.write("\n")

    def execute(self, models): # pylint: disable=too-many-branches
        """
        execute the model or models
        """

        if not isinstance(models, list):
            models = [models]

        for model in models: # pylint: disable=too-many-nested-blocks

            if model["ACTION"] == "add":

                self.data.setdefault(model['name'], {})
                self.ids.setdefault(model['name'], 0)

            elif model["ACTION"] == "remove":

                del self.data[model['name']]
                del self.ids[model['name']]

            elif model["ACTION"] == "change":

                name = model["MIGRATION"].get("name", model["DEFINITION"]["name"])

                if model["DEFINITION"]["name"] != name:

                    self.data[name] = self.data[model["DEFINITION"]["name"]]
                    self.ids[name] = self.ids[model["DEFINITION"]["name"]]

                    del self.data[model["DEFINITION"]["name"]]
                    del self.ids[model["DEFINITION"]["name"]]

                for field in model["MIGRATION"].get("fields"):

                    if field["ACTION"] == "add":

                        for record in self.data[name].values():
                            record[field['store']] = field.get("default")

                    elif field["ACTION"] == "remove":

                        for record in self.data[name].values():
                            del record[field['store']]

                    elif field["ACTION"] == "change":

                        store = field["MIGRATION"].get("store", field["DEFINITION"]["store"])

                        if field["DEFINITION"]["store"] != store:

                            for record in self.data[name].values():
                                record[store] = record[field["DEFINITION"]["store"]]
                                del record[field["DEFINITION"]["store"]]

    def load(self, load_path):
        """
        Load a file
        """

        with open(load_path, 'r') as load_file:
            self.execute(json.load(load_file))

    def list(self, source_path):
        """
        List the migration by pairs
        """

        migrations = {}

        for file_path in glob.glob(f"{source_path}/*-*.json"):

            file_name = file_path.rsplit("/", 1)[-1]
            kind, stamp = file_name.split('.')[0].split('-', 1)

            migrations.setdefault(stamp, {})
            migrations[stamp][kind] = file_name

        return migrations

    def migrate(self, source_path):
        """
        Migrate all the existing files to where we are
        """

        migrated = False

        migration_paths = sorted(glob.glob(f"{source_path}/migration-*.json"))

        if self.migrations is None:

            self.migrations = []

            self.load(f"{source_path}/definition.json")
            migrated = True

        else:

            for migration_path in migration_paths:
                if migration_path.rsplit("/migration-", 1)[-1].split('.')[0] not in self.migrations:
                    self.load(migration_path)
                    migrated = True

        for migration_path in migration_paths:
            migration = migration_path.rsplit("/migration-", 1)[-1].split('.')[0]
            if migration not in self.migrations:
                self.migrations.append(migration)

        return migrated


class TestCase(unittest.TestCase):
    """
    Extended unittest.TestCase with asserts used with klot-io
    """

    maxDiff = None

    def consistent(self, first, second):
        """
        A loose equals for checking only the parts of dictionares and lists you care about
        {"a": 1} is consistent with {"a": 1, "b": 2} while {"a": 2} is not
        [1,2] is consistent with [1,2,3] but [1,2,4] is not. Neither is [2,1]
        """

        if isinstance(first, dict) and isinstance(second, dict):

            for first_key, first_item in first.items():
                if first_key not in second or not self.consistent(first_item, second[first_key]):
                    return False

        elif isinstance(first, list) and isinstance(second, list):

            second_index = 0

            for first_item in first:

                found = False

                for second_index, second_item in enumerate(second[second_index:]):
                    if self.consistent(first_item, second_item):
                        found = True
                        break

                if not found:
                    return False

        else:

            return first == second

        return True

    def contains(self, member, container):
        """
        Checks to see if members is conistent with an item within container
        """

        for item in container:
            if self.consistent(member, item):
                return True

        return False

    def assertConsistent(self, first, second, message=None):
        """
        Asserts first is consistent with second
        """

        if not self.consistent(first, second):
            self.assertEqual(first, second, message)

    def assertContains(self, member, container, message=None):
        """
        Asserts member is contained within second
        """

        if not self.contains(member, container):
            self.assertIn(member, container, message)

    def assertFields(self, fields, data):
        """
        Asserts fields object in list form equals data
        """

        items = fields.to_list()

        self.assertEqual(len(items), len(data), "fields")

        for index, field in enumerate(items):
            self.assertEqual(field, data[index], index)

    def assertStatusValue(self, response, code, key, value):
        """
        Assert a response's code and keyed json value are equal.
        Good with checking API responses in full with an outout
        of the json if unequal
        """

        self.assertEqual(response.status_code, code, response.json)
        self.assertEqual(response.json[key], value)

    def assertStatusFields(self, response, code, fields, errors=None):
        """
        Assert a response's code and keyed json fields are equal.
        Good with checking API responses  of options with an outout
        of the json if unequal
        """

        self.assertEqual(response.status_code, code, response.json)

        self.assertEqual(len(fields), len(response.json['fields']), "fields")

        for index, field in enumerate(fields):
            self.assertEqual(field, response.json['fields'][index], index)

        if errors or "errors" in response.json:

            self.assertIsNotNone(errors, response.json)
            self.assertIn("errors", response.json, response.json)

            self.assertEqual(errors, response.json['errors'], "errors")

    def assertStatusModel(self, response, code, key, model):
        """
        Assert a response's code and keyed json model are consitent.
        Good with checking API responses of creates, gets with an outout
        of the json if inconsistent
        """

        self.assertEqual(response.status_code, code, response.json)
        self.assertConsistent(model, response.json[key])

    def assertStatusModels(self, response, code, key, models):
        """
        Assert a response's code and keyed json models are consitent.
        Good with checking API responses of lists with an outout
        of the json if inconsistent
        """

        self.assertEqual(response.status_code, code, response.json)
        self.assertEqual(len(models), len(response.json[key]), "model count")

        for index, model in enumerate(models):
            self.assertConsistent(model, response.json[key][index])
