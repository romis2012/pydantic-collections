import codecs
import os
import re
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

version = None

with codecs.open(os.path.join(os.path.abspath(os.path.dirname(__file__)),
                              'pydantic_collections', '__init__.py'), 'r', 'latin1') as fp:
    try:
        version = re.findall(r"^__version__ = '([^']+)'\r?$", fp.read(), re.M)[0]
    except IndexError:
        raise RuntimeError('Unable to determine version.')

if sys.version_info < (3, 7, 1):
    raise RuntimeError('pydantic-collections requires Python 3.6.1+')

with open('README.md') as f:
    long_description = f.read()

setup(
    name='pydantic-collections',
    author='Roman Snegirev',
    author_email='snegiryev@gmail.com',
    version=version,
    license='Apache 2',
    url='https://github.com/romis2012/pydantic-collections',
    description='Collections of pydantic models',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=['pydantic_collections'],
    keywords='python pydantic validation parsing serialization models',
    install_requires=['pydantic>=1.8.2']
)
