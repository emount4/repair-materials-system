"""Проверка, загрузка и атомарное сохранение JSON-файла проекта."""

import json
import os
from datetime import date
from pathlib import Path
from tempfile import NamedTemporaryFile

from utils import validate_number, validate_text


DATA_PATH = Path(__file__).resolve().parent / 'data' / 'inventory.json'


def validate_id(value: int) -> None:
    """Проверяет положительный целочисленный идентификатор."""
    if type(value) is not int or value <= 0:
        raise ValueError("ID должен быть положительным целым числом")


def validate_data(data: dict) -> None:
    """Проверяет структуру данных, ID и ссылки операций на материалы."""
    try:
        if not isinstance(data, dict):
            raise ValueError("Ожидается объект JSON")
        for key in ('materials', 'operations'):
            if not isinstance(data[key], list):
                raise ValueError(f"Поле {key} должно быть списком")
        material_ids = set()
        for material in data['materials']:
            validate_id(material['id'])
            if material['id'] in material_ids:
                raise ValueError("Повторяющийся ID материала")
            material_ids.add(material['id'])
            for key in ('name', 'unit', 'category'):
                validate_text(material[key])
            for key in ('price', 'quantity'):
                validate_number(material[key])
        operation_ids = set()
        for operation in data['operations']:
            validate_id(operation['id'])
            validate_id(operation['material_id'])
            if operation['id'] in operation_ids:
                raise ValueError("Повторяющийся ID операции")
            operation_ids.add(operation['id'])
            if operation['material_id'] not in material_ids:
                raise ValueError("Операция ссылается на неизвестный материал")
            if operation['kind'] not in ('receipt', 'expense'):
                raise ValueError("Неизвестный вид операции")
            validate_number(operation['quantity'], positive=True)
            date.fromisoformat(operation['date'])
            if (type(operation['cancelled']) is not bool
                    or not isinstance(operation['note'], str)):
                raise ValueError("Некорректные поля операции")
    except (KeyError, TypeError, OverflowError) as error:
        raise ValueError("Некорректная структура файла данных") from error


def load_data(path: Path = DATA_PATH) -> dict:
    """Загружает JSON; при отсутствии файла возвращает пустые коллекции."""
    try:
        with Path(path).open(encoding='utf-8') as stream:
            data = json.load(stream)
    except FileNotFoundError:
        return {'materials': [], 'operations': []}
    validate_data(data)
    return data


def save_data(data: dict, path: Path = DATA_PATH) -> None:
    """Заменяет файл целиком после успешной записи временного файла."""
    validate_data(data)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with NamedTemporaryFile(
            mode='w', encoding='utf-8', dir=path.parent,
            prefix=path.name, suffix='.tmp', delete=False,
        ) as stream:
            temporary = Path(stream.name)
            json.dump(
                data, stream, ensure_ascii=False, indent=2, allow_nan=False,
            )
            stream.write('\n')
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
