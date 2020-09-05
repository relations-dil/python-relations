"""
Main relations module for storing sources
"""

SOURCES = {}

class Source:

    def __init__(self, name):

        self.name = name
        self.register()

    def register(self):
        """
        Register a source
        """

        SOURCES[self.name] = self

def source(name):
    """
    Used to get a source
    """

    return SOURCES[name]
