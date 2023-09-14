Tutorial
========

In this tutorial, we will see how Libinsdb can be used to access the contents of an instance of `InstrumentDB <https://github.com/ziotom78/instrumentdb>`_. We will make use of the demo site https://insdbdemo.fisica.unimi.it, which is an instance of InstrumentDB containing a reduced set of information related to the `ESA Planck spacecraft <https://www.esa.int/Science_Exploration/Space_Science/Planck>`_.

Creating a virtual environnment
-------------------------------

Typically, the first thing you want to do when working on a Python project is to create a virtual environment for this tutorial so that you do not mess up with your global Python interpreter. You can create a virtual environment using the `venv` module:

.. code-block:: sh

    python3 -m venv ./venv

    # This works under Linux and a bash-like shell
    source ./venv/bin/activate

This command will create a new virtual environment in the ``venv`` folder and will activate it. (See the `official documentation <https://docs.python.org/3/tutorial/venv.html>`_ to learn how to activate the environment under different environments than Linux/bash.)

Installing Libinsdb
-------------------

Once you have activate your virtual environment, you can install Libinsdb using ``pip``:

.. code-block:: sh

    pip3 install libinsdb

Refer to :ref:`Installation` for further details.

Connecting to the database
--------------------------

Once Libinsdb is installed, we can use it in our codes. As stated above, we will use https://insdbdemo.fisica.unimi.it as our instrument database, so let's connect to it::

    from libinsdb import RemoteInsDb

    insdb = RemoteInsDb(
        server_address="https://insdbdemo.fisica.unimi.it",
        username="demo",
        password="planckdbdemo",
    )

In this case, we are providing the username ``demo`` and the password in cleartext through the code. However, this is applicable to the demo site, not in general: you should typically load these information either from the command line or from a parameter file; in the latter case, be sure *not* to upload this parameter file to any public repository (GitHub, GitLab, BitBucket, etc.), otherwise your credentials for the InstrumentDB website will be compromised!

Accessing information
---------------------

Once you have a working connection to the database, you can run queries using one of the methods :meth:`.InstrumentDatabase.query_entity`, :meth:`.InstrumentDatabase.query_quantity`, :meth:`.InstrumentDatabase.query_format_spec`, :meth:`.InstrumentDatabase.query_release`, :meth:`.InstrumentDatabase.query_data_file`. Each of them returns an object of the appropriate type:

- :class:`.Entity`;
- :class:`.Quantity`;
- :class:`.FormatSpecification`;
- :class:`.DataFile`.

Let's retrieve information about a data file::

    data_file = insdb.query_data_file(
        "/releases/planck2021/LFI/frequency_030_ghz/bandpass"
    )

The method returns a new instance of the :class:`.DataFile` class. If a real file is associated with the class, you can open it using the :meth:`.DataFile.open_data_file` method::

    with data_file.open_data_file(insdb) as my_file:
        contents = my_file.read()

Remember that the file is always opened in binary mode; thus, if you know it is a text file you can retrieve a string from ``contents`` via the ``decode`` method::

    decoded_contents = contents.decode("utf-8")

