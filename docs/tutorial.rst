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

Refer to :ref:`installation-label` for further details.

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

(The path we have used here is the one shown at the bottom of the page https://insdbdemo.fisica.unimi.it/browse/data_files/f155cb37-d12e-4645-952f-014086094613/.)
The method returns a new instance of the :class:`.DataFile` class. If a real file is associated with the class, you can open it using the :meth:`.DataFile.open_data_file` method::

    with data_file.open_data_file(insdb) as my_file:
        contents = my_file.read()

Remember that the file is always opened in binary mode; thus, if you know it is a text file you can retrieve a string from ``contents`` via the ``decode`` method::

    decoded_contents = contents.decode("utf-8")


Modifying the content of the database
-------------------------------------

If you are accessing a local copy of the database, only read-only operations are enabled. However, if you instantiate an object of type :class:`.RemoteInsDb` and your user has the proper access rights, then additional methods are available with respect to :class:`.LocalInsDb`:

- :meth:`.RemoteInsDb.patch` lets you to change any object in the database, be it a specification document, a data file, a quantity, etc.
- :meth:`.RemoteInsDb.delete` lets you to remove any object in the database.
- :meth:`.RemoteInsDb.post` lets you to add a new object in the database.

The most used operation is of course to add new objects to the database, which is the reason why :class:`.RemoteInsDb` provides a few additional high-level methods that wrap :meth:`.RemoteInsDb.post`:

1. :meth:`.RemoteInsDb.create_format_spec` creates a new format specification;
2. :meth:`.RemoteInsDb.create_entity` creates a new entity;
3. :meth:`.RemoteInsDb.create_quantity` creates a new quantity;
4. :meth:`.RemoteInsDb.create_data_file` creates a new data file;
5. :meth:`.RemoteInsDb.create_release` creates a new release.

Each of these high-level functions returns the URL of the new object and enables an easier syntax to specify where the new objects should be created::

    # With .post(), you must know the URL of the parent entity and be
    # sure to include the relevant keys in the dictionary
    response = db.post(
        url="http://localhost/api/quantities/",
        data={
            "name": "my_quantity",
            "format_spec": format_spec_url,
            "parent_entity": parent_entity_url,  # ←
        },
    )
    quantity_url = response["url"]

    # With .create_quantity, you just specify the path
    # where to store the quantity
    quantity_url = db.create_quantity(
        name="my quantity",
        parent_path="root/sub_entity1/sub_entity2",
        format_spec_url=format_spec_url,
    )


These instructions can be combined in a script so that a full tree of entities/quantities can be produced::

    connection = RemoteInsDb(
        server_address="http://localhost:8000",
        username="tomasi",
        password="z5i6o2t3o8m3",
    )

    # The tree structure is the following:
    # / root             with quantity "my_quantity" and one data file
    #   / sub_root
    #

    root_entity = connection.create_entity(name="root")
    sub_root_entity = connection.create_entity(name="sub_root", parent_path="root")
    format_spec_url = connection.create_format_spec(
        document_ref="ref01",
        document_title="Reference document",
        document_file=io.StringIO("Test doc"),
        document_file_name="ref01.txt",
        document_mime_type="text/plain",
        file_mime_type="text/csv",
    )
    quantity_url = connection.create_quantity(
        name="my_quantity", parent_path="root", format_spec_url=format_spec_url
    )

    data_file_url = connection.create_data_file(
        quantity="my_quantity",
        parent_path="root",
        data_file_path="/local_storage/my_data_file.csv",
    )

    release_url = connection.create_release(
        release_tag="rel1.0", data_file_url_list=[data_file_url]
    )


A real-world case
-----------------

The website https://insdbdemo.fisica.unimi.it shows a demo of InstrumentDB hosting a reduced instrument model of the ESA Planck spacecraft.
The code used to fill the database is available at https://github.com/ziotom78/fill_insdb_with_planck_rimo and can be used as a reference to use Libinsdb in a real-world scenario.
