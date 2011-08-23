import os
from distutils.core import setup

setup(
    name='python-hglib',
    version='0.1',
    author='Idan Kamara',
    author_email='idankk86@gmail.com',
    url='http://selenic.com/repo/python-hglib',
    description='Mercurial Python library',
    long_description=open(os.path.join(os.path.dirname(__file__), 'README')).read(),
    license='MIT',
    packages=['hglib'])
