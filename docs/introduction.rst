Introduction
============

Libinsdb is a client library for `InstrumentDB <https://instrumentdb.readthedocs.io/en/latest/?badge=latest>`_, a
database that can be used to hold specification and design documents about any scientific instrument. Libinsdb lets
to access the database either through its RESTful HTTP API or by directly reading a dump
of the database saved locally.

Here is an example showing how to use it:

.. code-block:: python

    from libinsdb import InstrumentDatabase

    insdb = InstrumentDatabase(
        local_folder="/opt/my_database_dump",
    )

    data_file = insdb.query_data_file(
        "/releases/v1.0/telescope/primary_mirror/design/cad20230101.step"
    )

