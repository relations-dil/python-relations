"""
Base Model module
"""

class Field:
    """
    Base field class
    """

    cls = None        # Data class to cast values as
    name = None       # Name used in models
    cast = True       # Whether or not to cast on set
    store = None      # Name to use when reading and writing
    value = None      # Value of the field
    default = None    # Default value
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
            raise Exception(f"Field name '{name}' {error} - use the store attribute for this name")

        self.name = name
        self.cls = cls

        # Just set what as sent

        for name, attribute in kwargs.items():
            setattr(self, name, attribute)

        # If store wasn't set, set it with name

        if self.store is None:
            self.store = self.name

    def define(self):
        """
        Place holder for generating defintions
        """

        if self.definition:
            return self.definition

        raise NotImplemented("define")

    def filter(self, value, operator="eq"):
        """
        Set a criterion for searching
        """

        if operator not in self.OPERATORS:
            raise Exception(f"Unknown operator {operator}")

        if self.criteria is None:
            self.criteria = {}

        if self.OPERATORS[operator]:

            self.criteria.setdefault(operator, [])

            if not isinstance(value, list):
                value = [value]

            self.criteria[operator].extend([self.cast(item) for item in value])

        else:

            self.criteria[operator] = self.cast(value)

    def match(self, value):
        """
        Check if this value matches our criteria
        """

        for operator, value in (self.criteria or {}).items():
            if (
                (operator == "in" and self.value not in value) or
                (operator in "ne" and self.value in value) or
                (operator == "eq" and self.value != value) or
                (operator == "gt" and self.value <= value) or
                (operator == "ge" and self.value < value) or
                (operator == "lt" and self.value >= value) or
                (operator == "le" and self.value > value)
            ):
                return False

        return True

    def read(self, values):
        """
        Loads the value from storage
        """

        self.value = values.get(self.store)

    def write(self, values):
        """
        Writes values to dict (if not readonly)
        """

        if not self.readonly:
            values[self.store] = value

    def _cast(self, value):
        """
        Get the proper value as it's supposed to be
        """

        if value is None or not self.cast:
            return value
        else:
            return self.cls(value)

    def __setattr__(self, name, value):
        """
        Use to set field values so everything is cost correctly
        """

        if name == "value":
            value = self._cast(value)

        object.__setattr__(self, name, value)

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

    def action(self, *args, **kwargs):

        _action = args[0] if len(args) else kwargs.get("_action")

        if _action is None:
            return self._action

        if _action not in self.ACTIONS:
            raise ValueError(f"unknown action {_action}")

        self._action = _action

    def filter(self, criterion, value):
        """
        Sets criterion on a field
        """

        if "__" in criterion:
            name, operator = criterion.split("__")
            self._names[name].filter(value, operator)
        else:
            self._names[criterion].filter(value)

    def match(self, values):
        """
        Sees if a record matches criteria in a dict
        """

        for field in record:
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

    def __len__(self):
        """
        Use for numnber of record
        """
        return len(self._order)

    def __iter__(self):
        """
        Use the _order of record
        """
        return self._order

    def __contains__(self, key):
        """
        Checks numerically or by name
        """

        if isinstance(key, int) and key < len(self._order):
            return True

        # This is so criterions work

        if key in self._names:
            return True

        return False

    def __getitem__(self, key):
        """
        Access numerically or by name
        """

        if isinstance(key, int):
            if key < len(self._order):
                return self._order[key].value
            else:
                raise IndexError(f"field {key} not found")

        if key in self._names:
            return self._names[key].value

        raise KeyError(f"field {key} not found")

    def __setattr__(self, name, value):
        """
        Use to set field values directly
        """

        if name in self._names:
            self._names[name].value = value
        else:
            object.__setattr__(self, name, value)

    def __getattribute__(self, name):
        """
        Use to get field values directly
        """

        if name in self._names:
            return self._names[name].value
        else:
            return object.__getattribute__(self, name)


