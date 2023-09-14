# Libinsdb

A library to interface Python scripts with an [InstrumentDB](https://github.com/ziotom78/instrumentdb) database.

## Documentation

The manual is available at <https://libinsdb.readthedocs.io/en/latest/>.

To build a copy of the documentation locally, run

    poetry install --with docs

to install the additional dependencies needed to update the documentation and then run

    poetry run make -C docs html

The index will be available in the folder `docs/_build/html/`.
