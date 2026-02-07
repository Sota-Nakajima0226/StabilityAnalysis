from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
import sys
import json


sys.path.append(str(Path(__file__).resolve().parent.parent))
from sqlite.db_connection import conn
from sqlite.entities import (
    Moduli9d,
    Moduli8d,
    MasslessSolution9d,
    Coset8d,
    JoinedModuli8d,
)


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


def select_joined_moduli_8d(
    conditions: Optional[Dict[str, Any]] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> List[JoinedModuli8d]:
    cur = conn.cursor()
    sql = """
    SELECT 
        m8.id,
        m9.a9,
        m9.g9,
        m8.delta
    FROM moduli_8d AS m8
    JOIN moduli_9d AS m9
    ON m9.id = m8.moduli_9d_id
    """

    params = []
    if conditions:
        where_clauses = []
        for col, value in conditions.items():
            where_clauses.append(f"m8.{col} = ?")
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
        entity = JoinedModuli8d(
            id=row[0], a9=json.loads(row[1]), g9=row[2], delta=json.loads(row[3])
        )
        results.append(entity)
    return results


def get_moduli_8d_ids(conditions: Optional[Dict[str, Any]] = None) -> List[int]:
    cur = conn.cursor()
    sql = """
    SELECT 
        id
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

    cur.execute(sql, params)
    rows = cur.fetchall()

    results = []
    for row in rows:
        results.append(row[0])
    return results


def select_coset_8d(
    conditions: Optional[Dict[str, Any]] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> List[Moduli8d]:
    cur = conn.cursor()
    sql = """
    SELECT 
        id,
        moduli_8d_id,
        massless_solution_9d_id,
        character
    FROM coset_8d
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
        entity = Coset8d(
            id=row[0],
            moduli_8d_id=row[1],
            massless_solution_9d_id=row[2],
            character=row[3],
        )
        results.append(entity)
    return results


def select_coset_8d_with_solutions(
    conditions: Optional[Dict[str, Any]] = None
) -> List[Moduli8d]:
    cur = conn.cursor()
    sql = """
    SELECT 
        ms9.element
    FROM coset_8d AS c8
    JOIN massless_solution_9d AS ms9
    ON ms9.id = c8.massless_solution_9d_id
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
        entity = Coset8d(
            id=row[0],
            moduli_8d_id=row[1],
            massless_solution_9d_id=row[2],
            character=row[3],
        )
        results.append(entity)
    return results


def count_records(table_name: str, where_data: dict | None = None) -> int:
    """
    Count records satisfying the conditions.

    Args:
        table_name (str): table name.
        where_data (dict | None, optional): conditions for records. Defaults to None.

    Returns:
        int: _description_
    """
    sql = f"SELECT COUNT(*) FROM {table_name}"
    values = []

    if where_data:
        where_clause = " AND ".join([f"{col} = ?" for col in where_data.keys()])
        sql += f" WHERE {where_clause}"
        values = list(where_data.values())

    cur = conn.execute(sql, values)
    return cur.fetchone()[0]


def get_massless_states_count_from_coset_8d() -> dict[int, dict[str, int]]:
    sql = """
        SELECT
            moduli_8d_id,
            SUM(character = 0) AS bosons,
            SUM(character = 2) AS fermions
        FROM coset_8d
        GROUP BY moduli_8d_id
    """

    cur = conn.execute(sql)

    result = {}
    for row in cur.fetchall():
        result[row[0]] = {
            "bosons": row[1] or 0,
            "fermions": row[2] or 0,
        }

    return result


##########
# UPDATE
##########
def bulk_update_by_id(table_name: str, update_data_list: list, id_column: str = "id"):
    """
    Execute bulk update.

    Args:
        table_name (str): table name.
        update_data_list (list): update data.
        id_column (str, optional): name of id column. Defaults to "id".
    """
    # Exclude id column from update data
    columns = [k for k in update_data_list[0].keys() if k != id_column]
    # Create SQL statement
    set_clause = ", ".join([f"{col} = ?" for col in columns])
    sql = f"""
        UPDATE {table_name}
        SET {set_clause}
        WHERE {id_column} = ?
    """
    # Create data to update
    values = []
    for row in update_data_list:
        row_values = [row[col] for col in columns]
        row_values.append(row[id_column])
        values.append(tuple(row_values))

    with conn:
        conn.executemany(sql, values)


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
