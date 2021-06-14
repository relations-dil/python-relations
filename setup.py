#!/usr/bin/env python

from setuptools import setup
setup(
    name="relations",
    version="0.5.0",
    package_dir = {'': 'lib'},
    py_modules = [
        'relations',
        'relations.source',
        'relations.sql',
        'relations.query',
        'relations.unittest',
        'relations.field',
        'relations.labels',
        'relations.model',
        'relations.record',
        'relations.relation'
    ],
    install_requires=[]
)
