
Releasing python-newick
=======================

Clone glottobank/python-newick and switch to the master branch. Then:

- Do platform test via tox:
  ```
  $ tox -r
  ```
  Make sure statement coverage is at 100%

- Make sure flake8 passes::
  ```
  $ flake8 --ignore=E711,E712,D100,D101,D103,D102,D301 --max-line-length=100 .
  ```

- Change version to the new version number in `setup.py`

- Bump version number:
  ```
  $ git commit -a -m"bumped version number"
  ```

- Create a release tag:
  ```
  $ git tag -a v<version> -m"first version to be released on pypi"
  ```

- Push to github:
  ```
  $ git push origin
  $ git push --tags
  ```

- Make sure your system Python has ``setuptools-git`` installed and release to
  PyPI::
  ```
  $ git checkout tags/v$1
  $ python setup.py sdist register upload
  ```
