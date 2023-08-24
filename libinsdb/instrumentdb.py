# -*- encoding: utf-8 -*-

import logging as log
from pathlib import Path
from uuid import UUID

from .objects import Entity, Quantity, DataFile, FormatSpecification
from .dbobject import LocalDatabase, RestfulConnection, DbObject


class InstrumentDatabase:
    def __init__(
        self,
        local_folder: str | Path | None,
        server_address: str | None = None,
        username: str | None = None,
        password: str | None = None,
    ):
        if local_folder:
            self.dbobject: DbObject = LocalDatabase(local_folder)
        elif server_address:
            if (username is None) or (password is None):
                raise ValueError(
                    "When connecting to a remote server, "
                    "you must provide a valid username and password"
                )
            self.dbobject = RestfulConnection(
                server=server_address, username=username, password=password
            )
        else:
            raise ValueError(
                "You must provide either flatfile_location= "
                "or url= to InstrumentDatabase.__init__()"
            )

        self.queried_objects = set()  # type: set[tuple[type, UUID]]

    def query_entity(self, identifier: UUID, track=True) -> Entity | None:
        """Return a :class:`.Entity` object from an UUID.

        If ``track`` is `True` (the default), then the UUID of the
        object will be kept in memory and will be returned by the
        method :meth:`.get_queried_entities`.

        """

        if not self.dbobject:
            return None

        result = self.dbobject.query_entity(identifier)
        if result and track:
            self.queried_objects.add((type(result), result.uuid))

        return result

    def query_quantity(self, identifier: UUID, track=True) -> Quantity | None:
        """Return a :class:`.Quantity` object from an UUID.

        If ``track`` is `True` (the default), then the UUID of the
        object will be kept in memory and will be returned by the
        method :meth:`.get_queried_quantities`.

        """

        if not self.dbobject:
            return None

        result = self.dbobject.query_quantity(identifier)
        if result and track:
            self.queried_objects.add((type(result), result.uuid))

        return result

    def query_data_file(self, identifier: str | UUID, track=True) -> DataFile | None:
        """Return a :class:`.DataFile` object from an UUID.

        If ``track`` is `True` (the default), then the UUID of the
        object will be kept in memory and will be returned by the
        method :meth:`.get_queried_data_files`.

        """
        if not self.dbobject:
            return None

        result = self.dbobject.query_data_file(identifier)
        if result and track:
            self.queried_objects.add((type(result), result.uuid))

        return result

    def query(
        self, identifier: str | UUID, track: bool = True
    ) -> DataFile | Quantity | Entity | FormatSpecification | None:
        """Query an object from the database

        The value of `identifier` can be one of the following:

        1. The string ``/quantities/UUID``, with ``UUID`` being the UUID of a
           quantity
        2. The string ``/entities/UUID``, which looks for an entity
        3. The string ``/format_specs/UUID``, which looks for an entity
        4. The string ``/data_files/UUID``, which looks for a data file
        5. A `UUID` object: in this case, the method assumes that a
           data file is being queried.
        6. A path in the form ``/release/entity/tree/…/quantity``; in this case,
           the method looks for the data file belonging to
           ``quantity`` within the entity tree and assigned to the
           specified release.

        The method returns an object belonging to one of the following
        classes: :class:`DataFile`, :class:`Quantity`,
        :class:`Entity`, :class:`FormatSpecification`.

        If ``track`` is `True` (the default), then the UUID of the
        object will be kept in memory and will be returned by the
        method :meth:`.get_queried_data_files`.

        """
        if not self.dbobject:
            return None

        result = self.dbobject.query(identifier)
        if result and track:
            self.queried_objects.add((type(result), result.uuid))
        return result

    def get_list_of_data_files(
        self, quantity_uuid: UUID, track: bool = False
    ) -> list[DataFile]:
        """Return a sorted list of the UUIDs of the data files belonging to a quantity.

        The result is sorted according to their upload date (oldest
        first, newest last).

        If ``track`` is `True`, then the UUID of the object will be
        kept in memory and will be returned by the method
        :meth:`.get_queried_data_files`. The default is ``False``, as
        this function is typically used to check which data files are
        available, not because the caller is going to use each of them.

        """
        quantity = self.query_quantity(quantity_uuid, track=track)
        if not quantity:
            return []

        data_files = []  # type: list[DataFile]
        for cur_data_file_uuid in quantity.data_files:
            cur_data_file = self.query_data_file(cur_data_file_uuid, track=track)
            if cur_data_file is not None:
                data_files.append(cur_data_file)

        return sorted(data_files, key=lambda x: x.upload_date)

    def get_queried_entities(self):
        """Return a list of the UUIDs of entities queried so far."""

        return [x[1] for x in self.queried_objects if x[0] == Entity]

    def get_queried_quantities(self):
        """Return a list of the UUIDs of quantities queried so far."""

        return [x[1] for x in self.queried_objects if x[0] == Quantity]

    def get_queried_data_files(self):
        """Return a list of the UUIDs of data files queried so far."""

        return [x[1] for x in self.queried_objects if x[0] == DataFile]
