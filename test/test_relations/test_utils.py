import sys
import unittest
import unittest.mock

import relations.unittest
from relations import Model


class PeanutButter(Model):
    pass


class Jelly(Model):
    pass


class Time(Jelly):
    pass


class TestModelsPresent(unittest.TestCase):
    def test_models_returns_correct_with_class(self):

        module = sys.modules[__name__]
        models = relations.models(module)
        assert len(models) == 3
        assert PeanutButter in models
        assert Jelly in models
        assert Time in models

    def test_models_from_base_works(self):

        module = sys.modules[__name__]
        models = relations.models(module, from_base=Jelly)
        assert len(models) == 1
        assert Time in models
        assert Jelly not in models
