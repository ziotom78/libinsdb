# -*- encoding: utf-8 -*-
from uuid import UUID

import pytest
import requests

from libinsdb.dbobject import RestfulConnection


def match_authentication(request, username, password):
    return (username in request.text) and (password in request.text)


def configure_connection(requests_mock) -> RestfulConnection:
    requests_mock.post(
        "http://localhost/api/login",
        json={
            "user": "test",
            "groups": [],
            "token": "d5469e1b0287b28874c34863e7d54179e998758c",
            "token_expires_in_minutes": 15,
        },
        additional_matcher=lambda request: match_authentication(
            request, username="test", password="12345"
        ),
    )

    connection = RestfulConnection(
        server="http://localhost",
        username="test",
        password="12345",
    )

    return connection


def test_connection(requests_mock):
    connection = configure_connection(requests_mock)
    assert connection.server == "http://localhost"
    assert "Authorization" in connection.auth_header


def test_query_entity(requests_mock):
    connection = configure_connection(requests_mock)

    requests_mock.get(
        "http://localhost/api/entities/8734a013-4184-412c-ab5a-963388beae34/",
        json={
            "uuid": "8734a013-4184-412c-ab5a-963388beae34",
            "url": "http://localhost/api/entities/8734a013-4184-412c-ab5a-963388beae34/",
            "name": "27M",
            "parent": "http://localhost/api/entities/b3386894-40a3-4664-aaf6-f78d944943e2/",
            "children": [],
            "quantities": [
                "http://localhost/api/quantities/6d1d72ac-ad22-4e94-9ff4-4c3fa8d47c53/"
            ],
        },
    )

    uuid = UUID("8734a013-4184-412c-ab5a-963388beae34")
    entity = connection.query_entity(uuid)
    assert entity.uuid == uuid
    assert entity.name == "27M"
    assert entity.full_path is None
    assert len(entity.quantities) == 1
    assert UUID("6d1d72ac-ad22-4e94-9ff4-4c3fa8d47c53") in entity.quantities
    assert entity.parent == UUID("b3386894-40a3-4664-aaf6-f78d944943e2")


def test_query_quantity(requests_mock):
    connection = configure_connection(requests_mock)

    requests_mock.get(
        "http://localhost/api/quantities/6d1d72ac-ad22-4e94-9ff4-4c3fa8d47c53/",
        json={
            "uuid": "6d1d72ac-ad22-4e94-9ff4-4c3fa8d47c53",
            "url": "http://localhost/api/quantities/6d1d72ac-ad22-4e94-9ff4-4c3fa8d47c53/",
            "name": "bandpass",
            "format_spec": "http://localhost/api/format_specs/e406caf2-95c0-4e18-8980-a86934479423/",
            "parent_entity": "http://localhost/api/entities/8734a013-4184-412c-ab5a-963388beae34/",
            "data_files": [
                "http://localhost/api/data_files/4d1b1d26-4af6-49d0-9790-87f6ad80a7a9/",
                "http://localhost/api/data_files/477fe137-92a1-405a-bf73-a5b9bc597a9f/",
                "http://localhost/api/data_files/7e8e5723-83de-40e5-952a-018746b29bb4/",
            ],
        },
    )

    uuid = UUID("6d1d72ac-ad22-4e94-9ff4-4c3fa8d47c53")
    quantity = connection.query_quantity(uuid)
    assert quantity.uuid == uuid
    assert quantity.entity == UUID("8734a013-4184-412c-ab5a-963388beae34")
    assert quantity.name == "bandpass"
    assert len(quantity.data_files) == 3
    assert UUID("4d1b1d26-4af6-49d0-9790-87f6ad80a7a9") in quantity.data_files
    assert UUID("477fe137-92a1-405a-bf73-a5b9bc597a9f") in quantity.data_files
    assert UUID("7e8e5723-83de-40e5-952a-018746b29bb4") in quantity.data_files
    assert quantity.format_spec == UUID("e406caf2-95c0-4e18-8980-a86934479423")


def test_query_data_file(requests_mock):
    connection = configure_connection(requests_mock)

    requests_mock.get(
        "http://localhost/api/data_files/4d1b1d26-4af6-49d0-9790-87f6ad80a7a9/",
        json={
            "uuid": "4d1b1d26-4af6-49d0-9790-87f6ad80a7a9",
            "url": "http://localhost/api/data_files/4d1b1d26-4af6-49d0-9790-87f6ad80a7a9/",
            "name": "bandpass_detector_27M.csv",
            "upload_date": "2021-11-03T00:00:00Z",
            "file_data": "http://localhost/data_files/4d1b1d26-4af6-49d0-9790-87f6ad80a7a9_bandpass_detector_27M.csv",
            "metadata": None,
            "quantity": "http://localhost/api/quantities/6d1d72ac-ad22-4e94-9ff4-4c3fa8d47c53/",
            "spec_version": "1.0",
            "dependencies": [],
            "plot_mime_type": "image/svg+xml",
            "plot_file": None,
            "comment": "",
            "release_tags": ["http://localhost/api/releases/planck2021/"],
            "download_link": "http://localhost/browse/data_files/4d1b1d26-4af6-49d0-9790-87f6ad80a7a9/download/",
            "plot_download_link": "http://localhost/browse/data_files/4d1b1d26-4af6-49d0-9790-87f6ad80a7a9/plot/",
        },
    )

    uuid = UUID("4d1b1d26-4af6-49d0-9790-87f6ad80a7a9")
    data_file = connection.query_data_file(uuid)
    assert data_file.uuid == uuid
    assert data_file.name == "bandpass_detector_27M.csv"
    assert data_file.quantity == UUID("6d1d72ac-ad22-4e94-9ff4-4c3fa8d47c53")
    assert data_file.metadata == {}
    assert data_file.data_file_local_path is None
    assert len(data_file.release_tags) == 1
    assert "planck2021" in data_file.release_tags
