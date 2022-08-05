#!/usr/bin/env python

from setuptools import setup

with open("README.md", "r") as readme_file:
    long_description = readme_file.read()

setup(
    name="relations-dil",
    version="0.6.11",
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
    install_requires=[],
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
