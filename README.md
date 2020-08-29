# python-relations
DB/API Modeling

# Models

## MySQL

The defintion for DB model has two purposes. First to generate code to create and alter tables. Second to specify how to read and write to the databse.

```python

# Simple as

class Person(relations.MySQLModel):
    id = relations.MySQLField(int,autoincrement=True)
    name = str
    data = dict

# Same as

class Person(relations.MySQLModel):

    table = "person"

    query = relations.Query(
        select={
            "id": "id"
            "label": "name"
        },
        from=table,
        order_by="name"
    )

    member = relations.Member(table=table)

    id = relations.MySQLField(int, autoincrement=True)
    name = str
    data = dict

    special = relations.Field(virtual=True) // Either works
    special = relations.Field(virtual=data) // Either works

```

## API

These are just defaults and overriable

- `OPTIONS /{entity}/` - Get fields to create with
  - request `{"entity": *}`
  - response `{"entity": [fields], errors: T/F, "ready": T/F}`
- `POST /{entity}/` - Create
  - request `{"entity": *}`
  - response `{"entity": *}`
- `GET /{entity}/` - Search
  - request
    - Can be in query `?field=value`
        - Split in/not in by ','
    - Can be in body `{"query": {"field": value}, "fields": []}` (fields to return)
    - fields for querying
        - field - equals
        - field__not - not equals
        - field__in - IN ()
        - field__not_in - NOT IN ()
        - field__gt - >
        - field__gte - >=
        - field__lt - <
        - field__lte - <=
        - might need something more advanced
    rsponse `{"entities": *}`
- `GET /{entity}/{id}` - Retrieve
  - response `{"entity": *}`
- `OPTIONS /{entity}/{id}` - Get fields to update with
  - request `{"entity": *}`
  - response `{"entity": [fields], errors: T/F, "ready": T/F}`
- `PATCH /{entity}/{id}` - Update
  - request `{"entity": *}`
  - response `{"entity": *}`
- `DELETE /{entity}/{id}` - Delete

Strings for URL will be format strings: - `/{entity}/{id}` and overriable

Strings for operations will be overridable too. __ etc.


## Redis

- `SET /{entity}/{id}` - Create/Update
- `GET /{entity}/*`  - List
- `GET /{entity}/{id}` - Retrieve
- `DEL /{entity}/{id}` - Delete

Redis will have an format string to specify it's key like `/{entity}/{id}`.

For searching, any field not specified will be replaced with '*'

# Members

Member defintions are used to query from other services. This only needing for models with fields with other services.

## MySQL

- query object
- option field/calculation
- label field/calculation

## API

- endpoint - uses list
- fields (optional)
- option - field/format string
- label - field/format string

## Redis

- query string
- option field/calculation
- label field/calculation

# Fields

Fields are put on models as a way of interacting in code. These should be enough to create fields in the database, but not too strict, no stricter than where they're going. If you're writing code, you shouldn't really need to check much at run time.

# Inputs

Inputs are put on models (can be derived from fields) as a way of interacting via the API.  This can be much heavier on validation much it's expected to interact with a user.

# Code (using people as an example)

## API

class Person(Model):

    query = Query()

    member = Member(table="person")

    id = MySQLField(int,autoincrement=True)
    name = str
    document = dict


class People(Relations):

    class Person:

        query = Query()

        class Member(MySQLMember):
            table = "person"

        class Fields:



    class Members:

        class Person(MySQLMember):


    class Models:

        Person(MySQLModel):

          member = Members.Person

          class Fields:


Stuff(Relations):

    People(MySQLMember):
