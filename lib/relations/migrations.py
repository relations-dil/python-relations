"""
Data definition module
"""

import os
import glob
import json
import datetime

import relations

class MigrationsError(Exception):
    """
    General migrations error
    """


class Migrations:
    """
    Class for handling Migrations changes
    """

    def __init__(self, directory="ddl"):

        self.directory = directory

    def current(self):
        """
        Get the previous snapshot
        """

        if not os.path.exists(f"{self.directory}/definition.json"):
            return {}

        with open(f"{self.directory}/definition.json", "r") as current_file:
            return json.load(current_file)

    @staticmethod
    def define(models):
        """
        Get definitions
        """

        return {model["name"]: model for model in [model.thy().define() for model in models]}

    @staticmethod
    def rename(name, adds, removes, renames):
        """
        Get which were actually rename
        """

        if not adds or not removes:
            return

        print(f"Please indicate if any {name} were renamed:")

        for remove in removes:
            remaining = [add for add in adds if add not in renames.values()]
            if not remaining:
                break
            for index, add in enumerate(remaining):
                print(f"[{index + 1}] {add}")
            rename = int(input(f"Which was {remove} renamed to? (return if none)") or '0')

            if 0 < rename <= len(remaining):
                renames[remove] = remaining[rename - 1]

        for remove, add in renames.items():
            removes.pop(removes.index(remove))
            adds.pop(adds.index(add))

    @staticmethod
    def lookup(name, fields):
        """
        Looks up a field by name
        """

        for field in fields:
            if name == field['name']:
                return field

        return None

    @staticmethod
    def field(current, define):
        """
        Find the differences in a field
        """

        migration = {}

        for attr in set(current.keys()).union(define.keys()):
            if current.get(attr) != define.get(attr):
                migration[attr] = define.get(attr)

        return migration

    @classmethod
    def fields(cls, model, current, define):
        """
        Find the differences in fields
        """

        migration = {}

        current_names = [field["name"] for field in current]
        define_names = [field["name"] for field in define]

        add = [name for name in define_names if name not in current_names]
        remove = [name for name in current_names if name not in define_names]
        rename = {}

        cls.rename(f"{model} fields", add, remove, rename)

        if add:
            migration["add"] = [field for field in define if field["name"] in add]

        if remove:
            migration["remove"] = remove

        change = {}

        for current_field in current:
            define_field = cls.lookup(rename.get(current_field['name'], current_field['name']), define)
            if define_field is not None and current_field != define_field:
                change[current_field['name']] = cls.field(current_field, define_field)

        if change:
            migration["change"] = change

        return migration

    @classmethod
    def indexes(cls, model, kind, current, define):
        """
        Find the differences in indexes
        """

        migration = {}

        add = [name for name in sorted(define.keys()) if name not in current]
        remove = [name for name in sorted(current.keys()) if name not in define]
        rename = {}

        cls.rename(f"{model} {kind}", add, remove, rename)

        if add:
            migration["add"] = {name: define[name] for name in add}

        if remove:
            migration["remove"] = remove

        if rename:

            for current_name, define_name in rename.items():
                if current[current_name] != define[define_name]:
                    raise MigrationsError(f"{model} {kind} {current_name} and {define_name} must have same fields to rename")

            migration["rename"] = rename

        return migration

    @classmethod
    def model(cls, current, define):
        """
        Find the differences in a model
        """

        model = f"{current['name']}/{define['name']}" if current['name'] != define['name'] else current['name']

        migration = {}

        for attr in set(["name", "title", "id"] + list(current.keys()) + list(define.keys())):
            if attr not in ["fields", "index", "unique"]:
                if current.get(attr) != define.get(attr):
                    migration[attr] = define.get(attr)

        if current["fields"] != define["fields"]:
            migration["fields"] = cls.fields(model, current["fields"], define["fields"])

        for attr in ["unique", "index"]:
            kind = "unique indexes" if attr == "unique" else "indexes"
            if current.get(attr) != define.get(attr):
                migration[attr] = cls.indexes(model, kind, current.get(attr, {}), define.get(attr, {}))

        return migration

    @classmethod
    def models(cls, current, define):
        """
        Find the differences in models
        """

        migration = {}

        add = [name for name in sorted(define.keys()) if name not in current]
        remove = [name for name in sorted(current.keys()) if name not in define]
        rename = {}

        cls.rename("models", add, remove, rename)

        if add:
            migration["add"] = {name: define[name] for name in add}

        if remove:
            migration["remove"] = {name: current[name] for name in remove}

        change = {}

        for name in current:
            define_model = define.get(rename.get(name, name))
            if define_model is not None and current[name] != define_model:
                change[name] = {
                    "definition": current[name],
                    "migration": cls.model(current[name], define_model)
                }

        if change:
            migration["change"] = change

        return migration

    def generate(self, models):
        """
        Updates a Migrations change
        """

        current = self.current()
        define = self.define(models)

        if current:

            if current == define:
                return False

            migration = self.models(current, define)

            stamp = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S-%f')

            os.rename(f"{self.directory}/definition.json", f"{self.directory}/definition-{stamp}.json")

            with open(f"{self.directory}/migration-{stamp}.json", "w") as migration_file:
                json.dump(migration, migration_file, indent=4, sort_keys=True)

        with open(f"{self.directory}/definition.json", "w") as current_file:
            json.dump(define, current_file, indent=4, sort_keys=True)

        return True

    def convert(self, name):
        """
        Converts definitions and migrations to source definitions and migrations based on a source name
        """

        source = relations.source(name)

        source_path = f"{self.directory}/{source.name}/{source.KIND}"

        os.makedirs(source_path, exist_ok=True)

        for file_path in glob.glob(f"{self.directory}/*.json"):

            file_name = file_path.split("/")[-1]

            if file_name.startswith("definition"):
                source.definition(file_path, source_path)

            elif file_name.startswith("migration"):
                source.migration(file_path, source_path)

    def list(self, name):
        """
        List out the migrations pairs for a source
        """

        source = relations.source(name)

        source_path = f"{self.directory}/{source.name}/{source.KIND}"

        return source.list(source_path)

    def load(self, name, file_name):
        """
        Load a file from a source
        """

        source = relations.source(name)

        return source.load(f"{self.directory}/{source.name}/{source.KIND}/{file_name}")

    def apply(self, name):
        """
        Applies source definitions and migrations based on a source name
        """

        source = relations.source(name)

        source_path = f"{self.directory}/{source.name}/{source.KIND}"

        return source.migrate(source_path)
