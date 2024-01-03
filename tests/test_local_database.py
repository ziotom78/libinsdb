# -*- encoding: utf-8 -*-

from uuid import UUID
from pathlib import Path

import pytest  # type: ignore

from libinsdb import LocalInsDb, Entity, Quantity, DataFile


def load_mock_database():
    curpath = Path(__file__).parent
    return LocalInsDb(storage_path=curpath / "mock_db_json")


def test_key_errors():
    imo = load_mock_database()

    with pytest.raises(KeyError):
        imo.query("/format_specs/aaaaaaaa-bbbb-cccc-dddd-eeeeeeffffff")

    with pytest.raises(KeyError):
        imo.query("/entities/aaaaaaaa-bbbb-cccc-dddd-eeeeeeffffff")

    with pytest.raises(KeyError):
        imo.query("/quantities/aaaaaaaa-bbbb-cccc-dddd-eeeeeeffffff")

    with pytest.raises(KeyError):
        imo.query("/data_files/aaaaaaaa-bbbb-cccc-dddd-eeeeeeffffff")

    with pytest.raises(KeyError):
        imo.query("/UNKNOWN_TAG/instrument/beams/horn01/horn01_grasp")

    with pytest.raises(KeyError):
        imo.query("/1.0/WRONG/PATH/horn01_grasp")

    with pytest.raises(KeyError):
        imo.query("/1.0/instrument/beams/horn01/UNKNOWN_QUANTITY")

    with pytest.raises(KeyError):
        # This might look correct, but quantity "horn01_synth" has no
        # data files in release 1.0
        imo.query("/1.0/instrument/beams/horn01/horn01_synth")


def test_query_uuid():
    db = load_mock_database()

    uuid = UUID("8734a013-4184-412c-ab5a-963388beae34")
    entity = db.query(f"/entities/{uuid}")
    assert isinstance(entity, Entity)
    assert entity.uuid == uuid

    uuid = UUID("6d1d72ac-ad22-4e94-9ff4-4c3fa8d47c53")
    quantity = db.query(f"/quantities/{uuid}")
    assert isinstance(quantity, Quantity)
    assert quantity.uuid == uuid

    uuid = UUID("ed8ef738-ef1e-474b-b867-646c74f89694")
    data_file = db.query(f"/data_files/{uuid}")
    assert isinstance(data_file, DataFile)
    assert data_file.uuid == uuid

    data_file = db.query(uuid)
    assert isinstance(data_file, DataFile)
    assert data_file.uuid == uuid


def test_get_queried_objects():
    db = load_mock_database()

    entity_uuid = UUID("8734a013-4184-412c-ab5a-963388beae34")
    _ = db.query(f"/entities/{entity_uuid}")

    quantity_uuid = UUID("6d1d72ac-ad22-4e94-9ff4-4c3fa8d47c53")
    _ = db.query(f"/quantities/{quantity_uuid}")

    # This is not being tracked…
    untracked_data_file_uuid = UUID("ed8ef738-ef1e-474b-b867-646c74f89694")
    _ = db.query(f"/data_files/{untracked_data_file_uuid}", track=False)

    # …but this will be
    tracked_data_file_uuid = UUID("25109593-c5e2-4b60-b06e-ac5e6c3b7b83")
    _ = db.query(f"/data_files/{tracked_data_file_uuid}")

    release_data_file_uuid = UUID("3ffd0d49-f06b-4c6a-9885-fb5b4f6db3ac")
    _ = db.query("/releases/planck2018/LFI/frequency_044_ghz/24M/bandpass")

    queried_files = db.get_queried_data_files()
    assert untracked_data_file_uuid not in queried_files
    assert tracked_data_file_uuid in queried_files
    assert release_data_file_uuid in queried_files


def test_query_release():
    db = load_mock_database()

    uuid = UUID("3ffd0d49-f06b-4c6a-9885-fb5b4f6db3ac")
    data_file = db.query("/releases/planck2018/LFI/frequency_044_ghz/24M/bandpass")
    assert data_file.uuid == uuid


def test_entry_hierarchy():
    db = load_mock_database()

    # This is the "27M" entity
    uuid = UUID("8734a013-4184-412c-ab5a-963388beae34")
    child_entity = db.query_entity(uuid)

    # Check that the parent is the "frequency_030_ghz" entity
    assert child_entity.parent == UUID("b3386894-40a3-4664-aaf6-f78d944943e2")


def test_schema_formats():
    for folder_name in [
        "mock_db_json",
        "mock_db_json_gz",
        "mock_db_yaml",
        "mock_db_yaml_gz",
    ]:
        mock_db_path = Path(__file__).parent / folder_name
        db = LocalInsDb(storage_path=mock_db_path)

        # This is the "27M" entity
        uuid = UUID("8734a013-4184-412c-ab5a-963388beae34")
        child_entity = db.query_entity(uuid)

        # Check that the parent is the "frequency_030_ghz" entity
        assert child_entity.parent == UUID("b3386894-40a3-4664-aaf6-f78d944943e2")
