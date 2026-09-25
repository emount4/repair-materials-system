"""Проверки изменения остатков и отмены операций."""

import pytest

from materials import add_material
from operations import Operation, cancel_operation, create_operation


def snapshot(inventory):
    materials, operations = inventory
    return (
        [material.to_data() for material in materials],
        [operation.to_data() for operation in operations],
    )


@pytest.fixture
def inventory():
    materials = []
    add_material(materials, 'Краска', 500, 10, 'л', 'Отделка')
    return materials, []


def test_receipt_expense_and_cancellation(inventory):
    materials, operations = inventory
    receipt = create_operation(materials, operations, 1, 'receipt', 5)
    expense = create_operation(
        materials, operations, 1, 'expense', 3, 'Кухня',
    )
    assert isinstance(receipt, Operation)
    assert expense.material is materials[0]
    assert 'Краска' in str(expense)
    assert materials[0].quantity == 12
    cancel_operation(materials, operations, 2)
    assert materials[0].quantity == 15
    assert operations[1].cancelled is True
    cancel_operation(materials, operations, 1)
    assert materials[0].quantity == 10
    assert len(operations) == 2


@pytest.mark.parametrize('quantity', [11, 0, -1, float('nan')])
def test_invalid_expense_does_not_change_data(inventory, quantity):
    before = snapshot(inventory)
    with pytest.raises(ValueError):
        create_operation(*inventory, 1, 'expense', quantity)
    assert snapshot(inventory) == before


def test_spent_receipt_cannot_be_cancelled(inventory):
    materials, operations = inventory
    create_operation(materials, operations, 1, 'receipt', 5)
    create_operation(materials, operations, 1, 'expense', 13)
    before = snapshot(inventory)
    with pytest.raises(ValueError, match='уже потрачены'):
        cancel_operation(materials, operations, 1)
    assert snapshot(inventory) == before


def test_repeated_cancellation_is_rejected(inventory):
    create_operation(*inventory, 1, 'expense', 1)
    cancel_operation(*inventory, 1)
    with pytest.raises(ValueError, match='уже отменена'):
        cancel_operation(*inventory, 1)
    assert inventory[0][0].quantity == 10


def test_fractional_stock_can_be_spent_completely():
    materials, operations = [], []
    add_material(materials, 'Краска', 500, 0.3, 'л', 'Отделка')
    create_operation(materials, operations, 1, 'expense', 0.1)
    create_operation(materials, operations, 1, 'expense', 0.2)
    assert materials[0].quantity == 0


def test_unknown_material_is_rejected(inventory):
    with pytest.raises(ValueError, match='не найден'):
        create_operation(*inventory, 99, 'receipt', 1)
    assert inventory[1] == []
