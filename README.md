# python-newick

[![Build Status](https://github.com/dlce-eva/python-newick/workflows/tests/badge.svg)](https://github.com/dlce-eva/python-newick/actions?query=workflow%3Atests)
[![codecov.io](https://codecov.io/github/dlce-eva/python-newick/coverage.svg?branch=master)](https://codecov.io/github/dlce-eva/python-newick?branch=master)
[![PyPI](https://badge.fury.io/py/newick.svg)](https://pypi.org/project/newick)


python package to read and write the 
[Newick format](https://en.wikipedia.org/wiki/Newick_format).


## Reading Newick

- From a string:
```python
>>> from newick import loads
>>> trees = loads('(A,B,(C,D)E)F;')
>>> trees[0].name
'F'
>>> [n.name for n in trees[0].descendants]
['A', 'B', 'E']
```

- From  a `file`-like object:
```python
>>> import io
>>> from newick import load
>>> with io.open('fname', encoding='utf8') as fp:
...     trees = load(fp)
```

- From a file name:
```python
>>> from newick import read
>>> trees = read('fname')
```

## Writing Newick

In parallel to the read operations there are three functions to serialize a single `Node` object or a `list` of `Node`
objects to Newick format:
- `dumps(trees) -> str`
- `dump(trees, fp)`
- `write(trees, 'fname')`

A tree may be assembled using the factory methods of the `Node` class:
- `Node.__init__`
- `Node.create`
- `Node.add_descendant`
