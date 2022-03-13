"""
Relations Module for handling models
"""

# pylint: disable=unsupported-membership-test,too-few-public-methods,too-many-branches,too-many-statements,too-many-instance-attributes

import copy

import functools

import relations

class ModelError(Exception):
    """
    Generic model Error for easier tracing
    """

    def __init__(self, model, message):

        self.model = model
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        """
        Might want to mention the model and info about it
        """
        return f"{self.model.NAME}: {self.message}"

class ModelIdentity:
    """
    Intermiedate statuc type class for constructing mode information with a full model
    """

    SOURCE = None   # Data source

    TITLE = None    # Title of the Model
    NAME = None     # Name of the Model
    ID = 0          # Ref of id field (assumes first field)
    TITLES = None   # Fields that make up the titles of the model
    LIST = None     # Default fields to list
    UNIQUE = None   # Unique indexes
    INDEX = None    # Regular indexes

    ORDER = None    # Default sort order
    CHUNK = 100     # Default chunk

    PARENTS = None  # Parent relationships (many/one to one)
    CHILDREN = None # Child relationships (one to many/one)
    SISTERS = None  # Sister relationships (many to many)
    BROTHERS = None # Brother relationships (many to many)

    _fields = None # Base record to create other records with
    _id = None     # Name of id field
    _titles = None  # Actual fields of the titles
    _list = None   # Actual fields to list
    _unique = None # Actual unique indexes
    _index = None  # Actual indexes
    _order = None  # Default sort order

    DEFINE = [
        "id",
        "unique",
        "index"
    ]

    UNDEFINE = [
        "ID",
        "TITLES",
        "LIST",
        "UNIQUE",
        "INDEX",
        "ORDER",
        "CHUNK",
        "PARENTS",
        "CHILDREN",
        "SISTERS",
        "BROTHERS"
    ]

    @staticmethod
    def underscore(name):
        """
        Turns camel case to underscored
        """
        underscored = []
        previous = True
        for letter in name:
            lowered = letter.lower()
            if not previous and lowered != letter:
                underscored.append('_')
            underscored.append(lowered)
            previous = (lowered != letter)

        return ''.join(underscored)

    @classmethod
    def thy(cls, self=None):
        """
        Base identity to be known without instantiating the class
        """

        # If self wasn't sent, we're just providing a shell of an instance

        if self is None:
            self = ModelIdentity()
            self.__dict__.update(cls.__dict__)

        # Use TITLE, NAME if set, else use class name

        setattr(self, 'TITLE', cls.TITLE or cls.__name__)
        setattr(self, 'NAME', cls.NAME or cls.underscore(self.TITLE))

        # Derive all the fields

        fields = relations.Record()

        for name, attribute in cls.__dict__.items():

            if name.startswith('_') or name != name.lower():
                continue # pragma: no cover

            if attribute in [bool, int, float, str, set, list, dict]:
                field = relations.Field(attribute)
            elif callable(attribute):
                field = relations.Field(type(attribute()), default=attribute)
            elif isinstance(attribute, set):
                field = relations.Field(set, options=sorted(attribute))
            elif isinstance(attribute, tuple) and attribute and isinstance(attribute[0], str):
                field = relations.Field(set, options=list(attribute))
            elif isinstance(attribute, list):
                field = relations.Field(type(attribute[0]), default=attribute[0], options=attribute)
            elif isinstance(attribute, tuple):
                field = relations.Field(*attribute)
            elif isinstance(attribute, dict):
                field = relations.Field(**attribute)
            elif isinstance(attribute, relations.Field):
                field = attribute
            else:
                continue # pragma: no cover

            field.name = name

            fields.append(field)

        setattr(self, '_fields', fields)

        # Determine the _id field name

        if cls.ID is not None:
            setattr(self, '_id', self._field_name(cls.ID))

        # Figure out the titles

        titles = self.TITLES

        if not titles:
            titles = []
            for field in self._fields._order:
                if self._id == field.name:
                    continue
                if field.kind in (int, str):
                    titles.append(field.name)
                    if field.kind == str and field._none is None:
                        field.none = False
                if field.kind == str:
                    break

        if isinstance(titles, str):
            titles = [titles]

        self._titles = titles

        for field in self._titles:
            if field.split('__', 1)[0] not in self._fields:
                raise ModelError(self, f"cannot find field {field} from titles")

        # Figure out the list

        if self.LIST:
            self._list = self.LIST
        else:
            self._list = list(self._titles)
            if self._id and self._id not in self._list:
                self._list.insert(0, self._id)

        if isinstance(self._list, str):
            self._list = [self._list]

        # Make sure all the list checks out

        for field in self._list:
            if field.split('__', 1)[0] not in self._fields:
                raise ModelError(self, f"cannot find field {field} from list")

        # Figure out unique indexes

        unique = self.UNIQUE

        if unique is None:
            unique = self._titles
        elif not unique:
            unique = {}

        if isinstance(unique, str):
            unique = [unique]

        if isinstance(unique, list):
            unique = {
                "-".join(unique): unique
            }

        if isinstance(unique, dict):
            self._unique = unique

        # Make sure all the unique indexes check out

        for unique in self._unique:
            for field in self._unique[unique]:
                if field.split('__')[0] not in self._fields:
                    raise ModelError(self, f"cannot find field {field} from unique {unique}")

        index = self.INDEX or {}

        if isinstance(index, str):
            index = [index]

        if isinstance(index, list):
            index = {
                "-".join(index): index
            }

        if isinstance(index, dict):
            self._index = index

        # Make sure all the indexes check out

        for index in self._index:
            for field in self._index[index]:
                if field.split('__')[0] not in self._fields:
                    raise ModelError(self, f"cannot find field {field} from index {index}")

        # Make sure all inject fields reference actual fields that are lists or dicts

        for field, inject in [(field, field.inject.split('__')[0]) for field in self._fields._order if field.inject]:
            if inject not in self._fields:
                raise relations.FieldError(field, f"cannot find field {inject} from inject {field.inject}")
            if self._fields._names[inject].kind not in [list, dict]:
                raise relations.FieldError(self, f"field {inject} not list or dict from inject {field.inject}")

        # Determine default sort order (if desired)

        if self.ORDER:
            self._order = self._ordering(self.ORDER)
        elif self.ORDER is None and len(self._unique) == 1:
            self._order = self._ordering(list(self._unique.values())[0])
        else:
            self._order = []

        # Initialize relation models

        self.PARENTS = cls.PARENTS or {}
        self.CHILDREN = cls.CHILDREN or {}
        self.SISTERS = cls.SISTERS or {}
        self.BROTHERS = cls.BROTHERS or {}

        # Have the the source do whatever it needs to

        self.SOURCE = cls.SOURCE

        if relations.source(self.SOURCE) is not None:
            relations.source(self.SOURCE).init(self)

        return self

    def _field_name(self, field):
        """
        Returns the name of the field, whether index or name
        """

        if field not in self._fields:
            raise ModelError(self, f"cannot find field {field} in {self.NAME}")

        if isinstance(field, str):
            return field

        return self._fields._order[field].name

    def _ordering(self, order):
        """
        Creates a prefix sorting list, including field checks
        """

        if isinstance(order, str):
            order = [order]

        ordering = []

        for sort in order:

            field = sort[1:] if sort[0] in ['-', '+'] else sort

            if field.split('__')[0] not in self._fields:
                raise ModelError(self, f"unknown sort field {field}")

            ordering.append(sort if sort != field else f"+{sort}")

        return ordering

    def _ancestor(self, field):
        """
        Looks up a parent class for a field
        """

        for relation in self.PARENTS.values():
            if field == relation.child_field:
                return relation

        return None

    def define(self):
        """
        define the identity
        """

        definition = {
            "fields": self._fields.define(),
        }

        for attr in self.DEFINE:
            if getattr(self, f"_{attr}") is not None:
                definition[attr] = getattr(self, f"_{attr}")

        for attr in self.__dict__:
            if attr[0] != '_' and attr == attr.upper() and attr not in self.UNDEFINE and getattr(self, attr) is not None:
                definition[attr.lower()] = getattr(self, attr)

        return definition

    def migrate(self, previous, definition=None):
        """
        migrates from a previous identity
        """

        if definition is None:
            definition = self.define()

        return relations.Migrations.model(previous, definition)


