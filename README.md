# Libinsdb

A library to interface Python scripts with an [InstrumentDB](https://github.com/ziotom78/instrumentdb) database.

## Documentation

A tutorial is avilable on [Google Colab](https://colab.research.google.com/drive/1GRCssFs_lGfku1DLvvEowW4fTKUSsLK6?usp=sharing).

The manual is available at <https://libinsdb.readthedocs.io/en/latest/>.

To build a copy of the documentation locally, run

    poetry install --with docs

to install the additional dependencies needed to update the documentation and then run

    poetry run make -C docs html

The index will be available in the folder `docs/_build/html/`.
