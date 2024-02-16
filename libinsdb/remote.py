# -*- encoding: utf-8 -*-
from __future__ import annotations

import json
from io import BufferedReader
from pathlib import Path
from tempfile import TemporaryFile
from typing import Any, Union, IO
from urllib.parse import urljoin
from uuid import UUID

from dateutil import parser

import requests

from .objects import FormatSpecification, Entity, Quantity, DataFile, Release
from .instrumentdb import InstrumentDatabase


class InstrumentDbConnectionError(Exception):
    """Exception raised when there are problems communicating with a remote database

    The fields of this class contain details about the failed requests:

    - ``response``: the ``requests.Response`` object associated with the failed
       request.

    - ``message``: a human-readable error message detailing what went wrong
    """

    def __init__(self, response: requests.Response, message: str):
        self.response = response
        self.url = response.url
        # See https://developer.mozilla.org/en-US/docs/Web/HTTP/Status
        self.http_code = response.status_code
        self.message = message

    def __str__(self):
        return (
            f"HTTP error {self.http_code} from {self.url}: "
            f"{self.message=}, {self.response=}"
        )


def extract_last_part_from_url(url: str) -> str:
    parts = [x for x in url.split("/") if x != ""]
    return parts[-1]


def uuid_from_url(url: str) -> UUID:
    """Given an URL, return the UUID

    The function assumes that the UUID is always the last component of the URL.
    This is always the case for the InstrumentDB API.
    """

    return UUID(extract_last_part_from_url(url))


def _validate_response_and_return_json(response: requests.Response) -> dict[str, Any]:
    """Check that the response is ok; otherwise, raise an InstrumentDBError"""

    if not response.ok:
        raise InstrumentDbConnectionError(
            message=response.text,
            response=response,
        )

    if response.content == b"":
        return {}

    try:
        return response.json()
    except requests.exceptions.JSONDecodeError as err:
        raise InstrumentDbConnectionError(
            message=f"{response=} returned {err=} with {response.reason=}",
            response=response,
        )


def _normalize_relative_path(parent_path: str) -> str:
    "Remove leading and trailing backslashes from a relative URL path"

    if parent_path.startswith("/"):
        parent_path.removeprefix("/")

    if parent_path.endswith("/"):
        parent_path.removesuffix("/")

    return parent_path


