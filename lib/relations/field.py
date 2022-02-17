"""
Relations Module for handling fields
"""

# pylint: disable=not-callable,unsupported-membership-test,not-an-iterable,misplaced-comparison-constant

import re
import copy
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
    titles = None      # Attributes to titles with JSON

    extract = None    # Fields to extract
    inject = None     # Field to inject

    default = None    # Default value
    none = None       # Whether to allow None (nulls)
    _none = None      # Original setting before override
    options = None    # Possible values (if not None)
    validation = None # How to validate values (if not None)
    length = None     # Length of the value
    format = None     # How to format the value instructions
    readonly = None   # Whether or not a field is readnoly
    auto = None       # Whether a field can be auto generated
    refresh = None    # Whether a field is to be refreshed if not touched

    value = None      # Value of the field
    original = None   # Original value (as export)
    criteria = None   # Values for searching
    changed = None    # Whether an field has changed for update only

    # Operators supported and whether allwo multiple values

    ATTRIBUTES = [
        'default',
        'replace'
    ]

    UNDEFINE = [
        "kind",
        "attr",
        "init",
        "titles",
        "value",
        "original",
        "changed",
        "criteria"
    ]

    OPERATORS = {
        'null': False,
        'eq': False,
        'gt': False,
        'gte': False,
        'lt': False,
        'lte': False,
        'like': False,
        'start': False,
        'end': False,
        'in': True,
        'has': True,
        'any': True,
        'all': True
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
        'titless',
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

    def __init__(self, kind, *args, **kwargs): # pylint: disable=too-many-branches,too-many-statements
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

        # If we're set, list, or dict, we can't be None and our default is
        # our type, so it's always a list or dict

        if self.kind in [set, list, dict]:
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

        if self.options is not None and self.kind != set:
            for option in self.options: # pylint: disable=not-an-iterable
                if not isinstance(option, self.kind):
                    raise FieldError(self, f"{option} option not {self.kind} for {self.name}")

        if self.validation is not None and not isinstance(self.validation, str) and not callable(self.validation):
            raise FieldError(self, f"{self.validation} validation not regex or method for {self.name}")

        # If the field isn't a standard type and lacks attr, throw an error

        if self.kind not in [bool, int, float, str, set, list, dict] and self.attr is None:
            raise FieldError(self, f"{self.kind.__name__} requires at least attr")

       # if there's attr and no titles, assume titles is attr

        if self.attr is not None and self.titles is None:
            self.titles = self.attr

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

        # Get titles into a list

        if isinstance(self.titles, str):
            self.titles = [self.titles]

        if self.format is None and self.titles is not None:
            self.format = [None for _ in self.titles]

        if self.format is not None and not isinstance(self.format, list):
            self.format = [self.format]

        # If extract is str, turn into list

        if isinstance(self.extract, str):
            self.extract = [self.extract]

        # If extract is list, turn into a dict, assuming str

        if isinstance(self.extract, list):
            self.extract = {extract: str for extract in self.extract}

    def __setattr__(self, name, value):
        """
        Use to set field values so everything is cast correctly
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

    def define(self):
        """
        Return data definitions structure
        """

        definition = {
            "kind": self.kind.__name__
        }

        for attr in self.__dict__:
            if attr == "extract":
                definition[attr] = {store: kind.__name__ for store, kind in self.__dict__[attr].items()}
            elif (
                attr[0] != '_' and attr == attr.lower() and attr not in self.UNDEFINE and
                getattr(self, attr) is not None and not callable(getattr(self, attr))
            ):
                definition[attr] = getattr(self, attr)

        return definition

    def valid(self, value): # pylint: disable=too-many-branches
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
                value = self.kind(**{init: self.get(value, store) for init, store in self.init.items()})
            else:
                value = self.kind(value)

        if self.options is not None:
            if self.kind == set:
                for each in value:
                    if each not in self.options:
                        raise FieldError(self, f"{each} not in {self.options} for {self.name}")
            elif value not in self.options:
                raise FieldError(self, f"{value} not in {self.options} for {self.name}")

        if self.validation is not None:
            if isinstance(self.validation, str):
                if not re.match(self.validation, value):
                    raise FieldError(self, f"{value} doesn't match {self.validation} for {self.name}")
            elif callable(self.validation):
                if not self.validation(value): # pylint: disable=not-callable
                    raise FieldError(self, f"{value} invalid for {self.name}")

        return value

    @staticmethod
    def split(field): # pylint: disable=too-many-branches
        """
        Splits field value into name and path
        """

        count = 0
        place = []
        places = []

        state = "place"

        for letter in field:

            if state == "place":

                place.append(letter)

                if letter != '_':
                    state = "placing"

            elif state == "placing":

                if letter == '_':
                    count += 1
                else:
                    count = 0

                if count == 2 and letter == '_':
                    places.append(''.join(place[:-1]))
                    place = []
                    count = 0
                    state = "place"
                else:
                    place.append(letter)

        if place:
            places.append(''.join(place))

        path = []

        for place in places:
            if '0' <= place[0] and place[0] <= '9':
                path.append(int(place))
            elif place[:1] == '_' and '0' <= place[1] and place[1] <= '9':
                path.append(-int(place[1:]))
            elif place[:2] == '__' and '0' <= place[2] and place[2] <= '9':
                path.append(place[2:])
            elif place[:3] == '___' and '0' <= place[3] and place[3] <= '9':
                path.append(str(-int(place[3:])))
            else:
                path.append(place)

        return path

    def filter(self, value, criterion="eq"): # pylint: disable=too-many-branches
        """
        Set a criterion in criteria
        """

        path = self.split(criterion)

        if not isinstance(path[-1], str) or path[-1].split("not_", 1)[-1] not in self.OPERATORS:
            operator = "eq"
            criterion = f"{criterion}__eq"
        else:
            operator = path.pop(-1)
            if operator.startswith("not_"):
                operator = operator.split("not_", 1)[-1]

        if path and self.kind in [bool, int, float, str]:
            raise FieldError(self, f"no path {path} with kind {self.kind.__name__}")

        if self.criteria is None:
            self.criteria = {}

        if value is None and operator == "eq":
            value = True
            operator = "null"
            criterion = f"{criterion[:-2]}null"

        if self.OPERATORS[operator]:

            self.criteria.setdefault(criterion, [])

            if not isinstance(value, (set, list, tuple)):
                value = [value]

            if path or self.kind in [set, list]:
                self.criteria[criterion].extend(value)
            else:
                self.criteria[criterion].extend(self.valid(item) for item in value)

        else:

            if operator == "null":
                self.criteria[criterion] = not (value == "false" or value == "no" or value == "0" or value == 0 or not value)
            elif path:
                self.criteria[criterion] = value
            else:
                self.criteria[criterion] = self.valid(value)

    def get(self, values, path):
        """
        Walk along to get a value
        """

        if isinstance(path, str):
            path = self.split(path)

        for place in path:
            if isinstance(place, int):
                if (
                    (not isinstance(values, list)) or
                    (place >= 0 and len(values) < place + 1) or
                    (place < 0 and len(values) < abs(place))
                ):
                    return None
            else:
                if (
                    (not isinstance(values, dict)) or
                    (place not in values)
                ):
                    return None
            values = values[place]

        return values

    def set(self, values, path, value): # pylint: disable=too-many-branches
        """
        Walk along to get a value
        """

        if isinstance(path, str):
            path = self.split(path)

        for index, place in enumerate(path):

            if index < len(path) - 1:
                default = {} if isinstance(path[index+1], str) else []
            else:
                default = value

            if isinstance(values, dict):

                if isinstance(place, int):
                    raise relations.FieldError(self, f"index {place} invalid for dict {values}")

                if place not in values:
                    values[place] = default

            else:

                if isinstance(place, str):
                    raise relations.FieldError(self, f"key {place} invalid for list {values}")

                while (
                    (place >= 0 and len(values) < place + 1) or
                    (place < 0 and len(values) < abs(place))
                ):
                    values.append(None)

                if values[place] is None:
                    values[place] = default

            if index < len(path) - 1:
                values = values[place]
            elif values[place] != value:
                values[place] = value

    def export(self):
        """
        Create a dictionary of object attributes
        """

        if self.kind == set:
            if self.options is not None:
                return [value for value in self.options if value in self.value]
            return sorted(self.value)

        if self.value is None or self.attr is None:
            return copy.deepcopy(self.value)

        values = {}

        if callable(self.attr):

            self.attr(values, self.value)

        else:

            for attr, store in self.attr.items():
                attr = getattr(self.value, attr)
                self.set(values, store, attr() if callable(attr) else attr)

        return values

    def apply(self, path, value):
        """
        Apply value at path
        """

        if self.kind in [bool, int, float, str]:
            raise FieldError(self, f"no apply for {self.kind.__name__}")

        values = self.export()

        if values is None:
            values = [] if self.kind in [set, list] else {}

        self.set(values, path, value)
        self.value = values

    def access(self, path):
        """
        Access value at path
        """

        if self.kind in [bool, int, float, str]:
            raise FieldError(self, f"no access for {self.kind.__name__}")

        return self.get(self.export(), path)

    def delta(self):
        """
        Detect if a field is different from original
        """

        return self.export() != self.original

    def write(self, values):
        """
        Writes values to dict for storage
        """

        value = self.export()
        if self.inject:
            self.set(values, self.inject.split('__', 1)[-1], value)
        else:
            values[self.store] = value

    def create(self, values):
        """
        Writes values to dict for creation
        """

        if not self.auto:
            self.write(values)
            self.original = self.export()

    def retrieve(self, values): # pylint: disable=too-many-return-statements,too-many-branches)
        """
        Check if this value satisfies our criteria
        """

        for operator, satisfy in (self.criteria or {}).items():

            value = values.get(self.store)

            if self.kind in [bool, int, float, str, set, list, dict]:
                value = self.valid(value)
            elif not value:
                value = value or {}

            path = self.split(operator)
            operator = path.pop().split('_')
            operator, invert = (operator[-1], len(operator) > 1)
            condition = False

            value = self.get(value, path)

            if operator == "null":
                condition = (satisfy == (value is None))

            elif value is None:
                condition = False

            elif operator == "in":
                condition = value  in satisfy

            elif operator == "eq":
                condition = value == satisfy

            elif operator == "gt":
                condition = value > satisfy

            elif operator == "gte":
                condition = value >= satisfy

            elif operator == "lt":
                condition = value < satisfy

            elif operator == "lte":
                condition = value <= satisfy

            elif operator == "like":
                condition = str(satisfy).lower() in str(value).lower()

            elif operator == "start":
                condition = str(value).lower().startswith(str(satisfy).lower())

            elif operator == "end":
                condition = str(value).lower().endswith(str(satisfy).lower())

            elif operator == "has":
                condition = all(item in value for item in satisfy)

            elif operator == "any":
                condition = any(item in value for item in satisfy)

            elif operator == "all":
                condition = all(item in value for item in satisfy) and len(value) == len(satisfy)

            if invert:
                condition = not condition

            if not condition:
                return False

        return True

    def like(self, values, like, parents, path=None):
        """
        Check if this value matchees a model's like or parents match
        """

        value = values.get(self.store)

        if self.titles is not None and path is None:
            if not value:
                return False
            for store in self.titles:
                if str(like).lower() in str(value[store]).lower():
                    return True
            return False

        if path:
            value = self.get(value, path)
        else:
            value = self.valid(value)

        if self.store in parents:
            return value in parents[self.store]

        return str(like).lower() in str(value).lower()

    def read(self, values):
        """
        Loads the value from storage
        """

        if self.inject:
            self.value = self.get(values, self.inject.split('__', 1)[-1])
        else:
            self.value = values.get(self.store)

        self.original = self.export()

    def title(self, path=None):
        """
        Get title at path
        """

        if self.kind in [bool, int, float, str]:
            return [self.value]

        if path is None:
            path = []

        if self.kind in [set, list, dict]:
            return [self.get(self.value, path)]

        values = self.export()

        if path:
            return [self.get(values, path)]

        return [self.get(values, title) for title in self.titles]

    def update(self, values):
        """
        Writes values to dict for updates, whether a record has its values changed
        """

        if self.refresh and not self.delta():
            self.value = self.default() if callable(self.default) else self.default

        if self.delta():
            self.write(values)
            self.original = self.export()

    def mass(self, values):
        """
        Writes values to dict for a mass update, whether any field has been set
        """

        if self.refresh and not self.changed:
            self.value = self.default() if callable(self.default) else self.default

        if self.changed:

            if self.inject:
                raise FieldError(self, "no mass update with inject")

            self.write(values)
