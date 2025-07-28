Using the Command-Line Interface (CLI)
======================================

Introduction
------------

Starting from version 0.9.0, Libinsdb provides ``insdb``, a stand-alone program that works on the terminal and lets users to navigate a *local* copy of a database. (It is not possible to access remote copies: for them, you must rely on the web interface provided by `InstrumentDB <https://github.com/ziotom78/instrumentdb>`_.)

The ``insdb`` program has been designed with the purpose of providing an exploratory interface to navigate complex hierarchies of entities.


Starting the CLI
----------------

To start ``insdb``, you just execute it from the command line:

.. code-block:: sh

    $ insdb PATH_TO_THE_DATABASE

where ``PATH_TO_THE_DATABASE`` is the folder where the database is saved. Be sure to activate the virtual environment where you installed Libinsdb before running ``insdb``, otherwise the command will fail.

The program accepts a few command-line options; you can get help on them by running ``insdb --help``.

Once the program has started, you will enter a `Read-Eval-Print Loop <https://en.wikipedia.org/wiki/Read%E2%80%93eval%E2%80%93print_loop>`_ (REPL). At the prompt

.. code-block:: text

    >

you can enter commands that will be executed immediately. To exit the program and go back to your shell, you can run ``quit`` or press the ``Ctrl-D`` key.


Navigating the Entity Tree
--------------------------

In the remainder of this chapter, we will assume you are navigating the demo database in Libinsdb’s GitHub repository <https://github.com/ziotom78/libinsdb>. Assuming you cloned the repository in ``~/libinsdb``, start ``insdb`` with the following command:

.. code-block:: sh

    $ insdb ~/libinsdb/tests/mock_db_json

The two most important commands to navigate the tree of entities are ``cd`` and ``ls``: the former will let you “enter” an entity, while the latter will show you all the children entities and quantities of the current entity. Both commands mimick the analogous commands found in the Linux/Mac OS X shells, where an “entity” behaves like a folder, and a “quantity” behaves like a file.

Let’s start with ``ls``. Type the command and press Enter:

.. code-block:: text

    > ls
    564faff1-ef68-4e40-a2d1-9adb8d00d5c1        payload/
    ff5c3ca2-6789-415e-ae4e-eb68d086baa4        LFI/
    ff2a87bd-9a64-4ab5-9456-d5ffeae9ea23        HFI/

Note that, unlike the POSIX ``ls`` command used in Linux and Mac OS X, here UUIDs are shown alongside the name of each entity. The trailing ``/`` indicates that ``payload``, ``LFI``, and ``HFI`` are entities and can be accessed using the ``cd`` command:

.. code-block:: text

    > cd HFI
    HFI>

You see that the prompt has changed and now shows that we “entered” the ``HFI`` entity. Running ``ls`` shows what’s inside it:

.. code-block:: text

    HFI> ls
    24a94d36-d114-48a0-ae0c-b7251bfcf239        frequency_100_ghz/
    a619e104-35ff-48e4-8408-a0e22af05303        frequency_143_ghz/
    a010e190-4db0-458b-a50e-12315c611c93        frequency_217_ghz/
    c703cb6f-398c-4b0d-ad98-6452ea01c19c        frequency_353_ghz/
    5bf75af1-d481-4fc6-a149-304a8ba8f519        frequency_545_ghz/
    c6bd5095-343f-4b16-a0f6-2eb2984799f1        frequency_857_ghz/
    8f2bf8be-d3cb-4dce-98ab-cea34b139650        full_focal_plane

Note that ``full_focal_plane`` does *not* end with a trailing ``/``. This happens because it is not an entity but a *quantity*. Thus, trying to entering it using ``cd`` raises an error:

.. code-block:: text

    HFI> cd full_focal_plane
    no entry 'full_focal_plane' here

Both ``ls`` and ``cd`` let the user to complete partial matches using the Tab key. Try to enter one of the ``frequency_*_ghz`` entries by typing `fr` and then pressing Tab (represented by ``↹`` in the example below):

.. code-block:: text

    HFI> cd fr↹
    HFI> cd frequency_‸

The caret symbol ``‸`` shows where the cursor has moved. Press Tab again:

.. code-block:: text

    HFI> cd frequency_↹
    frequency_100_ghz  frequency_143_ghz
    frequency_217_ghz  frequency_353_ghz
    frequency_545_ghz  frequency_857_ghz
    HFI> cd frequency_‸

