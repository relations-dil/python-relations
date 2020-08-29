#!/usr/bin/env python

from setuptools import setup, find_packages
setup(
    name="relations",
    version="0.1",
    package_dir = {'': 'lib'},
    py_modules = ['relations', 'relations.sql', 'relations.query'],
    install_requires=[
        'PyYAML==5.3.1',
        'PyMySQL==0.10.0',
        'redis==3.5.2',
        'requests==2.24.0'
    ]
)
