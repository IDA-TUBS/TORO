#!/usr/bin/env python

"""
| Copyright (C) 2020 Alex Bendrick
| TU Braunschweig, Germany
| All rights reserved.
| See LICENSE file for copyright and license details.

:Authors:
         - Alex Bendrick

Description
-----------

Setup
"""


from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="TORO",
    version="2.0",
    author="Alex Bendrick",
    author_email="al.bendrick@googlemail.com",
    description="TORO Tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/IDA-TUBS/TORO",
    license="MIT",
    packages=setuptools.find_packages(),
    install_requires=['argparse','setuptools', 'dill', 'networkx', 'matplotlib'], # and more
    python_requires='>=3.6, <4',
    classifiers=['Programming Language :: Python :: 3.6', 'Operating System :: OS Independent'],
)

# there has to be a better way to check for missing packages that can not be installed directly using pip
missing_packages = list()
optional_missing = list()
try:
    import graph_tool
except:
    missing_packages.append('graph_tool')
try:
    import pycpa
except:
    missing_packages.append('pyCPA')
try:
    import Amalthea2PyCPA
except:
    optional_missing.append('Amalthea2PyCPA')

if len(optional_missing) > 0:
    print("The following optional packages can to be installed manually: " + str(optional_missing))

if len(missing_packages) > 0:
    quit("The following packages need to be installed manually before proceeding: " + str(missing_packages))