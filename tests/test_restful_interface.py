# -*- encoding: utf-8 -*-

import datetime
from uuid import UUID

from libinsdb import Entity, Quantity, DataFile, Release, RemoteInsDb


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


def configure_connection(requests_mock) -> RemoteInsDb:
    create_mock_login(requests_mock=requests_mock, username="test", password="12345")
    connection = RemoteInsDb(
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
                "http://localhost/api/data_files/ed8ef738-ef1e-474b-b867-646c74f89694/",
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

    requests_mock.get(
        "http://localhost/browse/data_files/ed8ef738-ef1e-474b-b867-646c74f89694/download/",
        content=b",wavenumber_invcm,transmission,uncertainty\n"
        b"5,21.8,1.0908176716543607e-09,0.0\n"
        b"6,21.9,1.9241507361196885e-09,0.0\n"
        b"7,22.0,3.1679772841539037e-09,0.0\n"
        b"8,22.1,4.288060511185285e-09,0.0\n"
        b"9,22.2,1.0745973679430684e-08,0.0\n"
        b"10,22.3,1.951970852469696e-08,0.0\n"
        b"11,22.4,5.117663335253504e-08,0.0\n"
        b"12,22.5,4.8466211865735716e-08,0.0\n"
        b"13,22.6,1.4357553979899462e-07,0.0\n",
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


def configure_mock_release(requests_mock) -> None:
    requests_mock.get(
        "http://localhost/api/releases/planck2018/",
        json={
            "tag": "planck2018",
            "url": "http://localhost/api/releases/planck2018/",
            "rel_date": "2017-09-26T00:00:00Z",
            "comment": "Instrument specification for the Planck 2018 data release",
            "release_document": "http://localhost/release_documents/planck2018_1SUbbzL",
            "release_document_mime_type": "text/plain",
            "data_files": [
                "http://localhost/api/data_files/460024bb-5425-4e2d-bb41-aae7a46be20b/",
                "http://localhost/api/data_files/205dcd9e-f2bc-44b6-9b4d-a41b7ba42e76/",
                "http://localhost/api/data_files/90ceeaca-9b4b-48bf-86c8-6c5bff0cad7f/",
                "http://localhost/api/data_files/c6eb142e-abfe-4783-ac93-84f330624ff1/",
                "http://localhost/api/data_files/8237f6b7-0974-4221-9efb-9079eaecb4c2/",
                "http://localhost/api/data_files/3a29d860-2289-4691-82de-1fcb4adfff0e/",
                "http://localhost/api/data_files/3a514926-ea2e-4e69-996e-2eedc2894a1c/",
                "http://localhost/api/data_files/43638c42-e42c-49c0-8ee3-09218f5fa73c/",
                "http://localhost/api/data_files/f7248286-5c1d-481a-af34-50ecd4787935/",
                "http://localhost/api/data_files/c19c83d5-34cf-4c94-8bf5-3158422de7f0/",
                "http://localhost/api/data_files/ff8374ac-c347-4924-bf73-dc05d28c0ed3/",
                "http://localhost/api/data_files/24b9660c-b1a5-491e-916c-b9459219543e/",
                "http://localhost/api/data_files/43514e4a-bc6b-4a16-95f9-f1bc69f2e9cc/",
                "http://localhost/api/data_files/18190c40-d4dc-40cc-8d8f-959dc1c1cac0/",
                "http://localhost/api/data_files/02815676-74a9-4162-90a8-8949cdb19b95/",
                "http://localhost/api/data_files/2f56c103-589a-4119-86b3-c1a0b9b1dcac/",
                "http://localhost/api/data_files/b9b97cea-b57b-4daa-b523-3678eac839a1/",
                "http://localhost/api/data_files/a78a19cc-8043-4beb-a6f1-1ee4e59dd45b/",
                "http://localhost/api/data_files/c789e9c1-ac22-42bd-a518-322f418dc5ff/",
                "http://localhost/api/data_files/9de8972a-de9f-49fc-af57-2858d21f3f38/",
                "http://localhost/api/data_files/896a6499-6bf0-445d-85db-b311c27afc9a/",
                "http://localhost/api/data_files/3ffd0d49-f06b-4c6a-9885-fb5b4f6db3ac/",
                "http://localhost/api/data_files/d8c0754c-3399-4eee-ae0a-289717960b60/",
                "http://localhost/api/data_files/c4a3d09d-56e5-49f2-8fb1-3f26d58f3175/",
                "http://localhost/api/data_files/ae866452-107c-47f8-a506-59ed76777dc6/",
                "http://localhost/api/data_files/8d324497-1feb-4329-9db5-79fce23a3728/",
                "http://localhost/api/data_files/436505f3-573e-4c8c-93cb-e5260d1c62da/",
                "http://localhost/api/data_files/ed8ef738-ef1e-474b-b867-646c74f89694/",
                "http://localhost/api/data_files/3de6342d-7688-4d9c-ae84-f1216ccad186/",
                "http://localhost/api/data_files/7bf01b19-3124-46b4-84b5-a6ecace72583/",
                "http://localhost/api/data_files/fcd0b323-4d7b-406c-95a5-1337a96f611a/",
                "http://localhost/api/data_files/25109593-c5e2-4b60-b06e-ac5e6c3b7b83/",
                "http://localhost/api/data_files/87230a9f-70c7-4fa3-8843-834d52c9fd06/",
                "http://localhost/api/data_files/7ec5b87b-2785-49c6-ba28-ebcb707ebe18/",
                "http://localhost/api/data_files/f893bd42-3bb3-446b-a3af-b931b6466618/",
                "http://localhost/api/data_files/b35cc4a5-0628-4f8c-a008-e33062b8dc52/",
            ],
            "json_dump": "http://localhost/browse/releases/planck2018/download/",
        },
    )


def check_release(release: Release, tag: str) -> None:
    assert release.tag == tag
    assert release.rel_date == datetime.datetime(
        year=2017,
        month=9,
        day=26,
        hour=0,
        minute=0,
        second=0,
        tzinfo=datetime.timezone.utc,
    )
    assert (
        release.comment == "Instrument specification for the Planck 2018 data release"
    )
    assert len(release.data_files) == 36
    assert UUID("25109593-c5e2-4b60-b06e-ac5e6c3b7b83") in release.data_files


def test_query_release(requests_mock):
    connection = configure_connection(requests_mock)

    configure_mock_release(requests_mock)
    release = connection.query_release(tag="planck2018")

    check_release(release=release, tag="planck2018")


def test_download_file(requests_mock):
    connection = configure_connection(requests_mock)
    configure_mock_data_file(requests_mock)

    uuid = UUID("ed8ef738-ef1e-474b-b867-646c74f89694")
    data_file = connection.query_data_file(uuid)
    with data_file.open_data_file(connection) as f:
        assert f.read(11) == b",wavenumber"
