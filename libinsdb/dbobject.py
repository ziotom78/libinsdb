# -*- encoding: utf-8 -*-

from abc import ABC, abstractmethod
from datetime import datetime
import json
from pathlib import Path
from typing import Any, Union
from urllib.parse import urljoin
from uuid import UUID


import requests

from .objects import FormatSpecification, Entity, Quantity, DataFile, Release


class DbObject(ABC):
    """An abstract class representing a local/remote database

    This is the base class for :class:`.FlatFileDatabase` (local storage) and
    for :class:`.RestfulConnection`
    """

    def __init__(self):
        self._tracked_data_files = set()  # type: set[UUID]

    def add_uuid_to_tracked_list(self, uuid: UUID) -> None:
        self._tracked_data_files.add(uuid)

    def get_queried_data_files(self) -> set[UUID]:
        return self._tracked_data_files

    @abstractmethod
    def query_entity(self, identifier: UUID) -> Entity:
        raise NotImplementedError()

    @abstractmethod
    def query_quantity(self, identifier: UUID) -> Quantity:
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


class ConnectionError(Exception):
    """Exception raised when there are problems communicating with a remote database

    The fields of this class contain details about the failed requests:

    - ``response``: the ``requests.Response` object associated with the failed
       request.

    - ``url``: the URL of the failed request

    - ``http_code``: the HTTP response status code; see
       https://developer.mozilla.org/en-US/docs/Web/HTTP/Status

    - ``message``: a human-readable error message detailing what went wrong
    """

    def __init__(self, response: requests.Response, message: str):
        self.response = response
        self.url = response.url
        self.http_code = response.status_code
        self.message = message


def extract_last_part_from_url(url: str) -> str:
    parts = [x for x in url.split("/") if x != ""]
    return parts[-1]


def uuid_from_url(url: str) -> UUID:
    """Given an URL, return the UUID

    The function assumes that the UUID is always the last component of the URL.
    This is always the case for the InstrumentDB API.
    """

    return UUID(extract_last_part_from_url(url))


class RestfulConnection(DbObject):
    def __init__(self, server_address: str, username: str, password: str):
        super().__init__()

        self.server_address = server_address
        response = requests.post(
            urljoin(self.server_address, "/api/login"),
            data={"username": username, "password": password},
        )
        self._validate_response(response)
        self.auth_header = {"Authorization": "Token " + response.json()["token"]}

    def _validate_response(
        self, response: requests.Response, expected_http_code: int = 200
    ):
        if response.status_code != expected_http_code:
            raise ConnectionError(response, message="Unable to log in")

    def query_entity(self, identifier: UUID) -> Entity:
        response = requests.get(
            urljoin(self.server_address, f"/api/entities/{identifier}/"),
            headers=self.auth_header,
        )
        self._validate_response(response)
        entity_info = response.json()

        return Entity(
            uuid=identifier,
            name=entity_info["name"],
            full_path=None,
            parent=uuid_from_url(entity_info["parent"]),
            quantities=set([uuid_from_url(x) for x in entity_info["quantities"]]),
        )

    def query_format_spec(self, identifier: UUID) -> FormatSpecification:
        response = requests.get(
            urljoin(self.server_address, f"/api/format_specs/{identifier}/"),
            headers=self.auth_header,
        )
        self._validate_response(response)
        format_spec_info = response.json()

        return FormatSpecification(
            uuid=identifier,
            document_ref=format_spec_info["document_ref"],
            title=format_spec_info["title"],
            local_doc_file_path=None,
            doc_mime_type=format_spec_info["doc_mime_type"],
            file_mime_type=format_spec_info["file_mime_type"],
        )

    def query_quantity(self, identifier: UUID) -> Quantity:
        response = requests.get(
            urljoin(self.server_address, f"/api/quantities/{identifier}/"),
            headers=self.auth_header,
        )
        self._validate_response(response)
        quantity_info = response.json()

        return Quantity(
            uuid=identifier,
            name=quantity_info["name"],
            format_spec=uuid_from_url(quantity_info["format_spec"]),
            entity=uuid_from_url(quantity_info["parent_entity"]),
            data_files=set([uuid_from_url(x) for x in quantity_info["data_files"]]),
        )

    def _create_data_file_from_response(self, response: requests.Response) -> DataFile:
        data_file_info = response.json()

        parsed_metadata = data_file_info.get("metadata", None)

        return DataFile(
            uuid=uuid_from_url(data_file_info["uuid"]),
            name=data_file_info["name"],
            upload_date=data_file_info["upload_date"],
            metadata=parsed_metadata,
            data_file_local_path=None,
            quantity=uuid_from_url(data_file_info["quantity"]),
            spec_version=data_file_info["spec_version"],
            dependencies=set(
                [uuid_from_url(x) for x in data_file_info["dependencies"]]
            ),
            plot_file_local_path=None,
            plot_mime_type=data_file_info["plot_mime_type"],
            comment=data_file_info["comment"],
            release_tags=set(
                [extract_last_part_from_url(x) for x in data_file_info["release_tags"]]
            ),
        )

    def _query_data_file_from_uuid(self, uuid: UUID, track: bool) -> DataFile:
        response = requests.get(
            urljoin(self.server_address, f"/api/data_files/{uuid}/"),
            headers=self.auth_header,
        )
        self._validate_response(response)

        if track:
            self.add_uuid_to_tracked_list(uuid)

        return self._create_data_file_from_response(response)

    def query_data_file(
        self, identifier: Union[str, UUID], track: bool = True
    ) -> DataFile:
        if isinstance(identifier, UUID):
            return self._query_data_file_from_uuid(uuid=identifier, track=track)

        try:
            uuid = UUID(identifier)
            return self._query_data_file_from_uuid(uuid, track=track)
        except ValueError:
            # `identifier` is a path into the tree
            response = requests.get(
                urljoin(self.server_address, f"/releases/{identifier}/"),
                headers=self.auth_header,
            )
            self._validate_response(response)
            result = self._create_data_file_from_response(response)

            if track:
                self.add_uuid_to_tracked_list(result.uuid)

            return result


