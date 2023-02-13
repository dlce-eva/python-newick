# Changes

The `newick` package adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [v1.7.0] - 2023-02-13

Big performance improvement of parser by switching to accumulated tokens.


## [v1.6.0] - 2023-01-11

Support reading key-value data from node comments.


## [v1.5.0] - 2023-01-09

Full support for quoted labels and (nested) comments.


## [v1.4.0] - 2022-12-06

- Drop py3.6 compatibility
- Run tests on py3.11
- Added type hints.


## [v1.3.2] - 2021-12-14

- Backwards incompatibility through bug-fix: newick will not (incorrectly) parse
  invalid newick trees anymore, but raise `ValueError`.
- Run tests on py 3.10 as well.


## [v1.3.1] - 2021-10-14

Fixed support for node annotations for the case when annotations are between `:` and length.


## [v1.3.0] - 2021-05-04

Added support for reading and writing of node annotations (in comments).
