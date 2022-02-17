"""
Main relations module
"""

import re
import inspect

from relations.source import Source
from relations.field import Field, FieldError
from relations.titles import Titles
from relations.record import Record, RecordError
from relations.model import Model, ModelIdentity, ModelError
from relations.relation import Relation, OneTo, OneToOne, OneToMany
from relations.migrations import Migrations, MigrationsError

INDEX = re.compile(r'^-?\d+$')

SOURCES = {}  # Sources reference to use

def register(new_source):
    """
    Registers a source
    """

    SOURCES[new_source.name] = new_source


def source(name):
    """
    Returns a source
    """

    return SOURCES.get(name)


def models(module, from_base=None):
    """
    Returns all models
    Args:
        module (str): Python module in which to search.
        from_base (type, optional): Base class from which to filter children of
    """
    from_base = from_base or Model
    return [
        m[1]
        for m in inspect.getmembers(
            module,
            lambda model: inspect.isclass(model)
            and issubclass(model, from_base)
            and model is not from_base,
        )
    ]
