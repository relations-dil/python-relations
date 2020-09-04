"""
Module for intersting with PyMySQL
"""

import pymysql
import pymysql.cursors

import relations
import relations.query
import relations.model

class Source(relations.Source):
    """
    PyMySQL Source
    """

    connection = None
    database = None

    def __init__(self, name, host, database, cursorclass=pymysql.cursors.DictCursor, **kwargs):

        super().__init__(name)

        self.database = database
        self.connection = pymysql.connect(
            host=host, cursorclass=cursorclass, **{name: arg for name, arg in kwargs if name != "database"}
        )


class Field(relations.model.Field):
    """
    PyMySQL Field class
    """

    auto_increment = False

    RETRIEVE = {
        'eq': '=',
        'gt': '>',
        'ge': '>=',
        'lt': '<',
        'le': '<='
    }

    def __init__(self, name, cast, *args, **kwargs):
        """
        Set the name and what to cast it as and everything else be free form
        """

        super().__init(name, case, *args, **kwargs)

        if self.auto_increment:
            self.readonly = kwargs.get("readonly", True)

    def create(self, values):
        """
        Preps values to dict (if not readonly)
        """

        if not self.readonly:
            values[self.store] = f"s({field.strore})%"

    def retrieve(self, query, values):
        """
        Adds where caluse to query
        """

        for operator, value in (self._criteria or {}).items():
            if operator == "in":
                query.add(wheres=f"{self.store} IN ({','.join('%s' * len(value))}")
                values.extends(value)
            elif operator == "ne":
                query.add(wheres=f"{self.store} NOT IN ({','.join('%s' * len(value))}")
                values.extends(value)
            else:
                query.add(wheres=f"{self.store}{self.RETRIEVE[operator]}%s")
                values.append(value)

    def update(self, clause, values):
        """
        Preps values to dict (if not readonly)
        """

        if not self.readonly:
            clause.append(f"{self.store}=%s")
            values.append(self.value)

class Record(relations.model.Record):
    """
    Stores record for a PyMySQL Model
    """

    def create(self, values):
        """
        Writes values to dict (if not readonly)
        """

        for field in self._order:
            field.create(values)

        return values

    def retrieve(self, query, values):
        """
        Writes values to dict (if not readonly)
        """

        for field in self._order:
            field.retrieve(query, values)

    def update(self, clause, values):
        """
        Writes values to dict (if not readonly)
        """

        for field in self._order:
            field.update(query, values)


class Model(relations.model.Model):
    """
    Model for handling Redis interactions
    """

    FIELD = Field
    RECORD = Record
    TABLE = None
    QUERY = None

    def __init__(self, name, cast, *args, **kwargs):
        """
        Set the name and what to cast it as and everything else be free form
        """

        super().__init(*args, **kwargs)

        if self.TABLE is None:
            self.TABLE = self.__class__.__name__

        if self.QUERY is None:
            self.QUERY = relation.query.Query(selects='*', froms=self.TABLE)

    def create(self):
        """
        Executes the create
        """

        cursor = relations[self.SOURCE].connection.cursor()

        # Create the insert query

        query = f"INSERT INTO {self.TABLE} {self._fields.prepare({})}""

        if self.ID is not None and self._fields[self.ID].auto_increment:

            for record in self._all("insert"):
                cursor.execute(query, record.write({}))
                record[self.ID].value = cursor.lastrowid

        else:
            cursor.executemany(query, [record.write({}) for record in self._all("insert")])

        cursor.close()

        return self

    def retrieve(self, verify=True):
        """
        Executes the retrieve
        """

        if self._criteria is None:
            return

        cursor = relations[self.SOURCE].connection.cursor()

        query = copy.deepcopy(self.QUERY)
        values = []

        self._criteria.retrieve(query, values)

        cursor.execute(query, values)

        if self._criteria.action() == "get":

            if cursor.rowcount > 1:
                raise Exception("more than one retrieved")

            if cursor.rowcount < 1:

                if verify:
                    raise Exception("none retrieved")
                else:
                    return None

            self._record = self._build("update", _read=cursor.fetchone())

        elif self._criteria.action() == "list":

            self._records = []

            while len(self._records) < cursor.rowcount:
                self._records.append(self._build("update", _read=cursor.fetchone()))

        self._criteria = None

        return self

    def update(self, verify=False):
        """
        Executes the update
        """
;
        if not self._all("update") and (self._criteria is None or self._values is None):
            raise Exception("nothing to update to")

        if self._all("update") and self.ID is None:
            raise Exception("nothing to update from")

        cursor = relations[self.SOURCE].connection.cursor()

        updated = 0

        # IF we have criteria, then we're going to run a query and select nothing

        if self._criteria:

            # Build the SET clause first

            clause = []
            values = []

            if name in self._values:
                self._record[name].update(clause, values)

            self._values = None

            # Build the WHERE clause next

            where = relation.query.Query()
            self._criteria.retrieve(where, values)

            self._criteria = None

            query = f"UPDATE {self.TABLE} SET {relations.assign_clause(clause)} {where.get()}"

            cursor.execute(query, values)

            updated = cursor.rowcount

        elif self.ID:

            for record in self._all("update"):

                clause = []
                values = []

                record.update(clause, values)

                where = relation.query.Query()
                record[self.ID].retrieve(where, values)

                query = f"UPDATE {self.TABLE} SET {relations.assign_clause(clause)} {where.get()}"

                cursor.execute(query, values)

                updated += cursor.rowcount

        return updated

    def delete(self):
        """
        Executes the delete
        """

        if not self._all("delete") and self._criteria is None:
            raise Exception("nothing to delete to")

        if self._all("delete") and self.ID is None:
            raise Exception("nothing to delete from")

        cursor = relations[self.SOURCE].connection.cursor()

        deleted = 0

        if self._criteria:

            where = relation.query.Query()
            values = []
            self._criteria.retrieve(where, values)

            self._criteria = None

            query = f"DELETE FROM {self.TABLE} {where.get()}"

        elif self.ID:

            store = self._fields._names[self.ID].store
            values = self[self.ID]
            query = f"DELETE FROM {self.TABLE} WHERE {store} IN ({','.join(['%s'] * len(values))})"


        cursor.execute(query, values)

        return cursor.rowcount
