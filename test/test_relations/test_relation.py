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

        relation = relations.OneTo(Mom, Son, "sons", "mommy", "ident", "mom_ident")

        self.assertEqual(relation.parent_child_attr, "sons")
        self.assertEqual(relation.child_parent_attr, "mommy")
        self.assertEqual(relation.parent_id, "ident")
        self.assertEqual(relation.child_parent_ref, "mom_ident")

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
