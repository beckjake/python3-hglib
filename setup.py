import os, time
from distutils.core import setup

#Don't query mercurial for the version number because we're in git now
version = "0.1"

setup(
    name='python3-hglib',
    version=version,
    author='Jacob Beck',
    author_email='beckjake@gmail.com',
    url="//github.com/beckjake/python3-hglib.git",
    description='Mercurial Python library - Python3 port',
    long_description=open(os.path.join(os.path.dirname(__file__), 'README')).read(),
    license='MIT',
    packages=['hglib'])
