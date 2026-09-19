"""Проверки JSON и сохранности данных при ошибках."""

import json

import pytest

from materials import add_material
from operations import create_operation
from storage import load_data, save_data


def test_round_trip_and_missing_file(tmp_path):
    path = tmp_path / 'data' / 'inventory.json'
    data = load_data(path)
    assert data == {'materials': [], 'operations': []}
    add_material(data['materials'], 'Краска', 500, 3, 'л', 'Отделка')
    create_operation(data['materials'], data['operations'], 1, 'expense', 1)
    save_data(data, path)
    assert load_data(path) == data
    assert 'Краска' in path.read_text(encoding='utf-8')


@pytest.mark.parametrize('content', [
    '{broken', '[]', '{}', '{"materials": {}, "operations": []}',
    '{"materials": [null], "operations": []}',
])
def test_corrupt_file_is_not_overwritten(tmp_path, content):
    path = tmp_path / 'inventory.json'
    path.write_text(content, encoding='utf-8')
    with pytest.raises(ValueError):
        load_data(path)
    assert path.read_text(encoding='utf-8') == content


def test_invalid_reference_is_rejected(tmp_path):
    data = {'materials': [], 'operations': []}
    add_material(data['materials'], 'Краска', 500, 3, 'л', 'Отделка')
    create_operation(data['materials'], data['operations'], 1, 'expense', 1)
    data['operations'][0]['material_id'] = 99
    path = tmp_path / 'inventory.json'
    path.write_text(json.dumps(data), encoding='utf-8')
    with pytest.raises(ValueError, match='неизвестный материал'):
        load_data(path)


def test_failed_replace_preserves_previous_file(tmp_path, monkeypatch):
    path = tmp_path / 'inventory.json'
    data = {'materials': [], 'operations': []}
    save_data(data, path)
    original = path.read_bytes()
    add_material(data['materials'], 'Краска', 500, 3, 'л', 'Отделка')

    def deny_replace(*args):
        raise PermissionError('Нет доступа')

    monkeypatch.setattr('storage.os.replace', deny_replace)
    with pytest.raises(PermissionError):
        save_data(data, path)
    assert path.read_bytes() == original
    assert list(tmp_path.glob('*.tmp')) == []
