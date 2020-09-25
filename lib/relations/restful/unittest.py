"""
Module for unittesting and mocking general klot-io functionality
"""

#pylint: disable=unused-argument,invalid-name

import unittest

class TestCase(unittest.TestCase):
    """
    Extended unittest.TestCase with asserts used with klot-io
    """

    maxDiff = None

    def consistent(self, first, second):
        """
        A loose equals for checking only the parts of dictionares and lists you care about
        {"a": 1} is consistent with {"a": 1, "b": 2} while {"a": 2} is not
        [1,2] is consistent with [1,2,3] but [1,2,4] is not. Neither is [2,1]
        """

        if isinstance(first, dict) and isinstance(second, dict):

            for first_key, first_item in first.items():
                if first_key not in second or not self.consistent(first_item, second[first_key]):
                    return False

        elif isinstance(first, list) and isinstance(second, list):

            second_index = 0

            for first_item in first:

                found = False

                for second_index, second_item in enumerate(second[second_index:]):
                    if self.consistent(first_item, second_item):
                        found = True
                        break

                if not found:
                    return False

        else:

            return first == second

        return True

    def contains(self, member, container):
        """
        Checks to see if members is conistent with an item within container
        """

        for item in container:
            if self.consistent(member, item):
                return True

        return False

    def assertConsistent(self, first, second, message=None):
        """
        Asserts first is consistent with second
        """

        if not self.consistent(first, second):
            self.assertEqual(first, second, message)

    def assertContains(self, member, container, message=None):
        """
        Asserts member is contained within second
        """

        if not self.contains(member, container):
            self.assertIn(member, container, message)

    def assertStatusValue(self, response, code, key, value):
        """
        Assert a response's code and keyed json value are equal.
        Good with checking API responses in full with an outout
        of the json if unequal
        """

        self.assertEqual(response.status_code, code, response.json)
        self.assertEqual(response.json[key], value)

    def assertStatusModel(self, response, code, key, model):
        """
        Assert a response's code and keyed json model are consitent.
        Good with checking API responses of creates, gets with an outout
        of the json if inconsistent
        """

        self.assertEqual(response.status_code, code, response.json)
        self.assertConsistent(model, response.json[key])

    def assertStatusModels(self, response, code, key, models):
        """
        Assert a response's code and keyed json models are consitent.
        Good with checking API responses of lists with an outout
        of the json if inconsistent
        """

        self.assertEqual(response.status_code, code, response.json)

        for index, model in enumerate(models):
            self.assertConsistent(model, response.json[key][index])
