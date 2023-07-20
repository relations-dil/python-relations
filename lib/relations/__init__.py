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
from relations.relation import Relation, OneTo, OneToOne, OneToMany, ManyToMany
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


def models(module, from_base=Model):
    """
    Returns all models, based on mode
    """

    found = []

    for _, model in inspect.getmembers(module):

        if not inspect.isclass(model) or not issubclass(model, from_base) or model is from_base:
            continue

        found.append(model)

    return found