class Model:

    SOURCE = None    # Data source

    ID = 0           # Ref of id field (assumes first field)
    NAME = None      # Name of the model
    FIELD = Field    # Default field class
    RECORD = Record  # Default record clas

    _fields = None   # Base record to create other records with
    _values = None   # Values to use for update
    _record = None   # The current loaded single record (from get)
    _records = None  # The current loaded multiple reocrds (from list)
    _criteria = None # The current criteria record to search with

    def __init__(self, _action="create", *args, **kwargs):
        """
        Creation is implied but we want to set stuff and call create impliicitly
        """

        # Set name if not set

        if self.NAME is None:
            self.NAME = self.__class__.__name__

        # Create a fields list of actual field in the right format

        self._fields = self.RECORD()

        for name, attribute in self.__dict__.items():

            if name.startswith('_'):
                continue

            if attribute in [int, float, str, dict , list]:
                field = self.FIELD(name, attribute)
            elif isinstance(attribute, self.FIELD):
                field = attribute
            else:
                continue

            self._fields.append.add(field)

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

                    self._records.append(self, self._build("create", *args, **kwargs))

        else:

            self._criteria = self._build(_action, _defaults=False)
            self.filter(*args, **kwargs)

    def _input(self, _record, *args, **kwargs):
        """
        Fills in field values from args, kwargs
        """

        for index, value in enumerate(args):
            _record[index] = value

        for name, value in kwargs.items():
            _record[name] = value

    def _build(self, _action, _defaults=True, _read=None, *args, **kwargs):
        """
        Fills in record
        """

        record = copy.deepcopy(self._fields)
        record.action(_action)

        if _defaults:
            for field in record:
                field.value = field.default

        if _read is not None:
            record.read(_read)

        self._input(_record=record, *args, **kwargs)

        return record

    def _all(self, action=None):
        """
        Converts to all records, whether _record or _records
        """

        if self._records:
            return [record for record in self._records if action is None or record.action() == action]

        if self._record and (action == None or self._record.action() == action):
            return [self._record]

        return []

    def filter(self, *args, **kwargs):
        """
        Sets to return multiple records
        """

        for index, value in enumerate(args):
            self._criteria[index].filter(value)

        for name, value in kwargs.items():
            if name.split('__')[0] in self._criteria:
                record.filter(name, value)
            else:
                raise KeyError(f"unknown field for {name}")

        return self

    @classmethod
    def list(cls, *args, **kwargs):
        """
        Sets to return multiple records
        """

        return cls("list", *args, **kwargs)

    @classmethod
    def get(cls, *args, **kwargs):
        """
        For retrieving a single record, assumes it's there which can be overridden
        """

        return cls("get", *args, **kwargs)

    def set(self, *args, **kwargs):
        """
        Sets a single or multiple records or prepares to
        """

        # If we have criteria, build values to set later

        if self._criteria:

            self._values = self._values or []
            self._record = self._record or self._build("update", _defaults=False)

            for index, value in enumerate(args):
                field = self._record._order[index]
                self._values.append(field.name)
                field.value = value

            for name, value in kwargs.items():
                if name in self._fields and '__' not in name:
                    self._values.append(name)
                    self._record[name]= value

        else:

            for record in self._all():
                self._input(_record=record, *args, **kwargs)

        return self

    def add(self, count=0):
        """
        Adds records
        """

        if self._record:
            self._records = [self._record]
            self._record = None

        # If we have a count

        for record in range(_count):
            self._records.append(self, self._build("create"))

    def define(self):
        """
        Executes the create(s)
        """
        raise NotImplemented("create")

    def create(self):
        """
        Executes the create(s)
        """
        raise NotImplemented("create")

    def retrieve(self, verify=True):
        """
        Executes the retrieve, raising an exception if "get" and not gotten
        """

        # Make sure criteria is None'd

        raise NotImplemented("retrieve")

    def update(self):
        """
        Executes the update(s)
        """
        raise NotImplemented("update")

    def delete(self):
        """
        Executes the delete(s)
        """
        raise NotImplemented("delete")

    def execute(self):
        """
        Executes create(s), update(s), deletes(s)
        """

        self.create().update().delete()

    def __len__(self):
        """
        Use for numnber of record
        """

        self.retrieve()

        if self._records is not None:
            return len(self._records)

        if self._record is not None:
            return len(self._record)

        return 0

    def __iter__(self):
        """
        Use the order of record
        """

        self.retrieve()

        if self._records is not None:
            return self._records

        if self._record is not None:
            return self._record

        return None

    def __contains__(self, key):
        """
        Checks numerically or by name
        """

        self.retrieve()

        if self._records is not None and isinstance(key, int) and key < len(self._records):
            return True

        if self._record is not None and key in self._record:
            return True

        return False

    def __getitem__(self, key):
        """
        Access numerically or by name
        """

        self.retrieve()

        if self._records is not None:

            if isinstance(key, int) and key < len(self._records):
                return self._records[key]

            if key in self._fields:
                return [record[key].value for record in self._records]

        if self._record is not None and key in self._fields:
            return self._record[key].value

        raise KeyError(f"{key} not found")

    def __setattr__(self, name, value):
        """
        Use to set field values directly
        """

        if name in self._fields:

            self.retrieve()

            if self._records is not None:
                for record in self._records:
                    record[name].value = value
            elif self._record is not None:
                self._record[name].value = value
            else:
                raise ValueError("no records")

        else:

            object.__setattr__(self, name, value)

    def __getattribute__(self, name):
        """
        Use to get field values directly
        """

        if name in self._fields:

            self.retrieve()

            if self._records is not None:
                return [record[name].value for record in self._records]
            if self._record is not None:
                return self._record[name].value

            raise ValueError("no records")

        else:

            return object.__getattribute__(self, name)
