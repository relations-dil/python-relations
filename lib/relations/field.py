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

class Field:
    """
    Base field class
    """

    kind = None       # Data class to cast values as or validate

    name = None       # Name used in models
    store = None      # Name to use when reading and writing

    default = None    # Default value
    none = None       # Whether to allow None (nulls)
    _none = None      # Original setting before override
    options = None    # Possible values (if not None)
    validation = None # How to validate values (if not None)
    readonly = None   # Whether this field is readonly
    length = None     # Length of the value

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
        'ge': False,
        'lt': False,
        'le': False
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
        'many',
        'one',
        'prepare',
        'read',
        'retrieve',
        'satisfy',
        'set',
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

        if operator not in self.OPERATORS:
            raise FieldError(self, f"unknown operator '{operator}'")

        if self.criteria is None:
            self.criteria = {}

        if self.OPERATORS[operator]:

            self.criteria.setdefault(operator, [])

            if not isinstance(value, list):
                value = [value]

            self.criteria[operator].extend([self.valid(item) for item in value])

        else:

            self.criteria[operator] = self.valid(value)

    def satisfy(self, values):
        """
        Check if this value satisfies our criteria
        """

        value = self.valid(values.get(self.store))

        for operator, satisfy in (self.criteria or {}).items():
            if (
                (operator == "in" and value not in satisfy) or # pylint: disable=too-many-boolean-expressions
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

        self.value = self.valid(values.get(self.store))
        self.changed = False

    def write(self, values, update=False):
        """
        Writes values to dict (if not readonly)
        """

        if not self.readonly:
            if update and self.replace and not self.changed:
                self.value = self.default() if callable(self.default) else self.default
            values[self.store] = self.value
            self.changed = False
