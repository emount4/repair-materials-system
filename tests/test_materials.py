"""Проверки коллекций и сохраненного сценария ПР1."""

import pytest

from materials import (
    Material, add_material, calculate_cost, calculate_remaining,
    check_availability, filter_materials, find_materials, get_statistics,
    sort_materials,
)


def test_material_object_and_string_representation():
    material = Material(1, 'Краска', 500, 3, 'л', 'Отделка')
    assert material.id == 1
    assert material.name == 'Краска'
    assert material.is_available(2)
    assert not material.is_available(4)
    assert material.calculate_cost(2) == 1000
    assert '#1 Краска' in str(material)


def test_material_from_data_and_to_data():
    source = {
        'id': 1, 'name': 'Краска', 'price': 500, 'quantity': 3,
        'unit': 'л', 'category': 'Отделка',
    }
    assert Material.from_data(source).to_data() == source


def test_add_material_assigns_ids():
    materials = []
    first = add_material(materials, ' Краска ', 500, 3, 'л', 'Отделка')
    second = add_material(materials, 'Цемент', 300, 2, 'кг', 'Смеси')
    assert [item.id for item in materials] == [1, 2]
    assert first.name == 'Краска'
    assert second.quantity == 2


@pytest.mark.parametrize('price', [-1, float('nan'), float('inf'), True])
def test_add_material_rejects_invalid_price(price):
    materials = []
    with pytest.raises(ValueError):
        add_material(materials, 'Краска', price, 3, 'л', 'Отделка')
    assert materials == []


def test_search_sort_and_filter():
    materials = []
    paint = add_material(materials, 'Краска', 500, 3, 'л', 'Отделка')
    cement = add_material(materials, 'Цемент', 300, 2, 'кг', 'Смеси')
    assert find_materials(materials, 'КРАС') == [paint]
    assert find_materials(materials, 'нет') == []
    assert sort_materials(materials, 'price') == [cement, paint]
    assert materials == [paint, cement]
    assert list(filter_materials(materials, 'отделка')) == [paint]


def test_pr1_calculations():
    assert calculate_cost(99.5, 2) == 199
    assert check_availability(3, 3) == 'Материала достаточно'
    assert check_availability(2, 3) == 'Материала недостаточно'
    assert calculate_remaining(0.3, 0.1) == 0.2
    assert calculate_remaining(2, 3) == 0


def test_statistics_does_not_sum_incompatible_units():
    materials = []
    add_material(materials, 'Краска', 500, 3, 'л', 'Отделка')
    add_material(materials, 'Обои', 800, 0, 'рулон', 'отделка')
    assert get_statistics(materials) == {
        'count': 2, 'categories': 1, 'out_of_stock': 1, 'total_cost': 1500,
    }
    assert get_statistics([])['total_cost'] == 0


def test_cost_overflow_is_reported():
    with pytest.raises(ValueError):
        calculate_cost(1e308, 1e308)
