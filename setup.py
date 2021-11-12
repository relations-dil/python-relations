#!/usr/bin/env python

from setuptools import setup
setup(
    name="relations",
    version="0.6.4",
    package_dir = {'': 'lib'},
    py_modules = [
        'relations',
        'relations.source',
        'relations.unittest',
        'relations.field',
        'relations.labels',
        'relations.model',
        'relations.record',
        'relations.relation',
        'relations.migrations'
    ],
    install_requires=[]
)
