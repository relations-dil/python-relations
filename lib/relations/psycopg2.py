"""
Module for intersting with PyMySQL
"""

import copy

import psycopg2
import psycopg2.extras

import relations
import relations.query

class Source(relations.Source):
    """
    PyMySQL Source
    """

    RETRIEVE = {
        'eq': '=',
        'gt': '>',
        'ge': '>=',
        'lt': '<',
        'le': '<='
    }

    database = None   # Database to use
    schema = None     # Schema to use
    connection = None # Connection
    created = False   # If we created the connection

    def __init__(self, name, database, schema="public", connection=None, **kwargs):

        self.database = database
        self.schema = schema

        if connection is not None:
            self.connection = connection
        else:
            self.created = True
            self.connection = psycopg2.connect(
                cursor_factory=psycopg2.extras.RealDictCursor,
                **{name: arg for name, arg in kwargs.items() if name not in ["name", "database", "schema", "connection"]}
            )

    def __del__(self):

        if self.created:
            self.connection.close()

    def table(self, model):
        """
        Get the full table name
        """

        table = []

        if model.SCHEMA is not None:
            table.append(f'"{model.SCHEMA}"')
        else:
            table.append(f'"{self.schema}"')

        table.append(f'"{model.TABLE}"')

        return ".".join(table)

    def field_init(self, field):
        """
        Make sure there's primary_key
        """

        self.ensure_attribute(field, "primary_key")
        self.ensure_attribute(field, "serial")
        self.ensure_attribute(field, "definition")

    def model_init(self, model):
        """
        Init the model
        """

        self.record_init(model._fields)

        self.ensure_attribute(model, "DATABASE")
        self.ensure_attribute(model, "SCHEMA")
        self.ensure_attribute(model, "TABLE")
        self.ensure_attribute(model, "QUERY")
        self.ensure_attribute(model, "DEFINITION")

        if model.TABLE is None:
            model.TABLE = model.NAME

        if model.QUERY is None:
            model.QUERY = relations.query.Query(selects='*', froms=self.table(model))

        if model._id is not None:

            if model._fields._names[model._id].primary_key is None:
                model._fields._names[model._id].primary_key = True

            if model._fields._names[model._id].serial is None:
                model._fields._names[model._id].serial = True
                model._fields._names[model._id].readonly = True

    def field_define(self, field, definitions):
        """
        Add what this field is the definition
        """

        if field.definition is not None:
            definitions.append(field.definition)
            return

        definition = [f'"{field.store}"']

        default = None

        if field.kind == int:

            if field.serial:
                definition.append("SERIAL")
            else:
                definition.append("SMALLINT")

            if field.default is not None:
                default = f"DEFAULT {field.default}"

        elif field.kind == str:

            length = field.length if field.length is not None else 255

            definition.append(f"VARCHAR({length})")

            if field.default is not None:
                default = f"DEFAULT '{field.default}'"

        if field.not_null:
            definition.append("NOT NULL")

        if field.primary_key:
            definition.append("PRIMARY KEY")

        if default:
            definition.append(default)

        definitions.append(" ".join(definition))

    def model_define(self, cls):

        model = cls._thyself()

        if model.DEFINITION is not None:
            return model.DEFINITION

        definitions = []

        self.record_define(model._fields, definitions)

        sep = ',\n  '
        return f"CREATE TABLE IF NOT EXISTS {self.table(model)} (\n  {sep.join(definitions)}\n)"

    def field_create(self, field, fields, clause):
        """
        Adds values to clause if not readonly
        """

        if not field.readonly:
            fields.append(f'"{field.store}"')
            clause.append(f"%({field.store})s")
            field.changed = False

    def model_create(self, model):
        """
        Executes the create
        """

        cursor = self.connection.cursor()

        # Create the insert query

        fields = []
        clause = []

        self.record_create(model._fields, fields, clause)

        if model._id is not None and model._fields._names[model._id].serial:

            store = model._fields._names[model._id].store

            query = f'INSERT INTO {self.table(model)} ({",".join(fields)}) VALUES({",".join(clause)}) RETURNING {store}'

            for creating in model._each("create"):
                cursor.execute(query, creating._record.write({}))
                creating[model._id] = cursor.fetchone()[store]
        else:

            query = f'INSERT INTO {self.table(model)} ({",".join(fields)}) VALUES({",".join(clause)})'

            cursor.executemany(query, [model._record.write({}) for model in model._each("create")])

        cursor.close()

        for creating in model._each("create"):
            for parent_child, relation in creating.CHILDREN.items():
                if creating._children.get(parent_child):
                    creating._children[parent_child].create()
            creating._action = "update"
            creating._record._action = "update"

        model._action = "update"

        return model

    def field_retrieve(self, field, query, values):
        """
        Adds where caluse to query
        """

        for operator, value in (field.criteria or {}).items():
            if operator == "in":
                query.add(wheres=f'"{field.store}" IN ({",".join(["%s" for each in value])})')
                values.extend(value)
            elif operator == "ne":
                query.add(wheres=f'"{field.store}" NOT IN ({",".join(["%s" for each in value])})')
                values.extend(value)
            else:
                query.add(wheres=f'"{field.store}"{self.RETRIEVE[operator]}%s')
                values.append(value)

    def model_retrieve(self, model, verify=True):
        """
        Executes the retrieve
        """

        model._collate()

        cursor = self.connection.cursor()

        query = copy.deepcopy(model.QUERY)
        values = []

        self.record_retrieve(model._record, query, values)

        cursor.execute(query.get(), values)

        if model._mode == "one" and cursor.rowcount > 1:
            raise relations.model.ModelError(model, "more than one retrieved")

        if model._mode == "one" and model._role != "child":

            if cursor.rowcount < 1:

                if verify:
                    raise relations.model.ModelError(model, "none retrieved")
                else:
                    return None

            model._record = model._build("update", _read=cursor.fetchone())

        else:

            model._models = []

            while len(model._models) < cursor.rowcount:
                model._models.append(model.__class__(_read=cursor.fetchone()))

            model._record = None

        model._action = "update"

        cursor.close()

        return model

    def field_update(self, field, clause, values, changed=None):
        """
        Preps values to dict (if not readonly)
        """

        if not field.readonly and (changed is None or field.changed==changed):
            clause.append(f'"{field.store}"=%s')
            values.append(field.value)
            field.changed = False

    def model_update(self, model):
        """
        Executes the update
        """

        cursor = self.connection.cursor()

        updated = 0

        # If the overall model is retrieving and the record has values set

        if model._action == "retrieve" and model._record._action == "update":

            # Build the SET clause first

            clause = []
            values = []

            self.record_update(model._record, clause, values, changed=True)

            # Build the WHERE clause next

            where = relations.query.Query()
            self.record_retrieve(model._record, where, values)

            query = f"UPDATE {self.table(model)} SET {relations.sql.assign_clause(clause)} {where.get()}"

            cursor.execute(query, values)

            updated = cursor.rowcount

        elif model._id:

            store = model._fields._names[model._id].store

            for updating in model._each("update"):

                clause = []
                values = []

                self.record_update(updating._record, clause, values)

                values.append(updating[model._id])

                query = f'UPDATE {self.table(model)} SET {relations.sql.assign_clause(clause)} WHERE "{store}"=%s'

                cursor.execute(query, values)

                for parent_child, relation in updating.CHILDREN.items():
                    if updating._children.get(parent_child):
                        updating._children[parent_child].create().update()

                updated += cursor.rowcount

        else:

            raise relations.model.ModelError(model, "nothing to update from")

        return updated

    def model_delete(self, model):
        """
        Executes the delete
        """

        cursor = self.connection.cursor()

        deleted = 0

        if model._action == "retrieve":

            where = relations.query.Query()
            values = []
            self.record_retrieve(model._record, where, values)

            query = f"DELETE FROM {self.table(model)} {where.get()}"

        elif model._id:

            store = model._fields._names[model._id].store
            values = []

            for deleting in model._each():
                values.append(deleting[model._id])

            query = f'DELETE FROM {self.table(model)} WHERE "{store}" IN ({",".join(["%s"] * len(values))})'

        else:

            raise relations.model.ModelError(model, "nothing to delete from")

        cursor.execute(query, values)

        return cursor.rowcount
