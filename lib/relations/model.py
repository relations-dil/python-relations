"""
Base Model module
"""

import sys
import copy

class Field:
    """
    Base field class
    """

    name = None       # Name used in models
    kind = None       # Data class to cast values as or validate
    strict = True     # Whether or not to cast on set
    store = None      # Name to use when reading and writing
    value = None      # Value of the field
    search = None     # Values for searching
    default = None    # Default value
    changed = False   # Whether the values be set since read
    readonly = False  # Whether this field is readonly
    definition = None # Definition for storage creation

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
        'match',
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
                raise ValueError(f"field name '{value}' {error} - use the store attribute for this name")

            if self.store is None:
                self.store = value

        if name == "value":
            self.changed = True
            value = self.set(value)

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

        if value is None or not self.strict:

            return value

        elif isinstance(self.kind, list):

            for option in self.kind:
                if option == value:
                    return option

            raise ValueError(f"{value} not in {self.kind} for {self.name}")

        elif isinstance(self.kind, dict):

            for option, label in self.kind.items():
                if label == value:
                    return option

            raise ValueError(f"{value} not in {list(self.kind.values())} for {self.name}")

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

            raise ValueError(f"{value} not in {self.kind} for {self.name}")

        if isinstance(self.kind, dict):

            for option, label in self.kind.items():
                if option == value:
                    return label

            raise ValueError(f"{value} not in {list(self.kind.keys())} for {self.name}")

        return value

    def define(self):
        """
        Place holder for generating defintions
        """

        if self.definition:
            return self.definition

        raise NotImplementedError(f"need to implement 'define' on {self.__class__}")

    def cast(self, value):
        """
        Get the proper value as it's supposed to be
        """

    def filter(self, match, operator="eq"):
        """
        Set a criterion for searching
        """

        if operator not in self.OPERATORS:
            raise ValueError(f"unknown operator '{operator}'")

        if self.search is None:
            self.search = {}

        if self.OPERATORS[operator]:

            self.search.setdefault(operator, [])

            if not isinstance(match, list):
                match = [match]

            self.search[operator].extend([self.set(item) for item in match])

        else:

            self.search[operator] = self.set(match)

    def match(self, values):
        """
        Check if this value matches our search
        """

        value = self.set(values.get(self.store))

        for operator, match in (self.search or {}).items():
            if (
                (operator == "in" and value not in match) or
                (operator in "ne" and value in match) or
                (operator == "eq" and value != match) or
                (operator == "gt" and value <= match) or
                (operator == "ge" and value < match) or
                (operator == "lt" and value >= match) or
                (operator == "le" and value > match)
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


class Record:
    """
    Stores record for a Model
    """

    _order = None  # Access in order
    _names = None  # Access by name
    _action = None # What to do with this record

    ACTIONS = [
        'ignore',
        'create',
        'list',
        'get',
        'update',
        'delete'
    ]

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

        raise AttributeError()

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

        raise ValueError(f"unknown field '{key}'")

    def __getitem__(self, key):
        """
        Access numerically or by name
        """

        if isinstance(key, int):
            if key < len(self._order):
                return self._order[key].value

        if key in self._names:
            return self._names[key].value

        raise ValueError(f"unknown field '{key}'")

    def action(self, _action=None):

        if _action is None:
            return self._action

        if _action not in self.ACTIONS:
            raise ValueError(f"unknown action '{_action}'")

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

        raise ValueError(f"unknown criterion '{criterion}'")

    def match(self, values):
        """
        Sees if a record matches search in a dict
        """

        for field in self._order:
            if not field.match(values):
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


class Model:

    SOURCE = None    # Data source

    ID = 0           # Ref of id field (assumes first field)
    NAME = None      # Name of the model
    FIELD = Field    # Default field class
    RECORD = Record  # Default record clas

    PARENTS = {}     # Parent relationships
    CHILDREN = {}    # Child relationships
    SISTERS = {}     # Sister relationships
    BROTHERS = {}    # Brother relationships

    _fields = None   # Base record to create other records with
    _record = None   # The current loaded single record (from get/create)
    _models = None   # The current loaded multiple models (from list/create)
    _search = None   # The current record to search with

    def __init__(self, *args, **kwargs):
        """
        Creation is implied but we want to set stuff and call create impliicitly
        """

        # Set name if not set

        if self.NAME is None:
            self.NAME = self.__class__.__name__.lower()

        # Create a fields list of actual field in the right format

        self._fields = self.RECORD()

        for name, attribute in self.__class__.__dict__.items():

            if name.startswith('_') or name != name.lower():
                continue # pragma: no cover

            if attribute in [int, float, str, dict , list]:
                field = self.FIELD(attribute, name=name)
            elif isinstance(attribute, self.FIELD):
                field = attribute
                field.name = name
            else:
                continue # pragma: no cover

            self._fields.append(field)

        _action = self._extract(kwargs, '_action', "create")

        if _action == "create":

            if not args or not isinstance(args[0], list):

                self._record = self._build("create", *args, **kwargs)

            # If we're creating multiple records

            else:

                self._models = []

                for single in args[0]:

                    args = single if isinstance(single, list) else []
                    kwargs = single if isinstance(single, dict) else {}

                    model = copy.copy(self)
                    model._record = model._build("create", *args, **kwargs)

                    self._models.append(model)

        elif _action in ["get", "list"]:

            self._search = self._build(_action, _defaults=False)
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
                raise ValueError("no records")

        else:

            object.__setattr__(self, name, value)

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

            raise ValueError("no records")

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

        raise ValueError("no records")

    def __iter__(self):
        """
        Use the order of record
        """

        self._ensure()

        if self._record is not None:
            return iter(self._record)

        if self._models is not None:
            return iter(self._models)

        raise ValueError("no records")

    def __contains__(self, key):
        """
        Checks numerically or by name
        """

        self._ensure()

        if self._record is not None:
            return key in self._record

        if self._models is not None:
            return key in self._fields

        raise ValueError("no records")

    def __setitem__(self, key, value):
        """
        Access numerically or by name
        """

        self._ensure()

        if self._record is not None:

            self._record[key] = value

        elif self._models is not None:

            if isinstance(key, int):
                raise ValueError("no override")
            else:
                for model in self._models:
                    model[key] = value

        else:
            raise ValueError("no records")

    def __getitem__(self, key):
        """
        Access numerically or by name
        """

        self._ensure()

        if self._record is not None:
            return self._record[key]

        if self._models is not None:

            if isinstance(key, int):
                return self._models[key]

            return [model[key] for model in self._models]

        raise ValueError("no records")

    @classmethod
    def _parent(cls, parent):
        """
        Adds a parent to the class
        """

        cls.PARENTS[parent.child_parent] = parent

    @classmethod
    def _child(cls, child):
        """
        Adds a child to the class
        """

        cls.CHILDREN[child.parent_child] = child

    @classmethod
    def _sister(cls, sister):
        """
        Adds a sister to the class
        """

        cls.SISTERS[sister.brother_sister] = sister

    @classmethod
    def _brother(cls, brother):
        """
        Adds a brother to the class
        """

        cls.BROTHERS[brother.sister_brother] = brother

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

    @staticmethod
    def _input(record, *args, **kwargs):
        """
        Fills in field values from args, kwargs
        """

        field = 0

        for value in args:
            while record._order[field].readonly:
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

        self._input(record, *args, **kwargs)

        return record

    def _ensure(self):
        """
        Makes sure there's records if there's search
        """

        if self._search:

            if self._record:
                self.update(True)
            else:
                self.retrieve()

    def _records(self, action=None):
        """
        Converts to all records, whether _record or _models
        """

        if self._record and (action is None or self._record.action() == action):
            return [self._record]

        if self._models:
            return [model._record for model in self._models if action is None or model._record.action() == action]

        return []

    def filter(self, *args, **kwargs):
        """
        Sets to return multiple records
        """

        for index, value in enumerate(args):
            self._search.filter(index, value)

        for name, value in kwargs.items():
            self._search.filter(name, value)

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

        # If we have search, build values to set later

        if self._search:
            self._record = self._record or self._build("update", _defaults=False)

        for record in self._records():
            self._input(record, *args, **kwargs)

        return self

    def add(self, *args, **kwargs):
        """
        Adds records
        """

        if self._record:
            self._models = [copy.copy(self)]
            self._record = None

        _count = self._extract(kwargs, '_count', 1)

        for record in range(_count):
            model = copy.copy(self)
            model._record = self._build("create", *args, **kwargs)
            self._models.append(model)

        return self

    def define(self):
        """
        Executes the create(s)
        """
        raise NotImplementedError(f"need to implement 'define' on {self.__class__}")

    def create(self, verify=False):
        """
        Executes the create(s), reloading verifying
        """
        raise NotImplementedError(f"need to implement 'create' on {self.__class__}")

    def retrieve(self, verify=True):
        """
        Executes the retrieve, raising an exception if "get" and not gotten
        """
        raise NotImplementedError(f"need to implement 'retrieve' on {self.__class__}")

    def update(self, verify=False):
        """
        Executes the update(s), reloading verifying
        """
        raise NotImplementedError(f"need to implement 'update' on {self.__class__}")

    def delete(self):
        """
        Executes the delete(s)
        """
        raise NotImplementedError(f"need to implement 'delete' on {self.__class__}")

    def execute(self, verify=False):
        """
        Executes create(s), update(s), deletes(s)
        """

        self.create(verify)
        self.update(verify)
        self.delete()


class Relation:
    """
    Base Relation class
    """

    @staticmethod
    def field_name(field, model):
        """
        Returns the name of the field, whether index or name
        """

        if field not in model._fields:
            raise ValueError(f"cannot find field {field} in {model.NAME}")

        if isinstance(field, str):
            return field

        return model._fields._order[field].name

    @classmethod
    def relative_field(cls, model, relative, same=False):
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

        if model_id in relative._fields and (same or model_id != cls.field_name(relative.ID, relative)):
            return model_id

        raise ValueError(f"cannot determine field for {model.NAME} in {relative.NAME}")

class OneToMany(Relation):
    """
    Class that specific one to many relationships
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

class OneToOne(Relation):
    """
    Class that specific one to one relationships, with the sister being the primary (if there is one)
    """

    Sister = None         # Model having one record
    sister_field = None   # The id field of the sister to connect to the brother
    sister_brother = None # The name of the attribute on the sister model to reference brotherren
    Brother = None        # Model having many reocrds
    brother_field = None  # The if field in the brother to connect to the sister
    brother_sister = None # The name of the attribute on the brother to reference the sister

    def __init__(self, Sister, Brother, sister_brother=None, brother_sister=None, sister_field=None, brother_field=None):

        self.Sister = Sister
        self.Brother = Brother

        sister = self.Sister()
        brother = self.Brother()

        self.sister_brother = sister_brother if sister_brother is not None else brother.NAME
        self.brother_sister = brother_sister if brother_sister is not None else sister.NAME
        self.sister_field = self.field_name(sister_field if sister_field is not None else sister.ID, sister)
        self.brother_field = self.field_name(brother_field, brother) if brother_field is not None else self.relative_field(sister, brother, same=True)

        self.Sister._brother(self)
        self.Brother._sister(self)
