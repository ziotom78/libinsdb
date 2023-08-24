# -*- encoding: utf-8 -*-
from uuid import UUID

import pytest
import requests

from libinsdb import Entity, Quantity
from libinsdb.dbobject import RestfulConnection
from libinsdb.objects import DataFile


def match_authentication(request, username, password):
    return (username in request.text) and (password in request.text)


def create_mock_login(requests_mock, username: str, password: str) -> None:
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


def configure_connection(requests_mock) -> RestfulConnection:
    create_mock_login(requests_mock=requests_mock, username="test", password="12345")
    connection = RestfulConnection(
        server_address="http://localhost",
        username="test",
        password="12345",
    )

    return connection


def test_connection(requests_mock):
    connection = configure_connection(requests_mock)
    assert connection.server_address == "http://localhost"
    assert "Authorization" in connection.auth_header


def configure_mock_entity(requests_mock) -> None:
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


def check_entity(entity: Entity, uuid: UUID) -> None:
    assert entity.uuid == uuid
    assert entity.name == "27M"
    assert len(entity.quantities) == 1
    assert UUID("6d1d72ac-ad22-4e94-9ff4-4c3fa8d47c53") in entity.quantities
    assert entity.parent == UUID("b3386894-40a3-4664-aaf6-f78d944943e2")


def test_query_entity(requests_mock):
    connection = configure_connection(requests_mock)

    configure_mock_entity(requests_mock)
    uuid = UUID("8734a013-4184-412c-ab5a-963388beae34")
    entity = connection.query_entity(uuid)

    check_entity(entity=entity, uuid=uuid)


def configure_mock_quantity(requests_mock) -> None:
    requests_mock.get(
        "http://localhost/api/quantities/6d1d72ac-ad22-4e94-9ff4-4c3fa8d47c53/",
        json={
            "uuid": "6d1d72ac-ad22-4e94-9ff4-4c3fa8d47c53",
            "url": "http://localhost/api/quantities/6d1d72ac-ad22-4e94-9ff4-4c3fa8d47c53/",
            "name": "bandpass",
            "format_spec": "http://localhost/api/format_specs/e406caf2-95c0-4e18-8980-a86934479423/",
            "parent_entity": "http://localhost/api/entities/8734a013-4184-412c-ab5a-963388beae34/",
            "data_files": [
                "http://127.0.0.1:8000/api/data_files/ed8ef738-ef1e-474b-b867-646c74f89694/",
            ],
        },
    )


def check_quantity(quantity: Quantity, uuid: UUID) -> None:
    assert quantity.uuid == uuid
    assert quantity.entity == UUID("8734a013-4184-412c-ab5a-963388beae34")
    assert quantity.name == "bandpass"
    assert len(quantity.data_files) == 1
    assert UUID("ed8ef738-ef1e-474b-b867-646c74f89694") in quantity.data_files
    assert quantity.format_spec == UUID("e406caf2-95c0-4e18-8980-a86934479423")


def test_query_quantity(requests_mock):
    connection = configure_connection(requests_mock)
    configure_mock_quantity(requests_mock)

    uuid = UUID("6d1d72ac-ad22-4e94-9ff4-4c3fa8d47c53")
    quantity = connection.query_quantity(uuid)
    check_quantity(quantity=quantity, uuid=uuid)


def configure_mock_data_file(requests_mock) -> None:
    requests_mock.get(
        "http://localhost/api/data_files/ed8ef738-ef1e-474b-b867-646c74f89694/",
        json={
            "uuid": "ed8ef738-ef1e-474b-b867-646c74f89694",
            "url": "http://localhost/api/data_files/ed8ef738-ef1e-474b-b867-646c74f89694/",
            "name": "bandpass_detector_27M.csv",
            "upload_date": "2017-09-26T00:00:00Z",
            "file_data": "http://localhost/data_files/ed8ef738-ef1e-474b-b867-646c74f89694_bandpass_detector_27M.csv",
            "metadata": None,
            "quantity": "http://localhost/api/quantities/6d1d72ac-ad22-4e94-9ff4-4c3fa8d47c53/",
            "spec_version": "1.0",
            "dependencies": [],
            "plot_mime_type": "image/svg+xml",
            "plot_file": None,
            "comment": "",
            "release_tags": ["http://localhost/api/releases/planck2018/"],
            "download_link": "http://localhost/browse/data_files/ed8ef738-ef1e-474b-b867-646c74f89694/download/",
            "plot_download_link": "http://localhost/browse/data_files/ed8ef738-ef1e-474b-b867-646c74f89694/plot/",
        },
    )


