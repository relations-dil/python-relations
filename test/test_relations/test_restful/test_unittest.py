import unittest
import unittest.mock
import relations.restful.unittest


class TestUnitTest(relations.restful.unittest.TestCase):

    def test_consistent(self):

        # dict

        self.assertTrue(self.consistent({"a": 1}, {"a": 1, "b": 2}))
        self.assertFalse(self.consistent({"a": 2}, {"a": 1, "b": 2}))

        # list

        self.assertTrue(self.consistent([1, 2], [1, 2, 3]))
        self.assertFalse(self.consistent([1, 2, 4], [2, 1]))
        self.assertFalse(self.consistent([1, 2], [2, 1]))

        # else

        self.assertTrue(self.consistent("a", "a"))
        self.assertFalse(self.consistent("a", "b"))

    def test_contains(self):

        self.assertTrue(self.contains({"a": 1}, [{"a": 1, "b": 2}]))
        self.assertFalse(self.contains({"a": 2}, [{"a": 1, "b": 2}]))

    def test_assertConsistent(self):

        self.assertConsistent({"a": 1}, {"a": 1, "b": 2})

        with unittest.mock.patch('relations.restful.unittest.TestCase.assertEqual') as mock_equal:

            self.assertConsistent({"a": 2}, {"a": 1, "b": 2}, "nope")
            mock_equal.assert_called_once_with({"a": 2}, {"a": 1, "b": 2}, "nope")

    def test_assertContains(self):

        self.assertContains({"a": 1}, [{"a": 1, "b": 2}])

        with unittest.mock.patch('relations.restful.unittest.TestCase.assertIn') as mock_in:

            self.assertContains({"a": 2}, [{"a": 1, "b": 2}], "nope")
            mock_in.assert_called_once_with({"a": 2}, [{"a": 1, "b": 2}], "nope")

    def test_assertassertStatusValue(self):

        response = unittest.mock.MagicMock()

        response.status_code = 200
        response.json = {"a": 1}

        self.assertStatusValue(response, 200, "a", 1)

    def test_assertStatusModel(self):

        response = unittest.mock.MagicMock()

        response.status_code = 200
        response.json = {
            "model": {"a": 1}
        }

        self.assertStatusModel(response, 200, "model", {"a": 1})

    def test_assertStatusModels(self):

        response = unittest.mock.MagicMock()

        response.status_code = 200
        response.json = {
            "models": [
                {"a": 1}
            ]
        }

        self.assertStatusModels(response, 200, "models", [{"a": 1}])
