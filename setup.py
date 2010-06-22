#!/usr/bin/env python # -- coding: utf-8 --

__version__ = '1.0dev'

import os
import sys
import itertools

from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.rst')).read()

ROLES = """\
.. role:: mod(emphasis)
.. role:: term(emphasis)
"""

long_description = "\n\n".join((
    ROLES, README, CHANGES))
long_description = long_description.replace('.. code-block:: python', '::')

version = sys.version_info[:3]

install_requires = [
    'Django',
    'Django-Treebeard',
    'Django-Notify',
    'PasteScript',
    'PasteDeploy',
    'Iso8601',
    'Picoparse',
    'PyYaml',
    'Manuel',
    ]

setup(
    name="DjangoSMS",
    version=__version__,
    description="Messaging platform based on Python and the Django Web Framework",
    long_description=long_description,
    classifiers=[
       "Development Status :: 3 - Alpha",
       "Intended Audience :: Developers",
       "Programming Language :: Python",
      ],
    keywords="django sms",
    author="Malthe Borch and DjangoSMS community",
    author_email="mborch@gmail.com",
    install_requires=install_requires,
    license='BSD',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    tests_require = install_requires + ['manuel', 'nose'],
    entry_points="""
    [paste.app_factory]
    main = djangosms.core.wsgi:make_app
    """,
    )

