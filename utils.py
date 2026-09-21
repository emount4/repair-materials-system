"""Проверка данных и безопасный ввод с клавиатуры."""

from math import isfinite
from typing import Literal, overload


def validate_number(value: float, positive: bool = False) -> None:
    """Отклоняет нечисловые, бесконечные и недопустимые значения."""
    if (type(value) not in (int, float) or not isfinite(value)
            or value < 0 or (positive and value == 0)):
        sign = "положительное" if positive else "неотрицательное"
        raise ValueError(f"Требуется конечное {sign} число")


def validate_text(value: str) -> None:
    """Проверяет, что строка содержит непустой текст."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Текст не должен быть пустым")


def input_text(prompt: str) -> str:
    """Повторяет ввод до получения непустой строки."""
    while True:
        value = input(prompt).strip()
        try:
            validate_text(value)
            return value
        except ValueError as error:
            print(error)


@overload
def input_number(
    prompt: str, integer: Literal[True], positive: bool = False,
) -> int: ...


@overload
def input_number(
    prompt: str, integer: Literal[False] = False, positive: bool = False,
) -> float: ...


@overload
def input_number(
    prompt: str, integer: bool, positive: bool = False,
) -> int | float: ...


def input_number(
    prompt: str, integer: bool = False, positive: bool = False,
) -> int | float:
    """Читает число; допускает запятую в качестве десятичного разделителя."""
    while True:
        try:
            raw = input(prompt).strip().replace(',', '.')
            value = int(raw) if integer else float(raw)
            validate_number(value, positive)
            return value
        except (ValueError, OverflowError):
            kind = "целое число" if integer else "число"
            bound = "больше нуля" if positive else "не меньше нуля"
            print(f"Введите конечное {kind} {bound}.")


def input_choice(prompt: str, choices: set[str]) -> str:
    """Повторяет ввод, пока не выбран допустимый вариант."""
    while True:
        value = input(prompt).strip()
        if value in choices:
            return value
        print("Неизвестный вариант. Повторите ввод.")
