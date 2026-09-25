"""Объектная модель поступлений, расходов и их отмены."""

from datetime import date
from decimal import Decimal

from materials import Material, get_material
from utils import validate_number


class Operation:
    """Операция движения конкретного материала."""

    KINDS = {'receipt', 'expense'}

    def __init__(
        self, operation_id: int, material: Material, kind: str,
        quantity: float, operation_date: str, note: str = '',
        cancelled: bool = False,
    ) -> None:
        """Создать операцию, связанную с объектом материала."""
        Material.validate_id(operation_id)
        if not isinstance(material, Material):
            raise ValueError("Операция должна быть связана с материалом")
        if kind not in self.KINDS:
            raise ValueError("Неизвестный вид операции")
        validate_number(quantity, positive=True)
        try:
            date.fromisoformat(operation_date)
        except (TypeError, ValueError) as error:
            raise ValueError("Некорректная дата операции") from error
        if not isinstance(note, str) or type(cancelled) is not bool:
            raise ValueError("Некорректные поля операции")
        self.id = operation_id
        self.material = material
        self.kind = kind
        self.quantity = quantity
        self.date = operation_date
        self.note = note.strip()
        self.cancelled = cancelled

    @classmethod
    def from_data(
        cls, data: dict, materials: list[Material],
    ) -> "Operation":
        """Восстановить операцию из JSON и связать с объектом материала."""
        try:
            material = get_material(materials, data['material_id'])
        except ValueError as error:
            raise ValueError(
                "Операция ссылается на неизвестный материал",
            ) from error
        try:
            return cls(
                data['id'], material, data['kind'], data['quantity'],
                data['date'], data['note'], data['cancelled'],
            )
        except (KeyError, TypeError, OverflowError) as error:
            raise ValueError("Некорректная структура операции") from error

    def to_data(self) -> dict:
        """Преобразовать операцию в данные для JSON."""
        return {
            'id': self.id,
            'material_id': self.material.id,
            'kind': self.kind,
            'quantity': self.quantity,
            'date': self.date,
            'note': self.note,
            'cancelled': self.cancelled,
        }

    def cancel(self) -> None:
        """Отменить операцию и восстановить остаток материала."""
        if self.cancelled:
            raise ValueError("Операция уже отменена")
        if self.kind == 'receipt':
            try:
                self.material.spend(self.quantity)
            except ValueError as error:
                raise ValueError(
                    "Нельзя отменить поступление: материалы уже потрачены",
                ) from error
        else:
            self.material.receive(self.quantity)
        self.cancelled = True

    def __str__(self) -> str:
        """Вернуть строковое представление операции и ее состояния."""
        kind = "Поступление" if self.kind == 'receipt' else "Расход"
        status = "отменена" if self.cancelled else "действует"
        return (
            f"#{self.id} {self.date} | {kind} | "
            f"материал #{self.material.id} ({self.material.name}) | "
            f"{self.quantity:g} | {status} | {self.note}"
        )


def changed_quantity(current: float, change: float) -> float:
    """Вычислить остаток без ошибок вычитания десятичных дробей."""
    result = float(Decimal(str(current)) + Decimal(str(change)))
    validate_number(result)
    return result


def create_operation(
    materials: list[Material], operations: list[Operation], material_id: int,
    kind: str, quantity: float, note: str = '',
) -> Operation:
    """Создать операцию, изменить остаток и добавить объект в коллекцию."""
    if kind not in Operation.KINDS:
        raise ValueError("Неизвестный вид операции")
    validate_number(quantity, positive=True)
    if not isinstance(note, str):
        raise ValueError("Примечание должно быть строкой")
    material = get_material(materials, material_id)
    if kind == 'receipt':
        material.receive(quantity)
    else:
        material.spend(quantity)
    operation = Operation(
        max((item.id for item in operations), default=0) + 1,
        material, kind, quantity, date.today().isoformat(), note,
    )
    operations.append(operation)
    return operation


def cancel_operation(
    materials: list[Material], operations: list[Operation], operation_id: int,
) -> None:
    """Найти операцию и отменить ее методом объекта."""
    operation = next(
        (item for item in operations if item.id == operation_id), None,
    )
    if operation is None:
        raise ValueError("Операция с таким ID не найдена")
    operation.cancel()
