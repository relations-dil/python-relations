"""
Module for intersting with Redis
"""

import json
import redis
import relations
import relations.model

class Source(relations.Source)

    prefix = None
    connection = None

    def __init__(self, name, host, port=None, prefix=""):

        super().__init__(name)

        self.prefix = prefix
        self.connection = redis.Redis(host=host, port=port))

class Model(relations.Model):
    """
    Model for handling Redis interactions
    """

    def _key(self, record):

        return f"/{relations[self.SOURCE].prefix}/{self.NAME}/{record[self.ID].value}"

    def _keys(self, record):

        id = (record[self.ID].criteria or {}).get("eq", "*")

        return relations[self.SOURCE].connection.keys(f"/{relations[self.SOURCE].prefix}/{self.NAME}/{id}")

    def read(self, key, record):
        """
        Sets data
        """

        relations[self.SOURCE].connection.set(key, json.dumps(record._write({})))

    def write(self, key):
        """
        Gets data
        """

        values = relations[self.SOURCE].connection.get(self._key({self.ID: id}))

        if values is not None:
            values = json.loads(values)

        return values

    def create(self):
        """
        Executes the create
        """

        for record in self._all("create"):
            self.write(self._key(record), record)

        return self

    def retrieve(self, verify=True):
        """
        Executes the retrieve
        """

        if self._criteria is None:
            return

        keys = self._keys(self._criteria)

        if self._criteria.action() == "get":

            if len(keys) > 1:
                raise Exception("more than one retrieved")

            if len(keys) < 1:

                if verify:
                    raise Exception("none retrieved")
                else:
                    return None

            self._record = self._build("update", _read=self.read(keys[0]))

        elif self._criteria.action() == "list":

            self._records = []

            for key in keys:
                values = self.read(keys)
                if self._criteria.match(values)
                    self._records.append(self._build("update", _read=values))

        self._criteria = None

        return self

    def update(self):
        """
        Executes the update
        """

        if self._criteria:

            self.retrieve()
            self.set(**self._values)

        for record in self._all("update"):
            self.write(self._key(record), record)

        return len(records)

    def delete(self):
        """
        Executes the delete
        """

        if self._criteria:

            keys = self._keys(self._criteria)

            self._criteria = None

            for key in keys:
                relations[self.SOURCE].connection.delete(key)

            return len(keys)

        for record in self._all("delete"):
            relations[self.SOURCE].connection.delete(self._key(record))

        return len(records)
