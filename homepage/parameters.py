"""Validation of GET parameters shared by read-only search pages."""

from datetime import date
from math import isfinite


def quantity_parameter(raw):
    try:
        value = float(raw or '0')
    except ValueError as error:
        raise ValueError('Количество должно быть числом.') from error
    if not isfinite(value) or value < 0:
        raise ValueError('Количество должно быть конечным и неотрицательным.')
    return value


def date_parameter(raw):
    if raw:
        try:
            parsed = date.fromisoformat(raw)
        except ValueError as error:
            message = 'Укажите существующую дату в формате ГГГГ-ММ-ДД.'
            raise ValueError(message) from error
        if parsed.isoformat() != raw:
            raise ValueError('Укажите дату в формате ГГГГ-ММ-ДД.')
    return raw
