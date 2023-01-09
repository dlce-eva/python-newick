# python-newick

[![Build Status](https://github.com/dlce-eva/python-newick/workflows/tests/badge.svg)](https://github.com/dlce-eva/python-newick/actions?query=workflow%3Atests)
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

### Supported Newick dialects

#### Quoted node labels

Node labels in Newick may be quoted (i.e. enclosed in single quotes `'`) to make it possible to
add characters which are otherwise reserved to names. The `newick` package supports quoted labels,
but this comes at the price far slower reading (since all relevant Newick syntax must be detected
in a quote-aware way).

```python
>>> from newick import loads
>>> print(loads("('A:B','C''D')'E(F)'")[0].ascii_art())
         ┌─'A:B'
──'E(F)'─┤
         └─'C''D'
```

When creating Newick trees programmatically, names can be quoted (if necessary) automatically:
```python
>>> from newick import Node
>>> print(Node("A(F')", auto_quote=True).name)
'A(F'')'
>>> print(Node("A(F')", auto_quote=True).unquoted_name)
A(F')
```


#### Additional information in comments

The ["Newick specification"](http://biowiki.org/wiki/index.php/Newick_Format) states

> Comments are enclosed in square brackets and may appear anywhere

This has spawned a host of ad-hoc mechanisms to insert additional data into Newick trees.

The `newick` package allows to deal with comments in two ways.

- Ignoring comments:
  ```python
  >>> newick.loads('[a comment](a,b)c;', strip_comments=True)[0].newick
  '(a,b)c'
  ```
- Reading comments as node annotations: Several software packages use Newick comments to 
  store node annotations, e.g. *BEAST, MrBayes or TreeAnnotator. Provided there are no
  comments in places where they cannot be interpreted as node annotations, `newick` supports
  reading and writing these annotations:
  ```python
  >>> newick.loads('(a[annotation],b)c;')[0].descendants[0].name
  'a'
  >>> newick.loads('(a[annotation],b)c;')[0].descendants[0].comment
  'annotation'
  >>> newick.loads('(a[annotation],b)c;')[0].newick
  '(a[annotation],b)c'
  ```
  Annotations may come before or after the `:` which separates node label and length:
- ```python
  >>> newick.loads('(a[annotation]:2,b)c;')[0].descendants[0].length
  2.0
  >>> newick.loads('(a:[annotation]2,b)c;')[0].descendants[0].length
  2.0
  ```

Note that square brackets inside *quoted labels* will **not** be interpreted as comments
or annotations:
```python
>>> newick.loads("('a[label]',b)c;")[0].descendants[0].name
"'a[label]'"
>>> newick.loads("('a[label]',b)c;")[0].newick
"('a[label]',b)c"
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

- Displaying tree topology in the terminal:
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
