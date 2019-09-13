from setuptools import setup, find_packages


setup(
    name='newick',
    version="1.0.0",
    description='A python module to read and write the Newick format',
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author='The Glottobank consortium',
    author_email='forkel@shh.mpg.de',
    url='https://github.com/glottobank/python-newick',
    license="Apache 2",
    zip_safe=False,
    keywords='',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
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
