"""
Model Record Module
"""

import relations

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

        if name[0] != '_' and name in (self._names or []):
            self._names[name].value = value
            return

        apply = relations.Field.split(name)

        if apply[0] in (self._names or []):
            self._names[apply[0]].apply(apply[1:], value)
            return

        self.__dict__[name] = value

    def __getattr__(self, name):
        """
        Use to get field values directly
        """

        if name in (self._names or []):
            return self._names[name].value

        access = relations.Field.split(name)

        if access[0] in (self._names or []):
            return self._names[access[0]].access(access[1:])

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

        apply = relations.Field.split(key)

        if apply[0] in (self._names or []):
            self._names[apply[0]].apply(apply[1:], value)
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

        access = relations.Field.split(key)

        if access[0] in (self._names or []):
            return self._names[access[0]].access(access[1:])

        raise RecordError(self, f"unknown field '{key}'")

    def define(self):
        """
        Gets all the defintions for fields
        """

        return [field.define() for field in self._order]

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

    def export(self):
        """
        Exports value by name
        """

        return {field.name: field.export() for field in self._order}

    def create(self, values):
        """
        Writes values for create
        """

        inject = []

        for field in self._order:
            if field.inject:
                inject.append(field)
            else:
                field.create(values)

        for field in inject:
            field.create(values[self._names[field.inject.split('__')[0]].store])

        return values

    def retrieve(self, values):
        """
        Sees if a record satisfies criteria in a dict
        """

        for field in self._order:
            if not field.retrieve(values):
                return False

        return True

    def like(self, values, titles, like, parents):
        """
        Sees if a record matches a like value
        """

        for field in titles:
            field = relations.Field.split(field)
            if self._names[field[0]].like(values, like, parents, field[1:]):
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

    def update(self, values):
        """
        Writes values for update
        """

        inject = []

        for field in self._order:
            if field.inject:
                inject.append(field)
            else:
                field.update(values)

        for field in inject:
            if field.delta() or field.refresh:
                store = field.inject.split('__')[0]
                if self._names[store].store not in values:
                    self._names[store].write(values)
                field.update(values[self._names[store].store])

        return values

    def mass(self, values):
        """
        Writes values for update
        """

        inject = []

        for field in self._order:
            if field.inject:
                inject.append(field)
            else:
                field.mass(values)

        for field in inject:
            if field.changed or field.refresh:
                store = field.inject.split('__')[0]
                if self._names[store].store not in values:
                    self._names[store].write(values)
                field.mass(values[self._names[field.inject.split('__')[0]].store])

        return values