_DB_FLATFILE_SCHEMA_FILE_NAME = "schema.json"
_DB_FLATFILE_DATA_FILES_DIR_NAME = "data_files"
_DB_FLATFILE_FORMAT_SPEC_DIR_NAME = "format_spec"
_DB_FLATFILE_PLOT_FILES_DIR_NAME = "plot_files"
_DB_FLATFILE_RELEASE_DOCUMENT_DIR_NAME = "release_documents"


def _parse_format_spec(obj_dict: dict[str, Any]) -> FormatSpecification:
    if "doc_file_name" in obj_dict:
        doc_file_name = Path(obj_dict["doc_file_name"])
    else:
        doc_file_name = None

    return FormatSpecification(
        uuid=UUID(obj_dict["uuid"]),
        document_ref=obj_dict.get("document_ref", ""),
        title=obj_dict.get("title", ""),
        local_doc_file_path=doc_file_name,
        doc_mime_type=obj_dict.get("doc_mime_type", ""),
        file_mime_type=obj_dict.get("file_mime_type", ""),
    )


def _parse_entity(
    obj_dict: dict[str, Any], base_path="", parent: UUID | None = None
) -> tuple[Entity, list[dict[str, Any]]]:
    name = obj_dict["name"]
    return (
        Entity(
            uuid=UUID(obj_dict["uuid"]),
            name=name,
            full_path=f"{base_path}/{name}",
            parent=parent,
        ),
        obj_dict.get("children", []),
    )


def _walk_entity_tree_and_parse(
    dictionary: dict[UUID, Any],
    objs: list[dict[str, Any]],
    base_path: str = "",
    parent: UUID | None = None,
):
    for obj_dict in objs:
        obj, children = _parse_entity(
            obj_dict=obj_dict,
            base_path=base_path,
            parent=parent,
        )
        dictionary[obj.uuid] = obj

        if children:
            _walk_entity_tree_and_parse(
                dictionary=dictionary,
                objs=children,
                base_path=f"{base_path}/{obj.name}",
                parent=obj.uuid,
            )


def _parse_quantity(obj_dict: dict[str, Any]) -> Quantity:
    format_spec = None  # type: Union[UUID, None]
    if "format_spec" in obj_dict:
        format_spec = UUID(obj_dict["format_spec"])

    return Quantity(
        uuid=UUID(obj_dict["uuid"]),
        name=obj_dict.get("name", ""),
        format_spec=format_spec,
        entity=UUID(obj_dict["entity"]),
    )


