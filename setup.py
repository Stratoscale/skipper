import io
import os
import sys
from setuptools import setup

# Workaround: bdist_wheel doesn't support absolute paths in data_files
# (see: https://bitbucket.org/pypa/wheel/issues/92). 
if os.getuid() == 0 and 'bdist_wheel' in sys.argv:
    raise RuntimeError("This setup.py does not support wheels")

# read the contents the README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with io.open(os.path.join(this_directory, 'README.md'), 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    setup_requires=[
        'pbr >= 1.9',
        'setuptools >= 17.1'
    ],
    pbr=True,
    long_description=long_description,
    long_description_content_type='text/markdown'
)
