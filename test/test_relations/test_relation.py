import unittest
import unittest.mock

import relations
import relations.relation

class UnitTest(relations.Model):
    id = (int,)
    name = relations.Field(str, default="unittest")
    nope = False

class TestRelation(unittest.TestCase):

    maxDiff = None

    def setUp(self):

        self.source = unittest.mock.MagicMock()
        relations.SOURCES["TestModel"] = self.source

    def tearDown(self):

        del relations.SOURCES["TestModel"]

    def test_relative_field(self):

        class TestUnit(relations.Model):
            id = int
            name = str
            ident = int

        class Test(relations.Model):
            ident = int
            unit_id = int
            name = str

        class Unit(relations.Model):
            id = int
            test_unit_id = int
            test_ident = int
            name = str

        class Equal(relations.Relation):
            SAME = True

        class Unequal(relations.Relation):
            SAME = False

        testunit = TestUnit()
        test = Test()
        unit = Unit()

        self.assertEqual(relations.Relation.relative_field(testunit, unit), "test_unit_id")
        self.assertEqual(relations.Relation.relative_field(test, unit), "test_ident")
        self.assertEqual(relations.Relation.relative_field(test, testunit), "ident")
        self.assertEqual(Equal.relative_field(unit, testunit), "id")

        self.assertRaisesRegex(relations.ModelError, "cannot determine field for unit in test_unit", Unequal.relative_field, unit, testunit)

class TestOneTo(unittest.TestCase):

    maxDiff = None

    def test___init__(self):

        class Mom(relations.Model):
            id = int
            name = str
            ident = int

        class Son(relations.Model):
            id = int
            mom_id = int
            name = str
            mom_ident = int

        relation = relations.OneTo(Mom, Son)

        self.assertEqual(relation.Parent, Mom)
        self.assertEqual(relation.Child, Son)

        self.assertEqual(relation.parent_child_attr, "son")
        self.assertEqual(relation.child_parent_attr, "mom")
        self.assertEqual(relation.parent_id, "id")
        self.assertEqual(relation.child_parent_ref, "mom_id")
        self.assertIsNone(relation.child_inject)

        relation = relations.OneTo(Mom, Son, "sons", "mommy", "ident", "mom_ident")

        self.assertEqual(relation.parent_child_attr, "sons")
        self.assertEqual(relation.child_parent_attr, "mommy")
        self.assertEqual(relation.parent_id, "ident")
        self.assertEqual(relation.child_parent_ref, "mom_ident")

        # Injecting the parent id into a dict field of the child

        class Daughter(relations.Model):
            id = int
            name = str
            what = dict

        relation = relations.OneTo(Mom, Daughter, child_inject="what")

        self.assertEqual(relation.parent_child_attr, "daughter")
        self.assertEqual(relation.child_parent_attr, "mom")
        self.assertEqual(relation.parent_id, "id")
        self.assertEqual(relation.child_parent_ref, "mom_id")
        self.assertEqual(relation.child_inject, "what")

        fields = Daughter.thy()._fields._names

        self.assertIs(fields["mom_id"].kind, int)
        self.assertEqual(fields["mom_id"].inject, "what__relations__mom__id")
        self.assertTrue(fields["mom_id"].none)
        self.assertEqual(fields["what"].extract, {"relations__mom__id": int})

        self.assertIn("mom", Daughter.PARENTS)
        self.assertIn("daughter", Mom.CHILDREN)

        self.assertEqual(Daughter(name="kid", mom_id=7).mom_id, 7)
        self.assertIsNone(Daughter(name="loner").mom_id)

        # Another parent merges into the same dict field

        class Dad(relations.Model):
            id = int
            name = str

        relations.OneTo(Dad, Daughter, child_inject="what")

        fields = Daughter.thy()._fields._names

        self.assertEqual(fields["dad_id"].inject, "what__relations__dad__id")
        self.assertEqual(fields["what"].extract, {"relations__mom__id": int, "relations__dad__id": int})

        # Overrides, and merging into an existing extract

        class Twin(relations.Model):
            id = int
            name = str
            data = relations.Field(dict, extract="other")

        relation = relations.OneTo(Mom, Twin, "twins", "mommy", "ident", "parent", "data")

        self.assertEqual(relation.parent_child_attr, "twins")
        self.assertEqual(relation.child_parent_attr, "mommy")
        self.assertEqual(relation.parent_id, "ident")
        self.assertEqual(relation.child_parent_ref, "parent")

        fields = Twin.thy()._fields._names

        self.assertEqual(fields["parent"].inject, "data__relations__mom__ident")
        self.assertEqual(fields["data"].extract, {"other": str, "relations__mom__ident": int})

        # Other ways of declaring the dict field

        class Sister(relations.Model):
            id = int
            name = str
            what = dict, {"extract": "other"}

        class Brother(relations.Model):
            id = int
            name = str
            what = {"kind": dict, "extract": "other"}

        for Sibling in [Sister, Brother]:
            relations.OneTo(Mom, Sibling, child_inject="what")
            self.assertEqual(Sibling.thy()._fields._names["what"].extract, {"other": str, "relations__mom__id": int})

        # Same source is just model_id, different sources prefix the parent's source

        class Ally(relations.Model):
            SOURCE = "cumulus"
            id = int
            name = str

        class Friend(relations.Model):
            SOURCE = "Bucket-App"
            id = int
            name = str

        class Entity(relations.Model):
            SOURCE = "cumulus"
            id = int
            name = str
            what = dict

        relation = relations.OneTo(Ally, Entity, child_inject="what")

        self.assertEqual(relation.child_parent_ref, "ally_id")
        self.assertEqual(Entity.thy()._fields._names["ally_id"].inject, "what__relations__ally__id")

        relation = relations.OneTo(Friend, Entity, child_inject="what")

        self.assertEqual(relation.child_parent_ref, "bucket_app_friend_id")

        fields = Entity.thy()._fields._names

        self.assertEqual(fields["bucket_app_friend_id"].inject, "what__relations__bucket_app_friend__id")
        self.assertEqual(fields["what"].extract, {"relations__ally__id": int, "relations__bucket_app_friend__id": int})

        self.assertEqual(Entity(name="kid", bucket_app_friend_id=7).bucket_app_friend_id, 7)

        # Errors

        class Cousin(relations.Model):
            id = int
            name = str
            mom_id = int
            what = dict

        class Orphan(relations.Model):
            id = int
            name = str

        self.assertRaisesRegex(relations.ModelError, "field mom_id already exists in cousin", relations.OneTo, Mom, Cousin, child_inject="what")
        self.assertRaisesRegex(relations.ModelError, "cannot find field what in orphan", relations.OneTo, Mom, Orphan, child_inject="what")
        self.assertRaisesRegex(relations.ModelError, "field name not a dict in orphan", relations.OneTo, Mom, Orphan, child_inject="name")

        # Sources have to be dns compliant when they're used in a name

        for source in [None, "", "a_b", "-ab", "ab-", "a b", "a.b", "ab\n", "a" * 64]:

            class Stranger(relations.Model):
                SOURCE = source
                id = int
                name = str

            class Local(relations.Model):
                SOURCE = "cumulus"
                id = int
                name = str
                what = dict

            self.assertRaisesRegex(
                relations.ModelError, f"stranger: source {source} is not dns compliant", relations.OneTo, Stranger, Local, child_inject="what"
            )
            self.assertNotIn("stranger", Local.PARENTS or {})
            self.assertNotIn("stranger_id", Local.__dict__)

        class Fine(relations.Model):
            SOURCE = "a" * 63
            id = int
            name = str

        class Home(relations.Model):
            SOURCE = "cumulus"
            id = int
            name = str
            what = dict

        self.assertEqual(relations.OneTo(Fine, Home, child_inject="what").child_parent_ref, f"{'a' * 63}_fine_id")