def parse_data_file(obj_dict: dict[str, Any]) -> DataFile:
    dependencies = set()  # type: set[UUID]
    if "dependencies" in obj_dict:
        dependencies = set([UUID(x) for x in obj_dict["dependencies"]])

    if "file_name" in obj_dict:
        file_name = Path(obj_dict["file_name"])
    else:
        file_name = None

    if "plot_file" in obj_dict:
        plot_file_name = Path(obj_dict["plot_file"])
    else:
        plot_file_name = None

    return DataFile(
        uuid=UUID(obj_dict["uuid"]),
        name=obj_dict.get("name", ""),
        upload_date=datetime.fromisoformat(obj_dict["upload_date"]),
        metadata=obj_dict.get("metadata", None),
        data_file_local_path=file_name,
        quantity=UUID(obj_dict["quantity"]),
        spec_version=obj_dict.get("spec_version", ""),
        dependencies=dependencies,
        plot_file_local_path=plot_file_name,
        plot_mime_type=obj_dict.get("plot_mime_type", ""),
        comment=obj_dict.get("comment", ""),
        release_tags=None,  # We'll fill this later
    )


def _parse_release(obj_dict: dict[str, Any]) -> Release:
    return Release(
        tag=obj_dict["tag"],
        rel_date=datetime.fromisoformat(obj_dict["release_date"]),
        comments=obj_dict.get("comments", ""),
        data_files=set([UUID(x) for x in obj_dict.get("data_files", [])]),
    )


def _parse_data_file_path(path: str) -> tuple[str, str, str]:
    """Split a path to a data file into its components.

    Assuming that the path is in the following form:

        /relname/sequence/of/entities/…/quantity

    the function returns a tuple with three elements:

    1. The name of the release (``relname``)
    2. The full path to the entity owning the quantity
    3. The name of the quantity (``quantity``)
    """

    parts = [x for x in path.split("/") if x != ""]
    if len(parts) < 3:
        raise ValueError(f'Malformed path to data file: "{path}"')

    relname = parts[0]
    middle = parts[1:-1]
    quantity = parts[-1]

    return relname, "/" + ("/".join(middle)), quantity


class InstrumentDbFormatError(Exception):
    pass


