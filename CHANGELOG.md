# Changes

The `newick` package adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]

Backwards incompatibility through bug-fix: newick will not (incorrectly) parse
invalid newick trees anymore, but raise `ValueError`.


## [v1.3.1] - 2021-10-14

Fixed support for node annotations for the case when annotations are between `:` and length.


## [v1.3.0] - 2021-05-04

Added support for reading and writing of node annotations (in comments).
