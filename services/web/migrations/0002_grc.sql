-- 0002_grc.sql — risk register, incidents, vendors
CREATE TABLE IF NOT EXISTS risks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    likelihood  INTEGER NOT NULL CHECK (likelihood BETWEEN 1 AND 5),
    impact      INTEGER NOT NULL CHECK (impact BETWEEN 1 AND 5),
    framework   TEXT,
    article     TEXT,
    treatment   TEXT,
    status      TEXT NOT NULL DEFAULT 'open',
    owner_id    INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS incidents (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    title           TEXT NOT NULL,
    severity        TEXT NOT NULL DEFAULT 'Medium',
    type            TEXT NOT NULL DEFAULT 'ICT_INCIDENT',
    frameworks      TEXT,
    status          TEXT NOT NULL DEFAULT 'open',
    dora_deadline   DATETIME,
    nis2_deadline   DATETIME,
    owner_id        INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS vendors (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL UNIQUE,
    criticality     TEXT NOT NULL DEFAULT 'Medium',
    dora_art28      INTEGER NOT NULL DEFAULT 0,
    services        TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);
