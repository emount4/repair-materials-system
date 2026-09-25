"""Сценарии меню без изменения рабочих данных проекта."""

from main import main
from storage import load_data
from utils import input_number


def test_all_menu_actions_and_reload(tmp_path, monkeypatch, capsys):
    answers = iter([
        '99', '1', '9', '11',
        '2', '', 'Краска', 'ошибка', '-1', '500', '10', 'л', 'Отделка',
        '1', '3', 'КРАС', '4', 'price', '5', 'отделка',
        '6', '1', '12', '6', '1', '2',
        '7', '1', '5', 'Кухня', '8', '1', '3', '',
        '9', '10', '2', '10', '2', '8', '1', '100', '',
        '11', '0',
    ])
    monkeypatch.setattr('builtins.input', lambda prompt: next(answers))
    path = tmp_path / 'data'
    main(path)
    output = capsys.readouterr().out
    assert 'Необходимо докупить: 2' in output
    assert 'Остаток после использования: 8' in output
    assert 'уже отменена' in output
    assert 'Недостаточно материала' in output
    assert 'Стоимость запасов: 7500.00' in output
    data = load_data(path)
    assert data['materials'][0].quantity == 15
    assert data['operations'][1].cancelled is True
    assert data['operations'][0].material is data['materials'][0]
    answers = iter(['1', '0'])
    main(path)
    assert '15 л' in capsys.readouterr().out


def test_numeric_input_retries(monkeypatch):
    answers = iter(['nan', 'inf', '-1', 'текст', '2,5'])
    monkeypatch.setattr('builtins.input', lambda prompt: next(answers))
    assert input_number('Количество: ') == 2.5


def test_bad_file_stops_safely(tmp_path, capsys):
    path = tmp_path / 'data'
    path.mkdir()
    materials_path = path / 'materials.json'
    materials_path.write_text('{broken', encoding='utf-8')
    main(path)
    assert 'Не удалось загрузить данные' in capsys.readouterr().out
    assert materials_path.read_text(encoding='utf-8') == '{broken'


def test_save_failure_rolls_back_memory(tmp_path, monkeypatch, capsys):
    answers = iter(['2', 'Краска', '500', '10', 'л', 'Отделка', '1', '0'])
    monkeypatch.setattr('builtins.input', lambda prompt: next(answers))

    def deny_save(*args):
        raise PermissionError('Нет доступа')

    monkeypatch.setattr('main.save_data', deny_save)
    main(tmp_path / 'data')
    output = capsys.readouterr().out
    assert 'Изменения не применены' in output
    assert 'Материалы не найдены' in output
