# python-relations

DB/API Modeling

Relations is designed to be a simple, straight forward, flexible DAL.

Quite different from other DAL's, it has the singular, microservice based purpose to:
- Create models with very little code, independent of backends
- Create CRUD API with a database backend from those models with very little code
- Create microservices to use those same models but with that CRUD API as the backend

Take a second, because that's probably a new idea to some of you.

Say we create a service, composed of microservices, which in turn is to be consumed by other services made of microservices.

You should only need to define the model once. Your conceptual structure is the same, to the DB, the API, and anything using that API. You shouldn't have say that structure over and over. YOu shouldn't have to define CRUD endpoints over and over. That's so boring, tedious, and unnecessary.

Furthermore, the conceptual structure is based not the backend of what you've going to use at that moment of time (scaling matters) but on the relations, how the pieces interact. If you know the structure of the data, that's all you need to interact with the data.

So with Relations, Models and Fields are defined independent of any backend, which instead is set at runtime. So the API will use a DB, everything else will use that API.

# Example

This package specifically can't interact with any backend. Look to these:
- https://github.com/gaf3/python-relations-pymysql - MySQL backend
- https://github.com/gaf3/python-relations-psycopg2 - PostgreSQL backend
- https://github.com/gaf3/python-relations-restful - RESTful, create the CRUD API or use the CRUD API as a backend

I'm also working on Redis and SQLLite but they're not ready yet.

This package does come with a MockSource, and in-memory store.

Mainly used for unittesting, you can use it just to try things out.

```python

import time
import relations
import relations.unittest

# The SOURCE in a model is a string, used to access a source in Relations global registry

class BaseModel(relations.Model):
    SOURCE = "your-source"

# Using this BaseModel has the following Models automatically have the same SOURCE

class Unit(BaseModel):
    id = int
    name = str

class Test(BaseModel):
    id = int
    unit_id = int  # Relations aren't define here, but outside the models
    name = str

class Case(BaseModel):
    id = int
    test_id = int
    name = str


# Relations are defined assuming the parent field is (model)_(id) This is overriable.

relations.OneToMany(Unit, Test) # Creation a Relation from unit.id to test.unit_id
relations.OneToOne(Test, Case)  # Creation a Relation from test.id to case.test_id

# This defines the "your-source" to be an in memory store

relations.unittest.MockSource("your-source")

# Create Unit named yep and store (corete())

Unit("yep").create()

# Query a single Unit with the name "yep" and check it's id
self.assertEqual(Unit.one(name="yep").id, 1)

# Create to Units, named people and stuff, because name is the first non readdonly field
Unit([["people"], ["stuff"]]).create()

# Retrieve a single Unit with id 2, and set the name to "things" (but don't save)
unit = Unit.one(id=2).set(name="things")

# Save the update and see how many were updated
self.assertEqual(unit.update(), 1)

# Retrieve a single Unit with id 2, and set the name to "thing"
unit = Unit.one(2)
unit.name = "thing"

# Add a child test with name "more" (first non readonly that's not already set)
# Then grab the last test [-1] and add a case with name "lass"
unit.test.add("moar")[-1].case.add("lass")

# Check that one Unit was updated
self.assertEqual(unit.update(), 1)
self.assertEqual(unit.name, "thing")

# Verify the id's and names
self.assertEqual(unit.test[0].id, 1)
self.assertEqual(unit.test[0].name, "moar")
self.assertEqual(unit.test[0].case.id, 1)
self.assertEqual(unit.test[0].case.name, "lass")

# Find all the Tests with a parent Unit with name "thing", child case with name "lass" and an id greater than 0
tests = Test.many(unit__name="thing",case__name="lass", id__gt=0)
```

# Field

Defining fields can be done in lots of clever ways, which is probably a bad idea but that's what I'm going with currently.

```python
relations.Field(

    kind = None       # Data class to cast values as or validate

    name = None       # Name used in models
    store = None      # Name to use when reading and writing

    default = None    # Default value
    none = None       # Whether to allow None (nulls)
    options = None    # Possible values (if not None)
    validation = None # How to validate values (if not None), can regex or method
    readonly = None   # Whether this field is readonly
    length = None     # Length of the value

    value = None      # Value of the field
    changed = None    # Whether the values been changed since creation, retrieving
    replace = None    # Whether to replace the value with default on update
    criteria = None   # Values for searching
)
```

The odd creation of a Field is to allow for cleverness. Here's some clever defintions and their full equivlaents


