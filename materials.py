"""Объектная модель материалов и операции над их коллекцией."""

from collections.abc import Iterator
from decimal import Decimal

from utils import validate_number, validate_text


class Material:
    """Материал на складе индивидуального предпринимателя."""

    def __init__(
        self, material_id: int, name: str, price: float, quantity: float,
        unit: str, category: str,
    ) -> None:
        """Создать материал и проверить значения его атрибутов."""
        self.validate_id(material_id)
        for text in (name, unit, category):
            validate_text(text)
        validate_number(price)
        validate_number(quantity)
        self.id = material_id
        self.name = name.strip()
        self.price = price
        self.quantity = quantity
        self.unit = unit.strip()
        self.category = category.strip()

    @staticmethod
    def validate_id(value: int) -> None:
        """Проверить идентификатор материала."""
        if type(value) is not int or value <= 0:
            raise ValueError("ID должен быть положительным целым числом")

    @classmethod
    def from_data(cls, data: dict) -> "Material":
        """Создать материал из данных JSON."""
        try:
            return cls(
                data['id'], data['name'], data['price'], data['quantity'],
                data['unit'], data['category'],
            )
        except (KeyError, TypeError, OverflowError) as error:
            raise ValueError("Некорректная структура материала") from error

    def to_data(self) -> dict:
        """Преобразовать материал в данные для JSON."""
        return {
            'id': self.id,
            'name': self.name,
            'price': self.price,
            'quantity': self.quantity,
            'unit': self.unit,
            'category': self.category,
        }

    def calculate_cost(self, required_quantity: float) -> float:
        """Рассчитать стоимость указанного количества материала."""
        return calculate_cost(self.price, required_quantity)

    def is_available(self, required_quantity: float) -> bool:
        """Проверить наличие указанного количества материала."""
        validate_number(required_quantity)
        return self.quantity >= required_quantity

    def remaining_after(self, required_quantity: float) -> float:
        """Вернуть остаток после использования без изменения объекта."""
        return calculate_remaining(self.quantity, required_quantity)

    def receive(self, quantity: float) -> None:
        """Увеличить остаток материала."""
        validate_number(quantity, positive=True)
        self.quantity = _changed_quantity(self.quantity, quantity)

    def spend(self, quantity: float) -> None:
        """Уменьшить остаток материала, не допуская дефицита."""
        validate_number(quantity, positive=True)
        if quantity > self.quantity:
            raise ValueError("Недостаточно материала для списания")
        self.quantity = _changed_quantity(self.quantity, -quantity)

    def __str__(self) -> str:
        """Вернуть удобное строковое представление материала."""
        return (
            f"#{self.id} {self.name} | {self.category} | "
            f"{self.price:.2f} руб. | {self.quantity:g} {self.unit}"
        )


def _changed_quantity(current: float, change: float) -> float:
    result = float(Decimal(str(current)) + Decimal(str(change)))
    validate_number(result)
    return result


def calculate_cost(price: float, required_quantity: float) -> float:
    """Рассчитать стоимость количества материала с округлением до копеек."""
    validate_number(price)
    validate_number(required_quantity)
    result = float(Decimal(str(price)) * Decimal(str(required_quantity)))
    validate_number(result)
    return round(result, 2)


def check_availability(stock_quantity: float, required_quantity: float) -> str:
    """Вернуть текстовый статус наличия материала, как в ПР1."""
    validate_number(stock_quantity)
    validate_number(required_quantity)
    if stock_quantity >= required_quantity:
        return "Материала достаточно"
    return "Материала недостаточно"


def calculate_remaining(
    stock_quantity: float, required_quantity: float,
) -> float:
    """Вернуть остаток или ноль при недостаточном запасе."""
    validate_number(stock_quantity)
    validate_number(required_quantity)
    return float(max(
        Decimal('0'),
        Decimal(str(stock_quantity)) - Decimal(str(required_quantity)),
    ))


def add_material(
    materials: list[Material], name: str, price: float, quantity: float,
    unit: str, category: str,
) -> Material:
    """Создать материал с уникальным ID и добавить его в коллекцию."""
    material = Material(
        max((item.id for item in materials), default=0) + 1,
        name, price, quantity, unit, category,
    )
    materials.append(material)
    return material


def get_material(materials: list[Material], material_id: int) -> Material:
    """Найти материал по ID или сообщить об отсутствии."""
    for material in materials:
        if material.id == material_id:
            return material
    raise ValueError("Материал с таким ID не найден")


def find_materials(
    materials: list[Material], query: str,
) -> list[Material]:
    """Найти материалы по подстроке названия без учета регистра."""
    return [
        item for item in materials
        if query.casefold() in item.name.casefold()
    ]


def sort_materials(
    materials: list[Material], field: str = 'name',
) -> list[Material]:
    """Вернуть отсортированный список, не меняя исходную коллекцию."""
    if field not in {'name', 'price', 'quantity'}:
        raise ValueError("Неизвестное поле сортировки")
    return sorted(materials, key=lambda item: (
        getattr(item, field).casefold()
        if field == 'name' else getattr(item, field)
    ))


def filter_materials(
    materials: list[Material], category: str,
) -> Iterator[Material]:
    """Отобрать материалы выбранной категории без учета регистра."""
    for material in materials:
        if material.category.casefold() == category.strip().casefold():
            yield material


def get_statistics(materials: list[Material]) -> dict:
    """Посчитать виды, категории, отсутствующие позиции и стоимость запасов."""
    total = sum(
        Decimal(str(item.price)) * Decimal(str(item.quantity))
        for item in materials
    )
    total_cost = float(total)
    validate_number(total_cost)
    return {
        'count': len(materials),
        'categories': len({item.category.casefold() for item in materials}),
        'out_of_stock': sum(item.quantity == 0 for item in materials),
        'total_cost': round(total_cost, 2),
    }
