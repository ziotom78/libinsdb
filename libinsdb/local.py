# -*- encoding: utf-8 -*-

# For PEP 604
from __future__ import annotations

import json
import yaml
import gzip
from pathlib import Path
from typing import Any, Union, IO
from uuid import UUID

from dateutil import parser

from .objects import FormatSpecification, Entity, Quantity, DataFile, Release
from .instrumentdb import InstrumentDatabase


def _read_json(path: Path):
    with path.open("rt") as inpf:
        return json.load(inpf)


def _read_json_gz(path: Path):
    with gzip.open(path, "rt") as inpf:
        return json.load(inpf)


def _read_yaml(path: Path):
    with path.open("rt") as inpf:
        return yaml.safe_load(inpf)


def _read_yaml_gz(path: Path):
    with gzip.open(path, "rt") as inpf:
        return yaml.safe_load(inpf)


_DB_FLATFILE_SCHEMA_FILE_NAME = "schema"
_DB_FLATFILE_SCHEMA_FILE_EXTENSIONS = [
    (".json", _read_json),
    (".json.gz", _read_json_gz),
    (".yaml", _read_yaml),
    (".yaml.gz", _read_yaml_gz),
]
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


def parse_data_file(storage_path: Path, obj_dict: dict[str, Any]) -> DataFile:
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
        upload_date=parser.isoparse(obj_dict["upload_date"]),
        metadata=obj_dict.get("metadata", None),
        data_file_local_path=storage_path / file_name
        if file_name is not None
        else None,
        data_file_download_url=None,
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
        rel_date=parser.isoparse(obj_dict["release_date"]),
        comment=obj_dict.get("comments", ""),
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
    """
    Exception raised when a local InstrumentDB database has some internal error.
    """

    pass


class LocalInsDb(InstrumentDatabase):
    """A class that interfaces with a flat-file representation of a database.

    This class assumes that the storage is read-only: no change in the files
    is ever done!
    """

    def __init__(self, storage_path: Union[str, Path]):
        super().__init__()

        self.storage_path = Path(storage_path)

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

        found = False

        for cur_ext, _ in _DB_FLATFILE_SCHEMA_FILE_EXTENSIONS:
            schema_file_path = self.storage_path / (
                _DB_FLATFILE_SCHEMA_FILE_NAME + cur_ext
            )
            if schema_file_path.exists():
                found = True
                break

        if not found:
            raise InstrumentDbFormatError(
                ("no valid schema file found " 'in "{path}"').format(
                    path=self.storage_path.absolute()
                )
            )

    def read_schema(self) -> None:
        """Read the JSON file containing the metadata

        The schema file can be kept either in JSON or YAML format. If the
        schema file is compressed using GZip, this method will decompress
        it on the fly before parsing its contents.
        """

        schema = None
        for cur_ext, cur_parser in _DB_FLATFILE_SCHEMA_FILE_EXTENSIONS:
            schema_file_path = self.storage_path / (
                _DB_FLATFILE_SCHEMA_FILE_NAME + cur_ext
            )
            try:
                schema = cur_parser(schema_file_path)
            except FileNotFoundError:
                continue

        if not schema:
            raise InstrumentDbFormatError(
                ("no valid schema file found " 'in "{path}"').format(
                    path=self.storage_path.absolute()
                )
            )

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
            cur_data_file = parse_data_file(
                storage_path=self.storage_path, obj_dict=obj_dict
            )
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

    def query_entity(self, identifier: UUID | str) -> Entity:
        if isinstance(identifier, UUID):
            return self.entities[identifier]
        else:
            # `identifier` contains a path
            entity_uuid = self.path_to_entity[identifier]
            return self.entities[entity_uuid]

    def query_format_spec(self, identifier: UUID) -> FormatSpecification:
        return self.format_specs[identifier]

    def query_quantity(self, identifier: UUID | str) -> Quantity:
        if isinstance(identifier, UUID):
            return self.quantities[identifier]
        else:
            path_components = identifier.split("/")
            entity_path = "/".join(path_components[:-1])
            quantity_name = path_components[-1]

            entity_uuid = self.path_to_entity[entity_path]
            entity = self.entities[entity_uuid]
            for cur_quantity_uuid in entity.quantities:
                cur_quantity = self.quantities[cur_quantity_uuid]
                if cur_quantity.name == quantity_name:
                    return cur_quantity

            raise KeyError(
                f'quantity "{quantity_name}" not found for entity "{entity_path}"'
            )

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
                    self.add_uuid_to_tracked_list(uuid=uuid)

                return self.data_files[uuid]
            except ValueError:
                # We're dealing with a path
                stripped_identifier = identifier.removeprefix("/releases/")

                relname, entity_path, quantity_name = _parse_data_file_path(
                    stripped_identifier
                )
                print(f"DEBUG: {identifier=}, {stripped_identifier=}, {relname=}")
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

    def query_release(self, tag: str) -> Release:
        return self.releases[tag]

    def open_data_file(self, data_file: DataFile) -> IO:
        assert data_file.data_file_local_path is not None
        return data_file.data_file_local_path.open("rb")

    def merge(self, other: "LocalInsDb") -> None:
        """Merge another :class:`.LocalInsDb` object into this one"""

        self.format_specs = {**self.format_specs, **other.format_specs}
        self.entities = {**self.entities, **other.entities}
        self.quantities = {**self.quantities, **other.quantities}
        self.data_files = {**self.data_files, **other.data_files}
        self.releases = {**self.releases, **other.releases}
        self.path_to_entity = {**self.path_to_entity, **other.path_to_entity}
        self.path_to_quantity = {**self.path_to_quantity, **other.path_to_quantity}