```python
class Example:

    # Field(int, name="id", none=True)
    id = int

    # If the second argument is a bool and the kind isn't,
    # it indicates whether to allow None's

    # Field(str, name="name", none=False)
    name = str, False

    # If the second argument matches the kind, it is a default
    # value and assumes not to allow None's

    # Field(float, name="degreed", default=1.23, none=False)
    degreed = float, 1.23

    # If the second argument matches the kind, it is a default
    # value and assumes not to allow None's (because bool here)

    # Field(bool, name="flag", default=False, none=False)
    name = bool, False

    # If the first arg is a list, it'll use the first values type
    # as kind, and use the list as options to validate against

    # Field(str, name="status", options=["pass", "fail"], none=False)
    status = ["pass", "fail"]

    # If the last arg is dict, it casts it a kwargs

    # Field(str, name="status", options=["pass", "fail"], none=True)
    status = ["pass", "fail"], {"none": True}

    # If you provide a function as the first arg, it'll call the function
    # and take teh return value as the type. It'll also call the function
    # for teh field value each time you create it.

    # Field(flaat, name="create_ts", default=time.time, none=False)
    create_ts = time.time

    # If you provide an argument after the default, it'll assume it's the
    # replace bool, which if true uses the default when updating

    # Field(flaat, name="update_ts", default=time.time, replace=True, none=False)
    update_ts = time.time, True

    # All values are always cast as the kind, so even though time is floar,
    # you can easily use it as int by being explicit

    # Field(int, name="update_ts", default=time.time, replace=True, none=False)
    update_ts = int, time.time, True

    # If you want to just use the class instantiation, you do that.
    # I just like to make daring (something bad) decisions. Just remember
    # to exlcude the name. That'll be added later in ModelIdentity.

    # Field(int, name="update_ts", default=time.time, replace=True, one=False)
    update_ts = Field(int, default=time.time, replace=True, none=False)
```

# Model

```python
variable	=	call	action	mode	description
model	=	Model()	create	one	make single record
models	=	Model([])	create	many	make multiple records
model	=	Model().create()	update	one	create single record at source
model	=	Model([]).create()	update	one	create multiple records at source
model	=	Model.one()	retrieve	one	ready to retreieve single record, will in context
model	=	Model.one().retrieve()	update	one	retrieve single record, exception if not found
model	=	Model.one().retrieve(False)	update	one	retrieve single record, None if not found
models	=	Model.many()	retrieve	many	ready to retrieve multiple records, will in context
models	=	Model.many().retrieve()	update	many	retrieve multiple records
model	=	Model.one().retrieve().set()	update	one	retrieve a record and change values
updated	=	Model.one().retrieve().set().update()	update	one	retrieve a record, change values, update source
model	=	Model.one().set()	update	one	ready to update, will in context, return count of updated
updated	=	Model.one().set().update()	update	one	update at source, return count of updated
models	=	Model.many().retrieve().set()	update	many	retrieve records and change values
updated	=	Model.many().retrieve().set().update()	update	many	retrieve records, change values, update source
models	=	Model.many().set()	update	many	ready to update, will in context, return count of updated
updated	=	Model.many().set().update()	update	many	update at source, return count of updated
deleted	=	Model.one().retrieve().delete()	None	one	retrieve a record, then delete, return count of deleted
deleted	=	Model.one().delete()	None	one	will delete a record on source side and return count of deleted
deleted	=	Model.many().retrieve().delete()	None	many	retrieve records, return count of deleted
deleted	=	Model.many().delete()	None	many	will update records on source side and return count of deleted
```

# Parent

```python
call	action	mode	parent	description
Model().parent	retrieve	one	Yes	retrieve single record, fail if not found
Model([]).parent	retrieve	many	Yes	retrieve records, fail if no child fields not set
Model.one().parent	retrieve	one	Yes	induces retrieve on model, ready to retrieve on parent
Model.many().parent	retrieve	many	Yes	induces retrieve on model, ready to retrieve on parent
```

# Child

```python
call	action	mode	parent	description
Model().child	create	many	Yes	make multiple records (starts as [])
Model().child	create	one	Yes	make single record (starts as None)
Model().child.add()	create	many	Yes	adds a record to the list
Model().child.add()	create	one	Yes	builds a single record
Model([]).child	create	many	Yes	list of children models, ready to retrieve
Model([]).child	create	one	Yes	list of children models, ready to retrieve
Model().create()	update	many	Yes	will execute child creates
Model().create()	update	one	Yes	will execute child creates
Model([]).create()	update	many	Yes	will execute child creates
Model([]).create()	update	one	Yes	will execute child creates
Model.one().child	update	many	Yes	will induce retrieve of model, ready to retrieve of child
Model.one().child	update	one	Yes	will induce retrieve of model, ready to retrieve of child
Model.one().child.add()	update	many	Yes	will induce retrieve of model and child, add to child
Model.one().child.add()	update	one	Yes	will induce retrieve of model and child, add to child
Model.many().child	update	many	Yes	will induce retrieve of model, list of children models, ready to retrieve
Model.many().child	update	one	Yes	will induce retrieve of model, list of children models, ready to retrieve
Model.one().update()	update	many	Yes	will execute child creates/updates/deletes
Model.one().update()	update	one	Yes	will execute child creates/updates/deletes
Model.many().update()	update	many	Yes	will execute child creates/updates/deletes
Model.many().update()	update	one	Yes	will execute child creates/updates/deletes
Model.one().delete()	None	many	None	will execute model deletes, not children
Model.one().delete()	None	one	None	will execute model deletes, not children
Model.many().delete()	None	many	None	will execute model deletes, not children
Model.many().delete()	None	one	None	will execute model deletes, not children
```
