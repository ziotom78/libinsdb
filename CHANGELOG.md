# HEAD

# Version 0.9.0

-   Add a CLI program (`insdb`) to interactively browse a local database [#20](https://github.com/ziotom78/libinsdb/pull/20)

-   Drop support for Python 3.9 and add support for Python 3.13 [#19](https://github.com/ziotom78/libinsdb/pull/19)

# Version 0.8.0

-   Drop support for Python 3.8 and add support for Python 3.12 [#17](https://github.com/ziotom78/libinsdb/pull/17)

# Version 0.7.4

-   Fix a bug that caused errors even when accessing metadata in JSON files, if data files were not present [#16](https://github.com/ziotom78/libinsdb/pull/16)

# Version 0.7.3

-   Let the user specify the schema file name in `LocalInsDb` [#14](https://github.com/ziotom78/libinsdb/pull/14)

-   Add a link to a tutorial Jupyter notebook hosted on Google Colab [#11](https://github.com/ziotom78/libinsdb/pull/11)

# Version 0.7.2

-   Remove spurious DEBUG statement [e152872](https://github.com/ziotom78/libinsdb/commit/e1528724bdd8b06509b438d6297fdc19127483e9)

# Version 0.7.1

-   Fix an authentication problem with data files [#10](https://github.com/ziotom78/libinsdb/pull/10)

# Version 0.7.0

-   Be more tolerant with `/releases/` in data file paths [#8](https://github.com/ziotom78/libinsdb/pull/8)

# Version 0.6.0

-   Add `LocalInsDb.merge()` method to merge two databases [#7](https://github.com/ziotom78/libinsdb/pull/7)

# Version 0.5.0

-   Support schema.json.gz, schema.yaml, schema.yaml.gz files [#6](https://github.com/ziotom78/libinsdb/pull/6)

-   Fix flake8 warnings and MyPy type errors [#5](https://github.com/ziotom78/libinsdb/pull/5)

# Version 0.4.0

-   Support paths for `.query_entity()` and `.query_quantity()` [#4](https://github.com/ziotom78/libinsdb/pull/4)

# Version 0.3.0

-   Support dependencies in `RemoteInsDb.create_data_file` [#3](https://github.com/ziotom78/libinsdb/pull/3)

# Version 0.2.0

-   Add methods to `RemoteInsDb` to add/modify/delete objects in a remote database [#2](https://github.com/ziotom78/libinsdb/pull/2)

# Version 0.1.0

-   First public release
