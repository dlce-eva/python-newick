# python-newick

> [!IMPORTANT]  
> This project has been moved to https://gitlab.mpcdf.mpg.de/dlce-eva/python-newick

python package to read and write the 
[Newick format](https://en.wikipedia.org/wiki/Newick_format).


## Reading Newick

Since Newick specifies a format for a **set of trees**, all functions to read Newick return
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

While the set of reserved characters in Newick (`;(),:`) is relatively small, it's still often
seen as too restrictive, in particular when it comes to adding more data to tree nodes. Thus, Newick
provides two mechanisms to overcome this restriction:
- *quoted labels* to allow arbitrary text as node names,
- *comments* enclosed in square brackets.


#### Quoted node labels

Node labels in Newick may be quoted (i.e. enclosed in single quotes `'`) to make it possible to
add characters which are otherwise reserved. The `newick` package supports quoted labels.

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

Note: `newick` provides no support to parse structured data from node labels (as it can be found
in the trees distributed by the Genome Taxonomy Database).


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
  Annotations may come before and/or after the `:` which separates node label and length:
- ```python
  >>> newick.loads('(a[annotation]:2,b)c;')[0].descendants[0].length
  2.0
  >>> newick.loads('(a:[annotation]2,b)c;')[0].descendants[0].length
  2.0
  >>> newick.loads('(a[annotation1]:[annotation2]2,b)c;')[0].descendants[0].comments
  ['annotation1', 'annotation2']
  ```

Note that square brackets inside *quoted labels* will **not** be interpreted as comments
or annotations:
```python
>>> newick.loads("('a[label]',b)c;")[0].descendants[0].name
"'a[label]'"
>>> newick.loads("('a[label]',b)c;")[0].newick
"('a[label]',b)c"
```

Some support for reading key-value data from node comments is available as well. If the comment
format follows the [NHX](https://en.wikipedia.org/wiki/Newick_format#New_Hampshire_X_format) spec
or the `&<key>=<value>,...`-format used e.g. by the MrBayes or BEAST software, additional data
can be accessed from the `dict` `Node.properties`:
```python
>>> newick.loads('(A,B)C[&&NHX:k1=v1:k2=v2];')[0].properties
{'k1': 'v1', 'k2': 'v2'}
```

**Limitations:**

- **Typed** node properties are not supported. I.e. values in `Node.properties` are
  always strings. Since typed properties tend to be specific to the application writing the newick,
  this level of support would require more knowledge of the creation context of the tree than can
  safely be inferred from the Newick string alone.
  ```python
  >>> newick.loads('(A,B)C[&range={1,5},support="100"];')[0].properties
  {'range': '{1,5}', 'support': '"100"'}
  ```
- Node annotations in comments are not completely round-trip-safe. In particular multiple comments
  per node may be lumped together (using `|` as separator) when serializing a Newick node:
  ```python
  >>> newick.loads('(a,b)c[c1][c2]:3')[0].newick
  '(a,b)c[c1|c2]:3'
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