def check_data_file(data_file: DataFile, uuid: UUID) -> None:
    assert data_file.uuid == uuid
    assert data_file.name == "bandpass_detector_27M.csv"
    assert data_file.quantity == UUID("6d1d72ac-ad22-4e94-9ff4-4c3fa8d47c53")
    assert data_file.metadata is None
    assert len(data_file.release_tags) == 1
    assert "planck2018" in data_file.release_tags


def test_query_data_file(requests_mock):
    connection = configure_connection(requests_mock)
    configure_mock_data_file(requests_mock)

    uuid = UUID("ed8ef738-ef1e-474b-b867-646c74f89694")
    data_file = connection.query_data_file(uuid)
    check_data_file(data_file=data_file, uuid=uuid)


def test_metadata(requests_mock):
    connection = configure_connection(requests_mock)

    requests_mock.get(
        "http://localhost/api/data_files/25109593-c5e2-4b60-b06e-ac5e6c3b7b83/",
        json={
            "uuid": "25109593-c5e2-4b60-b06e-ac5e6c3b7b83",
            "url": "http://localhost/api/data_files/25109593-c5e2-4b60-b06e-ac5e6c3b7b83/",
            "name": "file",
            "upload_date": "2017-09-26T00:00:00Z",
            "file_data": None,
            "metadata": {
                "030": {
                    "frequency": "030",
                    "fwhm": 33.102652125,
                    "noise": 0.0001480171,
                    "centralfreq": 28.3999996185,
                    "fwhm_eff": 32.2879981995,
                    "fwhm_eff_sigma": 0.0209999997,
                    "ellipticity_eff": 1.3150000572,
                    "ellipticity_eff_sigma": 0.0309999995,
                    "solid_angle_eff": 1190.1109619141,
                    "solid_angle_eff_sigma": 0.7049999833,
                },
                "044": {
                    "frequency": "044",
                    "fwhm": 27.94348615,
                    "noise": 0.0001740843,
                    "centralfreq": 44.0999984741,
                    "fwhm_eff": 26.9969997406,
                    "fwhm_eff_sigma": 0.5830000043,
                    "ellipticity_eff": 1.1900000572,
                    "ellipticity_eff_sigma": 0.0299999993,
                    "solid_angle_eff": 831.6110229492,
                    "solid_angle_eff_sigma": 35.0410003662,
                },
                "070": {
                    "frequency": "070",
                    "fwhm": 13.07645961,
                    "noise": 0.0001518777,
                    "centralfreq": 70.4000015259,
                    "fwhm_eff": 13.218000412,
                    "fwhm_eff_sigma": 0.0309999995,
                    "ellipticity_eff": 1.2230000496,
                    "ellipticity_eff_sigma": 0.0370000005,
                    "solid_angle_eff": 200.8029937744,
                    "solid_angle_eff_sigma": 0.9909999967,
                },
            },
            "quantity": "http://localhost/api/quantities/c20f4b61-0162-4316-8d8e-d768287123e1/",
            "spec_version": "1.0",
            "dependencies": [],
            "plot_mime_type": None,
            "plot_file": None,
            "comment": "",
            "release_tags": ["http://localhost/api/releases/planck2018/"],
            "download_link": "http://localhost/browse/data_files/25109593-c5e2-4b60-b06e-ac5e6c3b7b83/download/",
            "plot_download_link": "http://localhost/browse/data_files/25109593-c5e2-4b60-b06e-ac5e6c3b7b83/plot/",
        },
    )

    uuid = UUID("25109593-c5e2-4b60-b06e-ac5e6c3b7b83")
    data_file = connection.query_data_file(uuid)
    assert data_file.uuid == uuid

    metadata = data_file.metadata
    assert isinstance(metadata, dict)
    assert "030" in metadata
    assert "044" in metadata
    assert "070" in metadata

    assert abs(metadata["030"]["ellipticity_eff"] - 1.3150000572) < 1e-7
