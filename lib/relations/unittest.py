"""
Unittest Tools for Relations
"""

# pylint: disable=unused-argument,arguments-differ

import relations

class MockSource(relations.Source):

    """
    Mock Source for Testing
    """

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
            model._fields._names[model._id].auto_increment = True
            model._fields._names[model._id].readonly = True

    def field_define(self, field, definitions):
        """
        define the field
        """
        definitions[field.store] = field.kind

    def model_define(self, cls):
        """
        define the model
        """

        model = cls._thyself()

        definitions = {}

        self.record_define(model._fields, definitions)

        return {
            model.NAME: definitions
        }

    def model_create(self, model):
        """
        Executes the create
        """

        for creating in model._each("create"):

            values = creating._record.write({})

            self.ids[model.NAME] += 1

            if model._id is not None and values.get(model._id) is None:
                values[model._fields._names[model._id].store] = self.ids[model.NAME]
                creating[model._id] = self.ids[model.NAME]

            self.data[model.NAME][self.ids[model.NAME]] = values

            for parent_child in creating.CHILDREN:
                if creating._children.get(parent_child):
                    creating._children[parent_child].create()

            creating._action = "update"
            creating._record._action = "update"

        model._action = "update"

        return model

    def model_retrieve(self, model, verify=True):
        """
        Executes the retrieve
        """

        model._collate()

        matches = []

        for record in self.data[model.NAME].values():
            if model._record.satisfy(record):
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

        return model

    def field_update(self, field, values, changed=None):
        """
        Updates values with the field's that changed
        """

        if not field.readonly and (changed is None or field.changed == changed):
            values[field.store] = field.value
            field.changed = False

    def model_update(self, model):
        """
        Executes the update
        """

        updated = 0

        # If the overall model is retrieving and the record has values set

        if model._action == "retrieve" and model._record._action == "update":

            values = {}
            self.record_update(model._record, values, changed=True)

            for record in self.data[model.NAME].values():
                if model._record.satisfy(record):
                    updated += 1
                    record.update(values)

        elif model._id:

            for updating in model._each("update"):

                values = {}
                self.record_update(updating._record, values)

                self.data[model.NAME][updating[model._id]].update(values)

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
                if model._record.satisfy(record):
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
