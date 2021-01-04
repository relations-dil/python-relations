#!/usr/bin/env python

from setuptools import setup, find_packages
setup(
    name="relations",
    version="0.1.0",
    package_dir = {'': 'lib'},
    py_modules = [
        'relations',
        'relations.sql',
        'relations.query',
        'relations.unittest',
        'relations.model',
        'relations.model.field',
        'relations.model.model',
        'relations.model.record',
        'relations.model.relation'
    ],
    install_requires=[]
)
