# How to prepare a new release

1. Update the version number both in `pyproject.toml` and in `libinsdb/__init__.py`
2. Run `poetry update`
3. Push the changes to `master`
4. Run `poetry build`
5. Run `poetry publish`
6. Prepare a new release using GitHub's web interface