class TestOneToMany(unittest.TestCase):

    maxDiff = None

    def test___init__(self):

        class Mom(relations.Model):
            id = int
            name = str

        class Son(relations.Model):
            id = int
            mom_id = int
            name = str

        relation = relations.OneToMany(Mom, Son)

        self.assertEqual(relation.Parent, Mom)
        self.assertEqual(relation.Child, Son)

        self.assertEqual(relation.parent_child_attr, "son")
        self.assertEqual(relation.child_parent_attr, "mom")
        self.assertEqual(relation.parent_id, "id")
        self.assertEqual(relation.child_parent_ref, "mom_id")

class TestOneToOne(unittest.TestCase):

    maxDiff = None

    def test___init__(self):

        class Mom(relations.Model):
            id = int
            name = str

        class Son(relations.Model):
            id = int
            name = str

        relation = relations.OneToOne(Mom, Son)

        self.assertEqual(relation.Parent, Mom)
        self.assertEqual(relation.Child, Son)

        self.assertEqual(relation.parent_child_attr, "son")
        self.assertEqual(relation.child_parent_attr, "mom")
        self.assertEqual(relation.parent_id, "id")
        self.assertEqual(relation.child_parent_ref, "id")

class TestManyToMany(unittest.TestCase):

    maxDiff = None

    def test___init__(self):

        class Sis(relations.Model):
            id = int
            name = str
            bro_id = set

        class Bro(relations.Model):
            id = int
            name = str
            sis_id = set

        class SisBro(relations.Model):
            bro_id = int
            sis_id = int

        relation = relations.ManyToMany(Sis, Bro, SisBro)

        self.assertEqual(relation.Sister, Sis)
        self.assertEqual(relation.Brother, Bro)
        self.assertEqual(relation.Tie, SisBro)
        self.assertTrue(relation.Tie.TIE)

        self.assertEqual(relation.sister_brother_ref, "bro_id")
        self.assertEqual(relation.brother_sister_ref, "sis_id")
        self.assertEqual(relation.sister_brother_attr, "bro")
        self.assertEqual(relation.brother_sister_attr, "sis")
        self.assertEqual(relation.sister_id, "id")
        self.assertEqual(relation.brother_id, "id")
        self.assertEqual(relation.tie_sister_ref, "sis_id")
        self.assertEqual(relation.tie_brother_ref, "bro_id")

        class SisTie(relations.Model):
            sis_id = int
            name = str
            bro_ident = set

        class BroTie(relations.Model):
            bro_id = int
            name = str
            sis_ident = set

        class SisBroTie(relations.Model):
            TIE = False
            sist = int
            brot = int

        relation = relations.ManyToMany(SisTie, BroTie, SisBroTie, "bros", "siss", "bro_ident", "sis_ident", "sis_id", "bro_id", "sist", "brot")

        self.assertEqual(relation.Sister, SisTie)
        self.assertEqual(relation.Brother, BroTie)
        self.assertEqual(relation.Tie, SisBroTie)
        self.assertFalse(relation.Tie.TIE)

        self.assertEqual(relation.sister_brother_ref, "bro_ident")
        self.assertEqual(relation.brother_sister_ref, "sis_ident")
        self.assertEqual(relation.sister_brother_attr, "bros")
        self.assertEqual(relation.brother_sister_attr, "siss")
        self.assertEqual(relation.sister_id, "sis_id")
        self.assertEqual(relation.brother_id, "bro_id")
        self.assertEqual(relation.tie_sister_ref, "sist")
        self.assertEqual(relation.tie_brother_ref, "brot")
