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

# Usage

# Creating

person = Person()
person.name = "Dave"
person.create()

persons = Person(_count=3)
persons[0].name = "Tom"
persons[1].name = "Dick"
persons[2].name = "Harry"
person.create()

# Or

person = Person(name="Dave").create()
persons = Person([{"name": "Tom"}, {"name": "Dick"}, {"name": "Harry"}]).create()

person = Person(name="Dave").create(True) # Will reload record after creation

# Retrieve (won't queruy until accesses)

person = Person.get().filter(id=1)
persons = Person.list().filter(name__in=["Tom", "Dick", "Harry"])

# Or (won't queruy until accesses)

person = Person.get(id=1)
persons = Person.list(name__in=["Tom", "Dick", "Harry"])

# Will query immediately

person = Person.get(id=1).retrieve() # Will throw and exception if greater or fewer than one found
persons = Person.list(name__in=["Tom", "Dick", "Harry"]).retrieve()

person = Person.get(id=1).retrieve(False) # Will throw an exception for greater than one found, not 0

# Updates

person.name = "David"
person.update() # Returns count of updated
person.update(True) # Will reload record after update

persons.birthday = True
persons.update() # Returns count of updated

# Or (for DB will do in a single query)

Person.get(id=1).set(name="David").update() # Returns count of updated
Person.list(name__in=["Tom", "Dick", "Harry"]).set(birthday=True).update() # Returns count of updated

# Deletes

person.delete() # Returns count of deleted
persons.delete() # Returns count of deleted

# Or (single query)

Person.get(id=1).delete() # Returns count of deleted
Person.list(name__in=["Tom", "Dick", "Harry"]).delete() # Returns count of deleted

# Mixed

persons = Person.list().filter(name__in=["Tom", "Dick", "Harry"])
persons[0].action() # Return 'update'
persons[1].action("ignore") # Won't propagate changes
persons[2].action("delete")
persons.add(name="Mary")
persons[3].action() # "insert"

persons[0].name "Thomas"
persons[1].name "Richard"

persons.create() # Will only affect 4th record
persons.update() # Will only affect 1st record, not 2nd
persons.delete() # Will only affect 3rd record

persons.execute() # Will act on all records


# Relations

class Person(relations.MySQLModel):
    id = relations.MySQLField(int,autoincrement=True)
    name = str
    data = dict

class Phone(relations.MySQLModel):
    id = relations.MySQLField(int, autoincrement=True)
    person_id = int
    kind = ["mobile", "office", "home"]
    number = str

class Employee(relations.MySQLModel):
    id = relations.MySQLField(int,autoincrement=True)
    person_id = int
    role = {
      0: "worker",
      1: "manager",
      2: "owner"
    }

class Skill(relations.MySQLModel):
    id = relations.MySQLField(int,autoincrement=True)
    name = str

relations.model.OneToMany(Person, Phone)
relations.model.OneToOne(Person, Employee)
relations.model.ManyToMany(Person, Skill)

### OneToMany

## Creating

# Child creation referencing Parent

person = Person("Dave").create()

# Equivalent

phone = Phone(person.id, "moble", "555-1212").create()
phone = Phone(person=person, kind="moble", number="555-1212").create()

# Person().phone = Phone.create([])

phone = Phone()
phone.person_id = person.id
phone.kind = "mobile"
phone.number = "555-1212"
phone.create()

phone = Phone()
phone.person = person
phone.kind = "mobile"
phone.number = "555-1212"
phone.create()

# Child creation from Parent

# Equivalent (person_id becomes readonly on phone)

person.phone.add("moble", "555-1212").create()

person.phone.add()
person.phone[0].kind = "mobile"
person.phone[0].number = "555-1212"
person.phone.create()

# Parent and Child creation

person = Person("Dave")
person.phone.add("moble", "555-1212")
person.create()  # Creates both person and phone records

## Retrieving

person = Person.get(1)
person.phone # Equivlanet to Phone.list(person_id=person.id)

persons = Person.list()
persons.phone # Equivalent to Phone.list(person_id__in=persons.id)

# Equivalent

persons = Person.list().phone.filter(kind="mobile")
persons = Person.list(phone__kind="mobile")

phones = Phone.list().person.filter(name="Dave")
phones = Phone.list(person__name="Dave")

## Updating

# When updating a parent, this implies propagate creates, updates, and deletes to children

person = Person.get(1)
person.phone.add("home", "555-2121")
person.phone.add("work", "555-1221")
person.update() # Creates the phone records, equivalent to person.phone.execute()

## Deleting

person = Person.get(1).delete() # Will delete all the phone records


### OneToOne

## Creating

# Child creation referencing Parent

person = Person("Dave").create()

# Equivalent

employee = Employee(person.id, "worker").create()

employee = Employee(person=person, role="worker").create()

employee = Employee()
employee.person_id = person.id
employee.role = "worker"
employee.create()

employee = Employee()
employee.person = person
employee.role = "worker"
employee.create()

# Child creation from Parent

# Equivalent (person_id becomes readonly on employee)

person.employee.set("worker").create()

person.employee.role = "worker"
person.employee.create()

# Parent and Child creation

person = Person("Dave")
person.employee.set("worker")
person.create()  # Creates both person and employee records

## Retrieving

person = Person.get(1)
person.employee # Equivlanet to Employee.get(person_id=person.id)

persons = Person.list()
persons.employee # Equivalent to Employee.list(person_id__in=persons.id)

# Equivalent

persons = Person.list().employee.filter(role="worker")
persons = Person.list(employee__role="worker")

employees = Employee.list().person.filter(name="Dave")
employees = Employee.list(person__name="Dave")

## Updating

# When updating a parent, this implies propagate creates, updates, and deletes to children

person = Person.get(1)
person.employee.set("worker")
person.update() # Creates the employee record, equivalent to person.employee.execute()

## Deleting

person = Person.get(1).delete() # Will delete all the employee record



### ManyToMany

# This isn't modeling as much as storing the values in another table

person = Person.get(1)

person.skill    # Selects records from the person_skill table where person_id=person.id

person.skill = [skill.id]
person.update() # Insert ignroe into person_skill and the delete from where person_id=person.id and skill_id not in [skill.id]

# Maybe we'll make PersonSkill a Model? Or maybe it'll be implied, a Model/Relation hybrid

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
