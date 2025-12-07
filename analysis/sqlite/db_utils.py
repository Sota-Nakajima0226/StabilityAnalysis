from pathlib import Path
from typing import List, Optional, Dict, Any
import sys
import json


sys.path.append(str(Path(__file__).resolve().parent.parent))
from sqlite.db_connection import conn
from sqlite.entities import Moduli9d, Moduli8d, MasslessSolution9d, Coset8d


##########
# INSERT
##########
def bulk_insert_moduli_9d(items: List[Moduli9d]):
    sql = """
    INSERT INTO moduli_9d (
        removed_nodes,
        a9,
        g9,
        gauge_group,
        maximal_enhanced,
        cosmological_constant,
        is_critical_point,
        hessian,
        type
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
    """
    values = [
        (
            item.removed_nodes,
            item.a9,
            item.g9,
            item.gauge_group,
            item.maximal_enhanced,
            item.cosmological_constant,
            item.is_critical_point,
            item.hessian,
            item.type,
        )
        for item in items
    ]

    with conn:
        conn.executemany(sql, values)


def bulk_insert_moduli_8d(items: List[Moduli8d]):
    sql = """
    INSERT INTO moduli_8d (
        removed_nodes,
        moduli_9d_id,
        delta,
        gauge_group,
        maximal_enhanced,
        cosmological_constant,
        is_critical_point,
        hessian,
        type
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
    """
    values = [
        (
            item.removed_nodes,
            item.moduli_9d_id,
            item.delta,
            item.gauge_group,
            item.maximal_enhanced,
            item.cosmological_constant,
            item.is_critical_point,
            item.hessian,
            item.type,
        )
        for item in items
    ]

    with conn:
        conn.executemany(sql, values)


def bulk_insert_massless_solution_9d(items: List[MasslessSolution9d]):
    sql = """
    INSERT INTO massless_solution_9d (
        moduli_9d_id,
        element
    )
    VALUES (?, ?);
    """
    values = [(item.moduli_9d_id, item.element) for item in items]

    with conn:
        conn.executemany(sql, values)


def bulk_insert_coset_8d(items: List[Coset8d]):
    sql = """
    INSERT INTO coset_8d (
        moduli_8d_id,
        massless_solution_9d_id,
        character
    )
    VALUES (?, ?, ?);
    """
    values = [
        (item.moduli_8d_id, item.massless_solution_9d_id, item.character)
        for item in items
    ]

    with conn:
        conn.executemany(sql, values)


##########
# SELECT
##########
def select_moduli_9d(conditions: Optional[Dict[str, Any]] = None) -> List[Moduli9d]:
    cur = conn.cursor()
    sql = """
    SELECT 
        id,
        removed_nodes,
        a9,
        g9,
        gauge_group,
        maximal_enhanced,
        cosmological_constant,
        is_critical_point,
        hessian,
        type
    FROM moduli_9d
    """

    params = []
    if conditions:
        where_clauses = []
        for col, value in conditions.items():
            where_clauses.append(f"{col} = ?")
            params.append(value)
        where_sql = " WHERE " + " AND ".join(where_clauses)
        sql += where_sql

    cur.execute(sql, params)
    rows = cur.fetchall()

    results = []
    for row in rows:
        entity = Moduli9d(
            id=row[0],
            removed_nodes=json.loads(row[1]),
            a9=json.loads(row[2]),
            g9=row[3],
            gauge_group=json.loads(row[4]),
            maximal_enhanced=row[5],
            cosmological_constant=row[6],
            is_critical_point=row[7],
            hessian=json.loads(row[8]) if row[8] else None,
            type=row[9],
        )
        results.append(entity)
    return results


def select_massless_solution_9d(
    conditions: Optional[Dict[str, Any]] = None,
) -> List[MasslessSolution9d]:
    cur = conn.cursor()
    sql = """
    SELECT 
        id,
        moduli_9d_id,
        element
    FROM massless_solution_9d
    """

    params = []
    if conditions:
        where_clauses = []
        for col, value in conditions.items():
            where_clauses.append(f"{col} = ?")
            params.append(value)
        where_sql = " WHERE " + " AND ".join(where_clauses)
        sql += where_sql

    cur.execute(sql, params)
    rows = cur.fetchall()

    results = []
    for row in rows:
        entity = MasslessSolution9d(
            id=row[0], moduli_9d_id=row[1], element=json.loads(row[2])
        )
        results.append(entity)
    return results


def select_moduli_8d(
    conditions: Optional[Dict[str, Any]] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> List[Moduli8d]:
    cur = conn.cursor()
    sql = """
    SELECT 
        id,
        moduli_9d_id,
        removed_nodes,
        delta,
        gauge_group,
        maximal_enhanced,
        cosmological_constant,
        is_critical_point,
        hessian,
        type
    FROM moduli_8d
    """

    params = []
    if conditions:
        where_clauses = []
        for col, value in conditions.items():
            where_clauses.append(f"{col} = ?")
            params.append(value)
        where_sql = " WHERE " + " AND ".join(where_clauses)
        sql += where_sql

    if limit:
        sql += " LIMIT ?"
        params.append(limit)
        if offset:
            sql += " OFFSET ?"
            params.append(offset)

    cur.execute(sql, params)
    rows = cur.fetchall()

    results = []
    for row in rows:
        entity = Moduli8d(
            id=row[0],
            moduli_9d_id=row[1],
            removed_nodes=json.loads(row[2]),
            delta=json.loads(row[3]),
            gauge_group=json.loads(row[4]),
            maximal_enhanced=row[5],
            cosmological_constant=row[6],
            is_critical_point=row[7],
            hessian=json.loads(row[8]) if row[8] else None,
            type=row[9],
        )
        results.append(entity)
    return results


##########
# DELETE
##########
def delete_records(table_name: str, conditions: Dict[str, Any]) -> int:
    """
    Delete records satisfying the conditions from the table.

    Args:
        table_name (str): name of a table.
        conditions (Dict[str, Any]): conditions.
    Returns:
        int: the number of deleted records.
    """
    cur = conn.cursor()

    where_clauses = []
    params = []

    for col, value in conditions.items():
        where_clauses.append(f"{col} = ?")
        params.append(value)

    where_sql = " AND ".join(where_clauses)
    sql = f"DELETE FROM {table_name} WHERE {where_sql}"

    cur.execute(sql, params)
    conn.commit()
    return cur.rowcount
