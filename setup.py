#!/usr/bin/env python

import os
from setuptools import setup

with open("README.md", "r") as readme_file:
    long_description = readme_file.read()

version = os.environ.get("BUILD_VERSION")

if version is None:
    with open("VERSION", "r") as version_file:
        version = version_file.read().strip()

setup(
    name="relations-dil",
    version=version,
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
    install_requires=[
        'overscore==0.1.1'
    ],
    url="https://github.com/relations-dil/python-relations",
    author="Gaffer Fitch",
    author_email="relations@gaf3.com",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license_files=('LICENSE.txt',),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License"
    ]
)
