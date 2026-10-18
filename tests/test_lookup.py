"""Поиск объектов предметной области по ID для консоли и веб-страниц."""

import pytest

from materials import Material, find_material_by_id, get_material
from operations import Operation, cancel_operation, find_operation_by_id


def test_material_lookup_returns_existing_object_or_none():
    material = Material(1, 'Краска', 100, 10, 'л', 'Отделка')
    assert find_material_by_id([material], 1) is material
    assert find_material_by_id([material], 999) is None
    assert find_material_by_id([], 1) is None
    assert get_material([material], 1) is material
    with pytest.raises(ValueError, match='не найден'):
        get_material([material], 999)


def test_operation_lookup_preserves_link_and_cancellation():
    material = Material(1, 'Краска', 100, 10, 'л', 'Отделка')
    operation = Operation(1, material, 'expense', 2, '2026-10-18')
    assert find_operation_by_id([operation], 1) is operation
    assert find_operation_by_id([operation], 999) is None
    assert find_operation_by_id([], 1) is None
    assert operation.material is material
    with pytest.raises(ValueError, match='не найдена'):
        cancel_operation([operation], 999)
    cancel_operation([operation], 1)
    assert operation.cancelled
    assert material.quantity == 12
