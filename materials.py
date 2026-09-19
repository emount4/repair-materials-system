"""Материалы, поиск, отбор и расчеты из ПР1."""

from collections.abc import Iterator
from decimal import Decimal

from utils import validate_number, validate_text


def calculate_cost(price: float, required_quantity: float) -> float:
    """Рассчитывает стоимость количества материала с округлением до копеек."""
    validate_number(price)
    validate_number(required_quantity)
    result = float(Decimal(str(price)) * Decimal(str(required_quantity)))
    validate_number(result)
    return round(result, 2)


def check_availability(stock_quantity: float, required_quantity: float) -> str:
    """Возвращает текстовый статус наличия материала, как в ПР1."""
    validate_number(stock_quantity)
    validate_number(required_quantity)
    if stock_quantity >= required_quantity:
        return "Материала достаточно"
    return "Материала недостаточно"


def calculate_remaining(
    stock_quantity: float, required_quantity: float,
) -> float:
    """Возвращает остаток или ноль при недостаточном запасе."""
    validate_number(stock_quantity)
    validate_number(required_quantity)
    return float(max(
        Decimal('0'),
        Decimal(str(stock_quantity)) - Decimal(str(required_quantity)),
    ))


def add_material(
    materials: list[dict], name: str, price: float, quantity: float,
    unit: str, category: str,
) -> dict:
    """Добавляет материал с уникальным идентификатором."""
    for text in (name, unit, category):
        validate_text(text)
    validate_number(price)
    validate_number(quantity)
    material = {
        'id': max((item['id'] for item in materials), default=0) + 1,
        'name': name.strip(), 'price': price, 'quantity': quantity,
        'unit': unit.strip(), 'category': category.strip(),
    }
    materials.append(material)
    return material


def get_material(materials: list[dict], material_id: int) -> dict:
    """Находит материал по ID или сообщает об отсутствии."""
    for material in materials:
        if material['id'] == material_id:
            return material
    raise ValueError("Материал с таким ID не найден")


def find_materials(materials: list[dict], query: str) -> list[dict]:
    """Ищет материалы по подстроке названия без учета регистра."""
    return [item for item in materials if query.casefold() in
            item['name'].casefold()]


def sort_materials(materials: list[dict], field: str = 'name') -> list[dict]:
    """Возвращает отсортированный список, не меняя исходную коллекцию."""
    if field not in {'name', 'price', 'quantity'}:
        raise ValueError("Неизвестное поле сортировки")
    return sorted(materials, key=lambda item: (
        item[field].casefold() if field == 'name' else item[field]
    ))


def filter_materials(materials: list[dict], category: str) -> Iterator[dict]:
    """Генератор материалов выбранной категории без учета регистра."""
    for material in materials:
        if material['category'].casefold() == category.strip().casefold():
            yield material


def get_statistics(materials: list[dict]) -> dict:
    """Считает виды, категории, отсутствующие материалы и стоимость запасов."""
    total = sum(
        Decimal(str(item['price'])) * Decimal(str(item['quantity']))
        for item in materials
    )
    total_cost = float(total)
    validate_number(total_cost)
    return {
        'count': len(materials),
        'categories': len({item['category'].casefold() for item in materials}),
        'out_of_stock': sum(item['quantity'] == 0 for item in materials),
        'total_cost': round(total_cost, 2),
    }
