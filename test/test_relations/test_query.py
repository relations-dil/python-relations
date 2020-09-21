import unittest
import unittest.mock

import relations.query

class TestQuery(unittest.TestCase):

    maxDiff = None

    def test__init__(self):

        query = relations.query.Query(
            selects={"this": "that", "that": "this"},
            froms={"persons": "people", "people": "persons"},
            wheres={"stuff": "things", "things": "stuff"},
            group_bys=["fee", "fie"],
            havings={"up": "down", "down": "up"},
            order_bys=["foe", "fum"],
            limits=[1,2],
            options=["DIS", "STINK"]
        )

        self.assertEqual(query.selects,"this AS that,that AS this")
        self.assertEqual(query.froms,"persons AS people,people AS persons")
        self.assertEqual(query.wheres,"stuff=things AND things=stuff")
        self.assertEqual(query.group_bys,"fee,fie")
        self.assertEqual(query.havings,"down=up AND up=down")
        self.assertEqual(query.order_bys,"foe,fum")
        self.assertEqual(query.limits,"1,2")
        self.assertEqual(query.options,"DIS STINK")

    def test_add(self):

        query = relations.query.Query(
            selects={"this": "that", "that": "this"},
            froms={"persons": "people", "people": "persons"},
            wheres={"stuff": "things", "things": "stuff"},
            group_bys=["fee", "fie"],
            havings={"up": "down", "down": "up"},
            order_bys=["foe", "fum"],
            limits=[1,2],
            options=["DIS", "STINK"]
        )

        query.add()

        self.assertEqual(query.selects,"this AS that,that AS this")
        self.assertEqual(query.froms,"persons AS people,people AS persons")
        self.assertEqual(query.wheres,"stuff=things AND things=stuff")
        self.assertEqual(query.group_bys,"fee,fie")
        self.assertEqual(query.havings,"down=up AND up=down")
        self.assertEqual(query.order_bys,"foe,fum")
        self.assertEqual(query.limits,"1,2")
        self.assertEqual(query.options,"DIS STINK")

        query.add(
            selects={"here": "there", "there": "here"},
            froms={"folks": "folken", "folken": "folks"},
            wheres={"items": "entities", "entities": "items"},
            group_bys=["fie", "fee"],
            havings={"left": "right", "right": "left"},
            order_bys=["fum", "foe"],
            limits=[3,4],
            options=["REAL", "BAD"]
        )

        self.assertEqual(query.selects,"this AS that,that AS this,there AS here,here AS there")
        self.assertEqual(query.froms,"persons AS people,people AS persons,folks AS folken,folken AS folks")
        self.assertEqual(query.wheres,"stuff=things AND things=stuff AND entities=items AND items=entities")
        self.assertEqual(query.group_bys,"fee,fie,fie,fee")
        self.assertEqual(query.havings,"down=up AND up=down AND left=right AND right=left")
        self.assertEqual(query.order_bys,"foe,fum,fum,foe")
        self.assertEqual(query.limits,"1,2,3,4")
        self.assertEqual(query.options,"DIS STINK REAL BAD")

    def test_set(self):

        query = relations.query.Query(
            selects={"this": "that", "that": "this"},
            froms={"persons": "people", "people": "persons"},
            wheres={"stuff": "things", "things": "stuff"},
            group_bys=["fee", "fie"],
            havings={"up": "down", "down": "up"},
            order_bys=["foe", "fum"],
            limits=[1,2],
            options=["DIS", "STINK"]
        )

        query.set()

        self.assertEqual(query.selects,"this AS that,that AS this")
        self.assertEqual(query.froms,"persons AS people,people AS persons")
        self.assertEqual(query.wheres,"stuff=things AND things=stuff")
        self.assertEqual(query.group_bys,"fee,fie")
        self.assertEqual(query.havings,"down=up AND up=down")
        self.assertEqual(query.order_bys,"foe,fum")
        self.assertEqual(query.limits,"1,2")
        self.assertEqual(query.options,"DIS STINK")

        query.set(
            selects={"here": "there", "there": "here"},
            froms={"folks": "folken", "folken": "folks"},
            wheres={"items": "entities", "entities": "items"},
            group_bys=["fie", "fee"],
            havings={"left": "right", "right": "left"},
            order_bys=["fum", "foe"],
            limits=[3,4],
            options=["REAL", "BAD"]
        )

        self.assertEqual(query.selects,"there AS here,here AS there")
        self.assertEqual(query.froms,"folks AS folken,folken AS folks")
        self.assertEqual(query.wheres,"entities=items AND items=entities")
        self.assertEqual(query.group_bys,"fie,fee")
        self.assertEqual(query.havings,"left=right AND right=left")
        self.assertEqual(query.order_bys,"fum,foe")
        self.assertEqual(query.limits,"3,4")
        self.assertEqual(query.options,"REAL BAD")

    def test_get(self):

        query = relations.query.Query(
            selects={"this": "that", "that": "this"},
            froms={"persons": "people", "people": "persons"},
            wheres={"stuff": "things", "things": "stuff"},
            group_bys=["fee", "fie"],
            havings={"up": "down", "down": "up"},
            order_bys=["foe", "fum"],
            limits=[1,2],
            options=["DIS", "STINK"]
        )

        self.assertEqual(query.get(),
           "SELECT DIS STINK this AS that,that AS this "
           "FROM persons AS people,people AS persons "
           "WHERE stuff=things AND things=stuff "
           "GROUP BY fee,fie "
           "HAVING down=up AND up=down "
           "ORDER BY foe,fum "
           "LIMIT 1,2"
        )

    def test_get_add(self):

        query = relations.query.Query(
            selects={"this": "that", "that": "this"},
            froms={"persons": "people", "people": "persons"},
            wheres={"stuff": "things", "things": "stuff"},
            group_bys=["fee", "fie"],
            havings={"up": "down", "down": "up"},
            order_bys=["foe", "fum"],
            limits=[1,2],
            options=["DIS", "STINK"]
        )

        self.assertEqual(query.get_add(),
           "SELECT DIS STINK this AS that,that AS this "
           "FROM persons AS people,people AS persons "
           "WHERE stuff=things AND things=stuff "
           "GROUP BY fee,fie "
           "HAVING down=up AND up=down "
           "ORDER BY foe,fum "
           "LIMIT 1,2"
        )


        self.assertEqual(query.get_add(
            selects={"here": "there", "there": "here"},
            froms={"folks": "folken", "folken": "folks"},
            wheres={"items": "entities", "entities": "items"},
            group_bys=["fie", "fee"],
            havings={"left": "right", "right": "left"},
            order_bys=["fum", "foe"],
            limits=[3,4],
            options=["REAL", "BAD"]
        ),
           "SELECT DIS STINK REAL BAD this AS that,that AS this,there AS here,here AS there "
           "FROM persons AS people,people AS persons,folks AS folken,folken AS folks "
           "WHERE stuff=things AND things=stuff AND entities=items AND items=entities "
           "GROUP BY fee,fie,fie,fee "
           "HAVING down=up AND up=down AND left=right AND right=left "
           "ORDER BY foe,fum,fum,foe "
           "LIMIT 1,2,3,4"
        )


    def test_get_set(self):

        query = relations.query.Query(
            selects={"this": "that", "that": "this"},
            froms={"persons": "people", "people": "persons"},
            wheres={"stuff": "things", "things": "stuff"},
            group_bys=["fee", "fie"],
            havings={"up": "down", "down": "up"},
            order_bys=["foe", "fum"],
            limits=[1,2],
            options=["DIS", "STINK"]
        )

        self.assertEqual(query.get_set(),
           "SELECT DIS STINK this AS that,that AS this "
           "FROM persons AS people,people AS persons "
           "WHERE stuff=things AND things=stuff "
           "GROUP BY fee,fie "
           "HAVING down=up AND up=down "
           "ORDER BY foe,fum "
           "LIMIT 1,2"
        )


        self.assertEqual(query.get_set(
            selects={"here": "there", "there": "here"},
            froms={"folks": "folken", "folken": "folks"},
            wheres={"items": "entities", "entities": "items"},
            group_bys=["fie", "fee"],
            havings={"left": "right", "right": "left"},
            order_bys=["fum", "foe"],
            limits=[3,4],
            options=["REAL", "BAD"]
        ),
           "SELECT REAL BAD there AS here,here AS there "
           "FROM folks AS folken,folken AS folks "
           "WHERE entities=items AND items=entities "
           "GROUP BY fie,fee "
           "HAVING left=right AND right=left "
           "ORDER BY fum,foe "
           "LIMIT 3,4"
        )

