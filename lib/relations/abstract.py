"""
Module for registering and access sources
"""

SOURCES = {}


def register(name, source):
    """
    Register a source
    """

    SOURCES[name] = source


def access(name):
    """
    Access a source
    """

    return SOURCES[name]
