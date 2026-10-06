"""
Main relations module
"""

import re
import inspect

from relations.source import Source, SourceError
from relations.field import Field, FieldError
from relations.titles import Titles
from relations.record import Record, RecordError
from relations.model import Model, ModelIdentity, ModelError
from relations.relation import Relation, OneTo, OneToOne, OneToMany, ManyToMany
from relations.migrations import Migrations, MigrationsError

INDEX = re.compile(r'^-?\d+$')
DNS = re.compile(r'^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\Z', re.IGNORECASE) # A dns label, what sources have to be named

SOURCES = {}  # Sources reference to use

def register(new_source):
    """
    Registers a source, its name has to be dns compliant so it's safe to use in names
    """

    if not isinstance(new_source.name, str) or not DNS.match(new_source.name):
        raise SourceError(f"source {new_source.name} is not dns compliant")

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
