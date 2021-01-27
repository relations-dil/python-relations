import sys
import unittest
import unittest.mock

import relations.unittest
from relations import Model


class PeanutButter(Model):
    pass


class Jelly(Model):
    pass


class TestModelsPresent(unittest.TestCase):
    def test_models_returns_correct_with_class(self):

        module = sys.modules[__name__]
        models = relations.models(module)
        assert len(models) == 2
        assert PeanutButter in models
        assert Jelly in models

