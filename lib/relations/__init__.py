"""
Main relations module for storing sources
"""

SOURCES = {}  # Sources reference to use

class Source:

    MODEL = None # Default model class to use when casting

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
