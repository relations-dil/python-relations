"""
Relations Module for handling labels
"""

import relations

class Labels:
    """
    Labels container
    """

    id = None
    label = None

    ids = None
    labels = None
    format = None
    parents = None

    def __init__(self, model):

        self.id = model._id
        self.label = model._label

        self.ids = []
        self.labels = {}
        self.format = []
        self.parents = {}

        for field in self.label:
            relation = model._ancestor(field)
            if relation is not None:
                self.parents[field] = relation.Parent.many(**{f"{relation.parent_field}__in": model[field]}).labels()
                self.format.extend(self.parents[field].format)
            elif field in model._fields._names:
                if isinstance(model._fields._names[field].format, list):
                    self.format.extend(model._fields._names[field].format)
                else:
                    self.format.append(model._fields._names[field].format)
            else:
                self.format.append(None)

    def __len__(self):
        """
        Use for number labels
        """

        return len(self.ids)

    def __contains__(self, id):
        """
        Use whether in ids
        """

        return id in self.ids

    def __iter__(self):
        """
        Use the order of ids
        """

        return iter(self.ids)

    def __setitem__(self, id, value):
        """
        Set by id
        """

        if id not in self.ids:
            self.ids.append(id)

        self.labels[id] = value

    def __getitem__(self, id):
        """
        Get by id
        """

        return self.labels[id]

    def __delitem__(self, id):
        """
        Delete by id
        """

        self.ids.pop(self.ids.index(id))

        del self.labels[id]

    def add(self, values): # pylint: disable=too-many-branches
        """
        Adds a label given values
        """

        label = []

        for name in self.label: # pylint: disable=too-many-nested-blocks

            if name in self.parents:

                if values[name] in self.parents[name]:
                    label.extend(self.parents[name][values[name]])
                else:
                    label.extend([None for each in self.parents[name].format])

            elif '__' in name:

                field, path = name.split('__', 1)

                if isinstance(values, dict):
                    label.append(relations.Field.walk(path, values[field]))
                else:

                    field = values._record._names[field]

                    if isinstance(field.value, (list, dict)):
                        label.append(relations.Field.walk(path, field.value))
                    else:
                        if field.value is not None:
                            export = field.export()
                            for piece in field.label:
                                label.append(relations.Field.walk(path, export))
                        else:
                            for piece in field.label:
                                label.append(None)
            else:

                if isinstance(values, dict):

                    label.append(values[name])

                else:

                    field = values._record._names[name]

                    if field.kind in [bool, int, float, str, list, dict]:

                        label.append(field.value)

                    else:
                        if field.value is not None:
                            export = field.export()
                            for piece in field.label:
                                label.append(export[piece])
                        else:
                            for piece in field.label:
                                label.append(None)

        self[values[self.id]] = label
