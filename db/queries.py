"""Execute the named, parameterized statements from sql/queries.sql."""

import sqlite3
from contextlib import closing
from functools import lru_cache

from db.database import BASE_DIR, get_connection


@lru_cache(maxsize=1)
def load_queries():
    queries = {}
    name = None
    lines = []
    source = BASE_DIR / 'sql' / 'queries.sql'
    for line in source.read_text(encoding='utf-8').splitlines():
        if line.startswith('-- name: '):
            if name is not None:
                queries[name] = '\n'.join(lines)
            name = line.removeprefix('-- name: ').strip()
            if name in queries:
                raise ValueError(f'Duplicate SQL query: {name}')
            lines = []
        else:
            lines.append(line)
    if name is not None:
        queries[name] = '\n'.join(lines)
    if not queries or not all(
        sqlite3.complete_statement(query) for query in queries.values()
    ):
        raise ValueError('Incomplete SQL query catalog')
    return queries


def fetch_all(name, parameters=()):
    with closing(get_connection()) as connection:
        return connection.execute(load_queries()[name], parameters).fetchall()


def fetch_one(name, parameters=()):
    with closing(get_connection()) as connection:
        return connection.execute(load_queries()[name], parameters).fetchone()
