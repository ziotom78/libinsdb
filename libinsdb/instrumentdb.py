# -*- encoding: utf-8 -*-
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Union, IO
from uuid import UUID


import requests

from .objects import FormatSpecification, Entity, Quantity, DataFile, Release


class InstrumentDatabase(ABC):
    """An abstract class representing a local/remote database

    This is the base class for :class:`.FlatFileDatabase` (local storage) and
    for :class:`.RestfulConnection`
    """

    def __init__(self) -> None:
        self._tracked_data_files = set()  # type: set[UUID]

    def add_uuid_to_tracked_list(self, uuid: UUID) -> None:
        self._tracked_data_files.add(uuid)

    def get_queried_data_files(self) -> set[UUID]:
        return self._tracked_data_files

    @abstractmethod
    def query_entity(self, identifier: UUID | str) -> Entity:
        "Return a :class:`Entity` object from either its UUID or path"
        raise NotImplementedError()

    @abstractmethod
    def query_quantity(self, identifier: UUID | str) -> Quantity:
        "Return a :class:`Quantity` object from either its UUID or path"
        raise NotImplementedError()

    @abstractmethod
    def query_format_spec(self, identifier: UUID) -> FormatSpecification:
        raise NotImplementedError()

    @abstractmethod
    def query_data_file(
        self, identifier: Union[str, UUID], track: bool = True
    ) -> DataFile:
        """Retrieve a data file

        The `identifier` parameter can be one of the following types:

        1. A ``uuid.UUID`` object
        2. A string representing a UUID
        3. A full path to an object included in a release. In this
           case, the path has the following form:

           /relname/sequence/of/entities/…/quantity

        If `track` is ``True``, the UUID of the object will be saved in
        a set and can be retrieved using the method
        :meth:`.get_queried_data_files`.
        """
        raise NotImplementedError()

    @abstractmethod
    def query_release(self, tag: str) -> Release:
        """Retrieve a release"""
        raise NotImplementedError()

    def query(
        self,
        identifier: Union[str, UUID],
        track: bool = True,
    ) -> Union[DataFile, Quantity, Entity, FormatSpecification]:
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

        """
        if isinstance(identifier, UUID):
            return self.query_data_file(identifier)

        for obj_type_name, method_to_call in [
            ("/data_files", lambda uuid: self.query_data_file(uuid, track=track)),
            ("/quantities", self.query_quantity),
            ("/entities", self.query_entity),
            ("/format_specs", self.query_format_spec),
        ]:
            if identifier.startswith(obj_type_name):
                uuid = UUID(identifier.split("/")[-1])
                return method_to_call(uuid)  # type: ignore

        if identifier.startswith("/releases"):
            # Drop the "/releases/" and go on
            identifier = identifier[len("/releases/") :]

        # Assume that "identifier" is a release name
        return self.query_data_file(identifier)

    @abstractmethod
    def open_data_file(self, data_file: DataFile) -> IO:
        """
        Open the data file for reading

        This is meant to be used as a context-manager.
        """
        raise NotImplementedError()
