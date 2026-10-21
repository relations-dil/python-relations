# python-relations

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

# Security

`relations.security` holds a model's verbs (create, count, retrieve, titles, update and delete) to rules. Put `Secure` in front of the model, give it a policy, and say who is acting:

```python

import relations
import relations.security

class Doc(relations.security.Secure, Base):
    id = int
    owner = str
    title = str
    locked = bool, False

# Rules by model name and verb. A scope is filter kwargs, or a function of the actor that gives them

relations.security.POLICY = relations.security.Policy({
    "doc": {
        "retrieve": relations.security.Rule(scope=lambda actor: {"owner": actor}),
        "create": relations.security.Rule(scope=lambda actor: {"owner": actor}),
        "update": relations.security.Rule(scope=lambda actor: {"owner": actor, "locked": False})
    }
})

with relations.security.acting("pat"):
    Doc.many().title                 # only pat's
    Doc(owner="sam", title="x").create()  # Denied
```

- No actor, or no rule, is no (`Denied`). `count` and `titles` use `retrieve`'s rule unless given their own.
- What an actor can't read is a miss, as if it weren't there. What they can read but can't write is `Denied`, so they're told.
- Scopes on the model's own fields are checked in memory, before the source. Those on relations are added to the source's query, and bulk updates and deletes are narrowed to what the actor can read and write, in the query they already make.
- `Rule(allow, scope, into, force, fields, check)`: `into` is what new values have to satisfy (the scope if not given, and `{}` lets a record be moved out of reach, after which it can't be read), `force` values are set whatever was sent, `fields` the names that can be read or written, and `check` a function of the actor and the record's values.
- Filtering, sorting and searching are held to the names the actor can read, or they'd be a way to find out what they can't. `Model.secure(**scope)` is `filter` for what security adds: it merges rather than filters in, so a scope can't be widened.
- `relations.security.system()` is for the code's own work, which isn't checked. Override `Policy.rule(actor, model, verb)` to get rules from somewhere else, such as a database.
