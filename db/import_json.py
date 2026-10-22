"""Import the existing JSON snapshot without replaying stock movements."""

import argparse
import sqlite3
from contextlib import closing
from pathlib import Path

from db.database import DB_PATH, get_connection, initialize_database
from storage import DATA_DIR, load_data


def import_json(source=DATA_DIR, database=None, *, replace=False):
    """Validate before import; replacement requires an explicit opt-in."""
    source = Path(source)
    for filename in ('materials.json', 'operations.json'):
        if not (source / filename).is_file():
            raise FileNotFoundError(source / filename)
    data = load_data(source)
    material_rows = [
        (m.id, m.name, m.price, m.quantity, m.unit, m.category)
        for m in data['materials']
    ]
    operation_rows = [
        (o.id, o.material.id, o.kind, o.quantity, o.date,
         o.note or None, int(o.cancelled))
        for o in data['operations']
    ]
    initialize_database(database)
    with closing(get_connection(database, create=True)) as connection:
        try:
            connection.execute('BEGIN IMMEDIATE')
            occupied = connection.execute(
                'SELECT (SELECT COUNT(*) FROM materials) '
                '+ (SELECT COUNT(*) FROM operations)',
            ).fetchone()[0]
            if occupied and not replace:
                raise ValueError('Database is not empty; use --replace '
                                 'only to replace its contents with JSON.')
            connection.execute('DELETE FROM operations')
            connection.execute('DELETE FROM materials')
            connection.executemany(
                'INSERT INTO materials '
                '(id, name, price, quantity, unit, category) '
                'VALUES (?, ?, ?, ?, ?, ?)', material_rows,
            )
            connection.executemany(
                'INSERT INTO operations '
                '(id, material_id, kind, quantity, date, note, cancelled) '
                'VALUES (?, ?, ?, ?, ?, ?, ?)', operation_rows,
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
    return len(material_rows), len(operation_rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=DATA_DIR)
    parser.add_argument('--database', type=Path, default=DB_PATH)
    parser.add_argument('--replace', action='store_true')
    args = parser.parse_args()
    try:
        counts = import_json(args.source, args.database, replace=args.replace)
    except (ValueError, OSError, OverflowError, sqlite3.Error) as error:
        parser.exit(1, f'Import failed: {error}\n')
    print(f'Imported materials: {counts[0]}; operations: {counts[1]}')


if __name__ == '__main__':
    main()
