# -*- encoding: utf-8 -*-

"""
The tests in this file ensure that the InstrumentDB class
behaves in the same way when used on a local database or
on remotely through the RESTful API.
"""

from pathlib import Path
from uuid import UUID

import pytest

from libinsdb import RestfulConnection, LocalDatabase
from libinsdb.dbobject import DbObject
from .test_restful_interface import (
    create_mock_login,
    configure_mock_entity,
    check_entity,
    configure_mock_quantity,
    configure_mock_data_file,
    check_quantity,
    check_data_file,
)


def check_all_objects_in_db(insdb: DbObject) -> None:
    uuid = UUID("8734a013-4184-412c-ab5a-963388beae34")
    entity = insdb.query_entity(uuid)
    check_entity(entity=entity, uuid=uuid)

    uuid = UUID("6d1d72ac-ad22-4e94-9ff4-4c3fa8d47c53")
    quantity = insdb.query_quantity(uuid)
    check_quantity(quantity=quantity, uuid=uuid)

    uuid = UUID("ed8ef738-ef1e-474b-b867-646c74f89694")
    data_file = insdb.query_data_file(uuid)
    check_data_file(data_file=data_file, uuid=uuid)

    data_file = insdb.query_data_file(str(uuid))
    check_data_file(data_file=data_file, uuid=uuid)

    data_file = insdb.query("/releases/planck2018/LFI/frequency_044_ghz/24M/bandpass")
    assert data_file.uuid == UUID("3ffd0d49-f06b-4c6a-9885-fb5b4f6db3ac")


def create_local_db() -> DbObject:
    cur_path = Path(__file__).parent
    return LocalDatabase(path=cur_path / "mock_db")


def test_locally():
    insdb = create_local_db()
    check_all_objects_in_db(insdb)


def test_remotely(requests_mock):
    create_mock_login(requests_mock=requests_mock, username="test", password="12345")
    configure_mock_entity(requests_mock)
    configure_mock_quantity(requests_mock)
    configure_mock_data_file(requests_mock)

    requests_mock.get(
        "http://localhost/releases/planck2018/LFI/frequency_044_ghz/24M/bandpass/",
        json={
            "uuid": "3ffd0d49-f06b-4c6a-9885-fb5b4f6db3ac",
            "url": "http://localhost/api/data_files/3ffd0d49-f06b-4c6a-9885-fb5b4f6db3ac/",
            "name": "bandpass_detector_24M.csv",
            "upload_date": "2017-09-26T00:00:00Z",
            "file_data": "http://localhost/data_files/3ffd0d49-f06b-4c6a-9885-fb5b4f6db3ac_bandpass_detector_24M.csv",
            "metadata": None,
            "quantity": "http://localhost/api/quantities/7dd86c18-cacb-4e40-9b9e-ff6d71f48a8c/",
            "spec_version": "1.0",
            "dependencies": [],
            "plot_mime_type": "image/svg+xml",
            "plot_file": None,
            "comment": "",
            "release_tags": ["http://localhost/api/releases/planck2018/"],
            "download_link": "http://localhost/browse/data_files/3ffd0d49-f06b-4c6a-9885-fb5b4f6db3ac/download/",
            "plot_download_link": "http://localhost/browse/data_files/3ffd0d49-f06b-4c6a-9885-fb5b4f6db3ac/plot/",
        },
    )

    insdb = RestfulConnection(
        server_address="http://localhost", username="test", password="12345"
    )
    check_all_objects_in_db(insdb)
