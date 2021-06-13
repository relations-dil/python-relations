"""
Relations Module for handling fields
"""

# pylint: disable=not-callable

import re
import relations

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
    label = None      # Attributes to label with JSON

    extract = None    # Field to extract
    inject = None     # Field to inject

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
        'export',
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

       # if there's attr and no label, assume label is attr

        if self.attr is not None and self.label is None:
            self.label = self.attr

       # if there's attr and no init, assume init is attr

        if self.attr is not None and self.init is None:
            self.init = self.attr

        # Get attr into a dict

        if isinstance(self.attr, str):
            self.attr = [self.attr]

        if isinstance(self.attr, list):
            self.attr = {attr: attr for attr in self.attr}

        # Get init into a dict

        if isinstance(self.init, str):
            self.init = [self.init]

        if isinstance(self.init, list):
            self.init = {init: init for init in self.init}

        # Get label into a list

        if isinstance(self.label, str):
            self.label = [self.label]

        if self.format is None and self.label is not None:
            self.format = [None for _ in self.label]

        if self.format is not None and not isinstance(self.format, list):
            self.format = [self.format]

        # If extract is set, field is readonly

        if self.extract is not None:
            self.readonly = True

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
            if self.init is not None and callable(self.init):
                value = self.init(value)
            elif self.init is not None and isinstance(value, dict):
                value = self.kind(**{init: value[store] for init, store in self.init.items()})
            else:
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

    @staticmethod
    def find(values, path, write=False): # pylint: disable=too-many-branches
        """
        Traverse a values to get to the last structure
        """

        if isinstance(path, str):
            path = path.split('__')

        for index, place in enumerate(path):

            if relations.INDEX.match(place):
                if values is None:
                    values = []
                place = int(place)
            else:
                if values is None:
                    values = {}
                if place[0] == '_':
                    place = place[1:]

            if index < len(path) - 1:

                default = [] if relations.INDEX.match(path[index+1]) else {}

                if write:

                    if isinstance(values, dict):
                        values.setdefault(place, default)
                    else:
                        while (place if place > -1 else abs(place + 1)) > len(values) - 1:
                            values.append(None)
                        if values[place] is None:
                            values[place] = default

                    values = values[place]

                else:

                    if isinstance(values, dict):
                        values = values.get(place, default)
                    elif (place if place > -1 else abs(place + 1)) > len(values) - 1 or values[place] is None:
                        values = default
                    else:
                        values = values[place]

        return values, place

    @classmethod
    def get(cls, values, path):
        """
        Retrieve value at path filling in what's expected
        """

        if not path:
            return values

        values, place = cls.find(values, path)

        if isinstance(values, list):
            if place > len(values) - 1:
                return None
            return values[place]

        return values.get(place)

    @classmethod
    def set(cls, values, path, value):
        """
        Retrieve value at path filling in what's expected
        """

        values, place = cls.find(values, path, write=True)

        values[place] = value

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

                value = self.get(value, path)

            if operator == "null":
                if satisfy != (value is None):
                    return False
                continue # pragma: no cover

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
            for store in self.label:
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

        if self.inject:
            self.value = self.get(values, self.inject.split('__')[1:])
        else:
            self.value = self.valid(values.get(self.store))
        self.changed = False

    def export(self):
        """
        Create a dictionary of object attributes
        """

        if self.value is None or self.attr is None:
            return self.value

        values = {}

        if callable(self.attr):

            self.attr(values, self.value)

        else:

            for attr, store in self.attr.items():
                attr = getattr(self.value, attr)
                self.set(values, store, attr() if callable(attr) else attr)

        return values

    def write(self, values, update=False):
        """
        Writes values to dict (if not readonly)
        """

        if not self.readonly:
            if update and self.replace and not self.changed:
                self.value = self.default() if callable(self.default) else self.default
            value = self.export()
            if self.inject:
                self.set(values, self.inject.split('__')[1:], value)
            else:
                values[self.store] = value

            self.changed = False

    def labels(self, path=None):
        """
        Get label at path
        """

        if self.kind in [bool, int, float, str]:
            return [self.value]

        if path is None:
            path = []

        if self.kind in [list, dict]:
            return [self.get(self.value, path)]

        values = self.export()

        if path:
            return [self.get(values, path)]

        return [self.get(values, label) for label in self.label]
