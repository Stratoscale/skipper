from setuptools import find_packages
from setuptools import setup
import os
import subprocess

setup(
    name='skipper',
    version='0.0.1',
    url='http://github.com/Stratoscale/skipper',
    author='Adir Gabai',
    author_mail='adir@stratoscale.com',
    packages=find_packages(include=['skipper*'])
)
