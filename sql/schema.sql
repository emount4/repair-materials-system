PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS materials (
    id INTEGER PRIMARY KEY CHECK (id > 0),
    name TEXT NOT NULL CHECK (length(trim(name)) > 0),
    price REAL NOT NULL CHECK (price >= 0),
    quantity REAL NOT NULL CHECK (quantity >= 0),
    unit TEXT NOT NULL CHECK (length(trim(unit)) > 0),
    category TEXT NOT NULL CHECK (length(trim(category)) > 0)
);

CREATE TABLE IF NOT EXISTS operations (
    id INTEGER PRIMARY KEY CHECK (id > 0),
    material_id INTEGER NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ('receipt', 'expense')),
    quantity REAL NOT NULL CHECK (quantity > 0),
    date TEXT NOT NULL CHECK (
        date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
        AND date(date, '+0 days') IS NOT NULL
        AND date(date, '+0 days') = date
    ),
    note TEXT,
    cancelled INTEGER NOT NULL DEFAULT 0 CHECK (cancelled IN (0, 1)),
    FOREIGN KEY (material_id) REFERENCES materials(id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS operations_material_date
    ON operations(material_id, date, cancelled);
