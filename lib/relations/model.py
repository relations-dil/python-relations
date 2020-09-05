"""
Base Model module
"""

import copy

class Field:
    """
    Base field class
    """

    cls = None        # Data class to cast values as
    name = None       # Name used in models
    strict = True     # Whether or not to cast on set
    store = None      # Name to use when reading and writing
    value = None      # Value of the field
    default = None    # Default value
    changed = False   # Whether the values be set since read
    readonly = False  # Whether this field is readonly
    criteria = None   # Values for searching
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

    def __init__(self, name, cls, **kwargs):
        """
        Set the name and what to cast it as and everything else be free form
        """

        error = None

        if name in self.RESERVED:
            error = "is reserved"

        if "__" in name:
            error = "cannot contain '__'"

        if name[0] == '_':
            error = "cannot start with '_'"

        if error:
            raise ValueError(f"field name '{name}' {error} - use the store attribute for this name")

        self.name = name
        self.cls = cls

        # Just set what as sent

        for name, attribute in kwargs.items():
            setattr(self, name, attribute)

        # If store wasn't set, set it with name

        if self.store is None:
            self.store = self.name

    def __setattr__(self, name, value):
        """
        Use to set field values so everything is cost correctly
        """

        if name == "value":
            value = self.cast(value)
            self.changed = True

        object.__setattr__(self, name, value)

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

        if value is None or not self.strict:
            return value
        else:
            return self.cls(value)

    def filter(self, match, operator="eq"):
        """
        Set a criterion for searching
        """

        if operator not in self.OPERATORS:
            raise ValueError(f"unknown operator '{operator}'")

        if self.criteria is None:
            self.criteria = {}

        if self.OPERATORS[operator]:

            self.criteria.setdefault(operator, [])

            if not isinstance(match, list):
                match = [match]

            self.criteria[operator].extend([self.cast(item) for item in match])

        else:

            self.criteria[operator] = self.cast(match)

    def match(self, values):
        """
        Check if this value matches our criteria
        """

        value = self.cast(values.get(self.store))

        for operator, match in (self.criteria or {}).items():
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

    _order = None # Access in order
    _names = None # Access by name
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
        Sees if a record matches criteria in a dict
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

    _fields = None   # Base record to create other records with
    _record = None   # The current loaded single record (from get)
    _records = None  # The current loaded multiple reocrds (from list)
    _criteria = None # The current criteria record to search with

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
                field = self.FIELD(name, attribute)
            elif isinstance(attribute, self.FIELD):
                field = attribute
            else:
                continue # pragma: no cover

            self._fields.append(field)

        _action = self._extract(kwargs, '_action', "create")

        # If we're creating

        if _action == "create":

            if not args or not isinstance(args[0], list):

                self._record = self._build("create", *args, **kwargs)

            # If we're creating multiple records

            else:

                self._records = []

                for single in args[0]:

                    args = single if isinstance(single, list) else []
                    kwargs = single if isinstance(single, dict) else {}

                    self._records.append(self._build("create", *args, **kwargs))

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
            elif self._records is not None:
                for record in self._records:
                    record[name] = value
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

            if self._records is not None:
                return [record[name] for record in self._records]

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

        if self._records is not None:
            return len(self._records)

        raise ValueError("no records")

    def __iter__(self):
        """
        Use the order of record
        """

        self._ensure()

        if self._record is not None:
            return iter(self._record)

        if self._records is not None:
            return iter(self._records)

        raise ValueError("no records")

    def __contains__(self, key):
        """
        Checks numerically or by name
        """

        self._ensure()

        if self._record is not None:
            return key in self._record

        if self._records is not None:
            return key in self._fields

        raise ValueError("no records")

    def __getitem__(self, key):
        """
        Access numerically or by name
        """

        self._ensure()

        if self._record is not None:
            return self._record[key]

        if self._records is not None:

            if isinstance(key, int):
                return self._records[key]

            return [record[key] for record in self._records]

        raise ValueError("no records")

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

        for index, value in enumerate(args):
            record[index] = value

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
        Makes sure there's records if there's criteria
        """

        if self._criteria:

            if self._record:
                self.update(True)
            else:
                self.retrieve()

    def _all(self, action=None):
        """
        Converts to all records, whether _record or _records
        """

        if self._record and (action is None or self._record.action() == action):
            return [self._record]

        if self._records:
            return [record for record in self._records if action is None or record.action() == action]

        return []

    def filter(self, *args, **kwargs):
        """
        Sets to return multiple records
        """

        for index, value in enumerate(args):
            self._criteria.filter(index, value)

        for name, value in kwargs.items():
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

        for record in self._all():
            self._input(record, *args, **kwargs)

        return self

    def add(self, *args, **kwargs):
        """
        Adds records
        """

        if self._record:
            self._records = [self._record]
            self._record = None

        _count = self._extract(kwargs, '_count', 1)

        for record in range(_count):
            self._records.append(self._build("create", *args, **kwargs))

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
