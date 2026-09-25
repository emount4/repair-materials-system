"""Проверки JSON и сохранности данных при ошибках."""

import json

import pytest

from materials import add_material
from operations import create_operation
from storage import load_data, save_data


def test_round_trip_and_missing_file(tmp_path):
    data_dir = tmp_path / 'data'
    data = load_data(data_dir)
    assert data == {'materials': [], 'operations': []}
    add_material(data['materials'], 'Краска', 500, 3, 'л', 'Отделка')
    create_operation(data['materials'], data['operations'], 1, 'expense', 1)
    save_data(data, data_dir)
    loaded = load_data(data_dir)
    assert loaded['materials'][0].to_data() == data['materials'][0].to_data()
    assert loaded['operations'][0].to_data() == data['operations'][0].to_data()
    assert loaded['operations'][0].material is loaded['materials'][0]
    assert 'Краска' in (data_dir / 'materials.json').read_text(
        encoding='utf-8',
    )
    assert 'expense' in (data_dir / 'operations.json').read_text(
        encoding='utf-8',
    )


@pytest.mark.parametrize('content', [
    '{broken', '{}', '{"materials": {}, "operations": []}',
    '{"materials": [null], "operations": []}',
])
def test_corrupt_file_is_not_overwritten(tmp_path, content):
    path = tmp_path / 'materials.json'
    path.write_text(content, encoding='utf-8')
    with pytest.raises(ValueError):
        load_data(tmp_path)
    assert path.read_text(encoding='utf-8') == content


def test_invalid_reference_is_rejected(tmp_path):
    data = {'materials': [], 'operations': []}
    add_material(data['materials'], 'Краска', 500, 3, 'л', 'Отделка')
    create_operation(data['materials'], data['operations'], 1, 'expense', 1)
    material_data = [item.to_data() for item in data['materials']]
    operation_data = [item.to_data() for item in data['operations']]
    operation_data[0]['material_id'] = 99
    (tmp_path / 'materials.json').write_text(
        json.dumps(material_data), encoding='utf-8',
    )
    (tmp_path / 'operations.json').write_text(
        json.dumps(operation_data), encoding='utf-8',
    )
    with pytest.raises(ValueError, match='неизвестный материал'):
        load_data(tmp_path)


def test_failed_replace_preserves_previous_file(tmp_path, monkeypatch):
    path = tmp_path
    data = {'materials': [], 'operations': []}
    save_data(data, path)
    original_materials = (path / 'materials.json').read_bytes()
    original_operations = (path / 'operations.json').read_bytes()
    add_material(data['materials'], 'Краска', 500, 3, 'л', 'Отделка')

    def deny_replace(*args):
        raise PermissionError('Нет доступа')

    monkeypatch.setattr('storage.os.replace', deny_replace)
    with pytest.raises(PermissionError):
        save_data(data, path)
    assert (path / 'materials.json').read_bytes() == original_materials
    assert (path / 'operations.json').read_bytes() == original_operations
    assert list(tmp_path.glob('*.tmp')) == []


def test_legacy_inventory_is_still_read(tmp_path):
    data = {'materials': [], 'operations': []}
    add_material(data['materials'], 'Краска', 500, 3, 'л', 'Отделка')
    payload = {
        'materials': [item.to_data() for item in data['materials']],
        'operations': [],
    }
    (tmp_path / 'inventory.json').write_text(
        json.dumps(payload), encoding='utf-8',
    )
    loaded = load_data(tmp_path)
    assert loaded['materials'][0].to_data() == payload['materials'][0]
