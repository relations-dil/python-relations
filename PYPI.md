# relations-dil

DB/API Modeling

Relations is designed to be a simple, straight forward, flexible DIL (data interface layer).

Quite different from other DIL's, it has the singular, microservice based purpose to:
- Create models with very little code, independent of backends
- Create CRUD API with a database backend from those models with very little code
- Create microservices to use those same models but with that CRUD API as the backend

Ya, that last one is kinda new I guess.

Say we create a service, composed of microservices, which in turn is to be consumed by other services made of microservices.

You should only need to define the model once. Your conceptual structure is the same, to the DB, the API, and anything using that API. You shouldn't have say that structure over and over. You shouldn't have to define CRUD endpoints over and over. That's so boring, tedious, and unnecessary.

Furthermore, the conceptual structure is based not the backend of what you've going to use at that moment of time (scaling matters) but on the relations, how the pieces interact. If you know the structure of the data, that's all you need to interact with the data.

So with Relations, Models and Fields are defined independent of any backend, which instead is set at runtime. So the API will use a DB, everything else will use that API.

This is package is just a piece of that whole process, the base abstract classes, etc. But with a mock source, you can see how it all works.

# Example

```python

import relations

# The SOURCE in a model is a string, used to access a source in Relations's global registry

class Base(relations.Model):
    SOURCE = "example"

# The Models automatically have the same SOURCE by using this Base

class Unit(Base):
    id = int
    name = str

class Test(Base):
    id = int
    unit_id = int  # Relations aren't defined here, but outside the models
    name = str

# Creation a Relation from unit.id to test.unit_id (default)

relations.OneToMany(Unit, Test)

# This defines the "example" source to be an in memory store

relations.unittest.MockSource("example")

# Create Unit named yep and store

Unit("yep").create()

# Query a single Unit with the name "yep" and access its id
Unit.one(name="yep").id # 1

# Create two Units, named people and stuff, because name is the first non readdonly field
Unit([["people"], ["stuff"]]).create()

# Retrieve a single Unit with name stuff, and set the name to "things" (but don't save)
unit = Unit.one(name="stuff").set(name="things")

# Save the update (returns number of records updated))
unit.update() # 1

# Retrieve a single Unit with id 2, and set the name to "thing"
unit = Unit.one(2)
unit.name = "thing"

# Add a child test with name "more" (first non readonly that's not already set)

unit.test.add("moar")
unit.update()

# Find all the Tests with a parent Unit with name "thing", and an id greater than 0
tests = Test.many(unit__name="thing", id__gt=0)
tests[0].name # "moar"
```
