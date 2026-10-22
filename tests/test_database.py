"""SQLite schema, import safety and execution of every project query."""

import json
import sqlite3
from contextlib import closing

import pytest

from db import database
from db.database import get_connection, initialize_database
from db.import_json import import_json
from db.queries import fetch_all, fetch_one, load_queries
from materials import Material
from operations import Operation
from storage import save_data


@pytest.fixture
def sql_data(tmp_path, monkeypatch):
    path = tmp_path / 'inventory.sqlite'
    source = tmp_path / 'source'
    monkeypatch.setattr(database, 'DB_PATH', path)
    paint = Material(1, 'Paint', 100, 10, 'l', 'Finish')
    cement = Material(2, 'Cement', 50, 0, 'kg', 'Mix')
    brush = Material(3, 'Brush', 25, 3, 'pcs', 'Finish')
    operations = [
        Operation(1, paint, 'receipt', 5, '2026-10-01'),
        Operation(2, paint, 'expense', 2, '2026-10-02'),
        Operation(3, brush, 'expense', 1, '2026-10-02', '', True),
    ]
    save_data({'materials': [paint, cement, brush], 'operations': operations},
              source)
    import_json(source)
    return path, source


def test_schema_rows_keys_and_repeated_initialization(sql_data):
    path, _ = sql_data
    initialize_database(path)
    with closing(get_connection()) as connection:
        assert connection.execute('PRAGMA foreign_keys').fetchone()[0] == 1
        row = connection.execute('SELECT * FROM materials WHERE id = 1')
        assert isinstance(row.fetchone(), sqlite3.Row)
        keys = connection.execute('PRAGMA foreign_key_list(operations)')
        assert keys.fetchone()['table'] == 'materials'
        result = connection.execute('PRAGMA integrity_check').fetchone()
        assert result[0] == 'ok'
        assert not connection.execute('PRAGMA foreign_key_check').fetchall()
    assert fetch_one('stock_summary')['count'] == 3


def test_import_preserves_snapshot_nulls_and_json(sql_data):
    _, source = sql_data
    before = {p.name: p.read_bytes() for p in source.glob('*.json')}
    assert fetch_one('material_detail', (1,))['quantity'] == 10
    assert fetch_one('operation_detail', (1,))['note'] is None
    assert fetch_one('operation_summary')['cancelled_count'] == 1
    assert before == {p.name: p.read_bytes() for p in source.glob('*.json')}
    with pytest.raises(ValueError, match='not empty'):
        import_json(source)
    assert import_json(source, replace=True) == (3, 3)
    assert fetch_one('stock_summary')['count'] == 3


def test_invalid_json_and_missing_source_do_not_replace_data(sql_data):
    _, source = sql_data
    (source / 'materials.json').write_text('[]', encoding='utf-8')
    with pytest.raises(ValueError):
        import_json(source, replace=True)
    assert fetch_one('stock_summary')['count'] == 3
    (source / 'materials.json').unlink()
    with pytest.raises(FileNotFoundError):
        import_json(source, replace=True)
    assert fetch_one('operation_summary')['operations_count'] == 3


def test_sql_failure_rolls_back_whole_replacement(sql_data):
    _, source = sql_data
    materials_file = source / 'materials.json'
    payload = json.loads(materials_file.read_text('utf-8'))
    payload[0]['id'] = 2 ** 80
    materials_file.write_text(json.dumps(payload), encoding='utf-8')
    (source / 'operations.json').write_text('[]', encoding='utf-8')
    with pytest.raises(OverflowError):
        import_json(source, replace=True)
    assert fetch_one('stock_summary')['count'] == 3
    assert fetch_one('operation_summary')['operations_count'] == 3


def test_missing_database_is_not_created_by_a_read(tmp_path):
    path = tmp_path / 'absent.sqlite'
    with pytest.raises(sqlite3.OperationalError):
        get_connection(path)
    assert not path.exists()


@pytest.mark.parametrize('statement, parameters', [
    ('UPDATE materials SET price = ? WHERE id = 1', (-1,)),
    ('UPDATE materials SET quantity = ? WHERE id = 1', (-1,)),
    ('UPDATE materials SET name = ? WHERE id = 1', (' ',)),
    ('UPDATE materials SET unit = ? WHERE id = 1', ('',)),
    ('UPDATE operations SET material_id = ? WHERE id = 1', (999,)),
    ('UPDATE operations SET quantity = ? WHERE id = 1', (0,)),
    ('UPDATE operations SET kind = ? WHERE id = 1', ('other',)),
    ('UPDATE operations SET cancelled = ? WHERE id = 1', (2,)),
    ('UPDATE operations SET date = ? WHERE id = 1', ('2026-02-30',)),
    ('UPDATE operations SET date = ? WHERE id = 1', ('yesterday',)),
    ('DELETE FROM materials WHERE id = ?', (1,)),
])
def test_database_rejects_invalid_values(sql_data, statement, parameters):
    with closing(get_connection(create=True)) as connection:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(statement, parameters)
        connection.rollback()


def test_every_catalog_query_is_executable(sql_data):
    bindings = {
        'materials_search': ('%Paint%', 1),
        'materials_in_stock': (1,),
        'operations_filter': ('expense', 'expense', '', '', 0, 0),
        'materials_without_expense': (1, '2026-10-02'),
        'frequent_materials': (1,),
        'material_detail': (1,),
        'operation_detail': (1,),
    }
    assert len(load_queries()) == 14
    for name in load_queries():
        result = fetch_all(name, bindings.get(name, ()))
        assert all(isinstance(row, sqlite3.Row) for row in result), name


def test_grouping_left_join_and_having(sql_data):
    categories = fetch_all('category_statistics')
    assert categories[0]['category'] == 'Finish'
    assert categories[0]['materials_count'] == 2
    assert categories[0]['stock_value'] == 1075
    assert categories[0]['average_price'] == 62.5
    activity = {row['id']: row for row in fetch_all('material_activity')}
    assert activity[1]['operations_count'] == 2
    assert activity[1]['received'] == 5
    assert activity[1]['spent'] == 2
    assert activity[2]['operations_count'] == 0
    assert activity[3]['operations_count'] == 0
    assert activity[3]['last_date'] is None
    assert [r['id'] for r in fetch_all('frequent_materials', (1,))] == [1]
    assert not fetch_all('frequent_materials', (2,))


def test_aggregates_join_and_date_search(sql_data):
    assert fetch_one('stock_summary')['total_cost'] == 1075
    summary = fetch_one('operation_summary')
    assert summary['operations_count'] == 3
    assert summary['active_count'] == 2
    assert summary['receipt_value'] == 500
    assert summary['expense_value'] == 200
    assert fetch_one('operation_detail', (2,))['material_name'] == 'Paint'
    assert len(fetch_all('active_operations')) == 2
    available = fetch_all('materials_without_expense', (1, '2026-10-02'))
    assert [row['id'] for row in available] == [3]
    assert [r['id'] for r in fetch_all('materials_in_stock', (4,))] == [1]


def test_empty_aggregates_and_sql_injection(sql_data):
    assert not fetch_all('materials_search', ("%' OR 1=1 --", 0))
    with closing(get_connection(create=True)) as connection:
        connection.execute('DELETE FROM operations')
        connection.execute('DELETE FROM materials')
        connection.commit()
    assert dict(fetch_one('stock_summary')) == {
        'count': 0, 'categories': 0, 'out_of_stock': 0, 'total_cost': 0,
    }
    assert fetch_one('operation_summary')['receipt_value'] == 0
    assert not fetch_all('category_statistics')
    assert not fetch_all('material_activity')