class RemoteInsDb(InstrumentDatabase):
    """A class that interfaces with a remote InstrumentDB server.

    This class implements the interface of the abstract class
    :class:`.InstrumentDatabase`, which means that it is able
    to access the database much like the class :class:`.LocalInsDb`.

    In addition, this class implements methods that are able to
    modify the content of the database, either by patching what is
    already saved in the database, by adding new objects, or by
    deleting existing ones.
    """

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
            raise InstrumentDbConnectionError(response, message="Unable to log in")

    def query_entity(self, identifier: UUID | str) -> Entity:
        try:
            if isinstance(identifier, str):
                uuid = UUID(identifier)
            else:
                uuid = identifier

            response = requests.get(
                urljoin(self.server_address, f"/api/entities/{uuid}/"),
                headers=self.auth_header,
            )
            self._validate_response(response)
            entity_info = response.json()

            return Entity(
                uuid=uuid,
                name=entity_info["name"],
                full_path=None,
                parent=uuid_from_url(entity_info["parent"]),
                quantities=set([uuid_from_url(x) for x in entity_info["quantities"]]),
            )
        except ValueError:
            # `identifier` is not a UUID, so it's probably a path
            identifier = str(identifier).removeprefix("/").removesuffix("/")
            response = requests.get(
                urljoin(self.server_address, f"/tree/{identifier}"),
                headers=self.auth_header,
            )
            self._validate_response(response)
            return self.query_entity(UUID(response.json()["uuid"]))

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

    def query_quantity(self, identifier: UUID | str) -> Quantity:
        try:
            if isinstance(identifier, str):
                uuid = UUID(identifier)
            else:
                uuid = identifier

            response = requests.get(
                urljoin(self.server_address, f"/api/quantities/{uuid}/"),
                headers=self.auth_header,
            )
            self._validate_response(response)
            quantity_info = response.json()

            return Quantity(
                uuid=uuid,
                name=quantity_info["name"],
                format_spec=uuid_from_url(quantity_info["format_spec"]),
                entity=uuid_from_url(quantity_info["parent_entity"]),
                data_files=set([uuid_from_url(x) for x in quantity_info["data_files"]]),
            )
        except ValueError:
            # `identifier` is not a UUID, so it's probably a path
            identifier = str(identifier).removeprefix("/").removesuffix("/")
            response = requests.get(
                urljoin(self.server_address, f"/tree/{identifier}"),
                headers=self.auth_header,
            )
            self._validate_response(response)
            return self.query_quantity(UUID(response.json()["uuid"]))

    def _create_data_file_from_response(self, response: requests.Response) -> DataFile:
        data_file_info = response.json()

        parsed_metadata = data_file_info.get("metadata", None)

        return DataFile(
            uuid=uuid_from_url(data_file_info["uuid"]),
            name=data_file_info["name"],
            upload_date=data_file_info["upload_date"],
            metadata=parsed_metadata,
            data_file_local_path=None,
            data_file_download_url=data_file_info["download_link"],
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
            full_identifier = identifier
            if not full_identifier.startswith("/releases/"):
                full_identifier = f"/releases/{identifier}"

            # `identifier` is a path into the tree
            response = requests.get(
                urljoin(self.server_address, full_identifier),
                headers=self.auth_header,
            )
            self._validate_response(response)
            result = self._create_data_file_from_response(response)

            if track:
                self.add_uuid_to_tracked_list(result.uuid)

            return result

    def query_release(self, tag: str) -> Release:
        response = requests.get(
            urljoin(self.server_address, f"/api/releases/{tag}/"),
            headers=self.auth_header,
        )
        self._validate_response(response)
        release_info = response.json()

        return Release(
            tag=release_info["tag"],
            rel_date=parser.isoparse(release_info["rel_date"]),
            comment=release_info["comment"],
            data_files=set([uuid_from_url(x) for x in release_info["data_files"]]),
        )

    def open_data_file(self, data_file: DataFile) -> IO:
        """This is meant to be used as a context-manager"""
        assert data_file.data_file_download_url is not None

        f = TemporaryFile("w+b")
        response = requests.get(
            str(data_file.data_file_download_url), allow_redirects=True
        )
        f.write(response.content)
        f.seek(0)

        return f

    def post(
        self, url: str, data: dict[str, Any], files: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Send a POST request to the server

        This method should be used to create a *new* object in the database,
        be it a format specification, an entity, a quantity, or a data file.

        If the object requires files to be associated with it (for example,
        a PDF document), you must pass it through the `files` parameter.

        If there is an error connecting to the server, a `InstrumentDBError`
        will be raised.
        """

        response = requests.post(
            url=url,
            data=data,
            files={} if files is None else files,
            headers=self.auth_header,
        )
        return _validate_response_and_return_json(response)

    def get(self, url: str, params: Any = None) -> dict[str, Any]:
        """Send a GET request to the server

        This method should be used to retrieve information about
        one or more objects in the database.

        If the object requires files to be associated with it (for example,
        a PDF document), you must pass it through the `files` parameter.

        If there is an error connecting to the server, a `InstrumentDBError`
        will be raised.
        """

        if url != "" and url[-1] != "/":
            url = url + "/"

        response = requests.get(
            url=url,
            headers=self.auth_header,
            params=params if params is not None else {},
        )
        return _validate_response_and_return_json(response)

    def patch(
        self, url: str, data: dict[str, Any], files: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Send a PATCH request to the server

        This method should be used to modify an existing object in the database.

        If the object requires files to be associated with it (for example,
        a PDF document), you must pass it through the `files` parameter.

        If there is an error connecting to the server, a `InstrumentDBError`
        will be raised.
        """

        response = requests.patch(
            url=url,
            data=data,
            files={} if files is None else files,
            headers=self.auth_header,
        )
        return _validate_response_and_return_json(response)

    def delete(self, url: str) -> dict[str, Any]:
        """Send a DELETE request to the server

        This method should be used to remove objects (entities, quantities,
        data files, format specifications) from the database.

        If there is an error connecting to the server, a `InstrumentDBError`
        will be raised.
        """

        response = requests.delete(
            url=url,
            headers=self.auth_header,
        )
        return _validate_response_and_return_json(response)

    def create_format_spec(
        self,
        document_ref: str,
        document_title: str,
        document_file: IO,
        document_file_name: str,
        document_mime_type: str,
        file_mime_type: str,
    ) -> str:
        """Add a new format specification to the database

        Each of the parameters to this method match the parameters needed by
        the API to create a format specification.

        Return the URL of the new format specification.
        """

        response = self.post(
            url=f"{self.server_address}/api/format_specs/",
            data={
                "document_ref": document_ref,
                "title": document_title,
                "doc_file_name": document_file_name,
                "doc_mime_type": document_mime_type,
                "file_mime_type": file_mime_type,
            },
            files={
                "doc_file": document_file,
            },
        )
        return response["url"]

    def create_entity(self, name: str, parent_path: str | None = None) -> str:
        """Add a new entity to the database

        This creates an entity named `name`, which is a child of the entity
        whose path is `parent_path` (a full path, not just the name of the
        parent entity!). If the latter is ``None``, the entity is placed
        at the topmost position in the tree (root).

        Return the URL of the new entity.
        """
        data = {"name": name}

        if parent_path is not None:
            parent_path = _normalize_relative_path(parent_path)
            response = self.get(
                url=f"{self.server_address}/tree/{parent_path}",
            )
            data["parent"] = response["url"]

        response = self.post(
            url=f"{self.server_address}/api/entities/",
            data=data,
        )
        return response["url"]

    def create_quantity(self, name: str, parent_path: str, format_spec_url: str) -> str:
        """Add a new quantity to the database

        This creates a quantity named `name`, which is placed within the entity
        whose path is `parent_path` (a full path, not just the name of the
        parent entity!). The parameter `format_spec_url` must be the URL of
        a format specification, which must already exist.

        Return the URL of the new quantity.
        """
        parent_path = _normalize_relative_path(parent_path)
        response = self.get(
            url=f"{self.server_address}/tree/{parent_path}",
        )

        parent_entity = response["url"]
        data = {
            "name": name,
            "format_spec": format_spec_url,
            "parent_entity": parent_entity,
        }

        response = self.post(
            url=f"{self.server_address}/api/quantities/",
            data=data,
        )
        return response["url"]

    def create_data_file(
        self,
        quantity: str,
        parent_path: str,
        data_file_path: Path | None = None,
        data_file_name: str | None = None,
        plot_file_path: Path | None = None,
        plot_file: BufferedReader | None = None,
        plot_file_name: str | None = None,
        plot_mime_type: str | None = None,
        upload_date: str | None = None,
        spec_version: str = "1.0",
        metadata: Any = None,
        comment: str = "",
        dependencies: list[str] | None = None,
    ) -> str:
        """Add a new data file to the database.

        This creates a data file for `quantity` (the name of the quantity
        holding this file, not its URL!) within the entity whose path is `parent_path`.

        All the other parameters are the same accepted by the RESTFul API exported
        by InstrumentDB to create a data file.

        Return the URL of the new data file.
        """
        assert not (
            (plot_file is not None) and (plot_file_path is not None)
        ), "you cannot specify both 'plot_file' and 'plot_file_path'"

        parent_path = _normalize_relative_path(parent_path)
        quantity_dict = self.get(
            url=f"{self.server_address}/tree/{parent_path}/{quantity}"
        )
        quantity_url = quantity_dict["url"]

        data = {
            "quantity": quantity_url,
            "spec_version": spec_version,
            "comment": comment,
            "name": data_file_name if not None else "file",
        }

        if upload_date is not None:
            data["upload_date"] = upload_date

        if plot_file_name is not None:
            data["plot_file_name"] = plot_file_name

        if plot_mime_type is not None:
            data["plot_mime_type"] = plot_mime_type

        if metadata is not None:
            if isinstance(metadata, str):
                data["metadata"] = metadata
            else:
                data["metadata"] = json.dumps(metadata)

        if dependencies:
            data["dependencies"] = dependencies

        files = {}

        files_to_close = []
        if data_file_path:
            data["name"] = data_file_path.name
            files["file_data"] = data_file_path.open("rb")
            files_to_close.append(files["file_data"])

        if plot_file:
            files["plot_file"] = plot_file
        elif plot_file_path:
            files["plot_file"] = plot_file_path.open("rb")
            files_to_close.append(files["plot_file"])

        url = f"{self.server_address}/api/data_files/"
        response = self.post(
            url=url,
            data=data,
            files=files,
        )

        for cur_file in files_to_close:
            # CPython automatically closes files, but this is not
            # the same with PyPy and Jython
            cur_file.close()

        return response["url"]

    def get_data_file_from_release(self, release: str, path: str):
        response = self.get(
            url=f"{self.server_address}/releases/{release}/{path}/",
        )
        return response["url"]

    def create_release(
        self,
        release_tag: str,
        data_file_url_list: list[str] | None = None,
        release_date: str | None = None,
        release_document_path: Path | None = None,
        release_document_mime_type: str | None = None,
        comment: str = "",
    ) -> str:
        """Add a new release to the database.

        This creates a release containing all the data files listed in
        `data_file_url_list` (list of the URLs of each data file).

        All the other parameters are the same to be passed to the
        RESTful API provided by InstrumentDB to create a release.

        Return the URL of the new release.
        """
        if data_file_url_list is None:
            data_file_url_list = []

        data = {
            "tag": release_tag,
            "comment": comment,
            "data_files": data_file_url_list,
        }
        files = {}

        if release_date:
            data["rel_date"] = release_date

        if release_document_mime_type:
            data["release_document_mime_type"] = release_document_mime_type

        files_to_close = []
        if release_document_path:
            release_document_file = release_document_path.open("rb")
            files_to_close.append(release_document_file)
            files["release_document"] = release_document_file

        response = self.post(
            url=f"{self.server_address}/api/releases/",
            data=data,
            files=files,
        )
        release_url = response["url"]

        for cur_file in files_to_close:
            cur_file.close()

        return release_url
