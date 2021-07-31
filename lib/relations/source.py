"""
relations module for storing sources
"""

# pylint: disable=too-many-public-methods

import relations

class Source:
    """
    Base Abstraction for Source
    """

    name = None
    KIND = None

    def __new__(cls, *args, **kwargs):
        """
        Register this source
        """

        self = object.__new__(cls)

        self.name = kwargs.get("name", args[0])

        for key in kwargs:
            setattr(self, key, kwargs[key])

        relations.register(self)

        return self

    def ensure_attribute(self, item, attribute, default=None): # pylint: disable=no-self-use
        """
        ensure the item has the attribute
        """
        if hasattr(item, attribute):
            return

        setattr(item, attribute, default)

    def field_init(self, field):
        """
        init the field
        """

    def record_init(self, record):
        """
        init the record
        """
        for field in record._order:
            self.field_init(field)

    def model_init(self, model):
        """
        init the model
        """
        self.record_init(model._fields)

    def field_define(self, field, *args, **kwargs):
        """
        define the field
        """

    def record_define(self, record, *args, **kwargs):
        """
        define the record
        """
        for field in record:
            self.field_define(field, *args, **kwargs)

    def model_define(self, model):
        """
        define the model
        """

    def field_add(self, migration, *args, **kwargs):
        """
        add the field
        """

    def field_remove(self, definition, *args, **kwargs):
        """
        remove the field
        """

    def field_change(self, definition, migration, *args, **kwargs):
        """
        change the field
        """

    def record_change(self, definition, migration, *args, **kwargs):
        """
        define the record
        """

        for add in migration.get('add', []):
            self.field_add(add, *args, **kwargs)

        for remove in migration.get('remove', []):
            self.field_remove(relations.Migrations.lookup(remove, definition), *args, **kwargs)

        for field in definition:
            if field["name"] in migration.get("change", {}):
                self.field_change(field, migration["change"][field['name']], *args, **kwargs)

    def model_add(self, migration):
        """
        define the model
        """

    def model_remove(self, definition):
        """
        define the model
        """

    def model_change(self, definition, migration):
        """
        define the model
        """

    def field_create(self, field, *args, **kwargs):
        """
        create the field
        """

    def record_create(self, record, *args, **kwargs):
        """
        create the record
        """
        for field in record._order:
            self.field_create(field, *args, **kwargs)

    def model_create(self, model):
        """
        create the model
        """

    def field_retrieve(self, field, *args, **kwargs):
        """
        retrieve the field
        """

    def record_retrieve(self, record, *args, **kwargs):
        """
        retrieve the record
        """
        for field in record._order:
            self.field_retrieve(field, *args, **kwargs)

    def model_retrieve(self, model, verify=True):
        """
        retrieve the model
        """

    def model_labels(self, model):
        """
        labels of the model
        """

    def field_update(self, field, *args, **kwargs):
        """
        update the field
        """

    def record_update(self, record, *args, **kwargs):
        """
        update the record
        """
        for field in record._order:
            self.field_update(field, *args, **kwargs)

    def field_mass(self, field, *args, **kwargs):
        """
        mass the field
        """

    def record_mass(self, record, *args, **kwargs):
        """
        mass the record
        """
        for field in record._order:
            self.field_mass(field, *args, **kwargs)

    def model_update(self, model):
        """
        update the model
        """

    def field_delete(self, field, *args, **kwargs):
        """
        delete the field
        """

    def record_delete(self, record, *args, **kwargs):
        """
        delete the record
        """
        for field in record._order:
            self.field_delete(field, *args, **kwargs)

    def model_delete(self, model):
        """
        delete the model
        """

    def definition_convert(self, file_path, source_path):
        """
        Concvert a general definition file to a source specific file
        """

    def migration_convert(self, file_path, source_path):
        """
        Concvert a general migration file to a source specific file
        """

    def execute(self, commands):
        """
        Execute a command or commands
        """

    def migrate(self, source_path):
        """
        Execute a command or commands
        """
