import unittest

import relations
import relations.unittest
import relations.security


class Folder(relations.security.Secure, relations.Model):

    SOURCE = "security"

    id = int
    owner = str
    name = str


class Note(relations.security.Secure, relations.Model):

    SOURCE = "security"

    id = int
    owner = str
    title = str
    body = str
    locked = bool, False
    folder_id = {"kind": int, "none": True}

    TITLES = ["title", "body"]


relations.OneToMany(Folder, Note)


class Tagged(relations.security.Secure, relations.Model):

    SOURCE = "security"

    id = int
    data = dict
    kind = str, {"inject": "data__kind"}

    UNIQUE = {}


def mine(actor):
    return {"owner": actor}


def policy(**rules):
    """
    Pat owns what is owner pat. Notes can be read and created by their owner, changed and deleted while
    they're not locked, and what's in rules takes the place of the rule for that verb
    """

    verbs = {
        "retrieve": relations.security.Rule(scope=mine),
        "create": relations.security.Rule(scope=mine),
        "update": relations.security.Rule(scope=lambda actor: {"owner": actor, "locked": False}, into=mine),
        "delete": relations.security.Rule(scope=lambda actor: {"owner": actor, "locked": False})
    }

    verbs.update(rules)

    return relations.security.Policy({"note": verbs, "folder": {"retrieve": relations.security.Rule(scope=mine)}})


class TestPolicy(unittest.TestCase):

    def test_rule(self):

        read = relations.security.Rule()
        every = relations.security.Rule()
        count = relations.security.Rule()

        unit = relations.security.Policy({"note": {"retrieve": read, "count": count}, "*": {"*": every}})

        self.assertIs(unit.rule("pat", Note(), "retrieve"), read)
        self.assertIs(unit.rule("pat", Note(), "count"), count)
        self.assertIs(unit.rule("pat", Note(), "titles"), read)
        self.assertIs(unit.rule("pat", Note(), "delete"), every)
        self.assertIs(unit.rule("pat", Folder(), "retrieve"), every)

        self.assertIsNone(relations.security.Policy().rule("pat", Note(), "retrieve"))

    def test_acting(self):

        self.assertIsNone(relations.security.current())
        self.assertIsNone(relations.security.cache())

        with relations.security.acting("pat"):
            self.assertEqual(relations.security.current(), "pat")
            relations.security.cache()["kept"] = True
            with relations.security.acting("sam"):
                self.assertEqual(relations.security.cache(), {})
            self.assertEqual(relations.security.cache(), {"kept": True})
            with relations.security.system():
                self.assertIs(relations.security.current(), relations.security.SYSTEM)
            self.assertEqual(relations.security.current(), "pat")

        self.assertIsNone(relations.security.current())


class Secured(unittest.TestCase):

    maxDiff = None

    def setUp(self):

        self.source = relations.unittest.MockSource("security")

        relations.security.POLICY = policy()

        with relations.security.system():
            Folder(owner="pat", name="pat's").create()
            Folder(owner="sam", name="sam's").create()
            Note([
                {"owner": "pat", "title": "a", "body": "one", "folder_id": 1},
                {"owner": "pat", "title": "b", "body": "two", "folder_id": 2, "locked": True},
                {"owner": "sam", "title": "c", "body": "three", "folder_id": 2}
            ]).create()

    def tearDown(self):

        relations.security.POLICY = None

        del relations.SOURCES["security"]

    def everything(self):

        with relations.security.system():
            return Note.many().title


