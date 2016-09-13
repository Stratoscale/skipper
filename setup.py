import os
from setuptools import find_packages
from distutils.core import setup



data_files = []
# Install data files only when installing as root
if os.getuid() == 0:
    data_files=[
        ('/etc/bash_completion.d', ['data/skipper-complete.sh']),
        ('/opt/skipper', ['data/skipper-entrypoint.sh']),
    ]

setup(
    name='strato-skipper',
    version='1.0.1',
    url='http://github.com/Stratoscale/skipper',
    author='Adir Gabai',
    author_email='adir@stratoscale.com',
    description='Easily dockerize your Git repository',
    packages=find_packages(include=['skipper*']),
    data_files=data_files,
    entry_points={
          'console_scripts': [
              'skipper = skipper.main:main',
          ],
      },
    install_requires=[
            'PyYAML>=3.11',
            'click>=6.6',
            'requests>=2.6.0',
            'tabulate>=0.7.5',
        ]
)
