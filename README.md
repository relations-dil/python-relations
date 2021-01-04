# python-relations
DB/API Modeling

# Models


The defintion for DB model has two purposes. First to generate code to create and alter tables. Second to specify how to read and write to the databse.

```python

# In your start code for MySQL (separate module)

import relations_pymysql

relations_pymysql.Source("your-source", database="test_source", host="my-host", port=int(os.environ["MYSQL_PORT"]))

# In your main code

import relations.model

class BaeeModel(relations.model.Model):
    SOURCE = "your-source"

class Unit(BaeeModel):
    id = int
    name = str

class Test(BaeeModel):
    id = int
    unit_id = int
    name = str

class Case(BaeeModel):
    id = int
    test_id = int
    name = str

relations.model.OneToMany(Unit, Test)
relations.model.OneToOne(Test, Case)

cursor = self.source.connection.cursor()

cursor.execute(Unit.define())
cursor.execute(Test.define())
cursor.execute(Case.define())

Unit("yep").create()
self.assertEqual(Unit.one(name="yep").id, 1)

Unit([["people"], ["stuff"]]).create()

unit = Unit.one(id=2).set(name="things")
self.assertEqual(unit.update(), 1)

unit = Unit.one(2)
unit.name = "thing"
unit.test.add("moar")[-1].case.add("lass")

self.assertEqual(unit.update(), 1)
self.assertEqual(unit.name, "thing")
self.assertEqual(unit.test[0].id, 1)
self.assertEqual(unit.test[0].name, "moar")
self.assertEqual(unit.test[0].case.id, 1)
self.assertEqual(unit.test[0].case.name, "lass")

tests = Test.many(unit__name="thing",case__name="lass", id__gt=0)

cursor.close()

```

# Model

```
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

```
call	action	mode	parent	description
Model().parent	retrieve	one	Yes	retrieve single record, fail if not found
Model([]).parent	retrieve	many	Yes	retrieve records, fail if no child fields not set
Model.one().parent	retrieve	one	Yes	induces retrieve on model, ready to retrieve on parent
Model.many().parent	retrieve	many	Yes	induces retrieve on model, ready to retrieve on parent
```

# Child

```
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
