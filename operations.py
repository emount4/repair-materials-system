"""Учет поступлений, расходов и отмены операций."""

from datetime import date
from decimal import Decimal

from materials import get_material
from utils import validate_number


def changed_quantity(current: float, change: float) -> float:
    """Вычисляет остаток без типичных ошибок вычитания десятичных дробей."""
    result = float(Decimal(str(current)) + Decimal(str(change)))
    validate_number(result)
    return result


def create_operation(
    materials: list[dict], operations: list[dict], material_id: int,
    kind: str, quantity: float, note: str = '',
) -> dict:
    """Регистрирует поступление или расход и обновляет остаток."""
    if kind not in {'receipt', 'expense'}:
        raise ValueError("Неизвестный вид операции")
    validate_number(quantity, positive=True)
    if not isinstance(note, str):
        raise ValueError("Примечание должно быть строкой")
    material = get_material(materials, material_id)
    if kind == 'expense' and quantity > material['quantity']:
        raise ValueError("Недостаточно материала для списания")
    balance = changed_quantity(
        material['quantity'], quantity if kind == 'receipt' else -quantity,
    )
    operation = {
        'id': max((item['id'] for item in operations), default=0) + 1,
        'material_id': material_id, 'kind': kind, 'quantity': quantity,
        'date': date.today().isoformat(), 'note': note.strip(),
        'cancelled': False,
    }
    material['quantity'] = balance
    operations.append(operation)
    return operation


def cancel_operation(
    materials: list[dict], operations: list[dict], operation_id: int,
) -> None:
    """Отменяет операцию однократно, сохраняя ее в истории."""
    operation = next(
        (item for item in operations if item['id'] == operation_id), None,
    )
    if operation is None:
        raise ValueError("Операция с таким ID не найдена")
    if operation['cancelled']:
        raise ValueError("Операция уже отменена")
    material = get_material(materials, operation['material_id'])
    quantity = operation['quantity']
    if operation['kind'] == 'receipt' and quantity > material['quantity']:
        raise ValueError(
            "Нельзя отменить поступление: материалы уже потрачены",
        )
    material['quantity'] = changed_quantity(
        material['quantity'],
        -quantity if operation['kind'] == 'receipt' else quantity,
    )
    operation['cancelled'] = True
