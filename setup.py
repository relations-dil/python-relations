#!/usr/bin/env python

from setuptools import setup
setup(
    name="python-relations",
    version="0.6.8",
    package_dir = {'': 'lib'},
    py_modules = [
        'relations',
        'relations.source',
        'relations.unittest',
        'relations.field',
        'relations.titles',
        'relations.model',
        'relations.record',
        'relations.relation',
        'relations.migrations'
    ],
    install_requires=[]
)
