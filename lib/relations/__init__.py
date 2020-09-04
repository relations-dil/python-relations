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

def __getattr__(name):
    """
    Used to get a source
    """

    return SOURCES[name]

def __getitem__(name):
    """
    Used to get a source
    """

    return SOURCES[name]
