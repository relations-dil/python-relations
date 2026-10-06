# Changelog

All notable changes to python-relations are recorded here, newest first. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow [SemVer](https://semver.org/).

## [Unreleased]

Shipping as 0.6.16.

### Added
- `child_inject` on `OneTo` (so `OneToMany` and `OneToOne` too): `relations.OneToMany(Unum, Entity, child_inject="what")` adds a nullable key field to the child, `unum_id`, stored inside the child's `what` dict at `what__relations__unum__id`, so a model shared between apps can take on an optional parent without being edited or getting a column. The dict field has to be named, it isn't touched (no `extract`), and several parents can use the same one. It raises a `ModelError` if the key field already exists, the named field is missing, or it isn't a dict. The relation keeps it as `relation.child_inject`.
- The key is named `<model>_<id>` when the parent and child share a source, else `<parent source>_<model>_<id>` (the source lowercased, `-` as `_`), like `bucket_app_pet_id`. `child_parent_ref` still overrides it.
- `relations.DNS` and `relations.SourceError`: source names have to be dns labels (letters, digits and hyphens, 1 to 63 characters, no leading or trailing hyphen), so they're safe to use in field names. `relations.register` raises a `SourceError` for any other name, and `OneTo` checks the parent's source when the two sources differ.
- A `VERSION` file as the one place the version is set: the `Makefile` reads it and mounts it, `testpypi` and `pypi` pass it as `BUILD_VERSION`, and `setup.py` reads `BUILD_VERSION` or the file.

### Changed
- An empty key means no parent: `Model._relate` returns `None` for a parent when its key is `None`, instead of a placeholder parent that matches nothing. Setting the key later still loads the parent.
- `Record.retrieve` checks an injected field where it's stored, in the field it lives inside, so filtering by an injected key works.
- `Field.write` doesn't store a `None` for an injected field whose path is only dict keys, it leaves the key out (or removes it): a missing key reads back as `None`, and storage has no JSON nulls to trip over. Paths through a list still set the `None`.

## [0.6.15] - 2026-06-08

- Added filtering through many-to-many ties by sibling attributes (for example `bro__name="Tom"`), matching models tied to any sibling that satisfies the criteria.

## [0.6.14] - 2026-06-06

- Added many-to-many relations with `ManyToMany`, a `TIE` model flag, and `SISTERS` and `BROTHERS` relationships, with tie fields that are not stored on the model itself.
- Added tie-aware querying and updating, including bulk creation of ties and tie set operators (`has`, `any`, `all`) in filters.
- Simplified `relations.models()` and moved more behavior into `Source`.

## [0.6.13] - 2023-06-27

- `MockSource` now enforces unique indexes, raising `UniqueError` on violations, and rolls back creates and updates that fail so data stays unchanged.

## [0.6.12] - 2022-11-25

- Switched path handling in `Field` to the external `overscore` package, removing the built-in `split`, `get` and `set` helpers, and added it to the requirements.

## [0.6.11] - 2022-08-05

- Packaging for PyPI: added a license file, a PyPI description (`PYPI.md`), and `testpypi` and `pypi` Makefile targets.
- Updated the README.

## [0.6.10] - 2022-05-01

- Added `relations.unittest.TestCase`, an extended `unittest.TestCase` with helpers such as `assertConsistent`, `assertContains`, `assertFields` and `assertStatusValue`.

## [0.6.9] - 2022-03-14

- Migration diffs now include any extra model attributes that changed, while still handling `fields`, `index` and `unique` separately.

## [0.6.8] - 2022-03-13

- Model attribute and item access now follows double-underscore paths through related models and nested values (for example `model.parent__name`).

## [0.6.7] - 2022-02-18

- Renamed labels to titles: `Labels` became `Titles` (`relations.titles`), the `LABEL` model attribute became `TITLES`, and the field `label` option became `titles`.
- Renamed `Field.labels()` to `Field.title()`.

## [0.6.6] - 2021-11-21

- Packaging change: the distribution was renamed to `python-relations` and the Docker image to `python-relations` after the move to a new GitHub organization.

## [0.6.5] - 2021-11-13

- Renamed `Source` methods for consistency, dropping the `model_` prefix (`init`, `define`, `create`, `count`, `retrieve`, `labels`, `update`, `delete`) and moving the action prefix to the end for field and record hooks (`create_field`, `create_record`); `Migrations` now calls `definition()` and `migration()` on the source.

## [0.6.4] - 2021-11-12

- `Model.query()` now builds queries through the source's `create_query`, `count_query`, `labels_query`, `update_query`, `delete_query` and `retrieve_query` methods and binds the result to the model.
- `MockSource` gained `MockQuery` and `SELECT`, `INSERT`, `UPDATE` and `DELETE` query classes to mimic a real source.

## [0.6.3] - 2021-09-29

- Fixed related models lingering after collation by clearing used parent and child models once they are applied.

## [0.6.2] - 2021-09-28

- Fixed setting a value at a path inside a JSON field when the position already holds a different value.

## [0.6.1] - 2021-09-26

- `Field.export()` now returns a deep copy of the value, so changing an export no longer affects the field.

## [0.6.0] - 2021-09-05

- Removed the bundled `relations.sql` and `relations.query` modules in preparation for the separate relations-sql package.
- Reworked filter operators: removed `ne` in favor of `not_` prefixed operators, added `start` and `end`, and added `Field.split()` for parsing double-underscore criteria with numeric and negative path parts.

## [0.5.7] - 2021-09-01

- Added `Model.query()` and `Source` hooks (`query_create`, `query_count`, `query_retrieve`, `query_labels`, `query_update`, `query_delete`) so a source can expose the query it would run.
- `model_create`, `model_retrieve`, `model_update` and `model_delete` on `Source` now accept extra arguments.

## [0.5.6] - 2021-08-27

- Added `set` as a field kind, with options checked per member, and made multi-value filters accept sets, lists and tuples.
- Added errors when a path key or index does not match the structure being traversed.

## [0.5.5] - 2021-08-22

- Added the list field operators `has`, `any` and `all` for filtering list values.

## [0.5.4] - 2021-08-12

- Filtering a field with `eq` or `ne` against `None` is now treated as a `null` check.

## [0.5.3] - 2021-08-12

- Added `Migrations.list()` and `Migrations.load()` plus matching `Source.list()` and `Source.load()` so applied migrations can be listed in pairs and verified against a source.

## [0.5.2] - 2021-08-08

- Added migrations: `Migrations` and `MigrationsError`, which compare the models' definitions to a saved snapshot in a `ddl` directory and generate definition and migration files, and `Source.migrate` to apply them (implemented for `MockSource`).
- Added `Field.define()` to produce a field's definition, and removed the old `define` handling in favor of building from the field list.

## [0.5.1] - 2021-06-16

- Added `Field.apply(path, value)` and `Field.access(path)` for setting and reading values at a path inside `list` and `dict` fields; models accept the same double-underscore paths as attributes (for example `model.data__key`).
- Fields created from `init` now read values by path rather than only top-level keys.

## [0.5.0] - 2021-06-14

- Reworked `extract` so a field can extract several values (a string, list or dict of paths to kinds) instead of a single one, and extract fields are no longer automatically `auto`.
- Unique and index definitions can now reference paths inside JSON fields, and `like` can search within a path.

## [0.4.9] - 2021-06-13

- Changes to object fields are now detected by comparing exports against the `original` value, using a new `Field.delta()`.
- Replaced `replace` with `auto` and `refresh` field options, and added `Field.create` and `Field.retrieve` hooks; `extract` fields are now marked `auto` instead of read-only.

## [0.4.8] - 2021-06-13

- Added `export()` on `Field`, `Record` and `Model` to convert values to plain data.

## [0.4.7] - 2021-06-02

- Added `Model.count()` (also returned by `len()` on a retrieve-many model) with `MockSource.model_count`.

## [0.4.6] - 2021-05-31

- Added `inject` fields to write a field's value into a path within another JSON field.
- Added full support for negative list indexes, and fixed updates of object and JSON values.

## [0.4.5] - 2021-05-30

- Added `extract` fields, which are read-only fields filled from values inside another list or dict field; models check that extracted fields exist and `MockSource` stores them.

## [0.4.4] - 2021-05-29

- Added storing custom objects in JSON fields through the `attr`, `init` and `label` field options, so a field of any class can be exported to and rebuilt from a dict.
- Labels can now be pulled from values inside JSON fields, and models can be created from a dict.

## [0.4.3] - 2021-05-27

- Added filtering inside `list` and `dict` fields using nested paths in filter names, with new `notlike` and `null` operators.
- Fields of custom types now raise a `FieldError` if they have no `attr`.

## [0.4.2] - 2021-05-11

- Added `Labels` (`relations.Labels`) and `Model.labels()` to build id-to-label lookups, following parent relations.
- Added a `format` attribute on `Field` and `labels` support in `Source` and `MockSource`.

## [0.4.1] - 2021-05-07

- Added a `LABEL` attribute on `Model` that names the fields forming its label; the default unique index now comes from it.
- Added a `like` filter for fuzzy matching, new `Field.like` and `Field.match` support, and the operators `gte`, `lte` and `like` (renaming `ge` and `le`).
- Added `overflow` tracking on models and a `CHUNK` setting that caps related-model lookups, plus relation access (`model[key]`) for parent and child fields.

## [0.4.0] - 2021-05-01

- Preparation for labels: the default unique index built from the model's fields is now named `label`.

## [0.3.12] - 2021-04-18

- Added a `TITLE` attribute on `Model`, defaulting to the class name, from which the default `NAME` is derived.

## [0.3.11] - 2021-03-30

- Added a `per_page` argument to `Model.limit()`.

## [0.3.10] - 2021-03-30

- Default model names are now converted from CamelCase to underscored (for example `MyModel` becomes `my_model`) via `Model.underscore()`.
- `Model.sort()` now raises an error on a single-record model and does nothing when called without arguments.

## [0.3.8] - 2021-03-09

- Reserved `limit` as a field name.

## [0.3.7] - 2021-02-28

- A field created from a list of options now defaults to the first option.

## [0.3.6] - 2021-02-23

- `limit()` now accepts zero, and an empty result set no longer raises a "no records" error.

## [0.3.5] - 2021-02-23

- Added `Model.limit(limit, start, page)` to limit and page retrieved records, with `MockSource` support.

## [0.3.4] - 2021-02-21

- Sort fields are now normalized with a `+` or `-` prefix, with unknown sort fields raising a `ModelError`; the logic is shared between `ORDER` and `sort()`.

## [0.3.3] - 2021-02-21

- Added `Model.sort()` for sorting results, a `ORDER` class attribute for a default sort order (defaulting to the model's unique index), and support in `MockSource`.
- Reserved `sort` as a field name.

## [0.3.2] - 2021-02-20

- Added bulk creation with `Model.bulk()`, using new `_bulk` and `_size` options to insert records in batches.
- Reserved `bulk` and `thy` as field names.

## [0.3.1] - 2021-02-05

- Renamed the internal `Model._thyself()` to the public `Model.thy()`.

## [0.3.0] - 2021-02-05

- Added `relations.models(module, from_base=None)` to find all `Model` subclasses in a module.

## [0.2.8] - 2021-01-19

- `list` and `dict` fields are now always non-`None` and default to their own type, even when `none` is set explicitly.
- Dropped an unused import in `setup.py`.

## [0.2.7] - 2021-01-18

- Unique `str` fields created by default for a model's index are now required (not `None`) unless `none` was set explicitly.

## [0.2.6] - 2021-01-18

- Added proper support for `list` and `dict` fields, which default to an empty value of their type and no longer allow `None`.
- Renamed the `make verify` target to `make setup` in the Makefile and Jenkinsfile.

## [0.2.5] - 2021-01-17

- A `replace` field is no longer reset to its default on update if it was changed explicitly; `MockSource` follows the same rule.

## [0.2.4] - 2021-01-17

- Added a `replace` option on `Field` that resets the value to its default on update.
- Added `bool` as a field kind; a single boolean field argument now sets `none`, and a trailing dict argument is treated as keyword arguments.

## [0.2.3] - 2021-01-17

- Added `UNIQUE` and `INDEX` class attributes on `Model` for declaring unique and regular indexes, with a default unique index derived from the first `int` or `str` fields, and an error when an index references an unknown field.

## [0.2.2] - 2021-01-17

- Added field validation and reorganized the package into flat modules (`relations.field`, `relations.model`, `relations.record`, `relations.relation`, `relations.source`), all still importable from `relations`.
- `Field` gained `none`, `options` and `validation` attributes, replacing `not_null`.

## [0.2.1] - 2021-01-08

- `Source` now stores any extra keyword arguments passed to its constructor as attributes on the source.

## [0.2.0] - 2021-01-04

- Removed the bundled PyMySQL, PostgreSQL, Redis and RESTful modules so the package contains only the core `Model`, `Field`, `Record`, `Relation` and `MockSource`.
- Added docstrings, brought the code to a clean pylint pass, reached full test coverage, and added README docs and version handling in the Makefile and `setup.py`.

## [0.1.0] - 2021-01-04

- Initial release of the backend-agnostic data layer: `Model`, `Field`, `Record` and `Relation` (`OneToOne`, `OneToMany`) classes under `relations.model`, with a `Source` base class and source registration via `relations.register()` and `relations.source()`.
- Included a `MockSource` for testing in `relations.unittest`, plus early SQL support (`relations.sql`, `relations.query`) with PyMySQL and PostgreSQL (`psycopg2`) sources, a Redis module and a RESTful resource module.
- Added function defaults for fields, closed connections the library created, and set up the Makefile, Dockerfile, Jenkinsfile, pylint config and install packaging.
