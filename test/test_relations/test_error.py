import unittest

import relations


class TestRelationsError(unittest.TestCase):

    maxDiff = None

    def test_hierarchy(self):

        self.assertTrue(issubclass(relations.RelationsError, Exception))

        errors = [
            relations.FieldError,
            relations.ModelError,
            relations.RecordError,
            relations.MigrationsError,
            relations.SourceError,
            relations.UniqueError,
            relations.NotFoundError,
            relations.MultipleError
        ]

        for error in errors:
            self.assertTrue(issubclass(error, relations.RelationsError), error)

        # a unique error is a model error too, so what caught one still does

        for error in [relations.UniqueError, relations.NotFoundError, relations.MultipleError]:
            self.assertTrue(issubclass(error, relations.ModelError))

        # one except catches all of them

        raised = [
            relations.FieldError("unittest", "oops"),
            relations.ModelError("unittest", "oops"),
            relations.RecordError("unittest", "oops"),
            relations.MigrationsError("oops"),
            relations.SourceError("oops"),
            relations.UniqueError("unittest", "oops"),
            relations.NotFoundError("unittest", "oops"),
            relations.MultipleError("unittest", "oops")
        ]

        for error in raised:
            with self.assertRaises(relations.RelationsError):
                raise error
