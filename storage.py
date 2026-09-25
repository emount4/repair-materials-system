"""Загрузка и атомарное сохранение объектов проекта в JSON."""

import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from materials import Material
from operations import Operation


DATA_DIR = Path(__file__).resolve().parent / 'data'
MATERIALS_FILE = 'materials.json'
OPERATIONS_FILE = 'operations.json'
LEGACY_FILE = 'inventory.json'
DATA_PATH = DATA_DIR


def _split_paths(path: Path) -> tuple[Path, Path, Path]:
    """Вернуть пути новых файлов и старого файла для совместимости."""
    path = Path(path)
    directory = path.parent if path.suffix == '.json' else path
    return (
        directory / MATERIALS_FILE,
        directory / OPERATIONS_FILE,
        directory / LEGACY_FILE,
    )


def _load_list(path: Path) -> list[dict]:
    with path.open(encoding='utf-8') as stream:
        data = json.load(stream)
    if not isinstance(data, list):
        raise ValueError(f"Файл {path.name} должен содержать список")
    return data


def _build_objects(
    material_data: list[dict], operation_data: list[dict],
) -> dict:
    """Преобразовать данные JSON в связанные объекты предметной области."""
    if not isinstance(material_data, list):
        raise ValueError("Файл материалов должен содержать список")
    if not isinstance(operation_data, list):
        raise ValueError("Файл операций должен содержать список")
    materials = [Material.from_data(item) for item in material_data]
    material_ids = [item.id for item in materials]
    if len(material_ids) != len(set(material_ids)):
        raise ValueError("Повторяющийся ID материала")
    operations = [
        Operation.from_data(item, materials) for item in operation_data
    ]
    operation_ids = [item.id for item in operations]
    if len(operation_ids) != len(set(operation_ids)):
        raise ValueError("Повторяющийся ID операции")
    data = {'materials': materials, 'operations': operations}
    validate_data(data)
    return data


def validate_data(data: dict) -> None:
    """Проверить коллекции объектов, идентификаторы и объектные связи."""
    try:
        materials = data['materials']
        operations = data['operations']
    except (KeyError, TypeError) as error:
        raise ValueError("Некорректная структура данных") from error
    if not isinstance(materials, list) or not all(
        isinstance(item, Material) for item in materials
    ):
        raise ValueError("Ожидается список объектов Material")
    if not isinstance(operations, list) or not all(
        isinstance(item, Operation) for item in operations
    ):
        raise ValueError("Ожидается список объектов Operation")
    for material in materials:
        Material.from_data(material.to_data())
    for operation in operations:
        Operation.from_data(operation.to_data(), materials)
    material_ids = [item.id for item in materials]
    operation_ids = [item.id for item in operations]
    if len(material_ids) != len(set(material_ids)):
        raise ValueError("Повторяющийся ID материала")
    if len(operation_ids) != len(set(operation_ids)):
        raise ValueError("Повторяющийся ID операции")
    if any(operation.material not in materials for operation in operations):
        raise ValueError("Операция ссылается на неизвестный материал")


def load_data(path: Path = DATA_PATH) -> dict:
    """Загрузить JSON и создать коллекции связанных объектов."""
    materials_path, operations_path, legacy_path = _split_paths(path)
    if not materials_path.exists() and not operations_path.exists():
        if not legacy_path.exists():
            return {'materials': [], 'operations': []}
        with legacy_path.open(encoding='utf-8') as stream:
            legacy_data = json.load(stream)
        try:
            material_data = legacy_data['materials']
            operation_data = legacy_data['operations']
        except (KeyError, TypeError) as error:
            raise ValueError("Некорректная структура данных") from error
        return _build_objects(material_data, operation_data)
    material_data = (
        _load_list(materials_path) if materials_path.exists() else []
    )
    operation_data = (
        _load_list(operations_path) if operations_path.exists() else []
    )
    return _build_objects(material_data, operation_data)


def save_data(data: dict, path: Path = DATA_PATH) -> None:
    """Преобразовать объекты и заменить JSON-файлы через временные файлы."""
    validate_data(data)
    materials_path, operations_path, _ = _split_paths(path)
    replacements = (
        (materials_path, [item.to_data() for item in data['materials']]),
        (operations_path, [item.to_data() for item in data['operations']]),
    )
    materials_path.parent.mkdir(parents=True, exist_ok=True)
    temporaries = []
    try:
        for file_path, payload in replacements:
            with NamedTemporaryFile(
                mode='w', encoding='utf-8', dir=file_path.parent,
                prefix=file_path.name, suffix='.tmp', delete=False,
            ) as stream:
                temporary = Path(stream.name)
                temporaries.append(temporary)
                json.dump(
                    payload, stream, ensure_ascii=False, indent=2,
                    allow_nan=False,
                )
                stream.write('\n')
        for temporary, (file_path, _) in zip(temporaries, replacements):
            os.replace(temporary, file_path)
    finally:
        for temporary in temporaries:
            if temporary.exists():
                temporary.unlink()
