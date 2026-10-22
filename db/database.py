"""Connection and explicit schema initialization for the project database."""

import argparse
import sqlite3
from contextlib import closing
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / 'data' / 'materials.sqlite'
SCHEMA_PATH = BASE_DIR / 'sql' / 'schema.sql'
MAX_ID = 2 ** 63 - 1


def get_connection(database=None, *, create=False):
    """Open a connection; normal reads never create a missing database."""
    path = Path(database if database is not None else DB_PATH).resolve()
    if create:
        path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(path)
    else:
        connection = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute('PRAGMA foreign_keys = ON')
    return connection


def initialize_database(database=None):
    """Create the schema without deleting or replacing existing data."""
    with closing(get_connection(database, create=True)) as connection:
        connection.executescript(SCHEMA_PATH.read_text(encoding='utf-8'))
        connection.commit()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, default=DB_PATH)
    args = parser.parse_args()
    initialize_database(args.database)
    print(f'Database initialized: {args.database.resolve()}')


if __name__ == '__main__':
    main()