class LocalDatabase(DbObject):
    """A class that interfaces with a flat-file representation of a database."""

    def __init__(self, path: Union[str, Path]):
        super().__init__()

        self.path = Path(path)

        self.format_specs = {}  # type: dict[UUID, FormatSpecification]
        self.entities = {}  # type: dict[UUID, Entity]
        self.quantities = {}  # type: dict[UUID, Quantity]
        self.data_files = {}  # type: dict[UUID, DataFile]
        self.releases = {}  # type: dict[str, Release]

        self.path_to_entity = {}  # type: dict[str, UUID]
        self.path_to_quantity = {}  # type: dict[str, UUID]

        self.check_consistency()
        self.read_schema()

    def check_consistency(self) -> None:
        """Perform some basic checks on the structure of the flat-file database

        If the structure of the folders is not compliant with the specifications,
        raise a :class:`.InstrumentDbFormatError` exception.

        The checks are not comprehensive, but they should spot the most
        obvious errors.
        """

        schema_file_path = self.path / _DB_FLATFILE_SCHEMA_FILE_NAME

        if not schema_file_path.exists():
            raise InstrumentDbFormatError(
                ("no valid schema file found " 'in "{path}"').format(
                    path=self.path.absolute()
                )
            )

    def read_schema(self) -> None:
        "Read the JSON file containing the metadata"
        schema_file = self.path / _DB_FLATFILE_SCHEMA_FILE_NAME

        with schema_file.open("rt") as inpf:
            schema = json.load(inpf)

        self.parse_schema(schema)

    def parse_schema(self, schema: dict[str, Any]) -> None:
        self.format_specs = {}
        for obj_dict in schema.get("format_specifications", []):
            cur_fmt_spec = _parse_format_spec(obj_dict)
            self.format_specs[cur_fmt_spec.uuid] = cur_fmt_spec

        self.entities = {}
        _walk_entity_tree_and_parse(self.entities, schema.get("entities", []))

        self.quantities = {}
        for obj_dict in schema.get("quantities", []):
            cur_quantity = _parse_quantity(obj_dict)
            self.quantities[cur_quantity.uuid] = cur_quantity

        self.data_files = {}
        for obj_dict in schema.get("data_files", []):
            cur_data_file = parse_data_file(obj_dict)
            self.data_files[cur_data_file.uuid] = cur_data_file

        self.releases = {}
        for obj_dict in schema.get("releases", []):
            cur_release = _parse_release(obj_dict)
            self.releases[cur_release.tag] = cur_release

        self.path_to_entity = {}
        for uuid, entity in self.entities.items():
            # For a local database, entity.full_path should *always* be set
            assert entity.full_path is not None
            self.path_to_entity[entity.full_path] = uuid

        self.path_to_quantity = {
            self.quantity_path(quantity.uuid): uuid
            for uuid, quantity in self.quantities.items()
        }

        for cur_uuid, cur_quantity in self.quantities.items():
            if cur_quantity.entity:
                entity = self.entities[cur_quantity.entity]
                entity.quantities.add(cur_uuid)

        for cur_uuid, cur_data_file in self.data_files.items():
            quantity = self.quantities[cur_data_file.quantity]
            quantity.data_files.add(cur_uuid)

        self._fill_release_tags()

    def _fill_release_tags(self):
        "Fix the value of `release_tags` for each data file"
        for cur_release_tag, cur_release in self.releases.items():
            for cur_uuid in cur_release.data_files:
                self.data_files[cur_uuid].release_tags.add(cur_release_tag)

    def quantity_path(self, uuid: UUID) -> str:
        quantity = self.quantities[uuid]
        assert quantity.entity
        entity = self.entities[quantity.entity]
        return f"{entity.full_path}/{quantity.name}"

    def query_entity(self, identifier: UUID) -> Entity:
        return self.entities[identifier]

    def query_format_spec(self, identifier: UUID) -> FormatSpecification:
        return self.format_specs[identifier]

    def query_quantity(self, identifier: UUID) -> Quantity:
        return self.quantities[identifier]

    def query_data_file(self, identifier: str | UUID, track: bool = True) -> DataFile:
        """Retrieve a data file

        The `identifier` parameter can be one of the following types:

        1. A ``uuid.UUID`` object
        2. A string representing a UUID
        3. A full path to an object included in a release. In this
           case, the path has the following form:

           /relname/sequence/of/entities/…/quantity

        """
        if isinstance(identifier, UUID):
            if track:
                self.add_uuid_to_tracked_list(uuid=identifier)

            return self.data_files[identifier]
        else:
            try:
                uuid = UUID(identifier)

                if track:
                    self.add_uuid_to_tracked_list(uuid=identifier)

                return self.data_files[uuid]
            except ValueError:
                # We're dealing with a path
                relname, entity_path, quantity_name = _parse_data_file_path(identifier)
                release_uuids = self.releases[relname].data_files
                entity = self.entities[self.path_to_entity[entity_path]]

                # Retrieve the quantity whose name matches the last
                # part of the path
                quantity = None
                for cur_uuid in entity.quantities:
                    cur_quantity = self.quantities[cur_uuid]
                    if cur_quantity.name == quantity_name:
                        quantity = self.quantities[cur_quantity.uuid]
                        break

                if not quantity:
                    raise KeyError(
                        (
                            'wrong path: "{id}" points to entity '
                            '"{path}", which does not have a quantity '
                            'named "{quantity}"'
                        ).format(
                            id=identifier, path=entity.full_path, quantity=quantity_name
                        )
                    )

                # Now check which data file has a UUID that matches
                # the one listed in the release
                for cur_uuid in quantity.data_files:
                    if cur_uuid in release_uuids:
                        if track:
                            self.add_uuid_to_tracked_list(uuid=cur_uuid)

                        return self.data_files[cur_uuid]

                raise KeyError(
                    (
                        'wrong path: "{id}" points to quantity '
                        '"{quantity}", which does not have data files '
                        'belonging to release "{relname}" '
                        "(data files are: {uuids})"
                    ).format(
                        id=identifier,
                        quantity=quantity_name,
                        relname=relname,
                        uuids=", ".join([str(x)[0:6] for x in quantity.data_files]),
                    )
                )
