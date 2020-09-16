"""
Base Model module
"""

import sys
import copy

import relations

class FieldError(Exception):

    def __init__(self, field, message):

        self.field = field
        self.message = message
        super().__init__(self.message)

class Field:
    """
    Base field class
    """

    name = None     # Name used in models
    kind = None     # Data class to cast values as or validate
    store = None    # Name to use when reading and writing
    value = None    # Value of the field
    changed = None  # Whether the values been changed since creation, retrieving
    criteria = None # Values for searching

    strict = True     # Whether or not to cast on set
    length = None     # Length of the value
    default = None    # Default value
    not_null = None   # Whether to allow nulls (None)
    readonly = False  # Whether this field is readonly

    # Operators supported and whether allwo multiple values

    OPERATORS = {
        'in': True,
        'ne': True,
        'eq': False,
        'gt': False,
        'ge': False,
        'lt': False,
        'le': False
    }

    RESERVED = [
        'define',
        'filter',
        'satisfy',
        'prepare',
        'read',
        'write',
        'append',
        'insert',
        'action',
        'list',
        'get',
        'set',
        'add',
        'create',
        'retrieve',
        'update',
        'delete',
        'execute'
    ]

    def __init__(self, kind, **kwargs):
        """
        Set the name and what to cast it as and everything else be free form
        """

        self.kind = kind
        self._kwargs = kwargs

        # Just set what as sent

        for name, attribute in kwargs.items():
            setattr(self, name, attribute)

    def __setattr__(self, name, value):
        """
        Use to set field values so everything is cost correctly
        """

        if name == "name":

            error = None

            if value in self.RESERVED:
                error = "is reserved"

            if "__" in value:
                error = "cannot contain '__'"

            if value[0] == '_':
                error = "cannot start with '_'"

            if error:
                raise FieldError(self, f"field name '{value}' {error} - use the store attribute for this name")

            if self.store is None:
                self.store = value

        if name == "value":
            value = self.set(value)
            self.changed = True

        object.__setattr__(self, name, value)

    def __getattribute__(self, name):
        """
        Use to set field values so everything is cost correctly
        """

        if name == "value":
            return self.get(object.__getattribute__(self, "value"))

        return object.__getattribute__(self, name)

    def set(self, value):
        """
        Returns the value to set
        """

        if not self.strict:

            return value

        elif value is None:

            if not self.not_null:
                return value

            raise FieldError(self, f"{value} not allowed for {self.name}")

        elif isinstance(self.kind, list):

            for option in self.kind:
                if option == value:
                    return option

            raise FieldError(self, f"{value} not in {self.kind} for {self.name}")

        else:

            return self.kind(value)

    def get(self, value):
        """
        Gets the value
        """

        if value is None or not self.strict:

            return value

        elif isinstance(self.kind, list):

            for option in self.kind:
                if option == value:
                    return option

            raise FieldError(self, f"{value} not in {self.kind} for {self.name}")

        return value

    def filter(self, value, operator="eq"):
        """
        Set a criterion in criteria
        """

        if operator not in self.OPERATORS:
            raise FieldError(self, f"unknown operator '{operator}'")

        if self.criteria is None:
            self.criteria = {}

        if self.OPERATORS[operator]:

            self.criteria.setdefault(operator, [])

            if not isinstance(value, list):
                value = [value]

            self.criteria[operator].extend([self.set(item) for item in value])

        else:

            self.criteria[operator] = self.set(value)

    def satisfy(self, values):
        """
        Check if this value satisfies our criteria
        """

        value = self.set(values.get(self.store))

        for operator, satisfy in (self.criteria or {}).items():
            if (
                (operator == "in" and value not in satisfy) or
                (operator in "ne" and value in satisfy) or
                (operator == "eq" and value != satisfy) or
                (operator == "gt" and value <= satisfy) or
                (operator == "ge" and value < satisfy) or
                (operator == "lt" and value >= satisfy) or
                (operator == "le" and value > satisfy)
            ):
                return False

        return True

    def read(self, values):
        """
        Loads the value from storage
        """

        self.value = values.get(self.store)
        self.changed = False

    def write(self, values):
        """
        Writes values to dict (if not readonly)
        """

        if not self.readonly:
            values[self.store] = self.value
            self.changed = False


class RecordError(Exception):

    def __init__(self, record, message):

        self.record = record
        self.message = message
        super().__init__(self.message)

