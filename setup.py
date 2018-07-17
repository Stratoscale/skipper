import os
import sys
import setuptools 

# Workaround: bdist_wheel doesn't support absolute paths in data_files
# (see: https://bitbucket.org/pypa/wheel/issues/92). 
if os.getuid() == 0 and 'bdist_wheel' in sys.argv:
    raise RuntimeError("This setup.py does not support wheels")

setuptools.setup(
    setup_requires=[
        'pbr >= 1.9',
        'setuptools >= 17.1'
    ],
    pbr=True
)