As there are many entries that begin with ``frequency_``, the program lists all the available matches. You can complete it by typing ``2`` and pressing Tab again:

.. code-block:: text

    HFI> cd frequency_2↹
    HFI> cd frequency_217_ghz‸

At this point, you can press Enter and have a look at the contents of this entity:

.. code-block:: text

    HFI> cd frequency_217_ghz
    frequency_217_ghz> ls
    1f755446-be00-4cca-8133-baa38468bed4        1/
    40e3b602-2eb0-4c7e-8ef9-0e9ce2a6b5d7        2/
    73106350-c2c7-43c5-924c-6404dcab8481        3/
    068aeb17-6a7b-487d-a74a-f37102e58577        4/
    fea6f626-c992-438d-8972-96111a19a46a        bandpass
    frequency_217_ghz> ‸


Inspecting Entities and Quantities
----------------------------------

The program ``insdb`` lets you show the details of any object in the database with the command ``show``. You can either provide the name of the entity/quantity or its UUID (the Tab key works in this context too, so you do not have to type UUIDs in full):

.. code-block:: text

    frequency_217_ghz> show 1
    Entity name         1
    UUID                1f755446-be00-4cca-8133-baa38468bed4
    Full path           /HFI/frequency_217_ghz/1
    Parent UUID         a010e190-4db0-458b-a50e-12315c611c93
    Quantities          ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┓
                        ┃ UUID                                 ┃ Name     ┃
                        ┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━┩
                        │ fc3798a6-0d9c-489d-a4bd-958921b4558b │ bandpass │
                        └──────────────────────────────────────┴──────────┘

    frequency_217_ghz> show bandpass
    Quantity name            bandpass
    UUID                     fea6f626-c992-438d-8972-96111a19a46a
    Parent entity            frequency_217_ghz
    Format specification     e406caf2-95c0-4e18-8980-a86934479423
    Data files               ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┓
                             ┃ UUID                                 ┃ Upload date ┃ File name       ┃
                             ┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━┩
                             │ 3a29d860-2289-4691-82de-1fcb4adfff0e │ 2017-09-26  │ bandpass217.csv │
                             │ d85fb364-56a2-4745-8139-a117d64d47f4 │ 2013-03-11  │ bandpass217.csv │
                             └──────────────────────────────────────┴─────────────┴─────────────────┘

    frequency_217_ghz> show 3a29d860-2289-4691-82de-1fcb4adfff0e
    Data file name           bandpass217.csv
    UUID                     3a29d860-2289-4691-82de-1fcb4adfff0e
    Local path               tests/mock_db_json/data_files/3a29d860-2289-4691-82de-1fcb4adfff0e_bandpass217.csv
    Parent quantity          fea6f626-c992-438d-8972-96111a19a46a
    Comment
    Specification version    1.0
    In releases              ┏━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
                             ┃ Tag        ┃ Date       ┃ Path to this object                                 ┃
                             ┡━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
                             │ planck2018 │ 2017-09-26 │ /releases/planck2018/HFI/frequency_217_ghz/bandpass │
                             └────────────┴────────────┴─────────────────────────────────────────────────────┘

Note that for data files you *must* provide an UUID. The filename alone will not work, as there might be the case that several data files share the same name, as it is the case for the ``bandpass`` shown above: both ``3a29d860`` and ``d85fb364`` share the name ``bandpass217.csv``. (This is expected, as they are two measurements of the same quantity.)

Working with Data Files
-----------------------

Apart from the command ``show`` we saw in the previous section, ``insdb`` provides two more commands to work with them: ``open`` and ``metadata``.

The ``open`` command accepts the UUID of a data file and starts the default application configured on your computer to open that kind of file; thus, the result depends on the applications installed on your computer. In the case of data file ``3a29d860`` (the bandpass for the 217 GHz HFI channel), which is a CSV file, my computer opens LibreOffice Calc; in other cases, Microsoft Excel or Apple Numbers might start instead:

.. code-block:: text

    frequency_217_ghz> open 3a29d860-2289-4691-82de-1fcb4adfff0e
    opening data file "tests/mock_db_json/data_files/3a29d860-2289-4691-82de-1fcb4adfff0e_bandpass217.csv"
    [LibreOffice Calc opens in a new window]

