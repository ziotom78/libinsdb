# How to prepare a new release

1. Update the version number in `docs/conf.py`, `pyproject.toml`, and `libinsdb/version.py`
2. Update the CHANGELOG
3. Push the changes to `master`
4. Run `uv build`
5. Run `uv publish dist/libinsdb-*.tar.gz`, changing `*` with the version you want to publish
6. Tag the release with `git tag -a vX.Y.Z` and run `git push --tags`
7. Prepare a new release using GitHub's web interface