class TestSecure(Secured):

    def test_no_actor(self):

        for call in (Note("a").create, Note.many().count, Note.many().retrieve, Note.many().titles):
            self.assertRaisesRegex(relations.security.Denied, "without an actor", call)

        self.assertRaisesRegex(relations.security.Denied, "without an actor", Note.many().set(title="x").update)

    def test_no_rule(self):

        relations.security.POLICY = policy(create=relations.security.Rule(allow=False))

        with relations.security.acting("pat"):
            self.assertRaisesRegex(relations.security.Denied, "note: cannot create", Note(owner="pat", title="x").create)

        relations.security.POLICY = None

        with relations.security.acting("pat"):
            self.assertRaisesRegex(relations.security.Denied, "note: cannot retrieve", Note.many().retrieve)

    def test_model_policy(self):

        class Own(relations.security.Secure, relations.Model):
            SOURCE = "security"
            NAME = "note"
            POLICY = relations.security.Policy({"note": {"retrieve": relations.security.Rule(scope={"owner": "sam"})}})
            id = int
            owner = str
            title = str

        with relations.security.acting("pat"):
            self.assertEqual(Own.many().title, ["c"])

    def test_system(self):

        with relations.security.system():
            self.assertEqual(Note.many().count(), 3)

    def test_retrieve(self):

        with relations.security.acting("pat"):

            self.assertEqual(Note.many().title, ["a", "b"])
            self.assertEqual(Note.many().count(), 2)
            self.assertEqual(Note.many().titles().ids, [1, 2])
            self.assertEqual(Note.one(title="a").retrieve().body, "one")

            # Not theirs is a miss, as not there is

            self.assertRaises(relations.NotFoundError, Note.one(title="c").retrieve)
            self.assertIsNone(Note.one(title="c").retrieve(False))

    def test_narrowed(self):

        with relations.security.acting("pat"):

            # What's asked can't widen it

            self.assertEqual(Note.many(owner__in=["pat", "sam"]).title, ["a", "b"])
            self.assertEqual(Note.many(owner="sam").title, [])
            self.assertEqual(Note.many(id__in=[2, 3]).title, ["b"])
            self.assertEqual(Note.many(id__in=[3]).title, [])
            self.assertEqual(Note.many(owner__not_in=["pat"]).title, [])

            # What's asked narrows it

            self.assertEqual(Note.many(locked=False).title, ["a"])
            self.assertEqual(Note.many(id__gt=1).title, ["b"])

        # What can't be put together

        relations.security.POLICY = policy(retrieve=relations.security.Rule(scope={"title__like": "a"}))

        with relations.security.acting("pat"):
            self.assertRaisesRegex(relations.security.Denied, "cannot merge like", Note.many(title__like="b").retrieve)

    def test_narrowed_in(self):

        # Filtering twice on an in gives the union, so a scope can't be filtered in

        relations.security.POLICY = policy(retrieve=relations.security.Rule(scope={"id__in": [1, 2]}))

        with relations.security.acting("pat"):

            self.assertEqual(Note.many(id__in=[2, 3]).title, ["b"])
            self.assertEqual(Note.many(id__in=[3]).title, [])
            self.assertEqual(Note.many(id=3).title, [])
            self.assertEqual(Note.many().title, ["a", "b"])

    def test_fields(self):

        relations.security.POLICY = policy(retrieve=relations.security.Rule(scope=mine, fields=["id", "owner", "title"]))

        with relations.security.acting("pat"):

            notes = Note.many().retrieve()

            self.assertEqual(notes.title, ["a", "b"])
            self.assertEqual(notes[0].export(), {"id": 1, "owner": "pat", "title": "a"})
            self.assertEqual(notes.export(), [{"id": 1, "owner": "pat", "title": "a"}, {"id": 2, "owner": "pat", "title": "b"}])
            self.assertRaisesRegex(relations.security.Denied, "cannot read body", getattr, notes[0], "body")
            self.assertRaisesRegex(relations.security.Denied, "cannot read body", notes[0].__getitem__, "body")
            self.assertRaisesRegex(relations.security.Denied, "cannot read body", notes[0].__getitem__, 3)

            # Can't be used to find out

            self.assertRaisesRegex(relations.security.Denied, "cannot filter on body", Note.many, body="one")
            self.assertRaisesRegex(relations.security.Denied, "cannot filter on body", Note.many, body__like="o")
            self.assertRaisesRegex(relations.security.Denied, "cannot filter on body", Note.many().filter, body="one")
            self.assertRaisesRegex(relations.security.Denied, "cannot filter on body", Note.many().filter, 1, "pat", "a", "one")
            self.assertRaisesRegex(relations.security.Denied, "cannot sort on body", Note.many().sort("-body").retrieve)
            self.assertRaisesRegex(relations.security.Denied, "cannot search", Note.many(like="one").retrieve)
            self.assertEqual(Note.many().sort("-title").title, ["b", "a"])

            # one

            note = Note.one(title="a").retrieve()
            self.assertRaises(relations.security.Denied, getattr, note, "body")
            self.assertEqual(note.title, "a")

    def test_secure(self):

        # Like filter, but it's the scope's, so it isn't held to what can be read, and it can't widen

        relations.security.POLICY = policy(retrieve=relations.security.Rule(scope=mine, fields=["id", "title"]))

        with relations.security.acting("pat"):

            notes = Note.many(id__in=[1, 2])
            self.assertIs(notes.secure(id__in=[2, 3], owner="pat"), notes)
            self.assertEqual(notes.title, ["b"])

            self.assertEqual(Note.many().secure(title="a").title, ["a"])
            self.assertEqual(Note.many(title="a").secure(title="b").title, [])
            self.assertRaisesRegex(relations.security.Denied, "cannot filter on body", Note.many().filter, body="one")

        with relations.security.system():
            self.assertEqual(Note.many().secure(owner="sam").title, ["c"])

        self.assertRaisesRegex(relations.ModelError, "can only secure retrieve", Note(owner="pat").secure, owner="pat")

    def test_fields_again(self):

        # Narrowing is the scope's, so asking again isn't taken for the actor asking for what they can't read

        relations.security.POLICY = policy(retrieve=relations.security.Rule(scope=mine, fields=["id", "title"]))

        with relations.security.acting("pat"):

            notes = Note.many()
            self.assertEqual(notes.count(), 2)
            self.assertEqual(notes.titles().ids, [1, 2])
            self.assertEqual(notes.title, ["a", "b"])

            # but what is added after is

            notes = Note.many()
            self.assertEqual(notes.count(), 2)
            self.assertRaisesRegex(relations.security.Denied, "cannot filter on body", notes.filter, body="one")

            notes = Note.many()
            self.assertEqual(notes.count(), 2)
            self.assertRaisesRegex(relations.security.Denied, "cannot filter on owner", notes.filter, owner="sam")

        # Not known when it's filtered, so it's held to it when it's used

        notes = Note.many(body="one")

        with relations.security.acting("pat"):
            self.assertRaisesRegex(relations.security.Denied, "cannot filter on body", notes.retrieve)
            self.assertRaisesRegex(relations.security.Denied, "cannot filter on body", notes.count)

        with relations.security.system():
            self.assertEqual(notes.title, ["a"])

    def test_create(self):

        with relations.security.acting("pat"):

            note = Note(owner="pat", title="d", body="four").create()
            self.assertEqual(note.id, 4)

            self.assertRaisesRegex(relations.security.Denied, "note: cannot create that note", Note(owner="sam", title="e").create)

            # many, each is held to it

            self.assertRaises(relations.security.Denied, Note([{"owner": "pat", "title": "f"}, {"owner": "sam", "title": "g"}]).create)

            bulk = Note.bulk()
            bulk.add(owner="pat", title="h")
            bulk.add(owner="sam", title="i")
            self.assertRaises(relations.security.Denied, bulk.create)

        self.assertEqual(self.everything(), ["a", "b", "c", "d"])

    def test_create_nothing_to_hold(self):

        # No owner can't be in a scope of an owner

        with relations.security.acting("pat"):
            self.assertRaises(relations.security.Denied, Note(title="d").create)

    def test_injected(self):

        relations.security.POLICY = relations.security.Policy({"tagged": {
            "retrieve": relations.security.Rule(scope={"kind": "a"}),
            "create": relations.security.Rule(scope={"kind": "a"}),
            "update": relations.security.Rule(scope={"kind": "a"}, into={"kind": "a"})
        }})

        with relations.security.system():
            Tagged(data={"x": 1}, kind="a").create()
            Tagged(data={"x": 2}, kind="b").create()

        with relations.security.acting("pat"):

            self.assertEqual(Tagged.many().data, [{"x": 1, "kind": "a"}])

            Tagged(data={"x": 3}, kind="a").create()
            self.assertRaises(relations.security.Denied, Tagged(data={"x": 4}, kind="b").create)

            tagged = Tagged.one(data__x=1).retrieve()
            tagged.data__x = 5
            self.assertEqual(tagged.update(), 1)

            tagged.kind = "b"
            self.assertRaisesRegex(relations.security.Denied, "to that", tagged.update)

    def test_create_force(self):

        relations.security.POLICY = policy(create=relations.security.Rule(force=lambda actor: {"owner": actor}))

        with relations.security.acting("sam"):
            note = Note(owner="pat", title="d").create()
            self.assertEqual(note.owner, "sam")

    def test_create_fields(self):

        relations.security.POLICY = policy(create=relations.security.Rule(scope=mine, fields=["owner", "title"]))

        with relations.security.acting("pat"):

            self.assertEqual(Note(owner="pat", title="d").create().title, "d")

            self.assertRaisesRegex(
                relations.security.Denied, "cannot write body", Note(owner="pat", title="e", body="five").create
            )

    def test_create_check(self):

        relations.security.POLICY = policy(create=relations.security.Rule(check=lambda actor, values: values["title"] != "no"))

        with relations.security.acting("pat"):

            Note(owner="pat", title="yes").create()
            self.assertRaises(relations.security.Denied, Note(owner="pat", title="no").create)

    def test_write_only(self):

        relations.security.POLICY = relations.security.Policy({"note": {"create": relations.security.Rule()}})

        with relations.security.acting("pat"):

            note = Note(owner="pat", title="d").create()

            self.assertRaisesRegex(relations.security.Denied, "no longer yours to read", getattr, note, "title")
            self.assertRaises(relations.security.Denied, note.export)

        self.assertEqual(self.everything(), ["a", "b", "c", "d"])

    def test_update(self):

        with relations.security.acting("pat"):

            note = Note.one(title="a").retrieve()
            note.body = "uno"
            self.assertEqual(note.update(), 1)

            self.assertEqual(Note.one(title="a").retrieve().body, "uno")

        # Theirs only to the extent they can read it, anything else is a miss

        with relations.security.system():
            note = Note.one(title="c").retrieve()

        note.body = "tres"

        with relations.security.acting("pat"):
            self.assertRaises(relations.NotFoundError, note.update)

    def test_update_denied(self):

        with relations.security.acting("pat"):

            # Can read it, can't change it (locked), so they're told

            note = Note.one(title="b").retrieve()
            note.body = "dos"
            self.assertRaisesRegex(relations.security.Denied, "note: cannot update that note", note.update)

            # Can't take it from them either

            self.assertRaisesRegex(relations.security.Denied, "cannot delete that note", Note.one(title="b").delete)

        self.assertEqual(self.everything(), ["a", "b", "c"])

    def test_update_into(self):

        with relations.security.acting("pat"):

            note = Note.one(title="a").retrieve()
            note.owner = "sam"
            self.assertRaisesRegex(relations.security.Denied, "cannot update that note to that", note.update)

        with relations.security.system():
            self.assertEqual(Note.one(title="a").retrieve().owner, "pat")

    def test_transfer(self):

        relations.security.POLICY = policy(update=relations.security.Rule(scope=mine, into={}))

        with relations.security.acting("pat"):

            note = Note.one(title="a").retrieve()
            note.owner = "sam"
            self.assertEqual(note.update(), 1)

            # Moved out of reach, so it's no longer theirs to read

            self.assertRaisesRegex(relations.security.Denied, "no longer yours to read", getattr, note, "title")
            self.assertRaises(relations.security.Denied, note.export)
            self.assertRaises(relations.security.Denied, note.__getitem__, "title")

            self.assertEqual(Note.many().title, ["b"])

        with relations.security.system():
            self.assertEqual(Note.one(title="a").retrieve().owner, "sam")

    def test_update_fields(self):

        relations.security.POLICY = policy(update=relations.security.Rule(scope=mine, fields=["title"]))

        with relations.security.acting("pat"):

            note = Note.one(title="a").retrieve()
            note.title = "aa"
            self.assertEqual(note.update(), 1)

            note.body = "uno"
            self.assertRaisesRegex(relations.security.Denied, "cannot write body", note.update)

    def test_update_force(self):

        relations.security.POLICY = policy(update=relations.security.Rule(scope=mine, force={"body": "forced"}, fields=["title"]))

        with relations.security.acting("pat"):

            note = Note.one(title="a").retrieve()
            note.title = "aa"
            note.update()

        with relations.security.system():
            self.assertEqual(Note.one(title="aa").retrieve().body, "forced")

    def test_update_check(self):

        relations.security.POLICY = policy(update=relations.security.Rule(scope=mine, check=lambda actor, values: False))

        with relations.security.acting("pat"):

            note = Note.one(title="a").retrieve()
            note.body = "uno"
            self.assertRaises(relations.security.Denied, note.update)

    def test_update_many(self):

        with relations.security.acting("pat"):

            notes = Note.many().retrieve()
            notes.set(body="all")

            # Each is held to it, the locked one being denied

            self.assertRaises(relations.security.Denied, notes.update)

    def test_delete(self):

        with relations.security.acting("pat"):

            self.assertEqual(Note.one(title="a").delete(), 1)
            self.assertRaises(relations.NotFoundError, Note.one(title="c").delete)

        self.assertEqual(self.everything(), ["b", "c"])

    def test_bulk(self):

        with relations.security.acting("pat"):

            # Only what can be read and changed is touched, the locked one being left alone

            self.assertEqual(Note.many().set(body="all").update(), 1)

            # What is set is held like any other

            self.assertRaises(relations.security.Denied, Note.many().set(owner="sam").update)

        with relations.security.system():
            self.assertEqual(Note.many().body, ["all", "two", "three"])

        with relations.security.acting("pat"):
            self.assertEqual(Note.many().delete(), 1)

        self.assertEqual(self.everything(), ["b", "c"])

    def test_bulk_rules(self):

        relations.security.POLICY = policy(update=relations.security.Rule(
            scope=mine, fields=["title"], force={"locked": True}, into={"locked": True}
        ))

        with relations.security.acting("pat"):

            self.assertRaisesRegex(relations.security.Denied, "cannot write body", Note.many().set(body="x").update)
            self.assertEqual(Note.many(title="a").set(title="aa").update(), 1)

        with relations.security.system():
            self.assertEqual(Note.one(title="aa").retrieve().locked, True)

        relations.security.POLICY = policy(update=relations.security.Rule(scope=mine, into={"title": "a"}))

        with relations.security.acting("pat"):
            self.assertRaisesRegex(relations.security.Denied, "to that", Note.many().set(title="z").update)
            self.assertEqual(Note.many(title="aa").set(title="a").update(), 1)

        relations.security.POLICY = policy(update=relations.security.Rule(scope=mine, into={"folder__name": "x"}))

        with relations.security.acting("pat"):
            self.assertRaisesRegex(relations.ModelError, "needs the source", Note.many().set(title="z").update)

        relations.security.POLICY = policy(retrieve=None)

        with relations.security.acting("pat"):
            self.assertEqual(Note.many().set(title="z").update(), 0)
            self.assertEqual(Note.many().delete(), 0)

    def test_relation_scope(self):

        # A scope on a relation is done by the source, which is all that can be done about an old record

        relations.security.POLICY = policy(
            retrieve=relations.security.Rule(scope={"folder__name": "pat's"}),
            update=relations.security.Rule(scope={"folder__name": "pat's"}, into=mine)
        )

        with relations.security.acting("pat"):

            self.assertEqual(Note.many().title, ["a"])

            note = Note.one(title="a").retrieve()
            note.body = "uno"
            self.assertEqual(note.update(), 1)

        # It can't be of a record that doesn't exist yet

        relations.security.POLICY = policy(create=relations.security.Rule(scope={"folder__name": "pat's"}))

        with relations.security.acting("pat"):
            self.assertRaisesRegex(relations.ModelError, "needs the source", Note(owner="pat", title="d").create)

    def test_relation_hop(self):

        with relations.security.system():
            Note(owner="pat", title="d", folder_id=2).create()

        with relations.security.acting("pat"):

            # What pat can see of their own, in a folder they can see, can be found

            self.assertEqual(Note.many(folder__name="pat's").title, ["a"])

            # but not by a folder they can't, which would give its name away

            self.assertEqual(Note.many(folder__name="sam's").title, [])

    def test_relation_hop_fields(self):

        relations.security.POLICY = relations.security.Policy({
            "note": {"retrieve": relations.security.Rule(scope=mine)},
            "folder": {"retrieve": relations.security.Rule(scope=mine, fields=["id", "owner"])}
        })

        with relations.security.acting("pat"):
            self.assertRaisesRegex(relations.security.Denied, "cannot filter on name", Note.many, folder__name="pat's")
