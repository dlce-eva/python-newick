# -*- coding: utf-8 -*-
from setuptools import setup, find_packages


requires = []


def read(fname):
    with open(fname) as fp:
        content = fp.read()
    return content


setup(
    name='newick',
    version="0.9.2",
    description='A python module to read and write the Newick format',
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    author='The Glottobank consortium',
    author_email='forkel@shh.mpg.de',
    url='https://github.com/glottobank/python-newick',
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
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy'
    ],
    py_modules=["newick"],
    install_requires=[],
    extras_require={
        'dev': [
            'flake8',
            'wheel',
            'twine',
        ],
        'test': [
            'ddt',
            'pytest>=3.1',
            'pytest-mock',
            'mock',
            'coverage>=4.2',
            'pytest-cov',
        ],
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
)