What ``open`` does behind the curtains is to rely on some OS-specific command that takes care of opening the file. For Windows, the command is ``start``; for Mac OS X it is ``open``; and for Linux it is ``xdg-open``. If you are using Linux and the command fails, check that you can start ``xdg-open`` from your default shell: it might be necessary to install it. (For instance, Ubuntu/Debian/Arch Linux users should install `xdg-utils <https://wiki.archlinux.org/title/Xdg-utils>`_.)

The ``metadata`` command requires the UUID of a data file and shows the metadata associated with it. In the case of ``bandpass`` there is no metadata:

.. code-block:: text

    frequency_217_ghz> metadata 3a29d860-2289-4691-82de-1fcb4adfff0e
    None

However, if we open data file ``25109593``, which corresponds to the most updated file associated with quantity ``LFI/reduced_focal_plane``, we can get some actual metadata. (Note that, when we use UUIDs, there is no need to navigate into the parent entity: UUIDs are unique and there is no ambiguity when using them to refer to any object.)

.. code-block:: text

    frequency_217_ghz> show 25109593-c5e2-4b60-b06e-ac5e6c3b7b83
    Data file name           file
    UUID                     25109593-c5e2-4b60-b06e-ac5e6c3b7b83
    Local path               None
    Parent quantity          c20f4b61-0162-4316-8d8e-d768287123e1
    Comment
    Specification version    1.0
    In releases              ┏━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
                             ┃ Tag        ┃ Date       ┃ Path to this object                          ┃
                             ┡━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
                             │ planck2018 │ 2017-09-26 │ /releases/planck2018/LFI/reduced_focal_plane │
                             └────────────┴────────────┴──────────────────────────────────────────────┘

    frequency_217_ghz> metadata 25109593-c5e2-4b60-b06e-ac5e6c3b7b83
    {
        '030': {
            'frequency': '030',
            'fwhm': 33.102652125,
            'noise': 0.0001480171,
            'centralfreq': 28.3999996185,
            'fwhm_eff': 32.2879981995,
            'fwhm_eff_sigma': 0.0209999997,
            'ellipticity_eff': 1.3150000572,
            'ellipticity_eff_sigma': 0.0309999995,
            'solid_angle_eff': 1190.1109619141,
            'solid_angle_eff_sigma': 0.7049999833
        },
        '044': {
            'frequency': '044',
            'fwhm': 27.94348615,
            'noise': 0.0001740843,
            'centralfreq': 44.0999984741,
            'fwhm_eff': 26.9969997406,
            'fwhm_eff_sigma': 0.5830000043,
            'ellipticity_eff': 1.1900000572,
            'ellipticity_eff_sigma': 0.0299999993,
            'solid_angle_eff': 831.6110229492,
            'solid_angle_eff_sigma': 35.0410003662
        },
        '070': {
            'frequency': '070',
            'fwhm': 13.07645961,
            'noise': 0.0001518777,
            'centralfreq': 70.4000015259,
            'fwhm_eff': 13.218000412,
            'fwhm_eff_sigma': 0.0309999995,
            'ellipticity_eff': 1.2230000496,
            'ellipticity_eff_sigma': 0.0370000005,
            'solid_angle_eff': 200.8029937744,
            'solid_angle_eff_sigma': 0.9909999967
        }
    }


Other Commands
--------------

Other useful commands are listed here:

- ``pwd`` prints the path to the currently selected entity
- ``releases`` prints a list of all the releases included in the database.
- ``tree`` shows a tree-like representation of all the entities and quantities within the current entity.

Troubleshooting and Tips
------------------------

- You can get help for all the commands with ``help COMMAND``. For instance:

  .. code-block:: text

      > help ls
      List the entities and quantities at the current level

      Usage: ls [-s] [-e]

      The command accepts the following flags:

        -s     Short format: do not print the UUIDs
        -e     Print entities but no quantities

- You can run single commands using the ``-c`` flag when invoking the executable ``insdb``:

  .. code-block:: sh

      $ insdb -c "show 87230a9f-70c7-4fa3-8843-834d52c9fd06" tests/mock_db_json/schema.json
      Data file name           file
      UUID                     87230a9f-70c7-4fa3-8843-834d52c9fd06
      Local path               None
      Parent quantity          a862183e-572f-4629-9eec-fb3abeb21aa2
      Comment
      Specification version    1.0
      In releases              ┏━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
                               ┃ Tag        ┃ Date       ┃ Path to this object                       ┃
                               ┡━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
                               │ planck2018 │ 2017-09-26 │ /releases/planck2018/LFI/full_focal_plane │
                               └────────────┴────────────┴───────────────────────────────────────────┘
