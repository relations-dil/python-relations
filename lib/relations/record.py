"""
Model Record Module
"""

class RecordError(Exception):
    """
    Record Error excception which capture the record with the issue
    """


    def __init__(self, record, message):

        self.record = record
        self.message = message
        super().__init__(self.message)

class Record:
    """
    Stores record for a Model
    """

    _order = None  # Access in order
    _names = None  # Access by name
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

    def keys(self):
        """
        Implements keys for converting to dict
        """
        return iter(self)

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

    def filter(self, criterion, value):
        """
        Sets criterion on a field
        """

        if isinstance(criterion, int):
            if criterion < len(self._order):
                return self._order[criterion].filter(value)
        else:
            if '__' in criterion:
                name, operator = criterion.split("__", 1)
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

    def match(self, values, label, like, parents):
        """
        Sees if a record satisfies criteria in a dict
        """

        for field in label:
            if self._names[field].match(values, like, parents):
                return True

        return False

    def read(self, values):
        """
        Loads the value from storage
        """

        for field in self._order:
            if field.inject:
                field.read(values[self._names[field.inject.split('__')[0]].store])
            else:
                field.read(values)

    def write(self, values, update=False):
        """
        Writes values to dict (if not readonly)
        """

        inject = []

        for field in self._order:
            if field.inject:
                inject.append(field)
            else:
                field.write(values, update=update)

        for field in inject:
            field.write(values[self._names[field.inject.split('__')[0]].store])

        return values