class TestQueryGet(unittest.TestCase):

    maxDiff = None

    def test_get(self):

        query = relations.query.Query(
            selects={"this": "that", "that": "this"},
            froms={"persons": "people", "people": "persons"},
            wheres={"stuff": "things", "things": "stuff"},
            group_bys=["fee", "fie"],
            havings={"up": "down", "down": "up"},
            order_bys=["foe", "fum"],
            limits=[1,2],
            options=["DIS", "STINK"]
        )

        self.assertEqual(relations.query.get(query),
           "SELECT DIS STINK this AS that,that AS this "
           "FROM persons AS people,people AS persons "
           "WHERE stuff=things AND things=stuff "
           "GROUP BY fee,fie "
           "HAVING down=up AND up=down "
           "ORDER BY foe,fum "
           "LIMIT 1,2"
        )

        query = {
            "selects": {"this": "that", "that": "this"},
            "froms": {"persons": "people", "people": "persons"},
            "wheres": {"stuff": "things", "things": "stuff"},
            "group_bys": ["fee", "fie"],
            "havings": {"up": "down", "down": "up"},
            "order_bys": ["foe", "fum"],
            "limits": [1,2],
            "options": ["DIS", "STINK"]
        }

        self.assertEqual(relations.query.get(query),
           "SELECT DIS STINK this AS that,that AS this "
           "FROM persons AS people,people AS persons "
           "WHERE stuff=things AND things=stuff "
           "GROUP BY fee,fie "
           "HAVING down=up AND up=down "
           "ORDER BY foe,fum "
           "LIMIT 1,2"
        )

        query = (
           "SELECT DIS STINK this AS that,that AS this "
           "FROM persons AS people,people AS persons "
           "WHERE stuff=things AND things=stuff "
           "GROUP BY fee,fie "
           "HAVING down=up AND up=down "
           "ORDER BY foe,fum "
           "LIMIT 1,2"
        )

        self.assertEqual(relations.query.get(query),
           "SELECT DIS STINK this AS that,that AS this "
           "FROM persons AS people,people AS persons "
           "WHERE stuff=things AND things=stuff "
           "GROUP BY fee,fie "
           "HAVING down=up AND up=down "
           "ORDER BY foe,fum "
           "LIMIT 1,2"
        )
