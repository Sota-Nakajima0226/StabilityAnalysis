from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
from sqlite.db_connection import conn


cur = conn.cursor()


# Define SQL to create tables
sql_create_moduli_9d = """
CREATE TABLE IF NOT EXISTS moduli_9d (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    removed_nodes TEXT NOT NULL,
    a9 TEXT NOT NULL,
    g9 TEXT NOT NULL,
    gauge_group TEXT,
    maximal_enhanced INTEGER,
    cosmological_constant INTEGER,
    is_critical_point INTEGER,
    hessian TEXT,
    type TEXT
);
"""
sql_create_moduli_8d = """
CREATE TABLE IF NOT EXISTS moduli_8d (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    moduli_9d_id INTEGER NOT NULL,
    removed_nodes TEXT NOT NULL,
    delta TEXT NOT NULL,
    gauge_group TEXT,
    maximal_enhanced INTEGER,
    cosmological_constant INTEGER,
    is_critical_point INTEGER,
    hessian TEXT,
    type TEXT,
    FOREIGN KEY (moduli_9d_id)
        REFERENCES moduli_9d(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);
"""
sql_create_massless_solution_9d = """
CREATE TABLE IF NOT EXISTS massless_solution_9d (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    moduli_9d_id INTEGER NOT NULL,
    element TEXT NOT NULL,
    FOREIGN KEY (moduli_9d_id)
        REFERENCES moduli_9d(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);
"""
sql_create_coset_8d = """
CREATE TABLE IF NOT EXISTS coset_8d (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    moduli_8d_id INTEGER NOT NULL,
    massless_solution_9d_id INTEGER NOT NULL,
    character INTEGER NOT NULL,
    FOREIGN KEY (moduli_8d_id)
        REFERENCES moduli_8d(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY (massless_solution_9d_id)
        REFERENCES massless_solution_9d(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);
"""

# Create Tables
cur.execute(sql_create_moduli_9d)
cur.execute(sql_create_moduli_8d)
cur.execute(sql_create_massless_solution_9d)
cur.execute(sql_create_coset_8d)
conn.commit()
