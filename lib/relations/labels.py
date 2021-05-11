"""
Relations Module for handling labels
"""

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
            else:
                self.format.append(model._fields._names[field].format)

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

    def add(self, values):
        """
        Adds a label given values
        """

        label = []

        for field in self.label:
            if field in self.parents:
                if values[field] in self.parents[field]:
                    label.extend(self.parents[field][values[field]])
                else:
                    label.extend([None for each in self.parents[field].format])
            else:
                label.append(values[field])

        self[values[self.id]] = label
