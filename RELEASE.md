# How to prepare a new release

1. Update the version number both in `pyproject.toml` and in `libinsdb/__init__.py`
2. Update the CHANGELOG
3. Run `poetry update`
4. Push the changes to `master`
5. Run `poetry build`
6. Run `poetry publish`
7. Prepare a new release using GitHub's web interface

