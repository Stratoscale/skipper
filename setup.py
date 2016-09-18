import os
from setuptools import find_packages
from distutils.core import setup


setup(
    setup_requires = [
        'pbr >= 1.9',
        'setuptools >= 17.1'
    ],
    pbr = True
)