class Record:
    """
    Stores record for a Model
    """

    ACTIONS = [
        'ignore',
        'create',
        'list',
        'get',
        'update',
        'delete'
    ]

    _order  = None  # Access in order
    _names  = None  # Access by name
    _action = None # What to do with this record

    def __init__(self):
        """
        Initialize _names and _order
        """

        self._order = []
        self._names = {}

    def insert(self, index, field):
        """
        Inserts a field to a specifc location
        """

        self._order.insert(index, field)
        self._names[field.name] = field

    def append(self, field):
        """
        Adds a field
        """

        self.insert(len(self._order), field)

    def __setattr__(self, name, value):
        """
        Use to set field values directly
        """

        if name[0] != '_' and name in self._names:
            self._names[name].value = value
        else:
            self.__dict__[name] = value

    def __getattr__(self, name):
        """
        Use to get field values directly
        """

        if name in (self._names or []):
            return self._names[name].value

        raise AttributeError(f"'{self}' object has no attribute '{name}'")

    def __len__(self):
        """
        Use for numnber of record
        """
        return len(self._order)

    def __iter__(self):
        """
        Use the _order of record to return the names
        """
        for field in self._order:
            yield field.name

    def __contains__(self, key):
        """
        Checks numerically or by name
        """

        if isinstance(key, int) and key < len(self._order):
            return True

        if key in self._names:
            return True

        return False

    def __setitem__(self, key, value):
        """
        Sets numerically or by name
        """

        if isinstance(key, int):
            if key < len(self._order):
                self._order[key].value = value
                return

        if key in self._names:
            self._names[key].value = value
            return

        raise RecordError(self, f"unknown field '{key}'")

    def __getitem__(self, key):
        """
        Access numerically or by name
        """

        if isinstance(key, int):
            if key < len(self._order):
                return self._order[key].value

        if key in self._names:
            return self._names[key].value

        raise RecordError(self, f"unknown field '{key}'")

    def action(self, _action=None):

        if _action is None:
            return self._action

        if _action not in self.ACTIONS:
            raise RecordError(self, f"unknown action '{_action}'")

        self._action = _action

    def filter(self, criterion, value):
        """
        Sets criterion on a field
        """

        if isinstance(criterion, int):
            if criterion < len(self._order):
                return self._order[criterion].filter(value)
        else:
            if '__' in criterion:
                name, operator = criterion.split("__")
                if name in self._names:
                    return self._names[name].filter(value, operator)
            if criterion in self._names:
                return self._names[criterion].filter(value)

        raise RecordError(self, f"unknown criterion '{criterion}'")

    def satisfy(self, values):
        """
        Sees if a record satisfies criteria in a dict
        """

        for field in self._order:
            if not field.satisfy(values):
                return False

        return True

    def read(self, values):
        """
        Loads the value from storage
        """

        for field in self._order:
            field.read(values)

    def write(self, values):
        """
        Writes values to dict (if not readonly)
        """

        for field in self._order:
            field.write(values)

        return values

class ModelError(Exception):

    def __init__(self, model, message):

        self.model = model
        self.message = message
        super().__init__(self.message)

