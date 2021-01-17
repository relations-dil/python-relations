"""
Main relations module
"""

from relations.source import Source
from relations.field import Field, FieldError
from relations.record import Record, RecordError
from relations.model import Model, ModelIdentity, ModelError
from relations.relation import Relation, OneTo, OneToOne, OneToMany

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
