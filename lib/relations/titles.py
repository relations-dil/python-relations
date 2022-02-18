"""
Relations Module for handling titles
"""

import relations

class Titles:
    """
    Titles container
    """

    id = None
    fields = None

    ids = None
    titles = None
    format = None
    parents = None

    def __init__(self, model):

        self.id = model._id
        self.fields = model._titles

        self.ids = []
        self.titles = {}
        self.format = []
        self.parents = {}

        for field in self.fields:
            relation = model._ancestor(field)
            if relation is not None:
                self.parents[field] = relation.Parent.many(**{f"{relation.parent_field}__in": model[field]}).titles()
                self.format.extend(self.parents[field].format)
            elif field in model._fields._names and model._fields._names[field].format is not None:
                self.format.extend(model._fields._names[field].format)
            else:
                self.format.append(None)

    def __len__(self):
        """
        Use for number titles
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

        self.titles[id] = value

    def __getitem__(self, id):
        """
        Get by id
        """

        return self.titles[id]

    def __delitem__(self, id):
        """
        Delete by id
        """

        self.ids.pop(self.ids.index(id))

        del self.titles[id]

    def add(self, model): # pylint: disable=too-many-branches
        """
        Adds a title given a model
        """

        title = []

        for name in self.fields: # pylint: disable=too-many-nested-blocks

            if name in self.parents:

                if model[name] in self.parents[name]:
                    title.extend(self.parents[name][model[name]])
                else:
                    title.extend([None for _ in self.parents[name].format])

            else:

                path = relations.Field.split(name)
                field = path.pop(0)

                title.extend(model._record._names[field].title(path))

        self[model[self.id]] = title
