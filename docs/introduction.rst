Introduction
============

Libinsdb is a client library for `InstrumentDB <https://instrumentdb.readthedocs.io/en/latest/?badge=latest>`_, a
database that can be used to hold specification and design documents about any scientific instrument. Libinsdb lets
to access the database either through its RESTful HTTP API or by directly reading a dump
of the database saved locally.

Here is an example showing how to access a local instance of an instrument database:

.. code-block:: python

    from libinsdb import LocalInsDb

    # The instrument database is kept locally: it was
    # dumped from a running InstrumentDB instance
    insdb = LocalInsDb(
        storage_path="/opt/my_database_dump",
    )

    data_file = insdb.query(
        "/releases/planck2021/LFI/frequency_030_ghz/bandpass",
    )

    print(f'Going to read file "{data_file.name}" from the database…")
    with data_file.open_data_file(insdb) as my_file:
        contents = my_file.read()


It's equally easy to access a remote database; in this case we access the demo
available at https://insdbdemo.fisica.unimi.it:

.. code-block:: python

    from libinsdb import RemoteInsDb

    # The instrument database is kept remotely, so we need
    # a username and a password to access it.
    insdb = RemoteInsDb(
        server_address="https://insdbdemo.fisica.unimi.it",
        username="demo",
        password="planckdbdemo",
    )

    data_file = insdb.query(
        "/releases/planck2021/LFI/frequency_030_ghz/bandpass",
    )

    print(f'Going to read file "{data_file.name}" from the database…")
    with data_file.open_data_file(insdb) as my_file:
        contents = my_file.read()

    # In the case of the Planck bandpasses, we know that they
    # are saved using UTF-8 encoding.
    print(contents.decode("utf-8"))



Local vs remote databases
-------------------------

As shown in the two examples above, Libinsdb lets you to interface a local copy or a remote database running the full server. There is one important difference between the two cases: you can alter the content of the database only if you are accessing a remote copy, while a local copy is always read-only. The reason for this is that changes in the database are handled by the remote InstrumentDB server, which implements full validation checks for every change.

