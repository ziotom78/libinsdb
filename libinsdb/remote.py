# -*- encoding: utf-8 -*-

from datetime import datetime
from typing import Any, Union
from urllib.parse import urljoin
from uuid import UUID


import requests

from .objects import FormatSpecification, Entity, Quantity, DataFile, Release
from .instrumentdb import InstrumentDatabase


class InstrumentDbConnectionError(Exception):
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


class RemoteInsDb(InstrumentDatabase):
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

    def query_release(self, tag: str) -> Release:
        response = requests.get(
            urljoin(self.server_address, f"/api/releases/{tag}/"),
            headers=self.auth_header,
        )
        self._validate_response(response)
        release_info = response.json()

        return Release(
            tag=release_info["tag"],
            rel_date=datetime.fromisoformat(release_info["rel_date"]),
            comment=release_info["comment"],
            data_files=set([uuid_from_url(x) for x in release_info["data_files"]]),
        )
