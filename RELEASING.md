
Releasing python-newick
=======================

Clone dlce-eva/python-newick and switch to the master branch. Then:

- Do platform test via tox:
  ```
  $ tox -r
  ```
  Make sure statement coverage is at 100%

- Make sure flake8 passes::
  ```
  $ flake8 src
  ```

- Edit `CHANGELOG.md`.

- Change the version to the new version number in
  - `setup.py`
  - `src/newick.py`
  - and note changes in `CHANGELOG.md`

- Create the release commit:
```shell
git commit -a -m "release <VERSION>"
```

- Create a release tag:
```shell
git tag -a v<VERSION> -m "<VERSION> release"
```

- Release to PyPI:
```shell
git checkout tags/v<VERSION>
rm dist/*
python setup.py sdist bdist_wheel
twine upload dist/*
```

- Push to github:
```shell
git push origin
git push --tags origin
```

- Append `.dev0` to the version number for the new development cycle in
  - `setup.py`
  - `src/newick.py`

- Commit/push the version change:
```shell
git commit -a -m "bump version for development"
git push origin
```
