import os
import re
import sys

from setuptools import setup

if sys.version_info < (3, 7, 1):
    raise RuntimeError('pydantic-collections requires Python 3.7.1+')


def get_version():
    here = os.path.dirname(os.path.abspath(__file__))
    filename = os.path.join(here, 'pydantic_collections', '__init__.py')
    contents = open(filename).read()
    pattern = r"^__version__ = '(.*?)'$"
    return re.search(pattern, contents, re.MULTILINE).group(1)


def get_long_description():
    with open('README.md', mode='r', encoding='utf8') as f:
        return f.read()


setup(
    name='pydantic-collections',
    author='Roman Snegirev',
    author_email='snegiryev@gmail.com',
    version=get_version(),
    license='Apache 2',
    url='https://github.com/romis2012/pydantic-collections',
    description='Collections of pydantic models',
    long_description=get_long_description(),
    long_description_content_type='text/markdown',
    packages=['pydantic_collections'],
    keywords='python pydantic validation parsing serialization models',
    install_requires=['pydantic>=1.8.2,<3.0', 'typing_extensions>=4.7.1'],
)
