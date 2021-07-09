"""
Data definition module
"""

import os
import json
import datetime

class Migrations:
    """
    Class for handling Migrations changes
    """

    def __init__(self, classes, directory="ddl"):

        self.classes = classes
        self.directory = directory

    def current(self):
        """
        Get the previous snapshot
        """

        if not os.path.exists(f"{self.directory}/definition.json"):
            return {}

        with open(f"{self.directory}/definition.json", "r") as current_file:
            return json.load(current_file)

    def define(self):
        """
        Get definitions
        """

        return {model["name"]: model for model in [cls.thy().define() for cls in self.classes]}

    @staticmethod
    def rename(name, addeds, removeds, renameds):
        """
        Get which were actually renamed
        """

        if not addeds or not removeds:
            return

        print(f"Please indicate if any {name} were renamed:")

        for removed in removeds:
            remaining = [added for added in addeds if added not in renameds.values()]
            if not remaining:
                break
            for index, added in enumerate(remaining):
                print(f"[{index + 1}] {added}")
            renamed = int(input(f"Which was {removed} renamed to? (return if none)") or '0')

            if 0 < renamed <= len(remaining):
                renameds[removed] = remaining[renamed - 1]

        for removed, added in renameds.items():
            removeds.pop(removeds.index(removed))
            addeds.pop(addeds.index(added))

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

        added = [name for name in define_names if name not in current_names]
        removed = [name for name in current_names if name not in define_names]
        renamed = {}

        cls.rename(f"{model} fields", added, removed, renamed)

        if added:
            migration["added"] = [field for field in define if field["name"] in added]

        if removed:
            migration["removed"] = [field for field in current if field["name"] in removed]

        changed = {}

        for current_field in current:
            define_field = cls.lookup(renamed.get(current_field['name'], current_field['name']), define)
            if define_field is not None and current_field != define_field:
                changed[current_field['name']] = cls.field(current_field, define_field)

        if changed:
            migration["changed"] = changed

        return migration

    @classmethod
    def indexes(cls, model, kind, current, define):
        """
        Find the differences in indexes
        """

        migration = {}

        added = [name for name in sorted(define.keys()) if name not in current]
        removed = [name for name in sorted(current.keys()) if name not in define]
        renamed = {}

        cls.rename(f"{model} {kind}", added, removed, renamed)

        if added:
            migration["added"] = {name: define[name] for name in added}

        if removed:
            migration["removed"] = {name: current[name] for name in removed}

        if renamed:

            for current_name, define_name in renamed.items():
                if current[current_name] != define[define_name]:
                    raise Exception(f"{model} {kind} {current_name} and {define_name} must have same fields to rename")

            migration["renamed"] = renamed

        return migration

    @classmethod
    def model(cls, current, define):
        """
        Find the differences in a model
        """

        model = f"{current['name']}/{define['name']}" if current['name'] != define['name'] else current['name']

        migration = {}

        for attr in ["name", "title", "id"]:
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

        added = [name for name in sorted(define.keys()) if name not in current]
        removed = [name for name in sorted(current.keys()) if name not in define]
        renamed = {}

        cls.rename("models", added, removed, renamed)

        if added:
            migration["added"] = {name: define[name] for name in added}

        if removed:
            migration["removed"] = {name: current[name] for name in removed}

        changed = {}

        for name in current:
            define_model = define.get(renamed.get(name, name))
            if define_model is not None and current[name] != define_model:
                changed[name] = {
                    "definition": current[name],
                    "migration": cls.model(current[name], define_model)
                }

        if changed:
            migration["changed"] = changed

        return migration

    def generate(self):
        """
        Updates a Migrations change
        """

        current = self.current()
        define = self.define()

        if current == define:
            return False

        migration = self.models(current, define)

        with open(f"{self.directory}/migration_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.json", "w") as migration_file:
            json.dump(migration, migration_file, indent=4, sort_keys=True)

        with open(f"{self.directory}/definition.json", "w") as current_file:
            json.dump(define, current_file, indent=4, sort_keys=True)

        return True
