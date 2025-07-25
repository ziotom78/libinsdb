# Libinsdb

[![CI](https://github.com/ziotom78/libinsdb/actions/workflows/tests.yml/badge.svg)](https://github.com/ziotom78/libinsdb/actions/workflows/tests.yml)
[![Documentation Status](https://readthedocs.org/projects/libinsdb/badge/?version=latest)](https://libinsdb.readthedocs.io/en/latest/)
[![PyPI version](https://img.shields.io/pypi/v/libinsdb.svg)](https://pypi.org/project/libinsdb/)
[![Python versions](https://img.shields.io/pypi/pyversions/libinsdb.svg)](https://pypi.org/project/libinsdb/)
[![License](https://img.shields.io/pypi/l/libinsdb.svg)](https://github.com/ziotom78/libinsdb/blob/main/LICENSE.md)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-orange)](https://docs.astral.sh/ruff/)
[![Checked with MyPy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)

A library to interface Python scripts with an [InstrumentDB](https://github.com/ziotom78/instrumentdb) database.

## Documentation

A tutorial is avilable on [Google Colab](https://colab.research.google.com/drive/1GRCssFs_lGfku1DLvvEowW4fTKUSsLK6?usp=sharing).

The manual is available at <https://libinsdb.readthedocs.io/en/latest/>.

To build a copy of the documentation locally, run

    uv install --with docs

to install the additional dependencies needed to update the documentation and then run

    uv run make -C docs html

The index will be available in the folder `docs/_build/html/`.

## Browsing the databases from the CLI

Starting from version 0.9, Libinsdb includes a command-line program, `insdb`, that can be used to browse a local database.

![](demo.gif)
