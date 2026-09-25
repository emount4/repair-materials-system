"""Консольный интерфейс системы учета материалов."""

from copy import deepcopy
from datetime import date

from materials import (
    Material, add_material, filter_materials, find_materials, get_material,
    get_statistics, sort_materials,
)
from operations import Operation, cancel_operation, create_operation
from storage import DATA_PATH, load_data, save_data
from utils import input_choice, input_number, input_text


MENU = """
1. Показать материалы
2. Добавить материал
3. Найти материал
4. Отсортировать материалы
5. Отобрать материалы по категории
6. Рассчитать стоимость и проверить наличие
7. Оформить поступление
8. Оформить расход
9. Показать историю операций
10. Отменить операцию
11. Показать статистику
0. Выход
"""


def show_materials(materials: list[Material]) -> None:
    """Выводит материалы с идентификаторами и остатками."""
    if not materials:
        print("Материалы не найдены.")
    for material in materials:
        print(material)


def select_material(materials: list[Material]) -> Material:
    """Запрашивает идентификатор существующего материала."""
    material_id = input_number("ID материала: ", integer=True, positive=True)
    return get_material(materials, material_id)


def show_calculation(materials: list[Material]) -> None:
    """Выполняет исходный сценарий ПР1 для выбранного материала."""
    material = select_material(materials)
    required = input_number("Необходимое количество: ")
    print(f"Материал: {material.name}")
    print(f"Стоимость: {material.calculate_cost(required):.2f} руб.")
    status = (
        "Материала достаточно" if material.is_available(required)
        else "Материала недостаточно"
    )
    print(status)
    if material.is_available(required):
        remaining = material.remaining_after(required)
        print(f"Остаток после использования: {remaining:g}")
    else:
        missing = required - material.quantity
        print(f"Необходимо докупить: {missing:g} {material.unit}")
        print(
            f"Стоимость недостающего: "
            f"{material.calculate_cost(missing):.2f} руб."
        )


def show_operations(operations: list[Operation]) -> None:
    """Показывает операции, включая отмененные."""
    if not operations:
        print("Операций пока нет.")
    for operation in operations:
        print(operation)


def handle_action(choice: str, data: dict) -> None:
    """Выполняет выбранный пункт меню над переданными данными."""
    materials, operations = data['materials'], data['operations']
    if choice == '1':
        show_materials(materials)
    elif choice == '2':
        add_material(
            materials, input_text("Название: "),
            input_number("Цена за единицу: "),
            input_number("Начальное количество: "),
            input_text("Единица измерения: "), input_text("Категория: "),
        )
    elif choice == '3':
        show_materials(find_materials(materials, input_text("Название: ")))
    elif choice == '4':
        field = input_choice("Поле (name/price/quantity): ", {
            'name', 'price', 'quantity',
        })
        show_materials(sort_materials(materials, field))
    elif choice == '5':
        category = input_text("Категория: ")
        show_materials(list(filter_materials(materials, category)))
    elif choice == '6':
        show_calculation(materials)
    elif choice in {'7', '8'}:
        material = select_material(materials)
        quantity = input_number("Количество: ", positive=True)
        note = input("Объект ремонта или примечание (необязательно): ").strip()
        create_operation(
            materials, operations, material.id,
            'receipt' if choice == '7' else 'expense', quantity, note,
        )
    elif choice == '9':
        show_operations(operations)
    elif choice == '10':
        operation_id = input_number(
            "ID операции: ", integer=True, positive=True,
        )
        cancel_operation(materials, operations, operation_id)
    elif choice == '11':
        statistics = get_statistics(materials)
        print(f"Видов материалов: {statistics['count']}")
        print(f"Категорий: {statistics['categories']}")
        print(f"Нет в наличии: {statistics['out_of_stock']}")
        print(f"Стоимость запасов: {statistics['total_cost']:.2f} руб.")


def main(data_path=DATA_PATH) -> None:
    """Загружает данные и сохраняет каждое успешное изменение."""
    print("Система учета материалов для ремонта")
    print(f"Дата: {date.today()}")
    try:
        data = load_data(data_path)
    except (OSError, ValueError) as error:
        print(f"Не удалось загрузить данные: {error}")
        print("Проверьте файл данных. Исходный файл сохранен без изменений.")
        return

    try:
        while True:
            print(MENU)
            choice = input_choice("Выберите действие: ", {
                str(number) for number in range(12)
            })
            if choice == '0':
                print("Работа завершена.")
                break
            updated = deepcopy(data)
            try:
                handle_action(choice, updated)
                if updated != data:
                    save_data(updated, data_path)
                    data = updated
                    print("Изменения сохранены.")
            except (OSError, ValueError) as error:
                print(f"Ошибка: {error}. Изменения не применены.")
    except (EOFError, KeyboardInterrupt):
        print("\nВвод прерван. Предыдущие изменения уже сохранены.")


if __name__ == '__main__':
    main()
