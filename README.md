# python-newick

[![Build Status](https://github.com/dlce-eva/python-newick/workflows/tests/badge.svg)](https://github.com/dlce-eva/python-newick/actions?query=workflow%3Atests)
[![codecov.io](https://codecov.io/github/dlce-eva/python-newick/coverage.svg?branch=master)](https://codecov.io/github/dlce-eva/python-newick?branch=master)
[![PyPI](https://badge.fury.io/py/newick.svg)](https://pypi.org/project/newick)

python package to read and write the 
[Newick format](https://en.wikipedia.org/wiki/Newick_format).


## Reading Newick

Since Newick specifies a format for a set of trees, all functions to read Newick return
a `list` of `newick.Node` objects.

- Reading from a string:
  ```python
  >>> from newick import loads
  >>> trees = loads('(A,B,(C,D)E)F;')
  >>> trees[0].name
  'F'
  >>> [n.name for n in trees[0].descendants]
  ['A', 'B', 'E']
  ```

- Reading from  a `file`-like object:
```python
>>> import io
>>> from newick import load
>>> with io.open('fname', encoding='utf8') as fp:
...     trees = load(fp)
```

- Reading from a path:
```python
>>> from newick import read
>>> trees = read('fname')
>>> import pathlib
>>> trees = read(pathlib.Path('fname'))
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


## Manipulating trees

- Diyplaying tree topology in the terminal:
  ```python
  >>> import newick
  >>> tree = newick.loads('(b,(c,(d,(e,(f,g))h)i)a)')[0]
  >>> print(tree.ascii_art())
      ┌─b
  ────┤
      │   ┌─c
      └─a─┤
          │   ┌─d
          └─i─┤
              │   ┌─e
              └─h─┤
                  │   ┌─f
                  └───┤
                      └─g
  ```
- Pruning trees: The example below prunes the tree such that `b`, `c` and `i` are the only
  remaining leafs.
  ```python
  >>> tree.prune_by_names(['b', 'c', 'i'], inverse=True)
  >>> print(tree.ascii_art())
      ┌─b
  ────┤
      │   ┌─c
      └─a─┤
          └─i
  ```
- Running a callable on a filtered set of nodes:
  ```python
  >>> tree.visit(lambda n: setattr(n, 'name', n.name.upper()), lambda n: n.name in ['a', 'b'])
  >>> print(tree.ascii_art())
      ┌─B
  ────┤
      │   ┌─c
      └─A─┤
          └─i
  ```
- Removing (topologically) redundant internal nodes:
  ```python
  >>> tree.prune_by_names(['B', 'c'], inverse=True)
  >>> print(tree.ascii_art())
      ┌─B
  ────┤
      └─A ──c
  >>> tree.remove_redundant_nodes(keep_leaf_name=True)
  >>> print(tree.ascii_art())
      ┌─B
  ────┤
      └─c
  ```
