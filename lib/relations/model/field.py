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
        'many',
        'one',
        'set',
        'add',
        'create',
        'retrieve',
        'update',
        'delete'
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
