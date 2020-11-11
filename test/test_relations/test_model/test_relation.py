import unittest
import unittest.mock

import relations
import relations.model
import relations.model.relation

class UnitTest(relations.model.Model):
    id = (int,)
    name = relations.model.Field(str, default="unittest")
    nope = False

class TestRelation(unittest.TestCase):

    maxDiff = None

    def setUp(self):

        self.source = unittest.mock.MagicMock()
        relations.SOURCES["TestModel"] = self.source

    def tearDown(self):

        del relations.SOURCES["TestModel"]

    def test_relative_field(self):

        class TestUnit(relations.model.Model):
            id = int
            name = str
            ident = int

        class Test(relations.model.Model):
            ident = int
            unit_id = int
            name = str

        class Unit(relations.model.Model):
            id = int
            testunit_id = int
            test_ident = int
            name = str

        class Equal(relations.model.Relation):
            SAME = True

        class Unequal(relations.model.Relation):
            SAME = False

        testunit = TestUnit()
        test = Test()
        unit = Unit()

        self.assertEqual(relations.model.Relation.relative_field(testunit, unit), "testunit_id")
        self.assertEqual(relations.model.Relation.relative_field(test, unit), "test_ident")
        self.assertEqual(relations.model.Relation.relative_field(test, testunit), "ident")
        self.assertEqual(Equal.relative_field(unit, testunit), "id")

        self.assertRaisesRegex(relations.model.ModelError, "cannot determine field for unit in testunit", Unequal.relative_field, unit, testunit)

class TestOneTo(unittest.TestCase):

    maxDiff = None

    def test___init__(self):

        class Mom(relations.model.Model):
            id = int
            name = str
            ident = int

        class Son(relations.model.Model):
            id = int
            mom_id = int
            name = str
            mom_ident = int

        relation = relations.model.OneTo(Mom, Son)

        self.assertEqual(relation.Parent, Mom)
        self.assertEqual(relation.Child, Son)

        self.assertEqual(relation.parent_child, "son")
        self.assertEqual(relation.child_parent, "mom")
        self.assertEqual(relation.parent_field, "id")
        self.assertEqual(relation.child_field, "mom_id")

        relation = relations.model.OneTo(Mom, Son, "sons", "mommy", "ident", "mom_ident")

        self.assertEqual(relation.parent_child, "sons")
        self.assertEqual(relation.child_parent, "mommy")
        self.assertEqual(relation.parent_field, "ident")
        self.assertEqual(relation.child_field, "mom_ident")

class TestOneToMany(unittest.TestCase):

    maxDiff = None

    def test___init__(self):

        class Mom(relations.model.Model):
            id = int
            name = str

        class Son(relations.model.Model):
            id = int
            mom_id = int
            name = str

        relation = relations.model.OneToMany(Mom, Son)

        self.assertEqual(relation.Parent, Mom)
        self.assertEqual(relation.Child, Son)

        self.assertEqual(relation.parent_child, "son")
        self.assertEqual(relation.child_parent, "mom")
        self.assertEqual(relation.parent_field, "id")
        self.assertEqual(relation.child_field, "mom_id")

class TestOneToOne(unittest.TestCase):

    maxDiff = None

    def test___init__(self):

        class Mom(relations.model.Model):
            id = int
            name = str

        class Son(relations.model.Model):
            id = int
            name = str

        relation = relations.model.OneToOne(Mom, Son)

        self.assertEqual(relation.Parent, Mom)
        self.assertEqual(relation.Child, Son)

        self.assertEqual(relation.parent_child, "son")
        self.assertEqual(relation.child_parent, "mom")
        self.assertEqual(relation.parent_field, "id")
        self.assertEqual(relation.child_field, "id")
