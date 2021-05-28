"""
Relations Module for handling fields
"""

# pylint: disable=not-callable

import re

class FieldError(Exception):
    """
    Field Error class that captures the field
    """

    def __init__(self, field, message):

        self.field = field
        self.message = message
        super().__init__(self.message)

class Field: # pylint: disable=too-many-instance-attributes
    """
    Base field class
    """

    kind = None       # Data class to cast values as or validate

    name = None       # Name used in models
    store = None      # Name to use when reading and writing
    attr = None       # Attributes to store in JSON
    init = None       # Attributes to create with JSON
    label = None       # Attributes to label with JSON

    default = None    # Default value
    none = None       # Whether to allow None (nulls)
    _none = None      # Original setting before override
    options = None    # Possible values (if not None)
    validation = None # How to validate values (if not None)
    readonly = None   # Whether this field is readonly
    length = None     # Length of the value
    format = None     # How to format the value instructions

    value = None      # Value of the field
    changed = None    # Whether the values been changed since creation, retrieving
    replace = None    # Whether to replace the value with default on update
    criteria = None   # Values for searching

    # Operators supported and whether allwo multiple values

    ATTRIBUTES = [
        'default',
        'replace'
    ]

    OPERATORS = {
        'in': True,
        'ne': True,
        'eq': False,
        'gt': False,
        'gte': False,
        'lt': False,
        'lte': False,
        'like': False,
        'notlike': False,
        'null': False
    }

    RESERVED = [
        'action',
        'add',
        'append',
        'bulk',
        'create',
        'define',
        'delete',
        'filter',
        'insert',
        'labels',
        'like',
        'limit',
        'many',
        'match',
        'one',
        'overflow',
        'prepare',
        'read',
        'retrieve',
        'satisfy',
        'set',
        'sort',
        'thy',
        'update',
        'write'
    ]

    def __init__(self, kind, *args, **kwargs): # pylint: disable=too-many-branches
        """
        Set the name and what to cast it as and everything else be free form
        """

        self.kind = kind

        # If the last arg is a dict, use it as kwargs

        if args and isinstance(args[-1], dict):
            args = list(args)
            kwargs = args.pop()

        # If there's only one arg, it's bool and the kind isn't,
        # assume is for none, making a field non None

        if len(args) == 1 and isinstance(args[0], bool) and self.kind != bool:
            self.none = args[0]
        # Else just set what as sent
        else:
            for index, attribute in enumerate(args):
                setattr(self, self.ATTRIBUTES[index], attribute)

        for name, attribute in kwargs.items():
            setattr(self, name, attribute)

        # Save the original for creating unique index by default

        self._none = self.none

        # If we're list or dict, we can't be None and our default is
        # our type, so it's always a list or dict

        if self.kind in [list, dict]:
            self.none = False
            if self.default is None:
                self.default = self.kind

        # If none isn't set, and there's no default, options, or validation, then
        # it's fine to be none. Else assume not None

        if self.none is None:
            if self.default is None and self.options is None and self.validation is None:
                self.none = True
            else:
                self.none = False

        if self.default is not None and not callable(self.default):
            if not isinstance(self.default, self.kind):
                raise FieldError(self, f"{self.default} default not {self.kind} for {self.name}")

        if self.options is not None:
            for option in self.options: # pylint: disable=not-an-iterable
                if not isinstance(option, self.kind):
                    raise FieldError(self, f"{option} option not {self.kind} for {self.name}")

        if self.validation is not None and not isinstance(self.validation, str) and not callable(self.validation):
            raise FieldError(self, f"{self.validation} validation not regex or method for {self.name}")

        # If the field isn't a standard type and lacks attr, throw an error

        if self.kind not in [bool, int, float, str, list, dict] and self.attr is None:
            raise FieldError(self, f"{self.kind.__name__} requires at least attr")

        # Get attr into a dict

        if isinstance(self.attr, str):
            self.attr = [self.attr]

        if isinstance(self.attr, list):
            self.attr = {attr: attr for attr in self.attr}

       # if there's attr and no init, assume init is attr

        if self.attr is not None and self.init is None:
            self.init = self.attr

        # Get init into a dict

        if isinstance(self.init, str):
            self.init = [self.init]

        if isinstance(self.init, list):
            self.init = {init: init for init in self.init}

       # if there's attr and no label, assume label is attr

        if self.attr is not None and self.label is None:
            self.label = self.attr

        # Get label into a dict

        if isinstance(self.label, str):
            self.label = [self.label]

        if isinstance(self.label, list):
            self.label = {label: label for label in self.label}

    def __setattr__(self, name, value):
        """
        Use to set field values so everything is cost correctly
        """

        if name == "name":

            error = None

            if value in self.RESERVED:
                error = "is reserved"
            elif "__" in value:
                error = "cannot contain '__'"
            elif value[0] == '_':
                error = "cannot start with '_'"

            if error:
                raise FieldError(self, f"field name '{value}' {error} - use the store attribute for this name")

            if self.store is None:
                self.store = value

        if name == "value":
            value = self.valid(value)
            self.changed = True

        object.__setattr__(self, name, value)

    def valid(self, value):
        """
        Returns the valid value, raising issues if invalid
        """

        # none rules all

        if value is None:
            if not self.none:
                raise FieldError(self, f"None not allowed for {self.name}")
            return value

        if not isinstance(value, self.kind):
            value = self.kind(value)

        if self.options is not None and value not in self.options: # pylint: disable=unsupported-membership-test
            raise FieldError(self, f"{value} not in {self.options} for {self.name}")

        if self.validation is not None:
            if isinstance(self.validation, str):
                if not re.match(self.validation, value):
                    raise FieldError(self, f"{value} doesn't match {self.validation} for {self.name}")
            elif callable(self.validation):
                if not self.validation(value): # pylint: disable=not-callable
                    raise FieldError(self, f"{value} invalid for {self.name}")

        return value

    def filter(self, value, operator="eq"):
        """
        Set a criterion in criteria
        """

        path = operator

        if operator not in self.OPERATORS:

            if self.kind in [bool, int, float, str]:
                raise FieldError(self, f"unknown operator '{operator}'")

            operator = operator.split("__")[-1]

            if operator not in self.OPERATORS:
                operator = "eq"
                path = f"{path}__eq"

        if self.criteria is None:
            self.criteria = {}

        if self.OPERATORS[operator]:

            self.criteria.setdefault(path, [])

            if not isinstance(value, list):
                value = [value]

            if path != operator:
                self.criteria[path].extend(value)
            else:
                self.criteria[path].extend([self.valid(item) for item in value])

        else:

            if operator == "null":
                self.criteria[path] = not (value == "false" or value == "no" or value == "0" or value == 0 or not value)
            elif path != operator:
                self.criteria[path] = value
            else:
                self.criteria[path] = self.valid(value)

    def satisfy(self, values): # pylint: disable=too-many-return-statements,too-many-branches)
        """
        Check if this value satisfies our criteria
        """

        for operator, satisfy in (self.criteria or {}).items():

            value = values.get(self.store)

            if self.kind in [bool, int, float, str, list, dict]:
                value = self.valid(value)
            elif not value:
                value = value or {}

            if operator not in self.OPERATORS:

                path = operator.split("__")
                operator = path.pop()

                for index, place in enumerate(path):

                    if index == len(path) - 1:
                        default = None
                    elif re.match(r'^\d+$', path[index+1]):
                        default = []
                    else:
                        default = {}

                    if re.match(r'^\d+$', place):

                        place = int(place)

                        if place < len(value):
                            value = value[place]
                        else:
                            value = default

                    else:

                        if place[0] == '_':
                            place = place[1:]

                        value = value.get(place, default)

            if operator == "null":
                if satisfy != (value is None):
                    return False
                continue

            if value is None:
                return False

            if operator == "in" and value not in satisfy:
                return False

            if operator in "ne" and value in satisfy:
                return False

            if operator == "eq" and value != satisfy:
                return False

            if operator == "gt" and value <= satisfy:
                return False

            if operator == "gte" and value < satisfy:
                return False

            if operator == "lt" and value >= satisfy:
                return False

            if operator == "lte" and value > satisfy:
                return False

            if operator == "like" and str(satisfy).lower() not in str(value).lower():
                return False

            if operator == "notlike" and str(satisfy).lower() in str(value).lower():
                return False

        return True

    def match(self, values, like, parents):
        """
        Check if this value matchees a model's like or parents match
        """

        value = values.get(self.store)

        if self.label is not None:
            if not value:
                return False
            if callable(self.label):
                return self.label(value, like)
            for store in self.label.values():
                if str(like).lower() in str(value[store]).lower():
                    return True
            return False

        value = self.valid(value)

        if self.store in parents:
            return value in parents[self.store]

        return str(like).lower() in str(value).lower()

    def read(self, values):
        """
        Loads the value from storage
        """

        value = values.get(self.store)

        if self.init is not None:
            if not value:
                return
            if callable(self.init):
                self.value = self.init(value)
            else:
                self.value = self.valid(self.kind(**{init: value[store] for init, store in self.init.items()}))
        else:
            self.value = self.valid(value)

        self.changed = False

    def write(self, values, update=False):
        """
        Writes values to dict (if not readonly)
        """

        if not self.readonly:

            if self.attr is not None:
                if not self.value:
                    return
                values[self.store] = {}
                if callable(self.attr):
                    values[self.store] = self.attr(self.value)
                else:
                    for attr, store in self.attr.items():
                        attr = getattr(self.value, attr)
                        values[self.store][store] = attr() if callable(attr) else attr
            else:
                if update and self.replace and not self.changed:
                    self.value = self.default() if callable(self.default) else self.default
                values[self.store] = self.value

            self.changed = False
