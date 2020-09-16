"""
Main relations module for storing sources
"""

SOURCES = {}  # Sources reference to use


def register(source):
    """
    Registers a source
    """

    SOURCES[source.name] = source


def source(name):
    """
    Returns a source
    """

    return SOURCES[name]


class Source:
    """
    Base Abstraction for Source
    """

    name = None

    def __new__(cls, *args, **kwargs):
        """
        Register this source
        """

        self = object.__new__(cls)

        self.name = kwargs.get("name", args[0])

        register(self)

        return self

    def ensure_attribute(self, item, attribute, default=None):
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
        pass

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
        pass

    def record_define(self, record, *args, **kwargs):
        """
        define the record
        """
        for field in record._order:
            self.field_define(field, *args, **kwargs)

    def model_define(self, model):
        """
        define the model
        """
        pass

    def field_create(self, field, *args, **kwargs):
        """
        create the field
        """
        pass

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
        pass

    def field_retrieve(self, field, *args, **kwargs):
        """
        retrieve the field
        """
        pass

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
        pass

    def field_update(self, field, *args, **kwargs):
        """
        update the field
        """
        pass

    def record_update(self, record, *args, **kwargs):
        """
        update the record
        """
        for field in record._order:
            self.field_update(field, *args, **kwargs)

    def model_update(self, model):
        """
        update the model
        """
        pass

    def field_delete(self, field, *args, **kwargs):
        """
        delete the field
        """
        pass

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
        pass

    def children_execute(self, model):
        """
        Execute everythong on the kids
        """

        for parent_child, relation in (model.CHILDREN or {}).items():
            if model._children.get(parent_child):
                model._children[parent_child].execute()