class Model(ModelIdentity):
    """
    Main model class
    """

    _record = None # The current loaded single record (from get/create)
    _models = None # The current loaded multiple models (from list/create)

    _parents = None  # Parent models
    _children = None # Children models
    _sisters = None  # Sister models
    _brothers = None # Brother models

    _role = None     # Whether we're a model, parent or child
    _mode = None     # Whether we're dealing with one or many
    _bulk = None     # Whether we're bulk inserting
    _chunk = None    # Default chunk size
    _size = None     # When to auto insert
    _like = None     # Current fuzzy match
    _sort = None     # What to sort by
    _limit = None    # If we're limiting, how much
    _offset = None   # If we're limiting, where to start
    _action = None   # Overall action of this model
    _related = None  # Which fields will be set automatically

    overflow = False # Whether our overflow limt was reached

    @staticmethod
    def _extract(kwargs, name, default=None):
        """
        Grabs and remove a value from kwargs so we can chain properly
        """

        if name in kwargs:
            value = kwargs[name]
            del kwargs[name]
            return value

        return default

    def __init__(self, *args, **kwargs):
        """
        Creation is implied but we want to set stuff and call create impliicitly
        """

        # Know thyself

        self.thy(self)

        # Initialize relation models

        self._parents = {}
        self._children = {}
        self._sisters = {}
        self._brothers = {}
        self._related = {}

        # Making things and explicit, we're going to derive a lot defaults from
        # context of what the user sent in

        # If a child's been sent in, we're a parent and we're retrieving as one

        _read = self._extract(kwargs, '_read')
        _child = self._extract(kwargs, '_child')
        _parent = self._extract(kwargs, '_parent')

        # Now just assume things were sent explicitly and we might override them
        # later because the logic here is pretty hairy

        self._role = "model"
        self._action = self._extract(kwargs, '_action', "create")

        self._chunk = self._extract(kwargs, '_chunk', self.CHUNK)

        # If we're being created from reading from a source

        if _read is not None:

            self._mode = "one"
            self._action = "update"
            self._record = self._build(self._action, _read=_read)

        # If we're being created as a parent

        elif _child is not None:

            self._related = _child
            self._role = "parent"
            self._mode = "one"
            self._action = "retrieve"

            self._record = self._build(self._action, _defaults=False)
            self.filter(*args, **kwargs)

        # If we being created as a child

        elif _parent is not None:

            self._related = _parent
            self._role = "child"
            self._mode = self._extract(kwargs, '_mode')
            self._action = "retrieve" if list(self._related.values())[0] is not None else "create"

            if self._action == "retrieve":
                self._record = self._build(self._action, _defaults=False)
                self.filter(*args, **kwargs)

        # If we're being created as a search

        elif self._action == "retrieve":

            self._mode = self._extract(kwargs, '_mode')
            self._record = self._build(self._action, _defaults=False)
            self.filter(*args, **kwargs)

        # IF we're just being straight up (now tell me) created

        elif self._action == "create":

            self._bulk = self._extract(kwargs, '_bulk', False)
            self._size = self._extract(kwargs, '_size', self._chunk)

            mode = "many" if self._bulk or (args and isinstance(args[0], list)) else "one"

            self._mode = self._extract(kwargs, '_mode', mode)
            self._related = self._extract(kwargs, '_related', {})

            if self._mode == "many":

                self._models = []

                if args:
                    for each in args[0]:
                        eargs = each if isinstance(each, list) else []
                        ekwargs = each if isinstance(each, dict) else {}
                        self._models.append(self.__class__(*eargs, **ekwargs))

            else:

                self._record = self._build(self._action, *args, **kwargs)

    def __setattr__(self, name, value):
        """
        Use to set field values directly
        """

        if name[0] != '_' and name == name.lower() and name.split('__')[0] in (object.__getattribute__(self, '_fields') or []):

            self._ensure()

            if self._role == "child" and self._mode == "one":
                if self._models:
                    setattr(self._models[0], name, value)
                else:
                    raise ModelError(self, "no record")
            elif self._mode == "one":
                self._record[name] = value
                if '__' not in name:
                    self._propagate(name, value)
            else:
                if self._models:
                    for model in self._models:
                        setattr(model, name, value)
                else:
                    raise ModelError(self, "no records")

        else:

            object.__setattr__(self, name, value)

    def __getattr__(self, name):
        """
        Used to get relation models directly
        """

        if name in self.PARENTS or name in self.CHILDREN:

            self._ensure()

            if self._mode == "one":
                return self._relate(name)

        if '__' not in name:
            raise AttributeError(f"'{self}' object has no attribute '{name}'")

        current = self
        path = relations.Field.split(name)

        for place in path:
            current = current[place]

        return current

    def __getattribute__(self, name):
        """
        Use to get field values directly
        """

        if name[0] != '_' and name == name.lower() and name.split('__')[0] in (object.__getattribute__(self, '_fields') or []):

            self._ensure()

            if self._role == "child" and self._mode == "one":
                if self._models:
                    return getattr(self._models[0], name)
                raise ModelError(self, "no record")

            if self._mode == "one":
                return self._record[name]

            if self._models is None:
                raise ModelError(self, "no records")

            return [getattr(model, name) for model in self._models]

        return object.__getattribute__(self, name)

    def __len__(self):
        """
        Use for number of records
        """

        if self._action == "retrieve" and self._mode == "many":
            return self.count()

        self._ensure()

        if self._role == "child" and self._mode == "one":
            if self._models:
                return len(self._models[0])
            return 0

        if self._mode == "one":
            return len(self._record)

        return len(self._models)

    def __iter__(self):
        """
        Use the order of record
        """

        self._ensure()

        if self._role == "child" and self._mode == "one":
            if self._models:
                return iter(self._models[0])
            return iter([])

        if self._mode == "one":
            return iter(self._record)

        return iter(self._models)

    def keys(self):
        """
        Use the order of record
        """

        self._ensure()

        if self._mode == "many":
            raise ModelError(self, "no keys with many")

        if self._role == "child":
            if self._models:
                return iter(self._models[0]._record._names)
            return iter([])
        return iter(self._record._names)

    def __contains__(self, key):
        """
        Checks numerically or by name
        """

        self._ensure()

        if self._role == "child" and self._mode == "one":

            if self._models:
                return key in self._models[0]

            return False

        if self._mode == "one":
            return key in self._record

        if self._models:
            return key in self._fields

        return False

    def __setitem__(self, key, value):
        """
        Access numerically or by name
        """

        self._ensure()

        if self._role == "child" and self._mode == "one":
            if self._models:
                self._models[0][key] = value
            else:
                raise ModelError(self, "no record")
        elif self._mode == "one":
            self._record[key] = value
            self._propagate(key, value)
        else:
            if isinstance(key, int):
                raise ModelError(self, "no override")
            if self._models:
                for model in self._models:
                    model[key] = value
            else:
                raise ModelError(self, "no records")

    def __getitem__(self, key):
        """
        Access numerically or by name
        """

        if isinstance(key, str) and '__' in key:
            return getattr(self, key)

        self._ensure()

        if self._role == "child" and self._mode == "one":
            if self._models:
                return self._models[0][key]
            raise ModelError(self, "no record")

        if self._mode == "one":
            if key in self.PARENTS or key in self.CHILDREN:
                return self._relate(key)
            return self._record[key]

        if self._models is None:
            raise ModelError(self, "no records")

        if isinstance(key, int):
            return self._models[key]

        return [model[key] for model in self._models]

    @classmethod
    def _parent(cls, relation):
        """
        Adds a parent to the class
        """

        cls.PARENTS = cls.PARENTS or {}
        cls.PARENTS[relation.child_parent] = relation

    @classmethod
    def _child(cls, relation):
        """
        Adds a child to the class
        """

        cls.CHILDREN = cls.CHILDREN or {}
        cls.CHILDREN[relation.parent_child] = relation

    # These aren't used yet and might need to go

    @classmethod
    def _sister(cls, relation):
        """
        Adds a sister to the class
        """

        cls.SISTERS = cls.SISTERS or {}
        cls.SISTERS[relation.brother_sister] = relation

    @classmethod
    def _brother(cls, relation):
        """
        Adds a brother to the class
        """

        cls.BROTHERS = cls.BROTHERS or {}
        cls.BROTHERS[relation.sister_brother] = relation

    def _relate(self, name):
        """
        Looks up a relation by attribute name
        """

        if name in self.PARENTS: # pylint: disable=no-else-return

            relation = self.PARENTS[name]

            if self._parents.get(name) is None:
                if self._action == "retrieve":
                    self._parents[name] = relation.Parent.many().limit(self._chunk)
                else:
                    self._parents[name] = relation.Parent(_child={relation.parent_field: self[relation.child_field]})

            return self._parents[name]

        elif name in self.CHILDREN:

            relation = self.CHILDREN[name]

            if self._children.get(name) is None:
                if self._action == "retrieve":
                    self._children[name] = relation.Child.many().limit(self._chunk)
                else:
                    self._children[name] = relation.Child(
                        _parent={relation.child_field: self._record[relation.parent_field]}, _mode=relation.MODE
                    )

            return self._children[name]

        return None

    def _collate(self):
        """
        Executes relatives criteria and adds to our own
        """

        for child_parent, relation in self.PARENTS.items():
            if self._parents.get(child_parent) is not None:
                self._record.filter(f"{relation.child_field}__in", self._parents[child_parent][relation.parent_field])
                self.overflow = self.overflow or self._parents[child_parent].overflow
                del self._parents[child_parent]

        for parent_child, relation in self.CHILDREN.items():
            if self._children.get(parent_child) is not None:
                self._record.filter(f"{relation.parent_field}__in", self._children[parent_child][relation.child_field])
                self.overflow = self.overflow or self._children[parent_child].overflow
                del self._children[parent_child]

    def _propagate(self, field, value):
        """
        Remove a relation when its field is set or reset a parent field
        """

        field_name = self._field_name(field)

        if field_name in self._related:
            self._related[field_name] = value

        for child_parent, relation in self.PARENTS.items():
            if field_name == relation.child_field:
                self._parents[child_parent] = None

        for parent_child, relation in self.CHILDREN.items():
            if field_name == relation.parent_field and self._relate(parent_child):
                self._relate(parent_child)[relation.child_field] = value

    def _input(self, record, *args, **kwargs):
        """
        Fills in field values from args, kwargs
        """

        field = 0

        for value in args:
            while record._order[field].auto or record._order[field].name in self._related:
                field += 1
            record[field] = value
            field += 1

        for name, value in kwargs.items():
            record[name] = value

    def _build(self, _action, *args, **kwargs):
        """
        Fills in record
        """

        _defaults = self._extract(kwargs, '_defaults', True)
        _read = self._extract(kwargs, '_read')

        record = copy.deepcopy(self._fields)
        record._action = _action

        if _defaults:
            for field in record._order:
                if field.default is not None:
                    field.value = field.default() if callable(field.default) else field.default

        if _read is not None:
            record.read(_read)

        for field, value in self._related.items():
            record[field] = value

        self._input(record, *args, **kwargs)

        return record

    def _ensure(self):
        """
        Makes sure there's records if there's criteria
        """

        if self._action == "retrieve":
            if self._record._action == "update":
                raise ModelError(self, "need to update")
            self.retrieve()

    def _each(self, action=None):
        """
        Converts to all models, whether _record or _models
        """

        if self._record and (action is None or self._action == action):
            return [self]

        if self._models:
            return [model for model in self._models if action is None or model._action == action]

        return []

    def filter(self, *args, **kwargs):
        """
        Sets to return multiple records
        """

        for field, value in self._related.items():
            self._record.filter(field, value)

        for index, value in enumerate(args):
            self._record.filter(index, value)

        for name, value in kwargs.items():

            if name == "like":

                self._like = value

            else:

                pieces = name.split('__', 1)

                relation = self._relate(pieces[0])

                if relation is not None:
                    relation.filter(**{pieces[1]: value})
                else:
                    self._record.filter(name, value)

        return self

    @classmethod
    def bulk(cls, size=None):
        """
        For inserting multiple records without getting id's
        """

        return cls(_action="create", _mode="many", _bulk=True, _size=size or cls.CHUNK)

    @classmethod
    def one(cls, *args, **kwargs):
        """
        For retrieving a single record
        """

        return cls(_action="retrieve", _mode="one", *args, **kwargs)

    @classmethod
    def many(cls, *args, **kwargs):
        """
        Sets to return multiple records
        """

        return cls(_action="retrieve", _mode="many", *args, **kwargs)

    def sort(self, *args):
        """
        Adding sorting to filtering or sorts existing records
        """

        if self._mode == "one":
            raise ModelError(self, "cannot sort one")

        if not args:
            return self

        sorting = self._ordering(args)

        # If we're retrieving, just add to existing

        if self._action == "retrieve":

            self._sort = self._sort or []
            self._sort.extend(sorting)

        else:

            def compare(model1, model2):
                for sort in sorting:
                    cmp = (model1[sort[1:]] > model2[sort[1:]]) - (model1[sort[1:]] < model2[sort[1:]])
                    return cmp if sort[0] == '+' else -cmp

            self._models = sorted(self._models, key=functools.cmp_to_key(compare))

        return self

    def limit(self, limit=None, start=0, page=None, per_page=None):
        """
        Adding sorting to filtering or sorts existing records
        """

        if limit is None:
            limit = self.CHUNK

        # If we're not retrieving, there's no point in limiting

        if self._action != "retrieve":

            raise ModelError(self, "can only limit retrieve")

        self._limit = per_page if per_page is not None else limit
        self._offset = (page - 1) * self._limit if page is not None else start

        return self

    def set(self, *args, **kwargs):
        """
        Sets a single or multiple records or prepares to
        """

        # If we're retrieving, make we're only getting one or we'll store
        if self._action == "retrieve":
            if self._mode == "one":
                self.retrieve()
            else:
                self._record._action = "update"

        for model in self._each():
            self._input(model._record, *args, **kwargs)

        return self

    def add(self, *args, **kwargs):
        """
        Adds records
        """

        self._ensure()

        _count = self._extract(kwargs, '_count', 1)

        if self._role == "child" and self._mode == "one":

            if self._models or _count > 1:
                raise ModelError(self, "only one allowed")

            self._models = [
                self.__class__(_action="create", _related=self._related, *args, **kwargs)
            ]

        elif self._mode == "one":

            raise ModelError(self, "only one allowed")

        else:

            if self._models is None:
                self._models = []

            for _ in range(_count):
                self._models.append(self.__class__(_action="create", _related=self._related, *args, **kwargs))

            if self._bulk and len(self._models) >= self._size:
                self.create()

        return self

    def export(self):
        """
        Converts to all models, whether _record or _models
        """

        self._ensure()

        if self._record:
            return self._record.export()

        if self._models:
            return [model.export() for model in self._models]

        return []

    @classmethod
    def define(cls, *args, **kwargs):
        """
        define the model
        """
        return relations.source(cls.SOURCE).define(cls.thy().define(), *args, **kwargs)

    def create(self, *args, **kwargs):
        """
        create the model
        """

        if self._action not in ["create", "update"]:
            raise ModelError(self, f"cannot create during {self._action}")

        return relations.source(self.SOURCE).create(self, *args, **kwargs)

    def count(self, *args, **kwargs):
        """
        count the models
        """

        if self._action not in ["update", "retrieve"]:
            raise ModelError(self, f"cannot count during {self._action}")

        return relations.source(self.SOURCE).count(self, *args, **kwargs)

    def retrieve(self, verify=True, *args, **kwargs):
        """
        retrieve the model
        """

        if self._action != "retrieve":
            raise ModelError(self, f"cannot retrieve during {self._action}")

        return relations.source(self.SOURCE).retrieve(self, verify, *args, **kwargs)

    def titles(self, *args, **kwargs):
        """
        retrieve the model
        """

        if self._action not in ["update", "retrieve"]:
            raise ModelError(self, f"cannot titles during {self._action}")

        return relations.source(self.SOURCE).titles(self, *args, **kwargs)

    def update(self, *args, **kwargs):
        """
        update the model
        """

        if self._action not in ["update", "retrieve"]:
            raise ModelError(self, f"cannot update during {self._action}")

        return relations.source(self.SOURCE).update(self, *args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        delete the model
        """

        if self._action not in ["update", "retrieve"]:
            raise ModelError(self, f"cannot delete during {self._action}")

        if self._action == "retrieve" and self._mode == "one":
            self.retrieve()

        return relations.source(self.SOURCE).delete(self, *args, **kwargs)

    def query(self, action=None, *args, **kwargs):
        """
        get the current query for the model
        """

        if self._action == "create":
            return relations.source(self.SOURCE).create_query(self, *args, **kwargs).bind(self)

        if self._action == "retrieve" and action == "count":
            return relations.source(self.SOURCE).count_query(self, *args, **kwargs).bind(self)

        if self._action == "retrieve" and action == "titles":
            return relations.source(self.SOURCE).titles_query(self, *args, **kwargs).bind(self)

        if action == "update" or (action is None and self._action == "update"):
            return relations.source(self.SOURCE).update_query(self, *args, **kwargs).bind(self)

        if action == "delete":
            return relations.source(self.SOURCE).delete_query(self, *args, **kwargs).bind(self)

        return relations.source(self.SOURCE).retrieve_query(self, *args, **kwargs).bind(self)
