"""
Unittest Tools for Relations
"""

# pylint: disable=unused-argument,arguments-differ,too-many-public-methods

import copy
import json
import relations

class MockSource(relations.Source):

    """
    Mock Source for Testing
    """

    KIND = "mock"

    ids = None  # ID's keyed by model names
    data = None # Data keyed by model names

    def __init__(self, name, **kwargs):

        self.ids = {}
        self.data = {}

    def field_init(self, field):
        """
        Make sure there's auto_increment
        """

        self.ensure_attribute(field, "auto_increment")

    def model_init(self, model):
        """
        Init the model
        """

        self.record_init(model._fields)

        # Even models without ids will have id's internally
        # They just won't be set in the model

        self.ids.setdefault(model.NAME, 0)
        self.data.setdefault(model.NAME, {})

        if model._id is not None and model._fields._names[model._id].auto_increment is None:
            model._fields._names[model._id].auto = True

    def field_define(self, field, definitions):
        """
        define the field
        """
        definitions.append({"ACTION": "define", **field})

    def model_define(self, model):
        """
        define the model
        """

        definitions = []

        self.record_define(model['fields'], definitions)

        return {"ACTION": "define", **model, "fields": definitions}

    def definition_file(self, file_path, source_path):
        """"
        Converts a definition file to a source definition file
        """

        definitions = []

        with open(file_path, "r") as definition_file:
            definition = json.load(definition_file)
            for name in sorted(definition.keys()):
                if definition[name]["source"] == self.name:
                    definitions.append(self.model_define(definition[name]))

        if definitions:
            file_name = file_path.split("/")[-1].split('.')[0]
            with open(f"{source_path}/{file_name}.json", "w") as source_file:
                source_file.write(json.dumps(definitions))
                source_file.write("\n")

    def field_add(self, migration, migrations):
        """
        add the field
        """

        migrations.append({"ACTION": "add", **migration})

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

        definitions = []

        self.record_define(definition['fields'], definitions)

        return {"ACTION": "add", **definition, "fields": definitions}

    def model_remove(self, definition):
        """
        remove the model
        """

        return {"ACTION": "remove", **definition}

    def model_change(self, definition, migration):
        """
        change the model
        """

        migrations = []

        self.record_change(definition['fields'], migration.get("fields", {}), migrations)

        return {"ACTION": "change", "DEFINITION": definition, "MIGRATION": {**migration, "fields": migrations}}

    def migration_file(self, file_path, source_path):
        """"
        Converts a migration file to a source definition file
        """

        migrations = []

        with open(file_path, "r") as migration_file:
            migration = json.load(migration_file)

            for add in sorted(migration.get('add', {}).keys()):
                if migration['add'][add]["source"] == self.name:
                    migrations.append(self.model_add(migration['add'][add]))

            for remove in sorted(migration.get('remove', {}).keys()):
                if migration['remove'][remove]["source"] == self.name:
                    migrations.append(self.model_remove(migration['remove'][remove]))

            for change in sorted(migration.get('change', {}).keys()):
                if migration['change'][change]['definition']["source"] == self.name:
                    migrations.append(
                        self.model_change(migration['change'][change]['definition'], migration['change'][change]['migration'])
                    )

        if migrations:
            file_name = file_path.split("/")[-1].split('.')[0]
            with open(f"{source_path}/{file_name}.json", "w") as source_file:
                source_file.write(json.dumps(migrations))
                source_file.write("\n")

    @staticmethod
    def extract(model, values):
        """
        Extracts from fields and injects into values
        """

        for extracting in [field for field in model._fields._order if field.extract]:
            for extract in extracting.extract:
                values[f"{extracting.store}__{extract}"] = extracting.get(values.get(extracting.store), extract)

        return values

    def model_create(self, model):
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

        for field in model._label:
            relation = model._ancestor(field)
            if relation:
                parent = relation.Parent.many(like=model._like).limit(model._chunk)
                parents[model._fields._names[field].store] = parent[relation.parent_field]
                model.overflow = model.overflow or parent.overflow

        likes = []

        for record in self.data[model.NAME].values():
            if model._record.like(record, model._label, model._like, parents):
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

    def model_count(self, model):
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

    def model_retrieve(self, model, verify=True):
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

    def model_labels(self, model):
        """
        Creates the labels structure
        """

        if model._action == "retrieve":
            self.model_retrieve(model)

        labels = relations.Labels(model)

        for labeling in model._each():
            labels.add(labeling)

        return labels

    def model_update(self, model):
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

    def model_delete(self, model):
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
