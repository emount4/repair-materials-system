from datetime import date


def calculate_cost(price, required_quantity):
    """Рассчитывает стоимость необходимого количества материала."""
    return price * required_quantity


def check_availability(stock_quantity, required_quantity):
    """Проверяет, достаточно ли материала в наличии."""
    if stock_quantity >= required_quantity:
        return "Материала достаточно"
    return "Материала недостаточно"


def calculate_remaining(stock_quantity, required_quantity):
    """Рассчитывает остаток материала после использования."""
    if stock_quantity >= required_quantity:
        return stock_quantity - required_quantity
    return 0


print("Система учета материалов для ремонта")
print(f"Дата: {date.today()}")
print()

material_name = input("Введите название материала: ")
price = float(input("Введите цену за единицу материала: "))
stock_quantity = float(input("Введите количество материала в наличии: "))
required_quantity = float(
    input("Введите необходимое количество материала: ")
)

cost = calculate_cost(price, required_quantity)
status = check_availability(
    stock_quantity,
    required_quantity
)
remaining = calculate_remaining(
    stock_quantity,
    required_quantity
)

print()
print("Результат:")
print(f"Материал: {material_name}")
print(f"Цена за единицу: {price:.2f} руб.")
print(f"Количество в наличии: {stock_quantity}")
print(f"Необходимое количество: {required_quantity}")
print(f"Стоимость необходимого количества: {cost:.2f} руб.")
print(f"Статус: {status}")

if stock_quantity >= required_quantity:
    print(f"Остаток после использования: {remaining}")
else:
    missing_quantity = required_quantity - stock_quantity
    missing_cost = missing_quantity * price

    print(f"Необходимо докупить: {missing_quantity}")
    print(f"Стоимость недостающего материала: {missing_cost:.2f} руб.")