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
        'relations.model.relation',
        'relations.restful',
        'relations.restful.resource',
        'relations.restful.source',
        'relations.restful.unittest',
        'relations.pymysql',
        'relations.psycopg2'
    ],
    install_requires=[
        'PyYAML==5.3.1',
        'PyMySQL==0.10.0',
        'psycopg2==2.8.6',
        'redis==3.5.2',
        'requests==2.24.0',
        'flask==1.1.2',
        'flask_restful==0.3.8'
    ]
)
