# -*- coding: utf8 -*-
#
# This file were created by Python Boilerplate. Use Python Boilerplate to start
# simple, usable and best-practices compliant Python projects.
#
# Learn more about it at: http://github.com/fabiommendes/python-boilerplate/
#

import os

from setuptools import setup, find_packages

# Meta information
version = open('VERSION').read().strip()
dirname = os.path.dirname(__file__)

# Save version and author to __meta__.py
path = os.path.join(dirname, 'totality', '__meta__.py')
data = '''# Automatically created. Please do not edit.
__version__ = u'%s'
__author__ = u'Beau Cronin'
''' % version
with open(path, 'wb') as F:
    F.write(data.encode())
    
setup(
    # Basic info
    name='totality-client',
    version=version,
    author='Beau Cronin',
    author_email='beau.cronin@gmail.com',
    url='https://github.com/str8d8a/totality-python',
    description='The official Python client for Totality',
    long_description=open('README.md').read(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Software Development :: Libraries',
    ],

    # Packages and depencies
    # package_dir={'': ''},
    packages=find_packages(''),
    install_requires=[
        'requests',
        'basket-case'
    ],
    extras_require={
        'dev': [
        ]
    },

    # Other configurations
    zip_safe=False,
    platforms='any',
)