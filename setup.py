import os
import sys
from setuptools import find_packages
from distutils.core import setup

# Workaround: bdist_wheel doesn't support absolute paths in data_files
# (see: https://bitbucket.org/pypa/wheel/issues/92). 
if os.getuid() == 0 and 'bdist_wheel' in sys.argv:
    raise RuntimeError("This setup.py does not support wheels")

setup(
    setup_requires = [
        'pbr >= 1.9',
        'setuptools >= 17.1'
    ],
    pbr = True
)