class Model:

    SOURCE = None   # Data source

    ID = 0          # Ref of id field (assumes first field)
    NAME = None     # Name of the model

    PARENTS = None  # Parent relationships
    CHILDREN = None # Child relationships
    SISTERS = None  # Sister relationships
    BROTHERS = None # Brother relationships

    _id = None     # Name of id field
    _fields = None # Base record to create other records with
    _record = None # The current loaded single record (from get/create)
    _models = None # The current loaded multiple models (from list/create)
    _criteria = None # The current record to search with

    _parents = None  # Parent models
    _children = None # Children models
    _sisters = None  # Sister models
    _brothers = None # Brother models

    _single = False    # Whether or not we'll only only single records (from OneToOne)
    _related = None    # Which fields will be set automatically

    def __init__(self, *args, **kwargs):
        """
        Creation is implied but we want to set stuff and call create impliicitly
        """

        # Set name if not set

        if self.NAME is None:
            self.NAME = self.__class__.__name__.lower()

        # Create a fields list of actual field in the right format

        self._fields = Record()

        # Whether we're OneToOne Child

        self._single = self._extract(kwargs, '_single', False)

        # Parent value to set on adds

        self._related = self._extract(kwargs, '_related', {})

        for name, attribute in self.__class__.__dict__.items():

            if name.startswith('_') or name != name.lower():
                continue # pragma: no cover

            if attribute in [int, float, str, dict , list]:
                field = Field(attribute)
            elif isinstance(attribute, tuple):
                field = Field(*attribute)
            elif isinstance(attribute, dict):
                field = Field(**attribute)
            elif isinstance(attribute, Field):
                field = attribute
            else:
                continue # pragma: no cover

            field.name = name

            self._fields.append(field)

        # Determine the _id field name

        if self.ID is not None:
            self._id = Relation.field_name(self.ID, self)

        # Have the the source do whatever it needs to

        if self.SOURCE is not None:
            relations.source(self.SOURCE).model_init(self)

        _action = self._extract(kwargs, '_action', "create")

        # Initialize relation models

        self._parents = {}
        self._children = {}
        self._sisters = {}
        self._brothers = {}

        if _action == "create":

            if not args or not isinstance(args[0], list):

                self._record = self._build("create", *args, **kwargs)

            # If we're creating multiple records

            else:

                self._models = []

                for single in args[0]:

                    sargs = single if isinstance(single, list) else []
                    skwargs = single if isinstance(single, dict) else {}
                    self._models.append(self.__class__(_action="create", _single=self._single, _related=self._related, *sargs, **skwargs))

        elif _action == "update":

            self._record = self._build("update", _read=self._extract(kwargs, '_read'))

        elif _action in ["get", "list"]:

            self._criteria = self._build(_action, _defaults=False)
            self.filter(*args, **kwargs)

    def __setattr__(self, name, value):
        """
        Use to set field values directly
        """

        if name[0] != '_' and name == name.lower() and name in (object.__getattribute__(self, '_fields') or []):

            self._ensure()

            if self._record is not None:
                self._record[name] = value
            elif self._models is not None:
                for model in self._models:
                    model[name] = value
            else:
                raise ModelError(self, "no records")

            self._propagate(name, value)

        else:

            object.__setattr__(self, name, value)

    def __getattr__(self, name):
        """
        Used to get relation models directly
        """

        relation = self._relate(name)

        if relation is not None:
            return relation

        raise AttributeError(f"'{self}' object has no attribute '{name}'")

    def __getattribute__(self, name):
        """
        Use to get field values directly
        """

        if name[0] != '_' and name == name.lower() and name in (object.__getattribute__(self, '_fields') or []):

            self._ensure()

            if self._record is not None:
                return self._record[name]

            if self._models is not None:
                return [model[name] for model in self._models]

            raise ModelError(self, "no records")

        else:

            return object.__getattribute__(self, name)

    def __len__(self):
        """
        Use for numnber of record
        """

        self._ensure()

        if self._record is not None:
            return len(self._record)

        if self._models is not None:
            return len(self._models)

        raise ModelError(self, "no records")

    def __iter__(self):
        """
        Use the order of record
        """

        self._ensure()

        if self._record is not None:
            return iter(self._record)

        if self._models is not None:
            return iter(self._models)

        raise ModelError(self, "no records")

    def __contains__(self, key):
        """
        Checks numerically or by name
        """

        self._ensure()

        if self._record is not None:
            return key in self._record

        if self._models is not None:
            return key in self._fields

        raise ModelError(self, "no records")

    def __setitem__(self, key, value):
        """
        Access numerically or by name
        """

        self._ensure()

        if self._record is not None:

            self._record[key] = value

        elif self._models is not None:

            if isinstance(key, int):
                raise ModelError(self, "no override")
            else:
                for model in self._models:
                    model[key] = value

        else:
            raise ModelError(self, "no records")

        self._propagate(key, value)

    def __getitem__(self, key):
        """
        Access numerically or by name
        """

        self._ensure()

        relation = self._relate(key)

        if relation is not None:
            return relation

        if self._record is not None:
            return self._record[key]

        if self._models is not None:

            if isinstance(key, int):
                return self._models[key]

            return [model[key] for model in self._models]

        raise ModelError(self, "no records")

    @classmethod
    def _parent(cls, relation):
        """
        Adds a parent to the class
        """

        cls.PARENTS = cls.PARENTS or {}
        cls.PARENTS[relation.child_parent] = relation

    @classmethod
    def _child(cls, relation):
        """
        Adds a child to the class
        """

        cls.CHILDREN = cls.CHILDREN or {}
        cls.CHILDREN[relation.parent_child] = relation

    @classmethod
    def _sister(cls, relation):
        """
        Adds a sister to the class
        """

        cls.SISTERS = cls.SISTERS or {}
        cls.SISTERS[relation.brother_sister] = relation

    @classmethod
    def _brother(cls, relation):
        """
        Adds a brother to the class
        """

        cls.BROTHERS = cls.BROTHERS or {}
        cls.BROTHERS[relation.sister_brother] = relation

    def _relate(self, name):
        """
        Looks up a relation by attribute name
        """

        if name in (self.PARENTS or {}):

            relation = self.PARENTS[name]

            if self._parents.get(name) is None:

                # If we have a single record

                if self._record is not None:

                    # If there's a value on the child field

                    if self[relation.child_field] is None:
                        raise ModelError(self, f"can't access {name} if {relation.child_field} not set")
                    else:
                        self._parents[name] = relation.Parent.get(**{relation.parent_field: self[relation.child_field]})

                # If we have multiple

                elif self._models is not None:

                    # Find all the satisfying parents

                    self._parents[name] = relation.Parent.list(
                        **{f"{relation.parent_field}__in": [value for value in self[relation.child_field] if value is not None]}
                    )

                elif self._criteria is not None:

                    self._parents[name] = relation.Parent.list()

            return self._parents[name]

        elif name in (self.CHILDREN or {}):

            relation = self.CHILDREN[name]

            if self._children.get(name) is None:

                # If we have a single record

                if self._record is not None:

                    _related = {relation.child_field: self._record[relation.parent_field]}

                    if self._record.action() == "create":

                        if isinstance(relation, OneToOne):
                            self._children[name] = relation.Child([], _single=True, _related=_related)
                        elif isinstance(relation, OneToMany):
                            self._children[name] = relation.Child([], _related=_related)

                    else:

                        if isinstance(relation, OneToOne):
                            self._children[name] = relation.Child.list(_single=True, _related=_related)
                        elif isinstance(relation, OneToMany):
                            self._children[name] = relation.Child.list(_related=_related)

                # If we have multiple

                elif self._models is not None:

                    values = [value for value in self[relation.parent_field] if value is not None]

                    if values:
                        self._children[name] = relation.Child.list(**{f"{relation.child_field}__in": values})
                    else:
                        self._children[name] = relation.Child([])

                elif self._criteria is not None:

                    self._children[name] = relation.Child.list()

            return self._children[name]

        return None

    def _collate(self):
        """
        Executes relatives criteria and adds to our own
        """

        if self._criteria is None:
            return

        for child_parent, relation in (self.PARENTS or {}).items():
            if self._parents.get(child_parent) is not None:
                self._criteria.filter(f"{relation.child_field}__in", self._parents[child_parent][relation.parent_field])

        for parent_child, relation in (self.CHILDREN or {}).items():
            if self._children.get(parent_child) is not None:
                self._criteria.filter(f"{relation.parent_field}__in", self._children[parent_child][relation.child_field])

    def _propagate(self, field, value):
        """
        Remove a relation when its field is set
        """

        field_name = Relation.field_name(field, self)

        for child_parent, relation in (self.PARENTS or {}).items():
            if field_name == relation.child_field:
                self._parents[child_parent] = None

        for parent_child, relation in (self.CHILDREN or {}).items():
            if field_name == relation.parent_field:
                if self._record is not None and len(self._children.get(parent_child, [])):
                    self._children[parent_child]._related[relation.child_field] = value
                    for child in (self._children[parent_child]._models or []):
                        child._related[relation.child_field] = value
                        child[relation.child_field] = value
                else:
                    self._children[parent_child] = None

    @staticmethod
    def _extract(kwargs, name, default=None):
        """
        Grabs and remove a value from kwargs so we can chain properly
        """

        if name in kwargs:
            value = kwargs[name]
            del kwargs[name]
            return value

        return default

    def _input(self, record, *args, **kwargs):
        """
        Fills in field values from args, kwargs
        """

        field = 0

        for value in args:
            while record._order[field].readonly or record._order[field].name in self._related:
                field += 1
            record[field] = value
            field += 1

        for name, value in kwargs.items():
            record[name] = value

    def _build(self, _action, *args, **kwargs):
        """
        Fills in record
        """

        _defaults = self._extract(kwargs, '_defaults', True)
        _read = self._extract(kwargs, '_read')

        record = copy.deepcopy(self._fields)
        record.action(_action)

        if _defaults:
            for field in record._order:
                field.value = field.default

        if _read is not None:
            record.read(_read)

        for field, value in self._related.items():
            record[field] = value

        self._input(record, *args, **kwargs)

        return record

    def _ensure(self):
        """
        Makes sure there's records if there's criteria
        """

        if self._criteria is not None:

            if self._record:
                self.update(True)
            else:
                self.retrieve()

    def each(self, action=None):
        """
        Converts to all records, whether _record or _models
        """

        if self._record and (action is None or self._record.action() == action):
            return [self]

        if self._models:
            return [model for model in self._models if action is None or model._record.action() == action]

        return []

    def filter(self, *args, **kwargs):
        """
        Sets to return multiple records
        """

        for field, value in self._related.items():
            self._criteria.filter(field, value)

        for index, value in enumerate(args):
            self._criteria.filter(index, value)

        for name, value in kwargs.items():

            pieces = name.split('__', 1)

            relation = self._relate(pieces[0])

            if relation is not None:
                relation.filter(**{pieces[1]: value})
            else:
                self._criteria.filter(name, value)

        return self

    @classmethod
    def list(cls, *args, **kwargs):
        """
        Sets to return multiple records
        """

        return cls(_action="list", *args, **kwargs)

    @classmethod
    def get(cls, *args, **kwargs):
        """
        For retrieving a single record, assumes it's there which can be overridden
        """

        return cls(_action="get", *args, **kwargs)

    def set(self, *args, **kwargs):
        """
        Sets a single or multiple records or prepares to
        """

        # If we have criteria, build values to set later

        if self._criteria:
            self._record = self._record or self._build("update", _defaults=False)

        for model in self.each():
            self._input(model._record, *args, **kwargs)

        return self

    def add(self, *args, **kwargs):
        """
        Adds records
        """

        self._ensure()

        _count = self._extract(kwargs, '_count', 1)

        if self._record or (self._single and (_count != 1 or self._models)):
            raise ModelError(self, "only one allowed")

        for record in range(_count):
            self._models.append(self.__class__(_action="create", _related=self._related, *args, **kwargs))

        return self

    def define(self, *args, **kwargs):
        """
        define the model
        """
        return relations.source(self.SOURCE).model_define(self, *args, **kwargs)

    def create(self, *args, **kwargs):
        """
        create the model
        """
        return relations.source(self.SOURCE).model_create(self, *args, **kwargs)

    def retrieve(self, verify=True, *args, **kwargs):
        """
        retrieve the model
        """
        return relations.source(self.SOURCE).model_retrieve(self, verify, *args, **kwargs)

    def update(self, *args, **kwargs):
        """
        update the model
        """
        return relations.source(self.SOURCE).model_update(self, *args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        delete the model
        """
        return relations.source(self.SOURCE).model_delete(self, *args, **kwargs)

    def execute(self):
        """
        Executes create(s), update(s), deletes(s)
        """

        if self.each("delete"):
            self.delete()

        if self.each("update"):
            self.update()

        if self.each("create"):
            self.create()

        return self


class Relation:
    """
    Base Relation class
    """

    SAME = None

    @staticmethod
    def field_name(field, model):
        """
        Returns the name of the field, whether index or name
        """

        if field not in model._fields:
            raise ModelError(model, f"cannot find field {field} in {model.NAME}")

        if isinstance(field, str):
            return field

        return model._fields._order[field].name

    @classmethod
    def relative_field(cls, model, relative):
        """
        Returns the name of the relative field, based on the relative name
        """

        # Check for the standard convention

        standard = f"{model.NAME}_id"

        if standard in relative._fields:
            return standard

        # Check to see if we're using the relative.ID, model.ID, model.relative_ID convention (diffent name for ID)

        model_id = cls.field_name(model.ID, model)

        simple = f"{model.NAME}_{model_id}"

        if simple in relative._fields:
            return simple

        # Check to see if we're using the relative.relative_id, model.model_id, model.relative_id patten

        if model_id in relative._fields and (cls.SAME or model_id != cls.field_name(relative.ID, relative)):
            return model_id

        raise ModelError(model, f"cannot determine field for {model.NAME} in {relative.NAME}")

class OneTo(Relation):
    """
    Class that specific one to * relationships
    """

    Parent = None       # Model having one record
    parent_field = None # The id field of the parent to connect to the child
    parent_child = None # The name of the attribute on the parent model to reference children
    Child = None        # Model having many reocrds
    child_field = None  # The if field in the child to connect to the parent field
    child_parent = None # The name of the attribute on the child to reference the parent

    def __init__(self, Parent, Child, parent_child=None, child_parent=None, parent_field=None, child_field=None):

        self.Parent = Parent
        self.Child = Child

        parent = self.Parent()
        child = self.Child()

        self.parent_child = parent_child if parent_child is not None else child.NAME
        self.child_parent = child_parent if child_parent is not None else parent.NAME
        self.parent_field = self.field_name(parent_field if parent_field is not None else parent.ID, parent)
        self.child_field = self.field_name(child_field, child) if child_field is not None else self.relative_field(parent, child)

        self.Parent._child(self)
        self.Child._parent(self)

class OneToMany(OneTo):
    """
    Class that specific one to many relationships
    """

    SAME = False

class OneToOne(OneTo):
    """
    Class that specific one to one relationships
    """

    SAME = True
