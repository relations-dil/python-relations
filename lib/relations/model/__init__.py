"""
Base Model module
"""

from relations.model.field import Field, FieldError
from relations.model.record import Record, RecordError
from relations.model.model import Model, ModelIdentity, ModelError
from relations.model.relation import Relation, OneTo, OneToOne, OneToMany
