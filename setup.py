# -*- coding: utf-8 -*-
from setuptools import setup


requires = []


def read(fname):
    with open(fname) as fp:
        content = fp.read()
    return content


setup(
    name='newick',
    version="0.6.0",
    description='A python module to read and write the Newick format',
    long_description=read("README.md"),
    author='The Glottobank consortium',
    author_email='forkel@shh.mpg.de',
    url='https://github.com/glottobank/python-newick',
    install_requires=requires,
    license="Apache 2",
    zip_safe=False,
    keywords='',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy'
    ],
    py_modules=["newick", "tests"],
    tests_require=['nose', 'coverage'],
)
